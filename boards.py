from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3
import os
from pathlib import Path
from datetime import date, datetime, timedelta

app = Flask(__name__)

# -----------------------------
# Configuration
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("CBSE_DATA_DIR", str(BASE_DIR / "data"))).expanduser().resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB = DATA_DIR / "cbse_grind.db"

# Change this when the official CBSE board target date is known.
BOARD_TARGET_DATE = "2027-02-15"

SUBJECTS = [
    ("maths", "Mathematics", "📐", "Maths by Shobhit Nirwan", "https://www.youtube.com/@MathsByShobhitNirwan"),
    ("science", "Science", "🔬", "Exphub 10th", "https://www.youtube.com/@exphub10th"),
    ("sst", "Social Science", "🌍", "Digraj Singh Rajput", "https://www.youtube.com/@DigrajSinghRajput214"),
    ("hindi", "Hindi", "🇮🇳", "Hindi Adhyapak", "https://www.youtube.com/@HindiAdhyapak"),
    ("english", "English", "📚", "Dear Sir", "https://www.youtube.com/@DearSir"),
    ("it", "Information Technology", "💻", "Readers Venue", "https://www.youtube.com/@ReadersVenue"),
]

CHAPTERS = {
    "maths": [
        "Real Numbers", "Polynomials", "Pair of Linear Equations in Two Variables",
        "Quadratic Equations", "Arithmetic Progressions", "Triangles", "Coordinate Geometry",
        "Introduction to Trigonometry", "Some Applications of Trigonometry", "Circles",
        "Areas Related to Circles", "Surface Areas and Volumes", "Statistics", "Probability"
    ],
    "science": [
        "Chemical Reactions and Equations", "Acids, Bases and Salts", "Metals and Non-metals",
        "Carbon and Its Compounds", "Life Processes", "Control and Coordination",
        "How do Organisms Reproduce?", "Heredity", "Light – Reflection and Refraction",
        "The Human Eye and the Colourful World", "Electricity", "Magnetic Effects of Electric Current",
        "Our Environment"
    ],
    "sst": [
        "The Rise of Nationalism in Europe", "Nationalism in India", "The Making of a Global World",
        "The Age of Industrialisation", "Print Culture and the Modern World", "Resources and Development",
        "Forest and Wildlife Resources", "Water Resources", "Agriculture", "Manufacturing Industries",
        "Lifelines of National Economy", "Power Sharing", "Federalism", "Gender, Religion and Caste",
        "Political Parties", "Outcomes of Democracy", "Development", "Sectors of the Indian Economy",
        "Money and Credit", "Globalisation and the Indian Economy", "Consumer Rights"
    ],
    "hindi": [
        "Literature - Chapter 1", "Literature - Chapter 2", "Literature - Chapter 3",
        "Literature - Chapter 4", "Literature - Chapter 5", "Literature - Chapter 6",
        "Grammar", "Writing Skills", "Full Literature Revision"
    ],
    "english": [
        "A Letter to God", "Nelson Mandela: Long Walk to Freedom", "Two Stories about Flying",
        "From the Diary of Anne Frank", "Glimpses of India", "Mijbil the Otter",
        "Madam Rides the Bus", "The Sermon at Benares", "The Proposal", "Poems",
        "Grammar", "Writing Skills", "Footprints Without Feet"
    ],
    "it": [
        "Communication Skills-II", "Self-Management Skills-II", "ICT Skills-II",
        "Entrepreneurial Skills-II", "Green Skills-II", "Digital Documentation",
        "Electronic Spreadsheet", "Database Management System", "Web Applications and Security"
    ],
}

STATUSES = ["Not Started", "Learning", "Revised", "PYQ Done", "Completed"]
REVISION_OFFSETS = {1: 1, 2: 3, 3: 7, 4: 14, 5: 30}

# Default timetable is inserted ONLY when the timetable table is empty.
# It is never used to overwrite an existing custom timetable.
TIMETABLE = []
for _day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
    if _day != "Sunday":
        TIMETABLE.append((_day, "08:00", "14:00", "School", "School"))
    TIMETABLE.extend([
        (_day, "06:20", "07:00", "Self Study", "Revision"),
        (_day, "16:00", "17:00", "Self Study", "Revision"),
        (_day, "17:00", "18:00", "Online Class 1", "Next Toppers"),
        (_day, "18:30", "19:40", "Self Study", "DPP / Homework"),
        (_day, "20:00", "21:00", "Online Class 2", "Next Toppers"),
        (_day, "21:30", "22:15", "Revision", "Practice"),
    ])

