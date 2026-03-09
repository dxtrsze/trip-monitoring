#!/usr/bin/env python3
"""
Migration script to add branch_name_v2 column to trip_detail table.
This also makes document_number nullable and populates branch_name_v2 from linked Data records.
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
        # Check current schema
        cursor.execute("PRAGMA table_info(trip_detail)")
        columns = {col[1]: col[2] for col in cursor.fetchall()}

        print("Current trip_detail columns:", list(columns.keys()))

        # Step 1: Make document_number nullable if it's NOT NULL
        if 'document_number' in columns and columns['document_number'].upper() == 'TEXT':
            print("\nMaking document_number nullable (SQLite requires recreating table)...")
            # SQLite doesn't support ALTER COLUMN directly, so we need to recreate
            cursor.execute("""
                CREATE TABLE trip_detail_new (
                    id INTEGER PRIMARY KEY,
                    document_number TEXT,
                    branch_name_v2 TEXT NOT NULL DEFAULT '',
                    data_ids TEXT,
                    area TEXT,
                    total_cbm REAL NOT NULL DEFAULT 0.0,
                    total_ordered_qty INTEGER NOT NULL DEFAULT 0,
                    trip_id INTEGER NOT NULL,
                    status TEXT,
                    cancel_reason TEXT,
                    cause_department TEXT,
                    arrive DATETIME,
                    departure DATETIME,
                    reason TEXT,
                    FOREIGN KEY(trip_id) REFERENCES trip (id)
                )
            """)

            # Copy existing data
            cursor.execute("""
                INSERT INTO trip_detail_new
                SELECT id, document_number, '', data_ids, area, total_cbm, total_ordered_qty,
                       trip_id, status, cancel_reason, cause_department, arrive, departure, reason
                FROM trip_detail
            """)

            # Drop old table and rename new one
            cursor.execute("DROP TABLE trip_detail")
            cursor.execute("ALTER TABLE trip_detail_new RENAME TO trip_detail")
            print("Table recreated with nullable document_number")

        # Add branch_name_v2 column if it doesn't exist
        cursor.execute("PRAGMA table_info(trip_detail)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'branch_name_v2' not in columns:
            print("\nAdding 'branch_name_v2' column...")
            cursor.execute("ALTER TABLE trip_detail ADD COLUMN branch_name_v2 TEXT DEFAULT ''")
        else:
            print("\n'branch_name_v2' column already exists")

        # Populate branch_name_v2 from linked Data records
        print("\nPopulating branch_name_v2 from linked Data records...")
        cursor.execute("SELECT id, data_ids FROM trip_detail WHERE data_ids IS NOT NULL AND data_ids != ''")
        trip_details = cursor.fetchall()

        updated_count = 0
        for detail_id, data_ids_str in trip_details:
            if not data_ids_str:
                continue

            # Get the first data_id to find the branch
            data_id_list = data_ids_str.split(',')
            if data_id_list and data_id_list[0]:
                # Query the data table for branch_name_v2
                cursor.execute("""
                    SELECT branch_name_v2, branch_name
                    FROM data
                    WHERE id = ?
                """, (data_id_list[0],))
                result = cursor.fetchone()

                if result:
                    branch_name_v2 = result[0] or result[1] or 'Unknown'
                    cursor.execute("""
                        UPDATE trip_detail
                        SET branch_name_v2 = ?
                        WHERE id = ?
                    """, (branch_name_v2, detail_id))
                    updated_count += 1

        print(f"Updated {updated_count} trip_detail records with branch_name_v2")

        conn.commit()
        print("\n✅ Migration completed successfully!")
        print("\n⚠️  IMPORTANT: After migration, please:")
        print("   1. Test the application thoroughly")
        print("   2. New schedules will be grouped by branch_name_v2")
        print("   3. Old schedules have been migrated with branch names from linked data")

    except sqlite3.Error as e:
        conn.rollback()
        print(f"\n❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
