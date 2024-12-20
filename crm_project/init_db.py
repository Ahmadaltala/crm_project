import sqlite3
import os

print("Current working directory:", os.getcwd())

def init_db():
    conn = sqlite3.connect('sample_auth.db')
    with open('schema.sql') as f:
        conn.executescript(f.read())
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")