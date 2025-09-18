import time
from .settings import DB, HUBSPOT_PRIVATE_APP_TOKEN, POLL_INTERVAL_SECONDS, DEFAULT_DRY_RUN
from .queue_db import get_conn, get_one_queued_for_update, mark_working, mark_done, mark_error
from .dedupe_core import run_dedupe

def loop():
    while True:
        conn = get_conn(DB)
        try:
            row = get_one_queued_for_update(conn)
            if not row:
                time.sleep(POLL_INTERVAL_SECONDS)
                continue
            job_id, uid, dry = row["id"], row["unique_identifier"], bool(row["dry_run"])
            mark_working(conn, job_id)
            try:
                run_dedupe(HUBSPOT_PRIVATE_APP_TOKEN, uid, dry or DEFAULT_DRY_RUN)
                mark_done(conn, job_id)
            except Exception as e:
                mark_error(conn, job_id, str(e))
        finally:
            conn.close()

if __name__ == "__main__":
    loop()