CSS = r'''
:root{--bg:#0f0f10;--panel:#181819;--panel2:#202021;--line:#343436;--text:#f4f4f5;--muted:#a3a3a8;--soft:#d7d7da}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--text);font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;line-height:1.45}a{color:inherit;text-decoration:none}.wrap{max-width:1120px;margin:auto;padding:18px}.brandbar{padding:16px 18px 10px;border-bottom:1px solid #29292b;background:#101011}.brand{display:block;text-align:center;font-size:25px;font-weight:900;letter-spacing:-.4px}.brand-sub{text-align:center;font-size:12px;color:var(--muted);margin-top:3px}.navwrap{position:sticky;top:0;z-index:20;background:rgba(18,18,19,.97);border-bottom:1px solid var(--line)}.nav{display:flex;gap:7px;align-items:center;overflow-x:auto;padding:9px 18px;scrollbar-width:none}.nav::-webkit-scrollbar{display:none}.nav a{padding:9px 12px;color:#aaaab0;white-space:nowrap;border:1px solid transparent;border-radius:10px;font-weight:650}.nav a:hover{background:#242426;border-color:#414143;color:#fff}.nav a.active{background:#2a2a2c;border-color:#59595d;color:#fff}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:13px}.grid2{display:grid;grid-template-columns:repeat(2,1fr);gap:13px}.card{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:17px}.hero{padding:20px 0}.stat{font-size:28px;font-weight:850;letter-spacing:-.5px}.muted{color:var(--muted)}.small{font-size:13px}.badge{display:inline-block;padding:5px 9px;border:1px solid #454548;border-radius:999px;color:#c6c6ca;font-size:12px}.subject{display:flex;gap:12px;align-items:center}.icon{font-size:28px}.progress{height:8px;background:#303033;border-radius:99px;overflow:hidden;margin:11px 0}.bar{height:100%;background:#ddd}.btnrow{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}.btn{display:inline-block;background:#eee;color:#151515;border:0;border-radius:10px;padding:10px 13px;font-weight:760;cursor:pointer;font:inherit}.btn2{background:#252527;color:#eee;border:1px solid #47474b}.field{margin:10px 0}.field label{display:block;color:#aaaab0;font-size:13px;margin-bottom:6px}input,select,textarea{width:100%;box-sizing:border-box;background:#141416;color:#fff;border:1px solid #3e3e42;border-radius:10px;padding:10px;font:inherit}textarea{resize:vertical}.tablebox{overflow:auto}.table{width:100%;border-collapse:collapse;min-width:650px}.table th,.table td{padding:10px;border-bottom:1px solid #343438;text-align:left;vertical-align:middle}.table th{color:#a8a8ae;font-size:13px}.check{display:flex;gap:10px;align-items:center;padding:10px 0;border-bottom:1px solid #333337}.check input{width:18px}.notice{padding:12px;border:1px solid #444449;border-radius:12px;color:#aaaab0;margin:14px 0;background:#171719}.footer{text-align:center;color:#727277;padding:28px}.pillrow{display:flex;gap:7px;flex-wrap:wrap;margin:12px 0}.pill{display:inline-block;padding:8px 11px;border:1px solid #3e3e42;border-radius:999px;color:#bfc0c5}.pill.active{background:#eee;color:#111;border-color:#eee}.status{font-size:12px;padding:5px 8px;border:1px solid #454549;border-radius:999px;white-space:nowrap}.due{border-color:#777}.overdue{border-color:#8a8a8f;background:#252527}.done{border-color:#777;background:#242426;color:#ddd}.rounds{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}.round{border:1px solid #3c3c40;border-radius:9px;padding:6px 8px;font-size:12px;color:#aaa}.round.done{background:#eee;color:#111;border-color:#eee}.round.today{border-color:#ddd;color:#fff}.round.overdue{border-color:#777;color:#ddd}.kpi{display:flex;justify-content:space-between;gap:10px;align-items:end}.empty{padding:25px 0;text-align:center;color:#888}.revision-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:13px}.revision-card{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:16px}.revision-meta{display:flex;justify-content:space-between;gap:10px;align-items:flex-start}.right{text-align:right}@media(max-width:850px){.grid{grid-template-columns:repeat(2,1fr)}.grid2,.revision-grid{grid-template-columns:1fr}}@media(max-width:500px){.grid{grid-template-columns:1fr 1fr}.wrap{padding:14px}.card{padding:14px}.nav{padding:9px 12px}.brandbar{padding-left:14px;padding-right:14px}.btn{padding:9px 11px}}
'''


def format_time(value):
    try:
        return datetime.strptime(value, "%H:%M").strftime("%I:%M %p").lstrip("0")
    except Exception:
        return value


app.jinja_env.filters["time12"] = format_time


def db():
    conn = sqlite3.connect(DB, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create/migrate schema without deleting user data."""
    conn = db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS subjects(
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            icon TEXT,
            channel_name TEXT,
            channel_url TEXT
        );
        CREATE TABLE IF NOT EXISTS chapters(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id TEXT NOT NULL,
            name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Not Started',
            UNIQUE(subject_id,name),
            FOREIGN KEY(subject_id) REFERENCES subjects(id)
        );
        CREATE TABLE IF NOT EXISTS tasks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_date TEXT NOT NULL,
            title TEXT NOT NULL,
            subject_id TEXT,
            done INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS timetable(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            subject TEXT NOT NULL,
            task TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS notes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS backlog(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            priority TEXT NOT NULL DEFAULT 'Medium'
        );
        CREATE TABLE IF NOT EXISTS revision_rounds(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter_id INTEGER NOT NULL,
            round_no INTEGER NOT NULL,
            due_date TEXT NOT NULL,
            completed_at TEXT,
            UNIQUE(chapter_id,round_no),
            FOREIGN KEY(chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_revision_due ON revision_rounds(due_date);
        CREATE INDEX IF NOT EXISTS idx_revision_chapter ON revision_rounds(chapter_id);
    """)

    # Seed subjects only when missing. Existing progress is preserved.
    existing_subjects = {r["id"] for r in conn.execute("SELECT id FROM subjects").fetchall()}
    for row in SUBJECTS:
        if row[0] not in existing_subjects:
            conn.execute("INSERT INTO subjects(id,name,icon,channel_name,channel_url) VALUES(?,?,?,?,?)", row)
        else:
            # Correct static metadata only; do not touch user progress.
            conn.execute(
                "UPDATE subjects SET name=?,icon=?,channel_name=?,channel_url=? WHERE id=?",
                (row[1], row[2], row[3], row[4], row[0])
            )

    # Add missing chapter definitions without replacing existing status.
    for subject_id, names in CHAPTERS.items():
        for chapter_name in names:
            conn.execute(
                "INSERT OR IGNORE INTO chapters(subject_id,name,status) VALUES(?,?,?)",
                (subject_id, chapter_name, "Not Started")
            )

    # IMPORTANT: timetable is initialized only once if empty.
    # Never delete/reseed it merely because a marker/sample row is absent.
    if conn.execute("SELECT COUNT(*) FROM timetable").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO timetable(day,start_time,end_time,subject,task) VALUES(?,?,?,?,?)",
            TIMETABLE
        )

    # Backfill revision rounds for any chapter that was already Completed.
    # This makes the new system compatible with an older database.
    completed = conn.execute("SELECT id FROM chapters WHERE status='Completed'").fetchall()
    for chapter in completed:
        ensure_revision_rounds(conn, chapter["id"])

    conn.commit()
    conn.close()


