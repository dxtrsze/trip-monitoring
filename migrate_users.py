#!/usr/bin/env python3
"""
Migration script to create the users table.
Run this script once to create the table.
"""

import sqlite3
import os

DB_PATH = 'instance/trip_monitoring.db'

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
        if cursor.fetchone():
            print("'user' table already exists")
            return

        # Create the user table
        print("Creating 'user' table...")
        cursor.execute('''
            CREATE TABLE user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                position VARCHAR(50) NOT NULL DEFAULT 'user',
                status VARCHAR(50) NOT NULL DEFAULT 'active'
            )
        ''')

        conn.commit()
        print("\nMigration completed successfully!")
        print("\nIMPORTANT: Run 'python3 create_admin.py' to create the default admin user.")

    except sqlite3.Error as e:
        conn.rollback()
        print(f"\nError during migration: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
