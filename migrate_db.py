#!/usr/bin/env python3
"""
Migration script to add arrival, departure, and reason columns to trip_detail table.
Run this script once to update the database schema.
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
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(trip_detail)")
        columns = [col[1] for col in cursor.fetchall()]

        # Add arrive column if it doesn't exist
        if 'arrive' not in columns:
            print("Adding 'arrive' column...")
            cursor.execute("ALTER TABLE trip_detail ADD COLUMN arrive DATETIME")
        else:
            print("'arrive' column already exists")

        # Add departure column if it doesn't exist
        if 'departure' not in columns:
            print("Adding 'departure' column...")
            cursor.execute("ALTER TABLE trip_detail ADD COLUMN departure DATETIME")
        else:
            print("'departure' column already exists")

        # Add reason column if it doesn't exist
        if 'reason' not in columns:
            print("Adding 'reason' column...")
            cursor.execute("ALTER TABLE trip_detail ADD COLUMN reason TEXT")
        else:
            print("'reason' column already exists")

        conn.commit()
        print("\nMigration completed successfully!")

    except sqlite3.Error as e:
        conn.rollback()
        print(f"\nError during migration: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