def ensure_revision_rounds(conn, chapter_id):
    """Create exactly five rounds for a completed chapter if absent.

    The schedule is anchored to the first time this chapter entered the
    revision system. A stored R1 due date is used as the anchor so repeated
    requests/restarts never shift dates.
    """
    existing = conn.execute(
        "SELECT * FROM revision_rounds WHERE chapter_id=? ORDER BY round_no",
        (chapter_id,)
    ).fetchall()
    if existing:
        return

    # The chapter table does not need a new completion column. For a new
    # completion, use today's date as the completion date/anchor.
    completed_date = date.today()
    for round_no, offset in REVISION_OFFSETS.items():
        due = completed_date + timedelta(days=offset)
        conn.execute(
            "INSERT OR IGNORE INTO revision_rounds(chapter_id,round_no,due_date,completed_at) VALUES(?,?,?,NULL)",
            (chapter_id, round_no, due.isoformat())
        )


def page(title, body, active="", **ctx):
    shell = """<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title }} · CBSE Grind</title><style>""" + CSS + """</style></head>
<body>
<header class="brandbar"><div class="wrap">
<a class="brand" href="{{ url_for('home') }}">🖤 CBSE Grind</a>
<div class="brand-sub">Class 10 · Study Dashboard</div>
</div></header>
<div class="navwrap"><nav><div class="wrap nav" id="mainNav">
<a class="{% if active=='Dashboard' %}active{% endif %}" href="{{ url_for('home') }}">Dashboard</a>
<a class="{% if active=='Subjects' %}active{% endif %}" href="{{ url_for('subjects') }}">Subjects</a>
<a class="{% if active=='Timetable' %}active{% endif %}" href="{{ url_for('timetable') }}">Timetable</a>
<a class="{% if active=='Tracker' %}active{% endif %}" href="{{ url_for('tracker') }}">Tracker</a>
<a class="{% if active=='Revision' %}active{% endif %}" href="{{ url_for('revision') }}">Revision</a>
<a class="{% if active=='Progress' %}active{% endif %}" href="{{ url_for('progress') }}">Progress</a>
<a class="{% if active=='Notes' %}active{% endif %}" href="{{ url_for('notes') }}">Notes</a>
<a class="{% if active=='Backlog' %}active{% endif %}" href="{{ url_for('backlog') }}">Backlog</a>
</div></nav></div>
<main class="wrap">""" + body + """</main>
<div class="wrap footer">CBSE Grind · Class 10 study dashboard 📚</div>
<script>document.addEventListener('DOMContentLoaded',function(){var n=document.querySelector('#mainNav a.active');if(n){try{n.scrollIntoView({behavior:'instant',block:'nearest',inline:'center'});}catch(e){}}});</script>
</body></html>"""
    return render_template_string(shell, title=title, active=active, **ctx)


def revision_row_dict(row, today):
    due = date.fromisoformat(row["due_date"])
    completed_at = row["completed_at"]
    if completed_at:
        status = "Completed"
        overdue_days = 0
    elif due < today:
        status = "Overdue"
        overdue_days = (today - due).days
    elif due == today:
        status = "Due Today"
        overdue_days = 0
    else:
        status = "Upcoming"
        overdue_days = 0
    return {
        "id": row["id"],
        "chapter_id": row["chapter_id"],
        "chapter": row["chapter"],
        "subject": row["subject"],
        "subject_id": row["subject_id"],
        "round_no": row["round_no"],
        "round_label": f"R{row['round_no']}",
        "due_date": due.strftime("%d %b %Y"),
        "due_iso": row["due_date"],
        "completed_at": completed_at or "",
        "status": status,
        "overdue_days": overdue_days,
    }


