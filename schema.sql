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
    number  INTEGER NOT NULL UNIQUE,
    name    TEXT
);

CREATE TABLE IF NOT EXISTS lessons (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    driver_id       INTEGER NOT NULL REFERENCES drivers(id),
    logbook_id      INTEGER NOT NULL REFERENCES logbooks(id),
    lesson_type_id  INTEGER NOT NULL REFERENCES lesson_types(id),
    lesson_date     TEXT NOT NULL,
    created_at      TEXT NOT NULL
);

-- Seed the 12 standard EDT lesson types
INSERT OR IGNORE INTO lesson_types (number, name) VALUES
  (1,  'Car Controls, Safety Checks & Legal Requirements'),
  (2,  'Correct Positioning'),
  (3,  'Changing Direction'),
  (4,  'Progression'),
  (5,  'Anticipation and Reaction'),
  (6,  'Night Driving'),
  (7,  'Eco-Friendly Driving'),
  (8,  'Motorway Driving'),
  (9,  'Urban Driving'),
  (10, 'Adverse Weather Conditions'),
  (11, 'Safety Topics & Sharing the Road'),
  (12, 'Post-Test Driving');

-- Backfill names for rows inserted before this column existed
UPDATE lesson_types SET name = CASE number
  WHEN 1  THEN 'Car Controls, Safety Checks & Legal Requirements'
  WHEN 2  THEN 'Correct Positioning'
  WHEN 3  THEN 'Changing Direction'
  WHEN 4  THEN 'Progression'
  WHEN 5  THEN 'Anticipation and Reaction'
  WHEN 6  THEN 'Night Driving'
  WHEN 7  THEN 'Eco-Friendly Driving'
  WHEN 8  THEN 'Motorway Driving'
  WHEN 9  THEN 'Urban Driving'
  WHEN 10 THEN 'Adverse Weather Conditions'
  WHEN 11 THEN 'Safety Topics & Sharing the Road'
  WHEN 12 THEN 'Post-Test Driving'
END WHERE name IS NULL;
