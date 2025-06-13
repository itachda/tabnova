from flask import Flask, render_template, request, jsonify
from database import init_db, sqlite3
from datetime import datetime, timedelta, date

app = Flask(__name__)
init_db()

def get_db():
    return sqlite3.connect("database.db")

@app.route("/")
def index():
    return render_template("index.html")

# تسجيل مستخدم
@app.route("/register", methods=["POST"])
def register_user():
    data = request.json
    telegram_id = data["id"]
    first_name = data["first_name"]
    referred_by = data.get("ref")
    is_premium = int(data.get("is_premium", 0))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO users (telegram_id, first_name, referred_by, nova, is_premium)
            VALUES (?, ?, ?, 0, ?)
        """, (telegram_id, first_name, referred_by, is_premium))
        db.commit()

        if referred_by:
            reward = 1000 if is_premium else 500
            cursor.execute("UPDATE users SET nova = nova + ? WHERE telegram_id = ?", (reward, referred_by))
            db.commit()
        return jsonify({"status": "new"})
    return jsonify({"status": "exists"})

# رصيد المستخدم
@app.route("/get_balance", methods=["POST"])
def get_balance():
    data = request.json
    telegram_id = data["id"]
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT nova FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cursor.fetchone()
    if row:
        return jsonify({"nova": row[0]})
    return jsonify({"error": "User not found"}), 404

# تسجيل دخول يومي
@app.route("/daily_login", methods=["POST"])
def daily_login():
    data = request.json
    telegram_id = data["id"]
    today = date.today()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT last_daily_login, login_streak FROM users WHERE telegram_id=?", (telegram_id,))
    row = cursor.fetchone()
    if not row:
        return jsonify({"error": "user not found"}), 404

    last_login_str, streak = row
    last_login = date.fromisoformat(last_login_str) if last_login_str else None
    if last_login == today:
        return jsonify({"status": "already_logged_in", "streak": streak})
    if last_login and (today - last_login).days == 1:
        streak += 1
    else:
        streak = 1

    reward_table = {1: 50, 2: 100, 3: 200, 4: 400, 5: 700, 6: 1000, 7: 1500}
    reward = reward_table.get(streak, 50)
    cursor.execute("""
        UPDATE users
        SET last_daily_login=?, login_streak=?, nova=nova + ?
        WHERE telegram_id=?
    """, (today.isoformat(), streak, reward, telegram_id))
    db.commit()
    return jsonify({"status": "rewarded", "streak": streak, "reward": reward})

# تحقق من المهام
@app.route("/verify_task", methods=["POST"])
def verify_task():
    data = request.json
    telegram_id = data["id"]
    task_code = data["task"]
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT id FROM completed_tasks WHERE telegram_id = ? AND task_code = ?
    """, (telegram_id, task_code))
    if cursor.fetchone():
        return jsonify({"status": "already_done"})
    cursor.execute("INSERT INTO completed_tasks (telegram_id, task_code) VALUES (?, ?)", (telegram_id, task_code))
    cursor.execute("UPDATE users SET nova = nova + 1000 WHERE telegram_id = ?", (telegram_id,))
    db.commit()
    return jsonify({"status": "rewarded"})

# لوحة المتصدرين
@app.route("/leaderboard", methods=["GET"])
def leaderboard():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT telegram_id, first_name, nova FROM leaderboard ORDER BY nova DESC LIMIT 100")
    rows = cursor.fetchall()
    def mask(name):
        return name[0] + "*" * (len(name) - 2) + name[-1] if len(name) > 2 else "*" * len(name)
    result = []
    for row in rows:
        tid, name, nova = row
        profile_url = f"https://t.me/i/userpic/320/{tid}.jpg"
        result.append({"name": mask(name), "nova": nova, "photo": profile_url})
    return jsonify(result)

