import sqlite3
from contextlib import closing
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_connection() as conn:
        conn.execute('''

            CREATE TABLE IF NOT EXISTS users (

                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL

            )

            ''')

        conn.execute('''

            CREATE TABLE IF NOT EXISTS notes (

                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                title TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                date TEXT NOT NULL

            )

            ''')


def delete_user_by_id(user_id):
    with closing(get_connection()) as conn:
        with conn:
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))


init_db()
