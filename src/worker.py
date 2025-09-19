# /home/boykomobil2000/pythonanywherededuplicatoin/src/worker.py
import time, sys
from .settings import DB, HUBSPOT_PRIVATE_APP_TOKEN, POLL_INTERVAL_SECONDS, DEFAULT_DRY_RUN
from .queue_db import get_conn, get_one_queued_for_update, mark_working, mark_done, mark_error
from .dedupe_core import run_dedupe

def loop():
    print("[worker] starting loop", flush=True)
    while True:
        try:
            conn = get_conn(DB)
            try:
                row = get_one_queued_for_update(conn)
                if not row:
                    time.sleep(POLL_INTERVAL_SECONDS)
                    continue
                job_id, uid, dry = row["id"], row["unique_identifier"], bool(row["dry_run"])
                print(f"[worker] picked job {job_id} (uid={uid}, dry={dry})", flush=True)
                mark_working(conn, job_id)
                try:
                    # Get initial contacts before processing
                    from .dedupe_core import fetch_contacts_by_unique
                    initial_contacts = fetch_contacts_by_unique(HUBSPOT_PRIVATE_APP_TOKEN, uid)
                    initial_found_record_ids = ",".join([c["id"] for c in initial_contacts]) if initial_contacts else ""
                    
                    # Run deduplication
                    result = run_dedupe(HUBSPOT_PRIVATE_APP_TOKEN, uid, dry or DEFAULT_DRY_RUN)
                    
                    # Extract results
                    new_merged_record_id = result.get("primary_id", "")
                    merge_count = result.get("merge_count", 0)
                    
                    # Mark job as done with merge data
                    mark_done(conn, job_id, initial_found_record_ids, new_merged_record_id, merge_count)
                    print(f"[worker] done job {job_id} (found: {len(initial_contacts) if initial_contacts else 0}, merged: {merge_count}, final: {new_merged_record_id})", flush=True)
                except Exception as e:
                    mark_error(conn, job_id, str(e))
                    print(f"[worker] error job {job_id}: {e}", file=sys.stderr, flush=True)
            finally:
                conn.close()
        except Exception as outer:
            print(f"[worker] outer exception: {outer}", file=sys.stderr, flush=True)
            time.sleep(5)

if __name__ == "__main__":
    loop()
