import os
import time
import sqlite3
from datetime import datetime
import glob
from flask import Flask, jsonify, request

DB_PATH = os.getenv("DB_PATH", "/data/app.db")

app = Flask(__name__)

# ---------- DB helpers ----------
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# ---------- Routes ----------

@app.get("/")
def hello():
    init_db()
    return jsonify(status="Bonjour tout le monde !")


@app.get("/health")
def health():
    init_db()
    return jsonify(status="ok")

@app.get("/add")
def add():
    init_db()

    msg = request.args.get("message", "hello")
    ts = datetime.utcnow().isoformat() + "Z"

    conn = get_conn()
    conn.execute(
        "INSERT INTO events (ts, message) VALUES (?, ?)",
        (ts, msg)
    )
    conn.commit()
    conn.close()

    return jsonify(
        status="added",
        timestamp=ts,
        message=msg
    )

@app.get("/consultation")
def consultation():
    init_db()

    conn = get_conn()
    cur = conn.execute(
        "SELECT id, ts, message FROM events ORDER BY id DESC LIMIT 50"
    )

    rows = [
        {"id": r[0], "timestamp": r[1], "message": r[2]}
        for r in cur.fetchall()
    ]

    conn.close()

    return jsonify(rows)

@app.get("/count")
def count():
    init_db()

    conn = get_conn()
    cur = conn.execute("SELECT COUNT(*) FROM events")
    n = cur.fetchone()[0]
    conn.close()

    return jsonify(count=n)

@app.get("/status")
def status():
    init_db()

    # 1. On compte le nombre d'événements dans la base
    conn = get_conn()
    cur = conn.execute("SELECT COUNT(*) FROM events")
    count_events = cur.fetchone()[0]
    conn.close()

    # 2. On cherche le dernier fichier de backup
    backup_files = glob.glob("/backup/*.db")
    
    # S'il n'y a pas encore de backup
    if not backup_files:
        return jsonify(
            count=count_events,
            last_backup_file="Aucun backup",
            backup_age_seconds=0
        )
        
    # S'il y a des backups, on prend le plus récent
    latest_backup = max(backup_files, key=os.path.getmtime)
    file_name = os.path.basename(latest_backup)
    
    # On calcule l'âge (heure actuelle - heure de création du fichier)
    file_age = int(time.time() - os.path.getmtime(latest_backup))
    
    # 3. On renvoie le tout au format JSON
    return jsonify(
        count=count_events,
        last_backup_file=file_name,
        backup_age_seconds=file_age
    )

# ---------- Main ----------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080)