import sqlite3
import json
from datetime import datetime

DB_PATH = "quizforge.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            questions TEXT NOT NULL,
            score TEXT DEFAULT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_flashcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            cards TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()

def create_user(name, email, password):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, password)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def save_quiz(user_id, title, questions):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO saved_quizzes (user_id, title, questions) VALUES (?, ?, ?)",
        (user_id, title, json.dumps(questions))
    )
    conn.commit()
    quiz_id = cursor.lastrowid
    conn.close()
    return quiz_id

def update_quiz_score(quiz_id, score):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE saved_quizzes SET score = ? WHERE id = ?",
        (score, quiz_id)
    )
    conn.commit()
    conn.close()

def get_user_quizzes(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM saved_quizzes WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    )
    quizzes = cursor.fetchall()
    conn.close()
    return quizzes

def get_quiz_by_id(quiz_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM saved_quizzes WHERE id = ?", (quiz_id,))
    quiz = cursor.fetchone()
    conn.close()
    return quiz

def save_flashcards(user_id, title, cards):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO saved_flashcards (user_id, title, cards) VALUES (?, ?, ?)",
        (user_id, title, json.dumps(cards))
    )
    conn.commit()
    fc_id = cursor.lastrowid
    conn.close()
    return fc_id

def get_user_flashcards(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM saved_flashcards WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    )
    cards = cursor.fetchall()
    conn.close()
    return cards

def get_flashcard_by_id(fc_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM saved_flashcards WHERE id = ?", (fc_id,))
    card = cursor.fetchone()
    conn.close()
    return card

def delete_quiz(quiz_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM saved_quizzes WHERE id = ?", (quiz_id,))
    conn.commit()
    conn.close()

def delete_flashcard(fc_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM saved_flashcards WHERE id = ?", (fc_id,))
    conn.commit()
    conn.close()