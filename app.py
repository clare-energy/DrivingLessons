from flask import Flask, render_template, request, jsonify, send_file
import sqlite3
from contextlib import closing
from datetime import datetime
import csv
import io

app = Flask(__name__)
DB = "lessons.db"


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/lessons")
def get_lessons():
    with closing(get_db()) as conn:
        rows = conn.execute("""
            SELECT l.id, l.driver_id, l.logbook_id, l.lesson_type_id,
                   d.driver_no, d.name,
                   lt.number AS lesson_number,
                   l.lesson_date,
                   lb.logbook_no,
                   (
                     SELECT MAX(lt2.number)
                     FROM lessons l2
                     JOIN lesson_types lt2 ON l2.lesson_type_id = lt2.id
                     WHERE l2.driver_id = l.driver_id
                   ) AS max_lesson
            FROM lessons l
            JOIN drivers d ON l.driver_id = d.id
            JOIN lesson_types lt ON l.lesson_type_id = lt.id
            JOIN logbooks lb ON l.logbook_id = lb.id
            ORDER BY l.lesson_date DESC
        """).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/lessons/<int:id>")
def get_lesson(id):
    with closing(get_db()) as conn:
        row = conn.execute("""
            SELECT l.id, l.driver_id, l.logbook_id, l.lesson_type_id,
                   d.driver_no, d.name,
                   lt.number AS lesson_number,
                   l.lesson_date,
                   lb.logbook_no
            FROM lessons l
            JOIN drivers d ON l.driver_id = d.id
            JOIN lesson_types lt ON l.lesson_type_id = lt.id
            JOIN logbooks lb ON l.logbook_id = lb.id
            WHERE l.id = ?
        """, (id,)).fetchone()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify(dict(row))


@app.route("/lessons", methods=["POST"])
def add_lesson():
    data = request.json or {}
    if not all(k in data for k in ("driver_id", "logbook_id", "lesson_type_id", "lesson_date")):
        return jsonify({"error": "Missing fields"}), 400

    with closing(get_db()) as conn:
        conn.execute("""
            INSERT INTO lessons (driver_id, logbook_id, lesson_type_id, lesson_date, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            data["driver_id"],
            data["logbook_id"],
            data["lesson_type_id"],
            data["lesson_date"],
            datetime.now().isoformat()
        ))
        conn.commit()
    return jsonify({"status": "created"}), 201


@app.route("/lessons/<int:id>", methods=["PUT"])
def update_lesson(id):
    data = request.json or {}
    if not all(k in data for k in ("driver_id", "logbook_id", "lesson_type_id", "lesson_date")):
        return jsonify({"error": "Missing fields"}), 400

    with closing(get_db()) as conn:
        conn.execute("""
            UPDATE lessons
            SET driver_id=?, logbook_id=?, lesson_type_id=?, lesson_date=?
            WHERE id=?
        """, (
            data["driver_id"],
            data["logbook_id"],
            data["lesson_type_id"],
            data["lesson_date"],
            id
        ))
        conn.commit()
    return jsonify({"status": "updated"})


@app.route("/lessons/<int:id>", methods=["DELETE"])
def delete_lesson(id):
    with closing(get_db()) as conn:
        conn.execute("DELETE FROM lessons WHERE id=?", (id,))
        conn.commit()
    return jsonify({"status": "deleted"})


@app.route("/driver_progress/<int:driver_id>")
def driver_progress(driver_id):
    with closing(get_db()) as conn:
        row = conn.execute("""
            SELECT MAX(lt.number) as max_lesson
            FROM lessons l
            JOIN lesson_types lt ON l.lesson_type_id = lt.id
            WHERE l.driver_id = ?
        """, (driver_id,)).fetchone()

    max_lesson = row["max_lesson"] if row["max_lesson"] else 0
    return jsonify({"next_lesson": max_lesson + 1})


@app.route("/drivers")
def get_drivers():
    with closing(get_db()) as conn:
        rows = conn.execute("SELECT * FROM drivers ORDER BY name").fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/drivers", methods=["POST"])
def add_driver():
    data = request.json or {}
    if not data.get("driver_no") or not data.get("name"):
        return jsonify({"error": "driver_no and name required"}), 400

    with closing(get_db()) as conn:
        conn.execute("INSERT INTO drivers (driver_no, name, dob) VALUES (?, ?, ?)",
                     (data["driver_no"], data["name"], data.get("dob") or None))
        conn.commit()
    return jsonify({"status": "created"}), 201


@app.route("/logbooks")
def get_logbooks():
    with closing(get_db()) as conn:
        rows = conn.execute("SELECT * FROM logbooks ORDER BY logbook_no").fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/logbooks", methods=["POST"])
def add_logbook():
    data = request.json or {}
    if not data.get("logbook_no"):
        return jsonify({"error": "logbook_no required"}), 400

    with closing(get_db()) as conn:
        conn.execute("INSERT INTO logbooks (logbook_no) VALUES (?)",
                     (data["logbook_no"],))
        conn.commit()
    return jsonify({"status": "created"}), 201


@app.route("/lesson_types")
def get_types():
    with closing(get_db()) as conn:
        rows = conn.execute("SELECT id, number FROM lesson_types ORDER BY number").fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/export")
def export_csv():
    with closing(get_db()) as conn:
        rows = conn.execute("""
            SELECT d.driver_no, d.name, lt.number, l.lesson_date, lb.logbook_no
            FROM lessons l
            JOIN drivers d ON l.driver_id = d.id
            JOIN lesson_types lt ON l.lesson_type_id = lt.id
            JOIN logbooks lb ON l.logbook_id = lb.id
            ORDER BY d.name, l.lesson_date
        """).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["DriverNo", "Name", "Lesson", "Date", "Logbook"])
    for r in rows:
        writer.writerow([r["driver_no"], r["name"], r["number"], r["lesson_date"], r["logbook_no"]])
    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name="lessons.csv"
    )


@app.route("/import", methods=["POST"])
def import_csv():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    stream = io.StringIO(file.stream.read().decode("utf-8"))
    reader = csv.DictReader(stream)

    imported = 0
    skipped = 0

    with closing(get_db()) as conn:
        for row in reader:
            d = conn.execute("SELECT id FROM drivers WHERE driver_no=?",
                             (row["DriverNo"],)).fetchone()
            if not d:
                cur = conn.execute("INSERT INTO drivers (driver_no, name) VALUES (?, ?)",
                                   (row["DriverNo"], row["Name"]))
                driver_id = cur.lastrowid
            else:
                driver_id = d["id"]

            lb = conn.execute("SELECT id FROM logbooks WHERE logbook_no=?",
                              (row["Logbook"],)).fetchone()
            if not lb:
                cur = conn.execute("INSERT INTO logbooks (logbook_no) VALUES (?)",
                                   (row["Logbook"],))
                logbook_id = cur.lastrowid
            else:
                logbook_id = lb["id"]

            lt = conn.execute("SELECT id FROM lesson_types WHERE number=?",
                              (row["Lesson"],)).fetchone()
            if not lt:
                skipped += 1
                continue

            conn.execute("""
                INSERT INTO lessons (driver_id, logbook_id, lesson_type_id, lesson_date, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (driver_id, logbook_id, lt["id"], row["Date"], datetime.now().isoformat()))
            imported += 1

        conn.commit()

    return jsonify({"status": "imported", "imported": imported, "skipped": skipped})


if __name__ == "__main__":
    app.run(debug=True)
