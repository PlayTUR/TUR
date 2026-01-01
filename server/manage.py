#!/usr/bin/env python3
import sqlite3
import sys
import os
import argparse

# Configuration matching main.py
# Ensure we use the DB in the same folder as this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "tur_server.db")
TBL_USERS = "u_data"

def get_db():
    return sqlite3.connect(DB_PATH)

def wipe_db():
    """Drops the database file to force a reset."""
    if os.path.exists(DB_PATH):
        confirmation = input(f"WARNING: This will PERMANENTLY DELETE '{DB_PATH}'. All users and stats will be lost.\nType 'DELETE' to confirm: ")
        if confirmation == "DELETE":
            os.remove(DB_PATH)
            print("Database deleted. Restart the server to recreate it.")
        else:
            print("Operation cancelled.")
    else:
        print("Database file not found.")

def list_users():
    """Lists all users and their status."""
    if not os.path.exists(DB_PATH):
        print("Database not found.")
        return

    conn = get_db()
    c = conn.cursor()
    try:
        # Check if is_admin column exists
        c.execute(f"SELECT id, uname, is_admin FROM {TBL_USERS}")
        rows = c.fetchall()
        print(f"{'ID':<5} {'USERNAME':<20} {'ROLE':<10}")
        print("-" * 40)
        for r in rows:
            role = "ADMIN" if r[2] == 1 else "USER"
            print(f"{r[0]:<5} {r[1]:<20} {role:<10}")
    except sqlite3.OperationalError:
        print("Error: Could not read user table. Database might be corrupt or old schema.")
    finally:
        conn.close()

def promote_user(username):
    """Promotes a user to ADMIN."""
    if not os.path.exists(DB_PATH):
        print("Database not found.")
        return

    conn = get_db()
    c = conn.cursor()
    
    c.execute(f"UPDATE {TBL_USERS} SET is_admin = 1 WHERE uname = ?", (username,))
    if c.rowcount > 0:
        conn.commit()
        print(f"User '{username}' is now an Admin!")
    else:
        print(f"User '{username}' not found.")
    
    conn.close()

def demote_user(username):
    """Demotes a user to normal status."""
    if not os.path.exists(DB_PATH):
        print("Database not found.")
        return

    conn = get_db()
    c = conn.cursor()
    
    c.execute(f"UPDATE {TBL_USERS} SET is_admin = 0 WHERE uname = ?", (username,))
    if c.rowcount > 0:
        conn.commit()
        print(f"User '{username}' is no longer an Admin.")
    else:
        print(f"User '{username}' not found.")
    
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="TUR Server Management Tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Reset
    subparsers.add_parser("reset", help="Wipe the database completely")
    
    # List
    subparsers.add_parser("list", help="List all users")
    
    # Promote
    promote_parser = subparsers.add_parser("promote", help="Promote a user to Admin")
    promote_parser.add_argument("username", help="Username to promote")

    # Demote
    demote_parser = subparsers.add_parser("demote", help="Demote a user (remove Admin)")
    demote_parser.add_argument("username", help="Username to demote")

    args = parser.parse_args()

    if args.command == "reset":
        wipe_db()
    elif args.command == "list":
        list_users()
    elif args.command == "promote":
        promote_user(args.username)
    elif args.command == "demote":
        demote_user(args.username)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