@app.route("/")
@app.route("/dashboard")
def home():
    today = date.today()
    conn = db()
    subjects = conn.execute("SELECT * FROM subjects ORDER BY CASE id WHEN 'maths' THEN 1 WHEN 'science' THEN 2 WHEN 'sst' THEN 3 WHEN 'hindi' THEN 4 WHEN 'english' THEN 5 WHEN 'it' THEN 6 ELSE 99 END").fetchall()
    total = conn.execute("SELECT COUNT(*) FROM chapters").fetchone()[0]
    completed = conn.execute("SELECT COUNT(*) FROM chapters WHERE status='Completed'").fetchone()[0]
    stats_rows = conn.execute("SELECT subject_id,status,COUNT(*) AS n FROM chapters GROUP BY subject_id,status").fetchall()
    stats = {(r["subject_id"], r["status"]): r["n"] for r in stats_rows}
    tasks = conn.execute("SELECT * FROM tasks WHERE task_date=? ORDER BY done,id", (today.isoformat(),)).fetchall()
    due_rows = conn.execute("""
        SELECT r.*, c.name AS chapter, c.subject_id, s.name AS subject
        FROM revision_rounds r
        JOIN chapters c ON c.id=r.chapter_id
        JOIN subjects s ON s.id=c.subject_id
        WHERE r.due_date <= ? AND r.completed_at IS NULL
        ORDER BY r.due_date, s.id, c.id, r.round_no
        LIMIT 8
    """, (today.isoformat(),)).fetchall()
    due_today = [revision_row_dict(r, today) for r in due_rows]
    conn.close()

    target = datetime.strptime(BOARD_TARGET_DATE, "%Y-%m-%d").date()
    days = max(0, (target - today).days)
    pct = round(completed * 100 / total) if total else 0
    task_done = sum(int(x["done"]) for x in tasks)

    body = """
<div class="hero"><span class="badge">CBSE CLASS 10 · BOARD MODE</span><h1>Stay consistent. Let the progress speak. 🖤</h1><p class="muted">Chapters, daily work, timetable, revision, progress and study channels — in one place.</p></div>
<div class="grid">
<div class="card"><div class="stat">{{ days }}</div><div class="muted small">days to target</div></div>
<div class="card"><div class="stat">{{ pct }}%</div><div class="muted small">chapter completion</div></div>
<div class="card"><div class="stat">{{ completed }}</div><div class="muted small">chapters completed</div></div>
<div class="card"><div class="stat">{{ task_done }} / {{ task_total }}</div><div class="muted small">today's tasks</div></div>
</div>
<div class="btnrow"><a class="btn" href="{{ url_for('tracker') }}">Today's Tracker</a><a class="btn btn2" href="{{ url_for('revision') }}">Open Revision</a></div>
<h2>Subjects</h2>
<div class="grid2">
{% for s in subjects %}
{% set t = stats.get((s.id,'Not Started'),0)+stats.get((s.id,'Learning'),0)+stats.get((s.id,'Revised'),0)+stats.get((s.id,'PYQ Done'),0)+stats.get((s.id,'Completed'),0) %}
{% set d = stats.get((s.id,'Completed'),0) %}
{% set p = ((d/t)*100)|round|int if t else 0 %}
<a class="card" href="{{ url_for('subject_detail', sid=s.id) }}"><div class="subject"><div class="icon">{{ s.icon }}</div><div><h3>{{ s.name }}</h3><div class="small muted">{{ s.channel_name }}</div></div></div><div class="progress"><div class="bar" style="width:{{ p }}%"></div></div><div class="small muted">{{ p }}% completed · {{ t }} chapters</div></a>
{% endfor %}</div>
<h2>Today's Revision</h2>
{% if due_today %}<div class="revision-grid">{% for r in due_today %}<div class="revision-card"><div class="revision-meta"><div><b>{{ r.chapter }}</b><div class="small muted">{{ r.subject }} · {{ r.round_label }}</div></div><span class="status {% if r.status=='Overdue' %}overdue{% else %}due{% endif %}">{{ r.status }}</span></div><p class="small muted">Due {{ r.due_date }}{% if r.status=='Overdue' %} · {{ r.overdue_days }} day{% if r.overdue_days != 1 %}s{% endif %} overdue{% endif %}</p><form method="post" action="{{ url_for('mark_revision', revision_id=r.id) }}"><button class="btn">Mark Revised ✓</button></form></div>{% endfor %}</div>{% else %}<div class="card empty">No revision is due today. Keep the streak going. ✦</div>{% endif %}
<div class="notice">Target date: <b>{{ target }}</b>. Set <code>BOARD_TARGET_DATE</code> to the official target once confirmed.</div>
"""
    return page("Dashboard", body, active="Dashboard", subjects=subjects, stats=stats, pct=pct, completed=completed, days=days, target=BOARD_TARGET_DATE, task_done=task_done, task_total=len(tasks), due_today=due_today)


@app.route("/subjects")
def subjects():
    conn = db()
    subjects = conn.execute("SELECT * FROM subjects ORDER BY rowid").fetchall()
    conn.close()
    body = """
<h1>Subjects</h1><p class="muted">Update chapter status or open the exact study channel.</p>
<div class="grid2">{% for s in subjects %}<div class="card"><div class="subject"><div class="icon">{{ s.icon }}</div><div><h3>{{ s.name }}</h3><div class="small muted">{{ s.channel_name }}</div></div></div><div class="btnrow"><a class="btn btn2" href="{{ url_for('subject_detail', sid=s.id) }}">Open Subject</a><a class="btn" href="{{ s.channel_url }}" target="_blank" rel="noopener">Study Channel ↗</a></div></div>{% endfor %}</div>
"""
    return page("Subjects", body, active="Subjects", subjects=subjects)


