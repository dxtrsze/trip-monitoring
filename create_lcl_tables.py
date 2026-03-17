#!/usr/bin/env python3
"""
Migration script to create LCL (Less than Container Load) tables.

This script creates:
- lcl_summary table: Stores aggregated summary data by posting date and branch
- lcl_detail table: Stores detailed serialized LCL records

Run this script to add the new tables to your existing database:
    python create_lcl_tables.py
"""

import sys
import os
from app import app, db
from models import LCLSummary, LCLDetail

def migrate():
    """Create LCL tables in the database."""
    with app.app_context():
        print("Starting LCL table migration...")

        try:
            # Create all tables (this will only create new tables, not modify existing ones)
            print("Creating LCL tables...")
            db.create_all()

            print("\n✅ Migration completed successfully!")
            print("\nCreated/verified tables:")
            print("  - lcl_summary")
            print("  - lcl_detail")

            # Verify tables were created
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()

            if 'lcl_summary' in tables and 'lcl_detail' in tables:
                print("\n✅ Verified: Both LCL tables exist in database")
            else:
                print("\n⚠️  Warning: Could not verify table creation")

            print("\nTable structure:")
            print("\nlcl_summary:")
            print("  - posting_date: Date (NOT NULL)")
            print("  - company: String(100) [default='FINDEN']")
            print("  - dept: String(100) [default='LOGISTICS']")
            print("  - branch_name: String(100) (NOT NULL)")
            print("  - tot_qty: Integer [default=0]")
            print("  - tot_cbm: Float [default=0.0]")
            print("  - created_at: DateTime")
            print("  - updated_at: DateTime")
            print("  - Unique constraint: (posting_date, branch_name)")

            print("\nlcl_detail:")
            print("  - sap_upload_date: Date (NOT NULL)")
            print("  - isms_upload_date: Date (nullable)")
            print("  - delivery_date: Date (nullable)")
            print("  - doc_type: String(50) (nullable)")
            print("  - dr_number: String(100) (nullable)")
            print("  - customer_name: String(100) (NOT NULL)")
            print("  - qty: Integer [default=0]")
            print("  - fr_whse: String(100) (nullable)")
            print("  - to_whse: String(100) (nullable)")
            print("  - model: String(100) (nullable)")
            print("  - serial_number: String(100) (NOT NULL)")
            print("  - itr_so: String(100) (nullable)")
            print("  - dr_it: String(100) (nullable)")
            print("  - cbm: Float [default=0.0]")
            print("  - created_at: DateTime")
            print("  - Unique constraint: (sap_upload_date, customer_name, serial_number)")

        except Exception as e:
            print(f"\n❌ Migration failed: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    migrate()
