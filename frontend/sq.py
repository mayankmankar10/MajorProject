import sqlite3

db_path = 'c:/manpower_connector/manpower.db'
conn = sqlite3.connect(db_path, timeout=30.0)
conn.execute('PRAGMA busy_timeout = 30000')  # Wait up to 30 seconds

try:
    cursor = conn.cursor()
    cursor.execute("DELETE FROM applications WHERE employee_id = 67")
    deleted = cursor.rowcount
    conn.commit()
    print(f"✅ Deleted {deleted} application(s) for employee 67")
    print("🎉 You can now re-apply to jobs!")
    print("Please refresh the Find Jobs page!")
except Exception as e:
    conn.rollback()
    print(f"❌ Error: {e}")
finally:
    conn.close()
