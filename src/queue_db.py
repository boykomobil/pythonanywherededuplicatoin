import pymysql
from typing import Optional, Tuple, Any, Dict

def get_conn(cfg: Dict[str, str]):
    return pymysql.connect(
        host=cfg["host"], user=cfg["user"], password=cfg["password"],
        database=cfg["database"], autocommit=True, cursorclass=pymysql.cursors.DictCursor
    )

def enqueue_job(conn, unique_identifier: str, dry_run: bool):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO jobs (unique_identifier, dry_run) VALUES (%s, %s)",
            (unique_identifier, int(dry_run)),
        )

def get_one_queued_for_update(conn) -> Optional[Dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, unique_identifier, dry_run FROM jobs "
            "WHERE status='queued' ORDER BY id LIMIT 1 FOR UPDATE"
        )
        return cur.fetchone()

def mark_working(conn, job_id: int):
    with conn.cursor() as cur:
        cur.execute("UPDATE jobs SET status='working', attempts=attempts+1 WHERE id=%s", (job_id,))

def mark_done(conn, job_id: int, initial_found_record_ids: str = None, new_merged_record_id: str = None, merge_count: int = 0):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE jobs SET status='done', last_error=NULL, initial_found_record_ids=%s, new_merged_record_id=%s, merge_count=%s WHERE id=%s", 
            (initial_found_record_ids, new_merged_record_id, merge_count, job_id)
        )

def mark_error(conn, job_id: int, msg: str):
    with conn.cursor() as cur:
        cur.execute("UPDATE jobs SET status='error', last_error=%s WHERE id=%s", (msg[:2000], job_id))
