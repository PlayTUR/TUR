
import sqlite3
import sys
import hashlib
import os

DB_PATH = "tur_server.db"

def list_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Debug: List tables
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = c.fetchall()
    print(f"Tables in {DB_PATH}: {[t[0] for t in tables]}")

    c.execute("SELECT id, uname, pw_h FROM u_data")
    rows = c.fetchall()
    print(f"Found {len(rows)} users:")
    for r in rows:
        print(f"ID: {r[0]}, Name: {r[1]}, Hash Preview: {r[2][:10]}...")
    conn.close()

def reset_password(username, new_password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if user exists
    c.execute("SELECT id FROM u_data WHERE uname = ?", (username,))
    row = c.fetchone()
    if not row:
        print(f"User '{username}' not found.")
        conn.close()
        return

    # Hash logic MUST MATCH server/main.py
    # Using bcrypt
    try:
        pw_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt(12)).decode()
        c.execute("UPDATE u_data SET pw_h = ? WHERE id = ?", (pw_hash, row[0]))
        conn.commit()
        print(f"Password for user '{username}' (ID: {row[0]}) has been reset.")
    except Exception as e:
        print(f"Error hashing password: {e}")
    
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            list_users()
        elif sys.argv[1] == "reset" and len(sys.argv) == 4:
            reset_password(sys.argv[2], sys.argv[3])
        else:
            print("Usage:")
            print("  python3 debug_users.py list")
            print("  python3 debug_users.py reset <username> <new_password>")
    else:
        print("Usage:")
        print("  python3 debug_users.py list")
        print("  python3 debug_users.py reset <username> <new_password>")
