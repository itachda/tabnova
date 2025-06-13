import sqlite3
from datetime import datetime

def update_leaderboard():
    db = sqlite3.connect("database.db")
    c = db.cursor()

    c.execute("DELETE FROM leaderboard")

    c.execute("""
        SELECT telegram_id, first_name, nova
        FROM users
        ORDER BY nova DESC
        LIMIT 100
    """)
    top_users = c.fetchall()

    for user in top_users:
        c.execute("""
            INSERT INTO leaderboard (telegram_id, first_name, nova)
            VALUES (?, ?, ?)
        """, (user[0], user[1], user[2]))

    db.commit()
    db.close()
    print(f"[{datetime.now()}] ✅ تم تحديث المتصدرين")

if __name__ == "__main__":
    update_leaderboard()
