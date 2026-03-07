import sqlite3

db_path = "data/raw/tfl_arrivals.sqlite"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM raw_arrivals;")
print("rows:", cur.fetchone()[0])

cur.execute("""
SELECT observed_at, stop_id, line_id, direction, time_to_station, expected_arrival
FROM raw_arrivals
ORDER BY id DESC
LIMIT 10;
""")
for row in cur.fetchall():
    print(row)

conn.close()