# بيانات الحساب الشخصي
@app.route("/my_profile", methods=["POST"])
def my_profile():
    data = request.json
    telegram_id = data["id"]
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT first_name, nova, login_streak, click_session_end
        FROM users WHERE telegram_id = ?
    """, (telegram_id,))
    user = cursor.fetchone()
    if not user:
        return jsonify({"error": "not found"}), 404

    name, nova, streak, click_end = user
    cursor.execute("SELECT COUNT(*) + 1 FROM users WHERE nova > ?", (nova,))
    rank = cursor.fetchone()[0]

    now = datetime.utcnow()
    if click_end:
        click_end_dt = datetime.fromisoformat(click_end)
        if click_end_dt > now:
            click_status = f"نشطة (ينتهي خلال {int((click_end_dt - now).total_seconds() // 60)} دقيقة)"
        else:
            click_status = "⛔ منتهية"
    else:
        click_status = "غير مفعّلة"

    return jsonify({"name": name, "nova": nova, "rank": rank, "streak": streak or 0, "click_status": click_status})

# الإحالة
@app.route("/referrals", methods=["POST"])
def get_referrals():
    data = request.json
    telegram_id = data["id"]
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT first_name FROM users WHERE referred_by = ?", (telegram_id,))
    referred_users = cursor.fetchall()
    def mask(name):
        return name[0] + "*" * (len(name) - 2) + name[-1] if len(name) > 2 else "*" * len(name)
    masked_names = [mask(name[0]) for name in referred_users]
    return jsonify({"count": len(masked_names), "names": masked_names})

# بدء جلسة نقر
@app.route("/start_click", methods=["POST"])
def start_click():
    data = request.json
    telegram_id = data["id"]
    now = datetime.utcnow()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT click_session_end FROM users WHERE telegram_id=?", (telegram_id,))
    row = cursor.fetchone()
    if row and row[0]:
        end_time = datetime.fromisoformat(row[0])
        if now < end_time:
            return jsonify({"status": "locked", "remaining": (end_time - now).total_seconds()})
    session_end = now + timedelta(minutes=20)
    cursor.execute("""
        UPDATE users
        SET last_click_start=?, click_session_end=?
        WHERE telegram_id=?
    """, (now.isoformat(), session_end.isoformat(), telegram_id))
    db.commit()
    return jsonify({"status": "ok", "end": session_end.isoformat()})

# تنفيذ نقرة واحدة
@app.route("/click", methods=["POST"])
def click():
    data = request.json
    telegram_id = data["id"]
    now = datetime.utcnow()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT click_session_end FROM users WHERE telegram_id=?", (telegram_id,))
    row = cursor.fetchone()
    if not row or not row[0]:
        return jsonify({"status": "expired"})
    session_end = datetime.fromisoformat(row[0])
    if now <= session_end:
        cursor.execute("UPDATE users SET nova = nova + 1 WHERE telegram_id=?", (telegram_id,))
        db.commit()
        return jsonify({"status": "clicked"})
    else:
        return jsonify({"status": "expired"})

# Webhook من TonAPI لتفعيل القوارير
@app.route("/ton_webhook", methods=["POST"])
def ton_webhook():
    data = request.json
    comment = data.get("payload", {}).get("comment", "")
    if not comment.startswith("bottle-"):
        return jsonify({"status": "ignored"})

    parts = comment.split("-")
    if len(parts) != 3:
        return jsonify({"status": "invalid"})

    bottle_type = parts[1]
    telegram_id = int(parts[2])

    db = get_db()
    cursor = db.cursor()
    now = datetime.utcnow()

    if bottle_type == "auto":
        session_end = now + timedelta(minutes=20)
        cursor.execute("""
            UPDATE users
            SET click_session_end = ?, last_click_start = ?, nova = nova + 7999
            WHERE telegram_id = ?
        """, (session_end.isoformat(), now.isoformat(), telegram_id))
    elif bottle_type == "instant":
        session_end = now + timedelta(minutes=20)
        cursor.execute("""
            UPDATE users
            SET click_session_end = ?, last_click_start = ?, nova = nova + 500
            WHERE telegram_id = ?
        """, (session_end.isoformat(), now.isoformat(), telegram_id))
    elif bottle_type == "mega":
        cursor.execute("""
            UPDATE users SET nova = nova + 19999 WHERE telegram_id = ?
        """, (telegram_id,))
    db.commit()
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(debug=True)
