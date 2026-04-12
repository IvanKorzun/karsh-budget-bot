import sqlite3

DB_NAME = "karsh.db"

def init_db():
    """Создает таблицу пользователей, если её нет"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                username TEXT,
                balance REAL DEFAULT 0.0
            )''')
        conn.commit()

def add_or_update_user(name, username, balance=0.0):
    """Добавляет или обновляет пользователя"""
    username = username.replace("@", "").lower() if username else ""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (name, username, balance) 
            VALUES (?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET username=excluded.username
        ''', (name, username, balance))
        conn.commit()

def delete_user(name):
    """Удаляет пользователя по имени"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE name = ?", (name,))
        conn.commit()

def get_all_users():
    """Возвращает список всех пользователей"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, username, balance FROM users")
        return cursor.fetchall()

def update_balance(name, amount):
    """Изменяет баланс пользователя"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance + ? WHERE name = ?", (amount, name))
        conn.commit()