@app.route("/subjects/<sid>", methods=["GET", "POST"])
def subject_detail(sid):
    conn = db()
    subject = conn.execute("SELECT * FROM subjects WHERE id=?", (sid,)).fetchone()
    if not subject:
        conn.close()
        return "Subject not found", 404

    if request.method == "POST":
        chapter_id = request.form.get("chapter_id")
        new_status = request.form.get("status")
        if new_status in STATUSES:
            chapter = conn.execute("SELECT id,status FROM chapters WHERE id=? AND subject_id=?", (chapter_id, sid)).fetchone()
            if chapter:
                old_status = chapter["status"]
                conn.execute("UPDATE chapters SET status=? WHERE id=? AND subject_id=?", (new_status, chapter_id, sid))
                # A chapter entering Completed gets exactly five revision rounds.
                if new_status == "Completed" and old_status != "Completed":
                    ensure_revision_rounds(conn, int(chapter_id))
                conn.commit()
        conn.close()
        return redirect(url_for("subject_detail", sid=sid))

    chapters = conn.execute("SELECT * FROM chapters WHERE subject_id=? ORDER BY id", (sid,)).fetchall()
    # Clean dictionaries for the template; no complex Jinja lookup logic.
    chapter_data = [{"id": x["id"], "name": x["name"], "status": x["status"]} for x in chapters]
    conn.close()

    body = """
<div class="btnrow"><a class="btn btn2" href="{{ url_for('subjects') }}">← Subjects</a><a class="btn" href="{{ subject.channel_url }}" target="_blank" rel="noopener">Open {{ subject.channel_name }} ↗</a></div>
<h1>{{ subject.icon }} {{ subject.name }}</h1><p class="muted">Not Started → Learning → Revised → PYQ Done → Completed</p>
<div class="card tablebox"><table class="table"><tr><th>Chapter</th><th>Status</th><th></th></tr>{% for ch in chapters %}<tr><td>{{ ch.name }}</td><td><form method="post" style="display:flex;gap:8px;align-items:center"><input type="hidden" name="chapter_id" value="{{ ch.id }}"><select name="status">{% for st in statuses %}<option {% if ch.status==st %}selected{% endif %}>{{ st }}</option>{% endfor %}</select><button class="btn">Save</button></form></td><td></td></tr>{% endfor %}</table></div>
"""
    return page(subject["name"], body, active="Subjects", subject=subject, chapters=chapter_data, statuses=STATUSES)


@app.route("/tracker", methods=["GET", "POST"])
def tracker():
    today = date.today().isoformat()
    conn = db()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            title = request.form.get("title", "").strip()
            if title:
                conn.execute("INSERT INTO tasks(task_date,title,subject_id) VALUES(?,?,?)", (today, title, request.form.get("subject_id") or None))
        elif action == "toggle":
            conn.execute("UPDATE tasks SET done=1-done WHERE id=? AND task_date=?", (request.form.get("id"), today))
        elif action == "delete":
            conn.execute("DELETE FROM tasks WHERE id=? AND task_date=?", (request.form.get("id"), today))
        conn.commit()
    tasks = conn.execute("SELECT tasks.*,subjects.name AS subject_name FROM tasks LEFT JOIN subjects ON subjects.id=tasks.subject_id WHERE task_date=? ORDER BY done,id", (today,)).fetchall()
    subjects = conn.execute("SELECT * FROM subjects ORDER BY rowid").fetchall()
    conn.close()
    total = len(tasks)
    done = sum(int(x["done"]) for x in tasks)
    pct = round(done * 100 / total) if total else 0
    body = """
<h1>Daily Tracker</h1><p class="muted">{{ today }}</p><div class="grid2"><div class="card"><h2>Add Task</h2><form method="post"><input type="hidden" name="action" value="add"><div class="field"><label>Task</label><input name="title" placeholder="e.g. Finish Electricity notes" required></div><div class="field"><label>Subject</label><select name="subject_id"><option value="">General</option>{% for s in subjects %}<option value="{{ s.id }}">{{ s.name }}</option>{% endfor %}</select></div><button class="btn">Add Task</button></form></div><div class="card"><h2>Today</h2><div class="stat">{{ done }} / {{ total }}</div><div class="progress"><div class="bar" style="width:{{ pct }}%"></div></div><div class="muted">{{ pct }}% complete</div></div></div><div class="card" style="margin-top:13px"><h2>Tasks</h2>{% for t in tasks %}<div class="check"><form method="post"><input type="hidden" name="action" value="toggle"><input type="hidden" name="id" value="{{ t.id }}"><input type="checkbox" onchange="this.form.submit()" {% if t.done %}checked{% endif %}></form><div style="flex:1;{% if t.done %}text-decoration:line-through;color:#666{% endif %}">{{ t.title }}{% if t.subject_name %}<div class="small muted">{{ t.subject_name }}</div>{% endif %}</div><form method="post"><input type="hidden" name="action" value="delete"><input type="hidden" name="id" value="{{ t.id }}"><button class="btn btn2">Delete</button></form></div>{% else %}<p class="muted">No tasks yet.</p>{% endfor %}</div>
"""
    return page("Daily Tracker", body, active="Tracker", today=today, tasks=tasks, subjects=subjects, done=done, total=total, pct=pct)


