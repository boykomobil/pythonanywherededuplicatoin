import os
from flask import Flask, request, jsonify
from .settings import HUBSPOT_APP_SECRET, DB, DEFAULT_DRY_RUN
from .signature_v3 import verify_v3
from .queue_db import get_conn, enqueue_job

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})

@app.route("/webhooks/hubspot", methods=["POST"])
def hubspot_webhook():
    # Verify signature v3 (enable once your webhook is set)
    if not verify_v3(
        HUBSPOT_APP_SECRET,
        request.headers,
        request.method,
        request.path,
        request.query_string.decode() if request.query_string else "",
        request.get_data(cache=False, as_text=False),
    ):
        return ("invalid signature", 401)

    events = request.get_json(force=True, silent=True) or []
    if isinstance(events, dict):
        events = [events]

    conn = get_conn(DB)
    enqueued = 0
    for ev in events:
        uid = (ev.get("objectId") or ev.get("properties", {}).get("unique_identifier") or "").strip()
        if uid:
            enqueue_job(conn, uid, DEFAULT_DRY_RUN)
            enqueued += 1
    return jsonify({"status":"ok","enqueued":enqueued})
