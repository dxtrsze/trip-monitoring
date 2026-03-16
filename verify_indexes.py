#!/usr/bin/env python3
"""
Verify Database Indexes
This script checks that all performance indexes are properly created and being used.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text

def verify_indexes():
    """Check that all performance indexes exist and are being used"""

    expected_indexes = {
        'data': ['idx_data_status', 'idx_data_due_date', 'idx_data_document_number', 'idx_data_status_due_date'],
        'schedule': ['idx_schedule_delivery_schedule'],
        'trip_detail': ['idx_trip_detail_departure'],
        'odo': ['idx_odo_datetime', 'idx_odo_plate_number', 'idx_odo_status']
    }

    with app.app_context():
        print("=" * 70)
        print("DATABASE INDEX VERIFICATION")
        print("=" * 70)
        print()

        # Check if indexes exist
        all_good = True
        for table_name, index_list in expected_indexes.items():
            print(f"\n📋 Table: {table_name}")
            print("-" * 70)

            result = db.session.execute(text(
                f"SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='{table_name}' ORDER BY name;"
            ))
            existing_indexes = [row[0] for row in result]
            existing_indexes = [idx for idx in existing_indexes if not idx.startswith('sqlite_')]  # Filter auto indexes

            for expected_index in index_list:
                if expected_index in existing_indexes:
                    print(f"  ✅ {expected_index}")
                else:
                    print(f"  ❌ {expected_index} - MISSING!")
                    all_good = False

        # Test query plans
        print("\n" + "=" * 70)
        print("QUERY PLAN VERIFICATION (Testing if indexes are being used)")
        print("=" * 70)
        print()

        test_queries = [
            ("Filter by status", "SELECT * FROM data WHERE status = 'Not Scheduled' LIMIT 10"),
            ("Filter by document_number", "SELECT * FROM data WHERE document_number = '345709'"),
            ("Filter by delivery_schedule", "SELECT * FROM schedule WHERE delivery_schedule >= '2026-01-01'"),
            ("Filter by departure", "SELECT * FROM trip_detail WHERE departure IS NULL"),
            ("Filter by status + due_date", "SELECT * FROM data WHERE status = 'Not Scheduled' AND due_date >= '2026-01-01'"),
        ]

        for query_name, query_sql in test_queries:
            print(f"🔍 {query_name}:")
            result = db.session.execute(text(f"EXPLAIN QUERY PLAN {query_sql}"))
            plan = result.fetchall()

            # Check if using index
            uses_index = any('USING INDEX' in str(row) for row in plan)

            if uses_index:
                print(f"  ✅ Using index: {plan[0][0]}")
            else:
                print(f"  ⚠️  WARNING: Not using index!")
                print(f"     Plan: {plan}")
            print()

        # Summary
        print("=" * 70)
        if all_good:
            print("✅ ALL INDEXES VERIFIED SUCCESSFULLY!")
        else:
            print("❌ SOME INDEXES ARE MISSING - Re-run add_performance_indexes.py")
        print("=" * 70)

        return all_good

if __name__ == '__main__':
    success = verify_indexes()
    sys.exit(0 if success else 1)
