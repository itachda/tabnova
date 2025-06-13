import sqlite3

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # المستخدمين
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            telegram_id INTEGER UNIQUE,
            first_name TEXT,
            referred_by INTEGER,
            is_premium BOOLEAN DEFAULT 0,
            nova INTEGER DEFAULT 0,
            last_click_start TIMESTAMP,
            click_session_end TIMESTAMP,
            last_daily_login DATE,
            login_streak INTEGER DEFAULT 0
        )
    ''')

    # قائمة المتصدرين اليومية
    c.execute('''
        CREATE TABLE IF NOT EXISTS leaderboard (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            first_name TEXT,
            nova INTEGER,
            created_at DATE DEFAULT (DATE('now'))
        )
    ''')

    # المهام المكتملة
    c.execute('''
        CREATE TABLE IF NOT EXISTS completed_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            task_code TEXT
        )
    ''')

    conn.commit()
    conn.close()