@app.route("/timetable", methods=["GET", "POST"])
def timetable():
    order = {d: i for i, d in enumerate(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], 1)}
    conn = db()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            vals = [request.form.get(k, "").strip() for k in ["day", "start_time", "end_time", "subject", "task"]]
            if all(vals):
                conn.execute("INSERT INTO timetable(day,start_time,end_time,subject,task) VALUES(?,?,?,?,?)", vals)
        elif action == "delete":
            conn.execute("DELETE FROM timetable WHERE id=?", (request.form.get("id"),))
        conn.commit()
    slots = conn.execute("SELECT * FROM timetable").fetchall()
    conn.close()
    slots = sorted(slots, key=lambda x: (order.get(x["day"], 99), x["start_time"], x["id"]))
    body = """
<h1>Timetable</h1><p class="muted">Your timetable is stored in SQLite. It will not be replaced on refresh or restart.</p><div class="card"><h2>Add Slot</h2><form method="post"><input type="hidden" name="action" value="add"><div class="grid"><div class="field"><label>Day</label><select name="day">{% for d in days %}<option>{{ d }}</option>{% endfor %}</select></div><div class="field"><label>Start</label><input type="time" name="start_time" required></div><div class="field"><label>End</label><input type="time" name="end_time" required></div><div class="field"><label>Subject</label><input name="subject" required></div></div><div class="field"><label>What to study</label><input name="task" required></div><button class="btn">Add Slot</button></form></div><div class="card" style="margin-top:13px"><div class="tablebox"><table class="table"><tr><th>Day</th><th>Time</th><th>Subject</th><th>Task</th><th></th></tr>{% for x in slots %}<tr><td>{{ x.day }}</td><td>{{ x.start_time|time12 }} – {{ x.end_time|time12 }}</td><td>{{ x.subject }}</td><td>{{ x.task }}</td><td><div class="btnrow"><a class="btn btn2" href="{{ url_for('timetable_edit', slot_id=x.id) }}">Edit</a><form method="post"><input type="hidden" name="action" value="delete"><input type="hidden" name="id" value="{{ x.id }}"><button class="btn btn2">Delete</button></form></div></td></tr>{% else %}<tr><td colspan="5" class="muted">No timetable slots. Add your own.</td></tr>{% endfor %}</table></div></div>
"""
    return page("Timetable", body, active="Timetable", slots=slots, days=list(order.keys()))


@app.route("/timetable/<int:slot_id>/edit", methods=["GET", "POST"])
def timetable_edit(slot_id):
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    conn = db()
    slot = conn.execute("SELECT * FROM timetable WHERE id=?", (slot_id,)).fetchone()
    if not slot:
        conn.close()
        return "Timetable slot not found", 404
    if request.method == "POST":
        vals = [request.form.get(k, "").strip() for k in ["day", "start_time", "end_time", "subject", "task"]]
        if all(vals) and vals[0] in order:
            conn.execute("UPDATE timetable SET day=?,start_time=?,end_time=?,subject=?,task=? WHERE id=?", (*vals, slot_id))
            conn.commit()
            conn.close()
            return redirect(url_for("timetable"))
    conn.close()
    body = """
<h1>Edit Timetable Slot</h1><div class="card"><form method="post"><div class="grid"><div class="field"><label>Day</label><select name="day">{% for d in days %}<option {% if slot.day==d %}selected{% endif %}>{{ d }}</option>{% endfor %}</select></div><div class="field"><label>Start</label><input type="time" name="start_time" value="{{ slot.start_time }}" required></div><div class="field"><label>End</label><input type="time" name="end_time" value="{{ slot.end_time }}" required></div><div class="field"><label>Subject</label><input name="subject" value="{{ slot.subject }}" required></div></div><div class="field"><label>What to study</label><input name="task" value="{{ slot.task }}" required></div><div class="btnrow"><button class="btn">Save Changes</button><a class="btn btn2" href="{{ url_for('timetable') }}">Cancel</a></div></form></div>
"""
    return page("Edit Timetable", body, active="Timetable", slot=slot, days=order)


