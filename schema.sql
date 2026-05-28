-- schema.sql
-- SQLite-compatible. For PostgreSQL:
--   - AUTOINCREMENT -> SERIAL or GENERATED ALWAYS AS IDENTITY
--   - TEXT -> VARCHAR(n) where appropriate

CREATE TABLE IF NOT EXISTS drivers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    driver_no   TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    dob         TEXT
);

CREATE TABLE IF NOT EXISTS logbooks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    logbook_no  TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS lesson_types (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    number  INTEGER NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS lessons (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    driver_id       INTEGER NOT NULL REFERENCES drivers(id),
    logbook_id      INTEGER NOT NULL REFERENCES logbooks(id),
    lesson_type_id  INTEGER NOT NULL REFERENCES lesson_types(id),
    lesson_date     TEXT NOT NULL,
    created_at      TEXT NOT NULL
);

-- Seed the 12 standard lesson types
INSERT OR IGNORE INTO lesson_types (number) VALUES
  (1),(2),(3),(4),(5),(6),(7),(8),(9),(10),(11),(12);
