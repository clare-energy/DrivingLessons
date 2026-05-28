import sqlite3

DB = "lessons.db"

with sqlite3.connect(DB) as conn:
    # Migrations first — add any missing columns before the schema seed runs
    migrations = [
        "ALTER TABLE drivers ADD COLUMN dob TEXT",
        "ALTER TABLE lesson_types ADD COLUMN name TEXT",
    ]
    for sql in migrations:
        try:
            conn.execute(sql)
            conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists

    # Schema: creates tables if missing, seeds/backfills data
    with open("schema.sql") as f:
        conn.executescript(f.read())

print(f"Database initialised: {DB}")
