#!/usr/bin/env python3
"""
Migration script to add 'litters', 'amount', and 'price_per_litter' columns to the odo table.
Run this script to update your existing database.
"""

import sqlite3
import os

def migrate():
    # Get the database path
    db_path = os.path.join('instance', 'trip_monitoring.db')

    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False

    print(f"Migrating database: {db_path}")

    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if columns already exist
        cursor.execute("PRAGMA table_info(odo)")
        columns = [col[1] for col in cursor.fetchall()]

        # Add litters column if it doesn't exist
        if 'litters' not in columns:
            print("Adding 'litters' column to odo table...")
            cursor.execute("ALTER TABLE odo ADD COLUMN litters FLOAT")
            print("✓ Added 'litters' column")
        else:
            print("✓ 'litters' column already exists")

        # Add amount column if it doesn't exist
        if 'amount' not in columns:
            print("Adding 'amount' column to odo table...")
            cursor.execute("ALTER TABLE odo ADD COLUMN amount FLOAT")
            print("✓ Added 'amount' column")
        else:
            print("✓ 'amount' column already exists")

        # Add price_per_litter column if it doesn't exist
        if 'price_per_litter' not in columns:
            print("Adding 'price_per_litter' column to odo table...")
            cursor.execute("ALTER TABLE odo ADD COLUMN price_per_litter FLOAT")
            print("✓ Added 'price_per_litter' column")
        else:
            print("✓ 'price_per_litter' column already exists")

        # Commit changes
        conn.commit()
        print("\nMigration completed successfully!")
        return True

    except sqlite3.Error as e:
        print(f"Error migrating database: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    migrate()
