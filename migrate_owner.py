import sqlite3

conn = sqlite3.connect("sql_app.db")

try:
    conn.execute("""
        ALTER TABLE robot_register
        ADD COLUMN owner_id INTEGER REFERENCES users(id)
    """)
    conn.commit()
    print("Column owner_id added successfully!")
except sqlite3.OperationalError as e:
    print(f"Notice: {e}")
finally:
    conn.close()