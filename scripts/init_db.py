import os, sys
from dotenv import load_dotenv
import pymysql

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.settings import DB  # noqa

def main():
    conn = pymysql.connect(
        host=DB["host"], user=DB["user"], password=DB["password"], database=DB["database"], autocommit=True
    )
    with open(os.path.join(os.path.dirname(__file__), "schema.sql"), "r") as f:
        sql = f.read()
    with conn.cursor() as cur:
        for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
            cur.execute(stmt)
    print("Database initialized.")

if __name__ == "__main__":
    load_dotenv()
    main()
