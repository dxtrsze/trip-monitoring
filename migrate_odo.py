#!/usr/bin/env python3
"""
Migration script to create the odo table for odometer readings.
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
        # Check if odo table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='odo'")
        if cursor.fetchone():
            print("❌ 'odo' table already exists")
            return

        # Create odo table
        print("Creating 'odo' table...")
        cursor.execute("""
            CREATE TABLE odo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plate_number TEXT NOT NULL,
                odometer_reading REAL NOT NULL,
                status TEXT NOT NULL,
                datetime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT NOT NULL,
                FOREIGN KEY (plate_number) REFERENCES vehicle (plate_number)
            )
        """)

        # Create indexes for better performance
        cursor.execute("CREATE INDEX idx_odo_plate_number ON odo(plate_number)")
        cursor.execute("CREATE INDEX idx_odo_status ON odo(status)")
        cursor.execute("CREATE INDEX idx_odo_datetime ON odo(datetime)")

        conn.commit()
        print("\n✅ Migration completed successfully!")
        print("\nThe 'odo' table has been created with the following columns:")
        print("  - id (primary key)")
        print("  - plate_number (foreign key to vehicle)")
        print("  - odometer_reading")
        print("  - status ('start odo', 'refill odo', 'end odo')")
        print("  - datetime")
        print("  - created_by")

    except sqlite3.Error as e:
        conn.rollback()
        print(f"\n❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