@app.route("/revision", methods=["GET"])
def revision():
    """Revision page deliberately uses simple pre-built dictionaries.

    No Jinja namespace hacks, tuple-key lookups, or complex mutations are
    required here. This avoids the previous template-side 500 failure mode.
    """
    filter_name = request.args.get("filter", "due")
    allowed = {"due", "overdue", "upcoming", "completed", "all"}
    if filter_name not in allowed:
        filter_name = "due"

    today = date.today()
    conn = db()
    rows = conn.execute("""
        SELECT r.id, r.chapter_id, r.round_no, r.due_date, r.completed_at,
               c.name AS chapter, c.subject_id, s.name AS subject
        FROM revision_rounds r
        JOIN chapters c ON c.id=r.chapter_id
        JOIN subjects s ON s.id=c.subject_id
        ORDER BY r.due_date, s.id, c.id, r.round_no
    """).fetchall()

    all_items = [revision_row_dict(r, today) for r in rows]
    completed_chapters_rows = conn.execute("""
        SELECT c.id, c.name AS chapter, c.subject_id, s.name AS subject
        FROM chapters c JOIN subjects s ON s.id=c.subject_id
        WHERE c.status='Completed'
        ORDER BY s.id, c.id
    """).fetchall()

    chapter_cards = []
    for c in completed_chapters_rows:
        rounds = [x for x in all_items if x["chapter_id"] == c["id"]]
        done_count = sum(1 for x in rounds if x["status"] == "Completed")
        chapter_cards.append({
            "chapter_id": c["id"],
            "chapter": c["chapter"],
            "subject": c["subject"],
            "rounds": rounds,
            "done_count": done_count,
            "percent": round(done_count * 100 / 5),
        })
    conn.close()

    if filter_name == "due":
        items = [x for x in all_items if x["status"] == "Due Today"]
    elif filter_name == "overdue":
        items = [x for x in all_items if x["status"] == "Overdue"]
    elif filter_name == "upcoming":
        items = [x for x in all_items if x["status"] == "Upcoming"]
    elif filter_name == "completed":
        items = [x for x in all_items if x["status"] == "Completed"]
    else:
        items = all_items

    counts = {
        "due": sum(x["status"] == "Due Today" for x in all_items),
        "overdue": sum(x["status"] == "Overdue" for x in all_items),
        "upcoming": sum(x["status"] == "Upcoming" for x in all_items),
        "completed": sum(x["status"] == "Completed" for x in all_items),
        "all": len(all_items),
    }

    body = """
<h1>Revision</h1><p class="muted">Five spaced revision rounds are created automatically when a chapter becomes Completed.</p>
<div class="pillrow">{% for key,label in [('due','Due Today'),('overdue','Overdue'),('upcoming','Upcoming'),('completed','Completed'),('all','All')] %}<a class="pill {% if filter_name==key %}active{% endif %}" href="{{ url_for('revision', filter=key) }}">{{ label }} · {{ counts[key] }}</a>{% endfor %}</div>
{% if items %}<div class="revision-grid">{% for r in items %}<div class="revision-card"><div class="revision-meta"><div><b>{{ r.chapter }}</b><div class="small muted">{{ r.subject }} · {{ r.round_label }}</div></div><span class="status {% if r.status=='Completed' %}done{% elif r.status=='Overdue' %}overdue{% else %}due{% endif %}">{{ r.status }}</span></div><p class="small muted">Due {{ r.due_date }}{% if r.status=='Overdue' %} · {{ r.overdue_days }} day{% if r.overdue_days != 1 %}s{% endif %} overdue{% endif %}{% if r.completed_at %} · Revised {{ r.completed_at }}{% endif %}</p>{% if r.status != 'Completed' %}<form method="post" action="{{ url_for('mark_revision', revision_id=r.id) }}"><button class="btn">Mark Revised ✓</button></form>{% endif %}</div>{% endfor %}</div>{% else %}<div class="card empty">No revision items in this view.</div>{% endif %}
<h2>Completed Chapters</h2><p class="muted">Revision progress is separate from chapter status.</p>
{% if chapter_cards %}<div class="revision-grid">{% for c in chapter_cards %}<div class="revision-card"><div class="kpi"><div><b>{{ c.chapter }}</b><div class="small muted">{{ c.subject }}</div></div><div class="right"><b>{{ c.done_count }}/5</b><div class="small muted">{{ c.percent }}%</div></div></div><div class="progress"><div class="bar" style="width:{{ c.percent }}%"></div></div><div class="rounds">{% for r in c.rounds %}<span class="round {% if r.status=='Completed' %}done{% elif r.status=='Overdue' %}overdue{% elif r.status=='Due Today' %}today{% endif %}">{{ r.round_label }} · {{ r.due_date }}{% if r.status=='Completed' %} ✓{% endif %}</span>{% endfor %}</div></div>{% endfor %}</div>{% else %}<div class="card empty">No completed chapters yet. Complete a chapter from Subjects and its five revision rounds will appear here.</div>{% endif %}
"""
    return page("Revision", body, active="Revision", items=items, chapter_cards=chapter_cards, counts=counts, filter_name=filter_name)


@app.route("/revision/<int:revision_id>/complete", methods=["POST"])
def mark_revision(revision_id):
    conn = db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    conn.execute("UPDATE revision_rounds SET completed_at=? WHERE id=? AND completed_at IS NULL", (now, revision_id))
    conn.commit()
    conn.close()
    next_url = request.referrer or url_for("revision")
    return redirect(next_url)


@app.route("/progress")
def progress():
    conn = db()
    subjects = conn.execute("SELECT * FROM subjects ORDER BY rowid").fetchall()
    data = []
    for s in subjects:
        total = conn.execute("SELECT COUNT(*) FROM chapters WHERE subject_id=?", (s["id"],)).fetchone()[0]
        completed = conn.execute("SELECT COUNT(*) FROM chapters WHERE subject_id=? AND status='Completed'", (s["id"],)).fetchone()[0]
        revised_stage = conn.execute("SELECT COUNT(*) FROM chapters WHERE subject_id=? AND status IN ('Revised','PYQ Done','Completed')", (s["id"],)).fetchone()[0]
        revision_total = conn.execute("SELECT COUNT(*) FROM revision_rounds r JOIN chapters c ON c.id=r.chapter_id WHERE c.subject_id=?", (s["id"],)).fetchone()[0]
        revision_done = conn.execute("SELECT COUNT(*) FROM revision_rounds r JOIN chapters c ON c.id=r.chapter_id WHERE c.subject_id=? AND r.completed_at IS NOT NULL", (s["id"],)).fetchone()[0]
        data.append({
            "name": s["name"], "icon": s["icon"], "total": total, "completed": completed,
            "revised_stage": revised_stage, "chapter_pct": round(completed * 100 / total) if total else 0,
            "revision_done": revision_done, "revision_total": revision_total,
            "revision_pct": round(revision_done * 100 / revision_total) if revision_total else 0,
        })
    conn.close()
    body = """
<h1>Progress</h1><p class="muted">Chapter completion and revision rounds are tracked separately.</p><div class="grid2">{% for x in data %}<div class="card"><div class="subject"><div class="icon">{{ x.icon }}</div><div><h3>{{ x.name }}</h3><div class="small muted">{{ x.completed }} / {{ x.total }} chapters completed</div></div></div><div class="progress"><div class="bar" style="width:{{ x.chapter_pct }}%"></div></div><div class="small">{{ x.chapter_pct }}% chapter completion · {{ x.revised_stage }} in revised-stage+</div><hr style="border:0;border-top:1px solid #343438;margin:14px 0"><div class="small muted">Revision rounds</div><div class="stat" style="font-size:22px">{{ x.revision_done }} / {{ x.revision_total }}</div><div class="progress"><div class="bar" style="width:{{ x.revision_pct }}%"></div></div><div class="small">{{ x.revision_pct }}% revision progress</div></div>{% endfor %}</div>
"""
    return page("Progress", body, active="Progress", data=data)


