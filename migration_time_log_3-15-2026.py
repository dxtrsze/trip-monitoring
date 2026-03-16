#!/usr/bin/env python3
"""
Migration script to add payroll and time tracking functionality
Date: March 15, 2026

This script will:
1. Add daily_rate, sched_start, and sched_end columns to the user table
2. Create the time_log table with all required columns
"""

import sqlite3
import os
from datetime import datetime

# Database path
DB_PATH = 'instance/trip_monitoring.db'

def migrate_database():
    """Execute the migration to add payroll columns and time_log table"""

    print("=" * 60)
    print("Migration: Time Log and Payroll Features")
    print("Date: March 15, 2026")
    print("=" * 60)
    print()

    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: Database file not found at {DB_PATH}")
        print("Please ensure the application has been initialized first.")
        return False

    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        print("✅ Successfully connected to database")
        print()

        # Step 1: Add columns to user table
        print("Step 1: Adding payroll columns to user table")
        print("-" * 60)

        new_columns = [
            ('daily_rate', 'REAL'),
            ('sched_start', 'VARCHAR(10)'),
            ('sched_end', 'VARCHAR(10)')
        ]

        for column_name, column_type in new_columns:
            # Check if column already exists
            cursor.execute("PRAGMA table_info(user)")
            columns = [col[1] for col in cursor.fetchall()]

            if column_name in columns:
                print(f"⚠️  Column '{column_name}' already exists in user table - skipping")
            else:
                try:
                    cursor.execute(f"ALTER TABLE user ADD COLUMN {column_name} {column_type}")
                    print(f"✅ Added column '{column_name}' ({column_type}) to user table")
                except sqlite3.OperationalError as e:
                    print(f"❌ Error adding column '{column_name}': {e}")

        print()

        # Step 2: Create time_log table
        print("Step 2: Creating time_log table")
        print("-" * 60)

        # Check if table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='time_log'")
        if cursor.fetchone():
            print("⚠️  Table 'time_log' already exists - skipping creation")
        else:
            create_table_sql = """
            CREATE TABLE time_log (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                time_in DATETIME NOT NULL,
                time_out DATETIME,
                hrs_rendered FLOAT,
                daily_rate FLOAT,
                over_time FLOAT DEFAULT 0.0,
                pay FLOAT,
                ot_pay FLOAT DEFAULT 0.0,
                sched_start VARCHAR(10),
                sched_end VARCHAR(10),
                created_at DATETIME NOT NULL,
                FOREIGN KEY(user_id) REFERENCES user (id)
            )
            """

            cursor.execute(create_table_sql)
            print("✅ Created table 'time_log' with the following columns:")
            print("   - id (INTEGER, PRIMARY KEY)")
            print("   - user_id (INTEGER, FOREIGN KEY -> user.id)")
            print("   - time_in (DATETIME)")
            print("   - time_out (DATETIME)")
            print("   - hrs_rendered (FLOAT)")
            print("   - daily_rate (FLOAT)")
            print("   - over_time (FLOAT, default 0.0)")
            print("   - pay (FLOAT)")
            print("   - ot_pay (FLOAT, default 0.0)")
            print("   - sched_start (VARCHAR(10))")
            print("   - sched_end (VARCHAR(10))")
            print("   - created_at (DATETIME)")

        print()

        # Commit changes
        conn.commit()
        print("=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
        print()

        # Verification
        print("Verification:")
        print("-" * 60)

        # Check user table columns
        cursor.execute("PRAGMA table_info(user)")
        user_columns = [col[1] for col in cursor.fetchall()]
        print(f"✅ User table has {len(user_columns)} columns")

        # Check time_log table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='time_log'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(time_log)")
            timelog_columns = [col[1] for col in cursor.fetchall()]
            print(f"✅ Time_log table exists with {len(timelog_columns)} columns")

        print()

        return True

    except sqlite3.Error as e:
        print(f"❌ SQLite error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        if conn:
            conn.close()
            print("Database connection closed")

if __name__ == "__main__":
    success = migrate_database()

    if success:
        print("✅ Migration completed successfully!")
        print()
        print("Next steps:")
        print("1. Restart your Flask application")
        print("2. The new TimeLog model is now available in models.py")
        print("3. You can start tracking time logs and payroll data")
        exit(0)
    else:
        print("❌ Migration failed!")
        print("Please check the error messages above and try again.")
        exit(1)
