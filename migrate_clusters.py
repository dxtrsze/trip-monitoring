#!/usr/bin/env python3
"""
Migration script to create the clusters table.
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
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cluster'")
        if cursor.fetchone():
            print("'cluster' table already exists")
            return

        # Create the cluster table
        print("Creating 'cluster' table...")
        cursor.execute('''
            CREATE TABLE cluster (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                no VARCHAR(50) NOT NULL,
                weekly_schedule VARCHAR(100),
                delivered_by VARCHAR(100),
                location VARCHAR(100),
                category VARCHAR(100),
                area VARCHAR(100),
                branch VARCHAR(100),
                frequency VARCHAR(100),
                frequency_count VARCHAR(50),
                tl VARCHAR(100),
                delivery_mode VARCHAR(100),
                active_branches TEXT
            )
        ''')

        conn.commit()
        print("\nMigration completed successfully!")

    except sqlite3.Error as e:
        conn.rollback()
        print(f"\nError during migration: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
