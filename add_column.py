
import sqlite3

conn = sqlite3.connect("sql_app.db")

conn.execute("""
    ALTER TABLE robot_sensors
    ADD COLUMN created_at DATETIME
""")

conn.execute("""
    UPDATE robot_sensors
    SET created_at = CURRENT_TIMESTAMP
    WHERE created_at IS NULL
""")

conn.commit()
conn.close()

print("created_at column added successfully!")
