#!/usr/bin/env python3
"""
Script to delete all data from LCL (Less than Container Load) tables
Deletes: lcl_detail, lcl_summary tables

This script uses SQLAlchemy ORM and is database-agnostic
Compatible with SQLite, PostgreSQL, and other databases

Usage:
    python clear_lcl_data.py
"""

import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import LCLSummary, LCLDetail


def clear_lcl_data():
    """Clear all LCL data using SQLAlchemy ORM"""
    print(f"Starting LCL data cleanup: {datetime.now()}")
    print(f"Database: SQLAlchemy ORM (Database-Agnostic)")

    with app.app_context():
        try:
            # Define tables to clear (in dependency order: details first, then summary)
            tables_to_clear = [
                ('lcl_detail', LCLDetail, 'LCL Detail records'),
                ('lcl_summary', LCLSummary, 'LCL Summary records'),
            ]

            print(f"\nTables to clear: {', '.join([t[0] for t in tables_to_clear])}")

            # Count rows before deletion
            total_rows = 0
            print(f"\n📊 Rows before deletion:")
            for table_name, model_class, description in tables_to_clear:
                count = db.session.query(model_class).count()
                total_rows += count
                print(f"  {table_name}: {count:,} rows ({description})")

            print(f"\n📌 Total rows to delete: {total_rows:,}")

            if total_rows == 0:
                print("\n✅ No LCL data found. Nothing to delete.")
                return True

            # Delete data in order
            print(f"\n🗑️  Deleting data:")

            for table_name, model_class, description in tables_to_clear:
                try:
                    # Use SQLAlchemy ORM to delete all records
                    deleted_count = db.session.query(model_class).delete()
                    db.session.flush()  # Flush to execute without committing yet
                    print(f"  ✓ Cleared {table_name}: {deleted_count:,} rows deleted")

                except Exception as e:
                    print(f"  ✗ Error clearing {table_name}: {e}")
                    raise

            # Verify tables are empty
            print(f"\n🔍 Verifying tables are empty:")
            all_empty = True
            for table_name, model_class, description in tables_to_clear:
                count = db.session.query(model_class).count()
                status = "✓" if count == 0 else "✗"
                print(f"  {table_name}: {count:,} rows {status}")
                if count > 0:
                    all_empty = False

            # Commit the changes
            db.session.commit()

            if all_empty:
                print("\n" + "=" * 60)
                print("✅ LCL data cleanup completed successfully!")
                print(f"✅ Deleted {total_rows:,} total rows")
                print("=" * 60)
                return True
            else:
                print("\n⚠️  Warning: Some tables still contain data")
                return False

        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error during cleanup: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main function with user confirmation"""
    print("=" * 60)
    print("LCL DATA CLEANUP SCRIPT")
    print("=" * 60)
    print("\nThis will DELETE ALL data from:")
    print("  • lcl_detail table")
    print("  • lcl_summary table")
    print("\n⚠️  WARNING: This action cannot be undone!")

    # Check if data exists first
    with app.app_context():
        detail_count = db.session.query(LCLDetail).count()
        summary_count = db.session.query(LCLSummary).count()
        total = detail_count + summary_count

    if total == 0:
        print("\n✅ No LCL data found in database. Nothing to delete.")
        print("\nExiting...")
        return 0

    print(f"\n📊 Current data:")
    print(f"  • LCL Detail: {detail_count:,} records")
    print(f"  • LCL Summary: {summary_count:,} records")
    print(f"  • Total: {total:,} records")

    print("\n" + "-" * 60)
    print("Press Ctrl+C to cancel, or")
    import time

    try:
        for i in range(5, 0, -1):
            print(f"Starting in {i}...", flush=True)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        print("\nExiting...")
        return 1

    print("\nExecuting...\n")
    success = clear_lcl_data()

    if success:
        print("\n✨ You can now upload fresh LCL data.")
        return 0
    else:
        print("\n❌ Cleanup completed with errors")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
