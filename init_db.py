import sqlite3

DB = "lessons.db"

with sqlite3.connect(DB) as conn:
    with open("schema.sql") as f:
        conn.executescript(f.read())

    # Migrations: add columns that may not exist in older databases
    migrations = [
        "ALTER TABLE drivers ADD COLUMN dob TEXT",
    ]
    for sql in migrations:
        try:
            conn.execute(sql)
            conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists

print(f"Database initialised: {DB}")
