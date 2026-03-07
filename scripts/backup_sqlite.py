# scripts/backup_sqlite.py
import sqlite3
import shutil
from pathlib import Path
import sys
import time

SRC = Path("data/raw/tfl_arrivals.sqlite")
DST = Path("data/raw/tfl_arrivals_final_backup.sqlite")

if len(sys.argv) >= 2:
    DST = Path(sys.argv[1])

print("Source:", SRC)
print("Destination:", DST)
print("Starting safe backup using sqlite3.Connection.backup() ...")

# attempt backup with retries (in case DB is heavily busy)
for attempt in range(1, 6):
    try:
        src_conn = sqlite3.connect(str(SRC), timeout=30)
        dest_conn = sqlite3.connect(str(DST))
        with dest_conn:
            src_conn.backup(dest_conn)
        src_conn.close()
        dest_conn.close()
        print("Backup completed successfully.")
        break
    except Exception as e:
        print(f"Attempt {attempt} failed: {e}")
        if attempt < 5:
            print("Retrying in 5 seconds...")
            time.sleep(5)
        else:
            raise