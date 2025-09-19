from flask import Flask, request, jsonify
from .queue_db import get_conn, enqueue_job
from .settings import DB, DEFAULT_DRY_RUN
from urllib.parse import parse_qs
import json, os

app = Flask(__name__)

@app.route("/webhooks/hubspot", methods=["POST"])
def hubspot_webhook():
    # Optional simple token while sig-v3 is disabled
    # token = os.getenv("INBOUND_TOKEN")
    # if token and request.headers.get("X-Webhook-Token") != token:
    #     return ("forbidden", 403)

    raw = request.get_data(cache=False, as_text=True)
    ct  = request.headers.get("Content-Type", "")
    app.logger.info(f"[webhook] ct={ct!r} raw={raw!r}")

    uids = []

    # Try JSON first
    payload = request.get_json(silent=True)
    app.logger.info(f"[webhook] parsed_json={payload!r}")

    # A) Workflow (JSON dict): {"unique_identifier": "..."} (optionally also hs_object_id)
    if isinstance(payload, dict):
        uid = payload.get("unique_identifier") or payload.get("hs_object_id")
        if uid:
            uids.append(str(uid))

    # B) App Webhooks v3: [{"objectId": 123, ...}, ...]
    if isinstance(payload, list):
        for evt in payload:
            oid = evt.get("objectId")
            if oid is not None:
                uids.append(str(oid))

    # C) If JSON was missing/None, try form-encoded (HubSpot sometimes sends key=value)
    if not uids and raw:
        form = parse_qs(raw)               # e.g. "unique_identifier=abc-123"
        # parse_qs gives lists: {"unique_identifier": ["abc-123"]}
        val = (form.get("unique_identifier") or form.get("hs_object_id") or [None])[0]
        if val:
            uids.append(str(val))

        # Also try decoding JSON string inside the raw (rare but happens)
        if not uids:
            try:
                obj = json.loads(raw)
                if isinstance(obj, dict):
                    val = obj.get("unique_identifier") or obj.get("hs_object_id")
                    if val:
                        uids.append(str(val))
            except Exception:
                pass

    # De-dup within this request
    uids = list(dict.fromkeys(uids))

    enq = 0
    if uids:
        conn = get_conn(DB)
        try:
            for uid in uids:
                enqueue_job(conn, uid, DEFAULT_DRY_RUN)   # relies on jobs.status default 'queued'
                enq += 1
        finally:
            conn.close()

    app.logger.info(f"[webhook] uids={uids} enqueued={enq}")
    return jsonify({"status": "ok", "enqueued": enq})


@app.get("/results/<unique_identifier>")
def get_results(unique_identifier: str):
    """Get deduplication results by unique_identifier"""
    conn = get_conn(DB)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    id, enqueued_at, unique_identifier, status, attempts,
                    initial_found_record_ids, new_merged_record_id, merge_count, last_error
                FROM jobs 
                WHERE unique_identifier = %s 
                ORDER BY enqueued_at DESC 
                LIMIT 1
            """, (unique_identifier,))
            job = cur.fetchone()
            
            if not job:
                return jsonify({"error": "No results found for this unique_identifier"}), 404
            
            # Parse the comma-separated record IDs
            old_record_ids = []
            if job["initial_found_record_ids"]:
                old_record_ids = job["initial_found_record_ids"].split(",")
            
            return jsonify({
                "unique_identifier": job["unique_identifier"],
                "status": job["status"],
                "enqueued_at": job["enqueued_at"].isoformat() if job["enqueued_at"] else None,
                "attempts": job["attempts"],
                "old_record_ids": old_record_ids,
                "new_record_id": job["new_merged_record_id"],
                "merge_count": job["merge_count"],
                "error": job["last_error"]
            })
    finally:
        conn.close()

@app.get("/health")
def health():
    # keep it fast and dependency-free (no DB calls here)
    return jsonify({
        "status": "ok",
        "service": "deduplication-manager",
        "db_host": DB.get("host", "unknown")
    }), 200