@app.route("/notes", methods=["GET", "POST"])
def notes():
    conn = db()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            title = request.form.get("title", "").strip()
            bodytxt = request.form.get("body", "").strip()
            if title and bodytxt:
                conn.execute("INSERT INTO notes(title,body,created_at) VALUES(?,?,?)", (title, bodytxt, datetime.now().strftime("%Y-%m-%d %H:%M")))
        elif action == "delete":
            conn.execute("DELETE FROM notes WHERE id=?", (request.form.get("id"),))
        conn.commit()
    saved = conn.execute("SELECT * FROM notes ORDER BY id DESC").fetchall()
    conn.close()
    body = """
<h1>Notes</h1><div class="grid2"><div class="card"><h2>New Note</h2><form method="post"><input type="hidden" name="action" value="add"><div class="field"><label>Title</label><input name="title" required></div><div class="field"><label>Note</label><textarea name="body" rows="8" required></textarea></div><button class="btn">Save Note</button></form></div><div class="card"><h2>Saved Notes</h2>{% for n in saved %}<div style="padding:12px 0;border-bottom:1px solid #28282b"><b>{{ n.title }}</b><div class="small muted">{{ n.created_at }}</div><p style="white-space:pre-wrap">{{ n.body }}</p><form method="post"><input type="hidden" name="action" value="delete"><input type="hidden" name="id" value="{{ n.id }}"><button class="btn btn2">Delete</button></form></div>{% else %}<p class="muted">No notes saved yet.</p>{% endfor %}</div></div>
"""
    return page("Notes", body, active="Notes", saved=saved)


@app.route("/backlog", methods=["GET", "POST"])
def backlog():
    conn = db()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            subject = request.form.get("subject", "").strip()
            topic = request.form.get("topic", "").strip()
            priority = request.form.get("priority", "Medium")
            if subject and topic and priority in {"High", "Medium", "Low"}:
                conn.execute("INSERT INTO backlog(subject,topic,priority) VALUES(?,?,?)", (subject, topic, priority))
        elif action == "toggle":
            bid = request.form.get("id")
            row = conn.execute("SELECT status FROM backlog WHERE id=?", (bid,)).fetchone()
            if row:
                conn.execute("UPDATE backlog SET status=? WHERE id=?", ("Done" if row["status"] == "Pending" else "Pending", bid))
        elif action == "delete":
            conn.execute("DELETE FROM backlog WHERE id=?", (request.form.get("id"),))
        conn.commit()
    items = conn.execute("SELECT * FROM backlog ORDER BY CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END,id").fetchall()
    conn.close()
    pending = sum(x["status"] == "Pending" for x in items)
    done = sum(x["status"] == "Done" for x in items)
    body = """
<h1>Backlog</h1><p class="muted">Track pending classes, lectures, chapters or study work.</p><div class="grid2"><div class="card"><h2>Add Backlog</h2><form method="post"><input type="hidden" name="action" value="add"><div class="field"><label>Subject</label><input name="subject" placeholder="e.g. Science" required></div><div class="field"><label>Backlog Topic / Class</label><input name="topic" placeholder="e.g. Electricity Class 4" required></div><div class="field"><label>Priority</label><select name="priority"><option>High</option><option selected>Medium</option><option>Low</option></select></div><button class="btn">Add to Backlog</button></form></div><div class="card"><h2>Backlog Summary</h2><div class="stat">{{ pending }} pending</div><p class="muted">{{ done }} completed · {{ total }} total</p></div></div><div class="card" style="margin-top:13px"><h2>Your Backlog</h2><div class="tablebox"><table class="table"><tr><th>Subject</th><th>Topic / Class</th><th>Priority</th><th>Status</th><th></th></tr>{% for x in items %}<tr><td>{{ x.subject }}</td><td>{{ x.topic }}</td><td><span class="badge">{{ x.priority }}</span></td><td>{{ x.status }}</td><td><div class="btnrow"><form method="post"><input type="hidden" name="action" value="toggle"><input type="hidden" name="id" value="{{ x.id }}"><button class="btn">{% if x.status=='Pending' %}Done{% else %}Pending{% endif %}</button></form><form method="post"><input type="hidden" name="action" value="delete"><input type="hidden" name="id" value="{{ x.id }}"><button class="btn btn2">Delete</button></form></div></td></tr>{% else %}<tr><td colspan="5" class="muted">No backlog yet. Add your pending work here.</td></tr>{% endfor %}</table></div></div>
"""
    return page("Backlog", body, active="Backlog", items=items, pending=pending, done=done, total=len(items))


# Initialize once at process startup, never on every request.
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
