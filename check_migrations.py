#!/usr/bin/env python3
"""
Migration Checker Script
Checks your database schema and tells you which migrations to run.
"""

import sqlite3
import os

DB_PATH = 'instance/trip_monitoring.db'

def check_migrations():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database {DB_PATH} not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 60)
    print("CHECKING DATABASE SCHEMA")
    print("=" * 60)
    print(f"\nDatabase: {DB_PATH}\n")

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"📋 Tables found: {', '.join(tables)}\n")

    migrations_needed = []

    # Check trip_detail table
    print("Checking trip_detail table...")
    if 'trip_detail' in tables:
        cursor.execute("PRAGMA table_info(trip_detail)")
        columns = [col[1] for col in cursor.fetchall()]

        print(f"  Current columns: {', '.join(columns)}")

        # Check for branch_name_v2
        if 'branch_name_v2' not in columns:
            print("  ⚠️  Missing: branch_name_v2")
            migrations_needed.append('migrate_branch_name.py')
        else:
            print("  ✅ branch_name_v2 exists")

        # Check for arrive/departure/reason
        if 'arrive' not in columns:
            print("  ⚠️  Missing: arrive column")
            migrations_needed.append('migrate_db.py')
        else:
            print("  ✅ arrive, departure, reason exist")
    else:
        print("  ❌ trip_detail table not found")

    print()

    # Check odo table
    print("Checking odo table...")
    if 'odo' not in tables:
        print("  ⚠️  Missing: odo table")
        migrations_needed.append('migrate_odo.py')
    else:
        cursor.execute("PRAGMA table_info(odo)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"  ✅ odo table exists with columns: {', '.join(columns)}")

    print()

    # Check user table
    print("Checking user table...")
    if 'user' in tables:
        cursor.execute("PRAGMA table_info(user)")
        columns = [col[1] for col in cursor.fetchall()]

        print(f"  Current columns: {', '.join(columns)}")

        # Check for position and status columns
        if 'position' not in columns or 'status' not in columns:
            print("  ⚠️  Missing: position or status columns")
            migrations_needed.append('migrate_users.py')
        else:
            print("  ✅ position, status columns exist")
    else:
        print("  ❌ user table not found")

    print()

    # Check cluster table
    print("Checking cluster table...")
    if 'cluster' in tables:
        cursor.execute("PRAGMA table_info(cluster)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"  ✅ cluster table exists with columns: {', '.join(columns)}")
    else:
        print("  ⚠️  Missing: cluster table")
        migrations_needed.append('migrate_clusters.py')

    print()
    print("=" * 60)

    if migrations_needed:
        # Remove duplicates while preserving order
        unique_migrations = list(dict.fromkeys(migrations_needed))
        print("MIGRATIONS NEEDED:")
        print("=" * 60)
        for i, migration in enumerate(unique_migrations, 1):
            print(f"{i}. uv run {migration}")
        print()
        print("Run them in the order listed above.")
    else:
        print("✅ All migrations are up to date! No migrations needed.")

    print("=" * 60)
    conn.close()

if __name__ == '__main__':
    check_migrations()
