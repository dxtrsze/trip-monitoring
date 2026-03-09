#!/usr/bin/env python3
"""
Migration script to add user_id foreign key to manpower table.
Run this script once to add the column.
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
        # Check if column already exists
        cursor.execute("PRAGMA table_info(manpower)")
        columns = [col[1] for col in cursor.fetchall()]

        # Add user_id column if it doesn't exist
        if 'user_id' not in columns:
            print("Adding 'user_id' column to manpower table...")
            cursor.execute("ALTER TABLE manpower ADD COLUMN user_id INTEGER")
        else:
            print("'user_id' column already exists")

        conn.commit()
        print("\nMigration completed successfully!")

    except sqlite3.Error as e:
        conn.rollback()
        print(f"\nError during migration: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
