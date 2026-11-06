import sqlite3
conn = sqlite3.connect("movies.db")
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS movies;")
cur.execute("DROP TABLE IF EXISTS users;")

cur.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    password TEXT DEFAULT '',
    fullname TEXT NOT NULL,
    email TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    profile_pic TEXT
);
""")

cur.execute("""
CREATE TABLE movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    genre TEXT,
    year INTEGER,
    rating REAL,
    poster TEXT,
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")

conn.commit()
conn.close()
print("Database schema reset successfully.")