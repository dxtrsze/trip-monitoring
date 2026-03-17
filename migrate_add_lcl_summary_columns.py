#!/usr/bin/env python3
"""
Migration script to add additional columns to lcl_summary table

This script adds the following columns:
- prep_date, waybill_no, 3pl, ref_docs, freight_category
- shipping_line, container_no, seal_no, tot_boxes, declared_value
- freight_charge, length_width_height, total_kg, remarks
- port_of_destination, order_date, booked_date, actual_pickup_date
- etd, atd, eta, ata, actual_delivered_date, received_by
- status, detailed_remarks, actual_delivery_leadtime
- received_date_to_pick_up_date, year, pick_up_month
- total_freight_charge, billing_date, billing_no, billing_status, team_lead

Run this script to update the existing database:
    python migrate_add_lcl_summary_columns.py
"""

import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text

def migrate():
    """Add new columns to lcl_summary table"""
    with app.app_context():
        print("Starting LCL summary table migration...")
        print(f"Migration time: {datetime.now()}")

        try:
            # Check current table structure
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('lcl_summary')]

            print(f"\n📊 Current columns in lcl_summary ({len(columns)} total):")
            for col in sorted(columns):
                print(f"  - {col}")

            # Define new columns to add
            new_columns = {
                'prep_date': 'DATE',
                'waybill_no': 'VARCHAR(100)',
                '3pl': 'VARCHAR(100)',  # Note: '3pl' will be quoted in SQL
                'ref_docs': 'VARCHAR(200)',
                'freight_category': 'VARCHAR(100)',
                'shipping_line': 'VARCHAR(100)',
                'container_no': 'VARCHAR(100)',
                'seal_no': 'VARCHAR(100)',
                'tot_boxes': 'INTEGER',
                'declared_value': 'FLOAT',
                'freight_charge': 'FLOAT',
                'length_width_height': 'VARCHAR(100)',
                'total_kg': 'FLOAT',
                'remarks': 'TEXT',
                'port_of_destination': 'VARCHAR(100)',
                'order_date': 'DATE',
                'booked_date': 'DATE',
                'actual_pickup_date': 'DATE',
                'etd': 'DATE',
                'atd': 'DATE',
                'eta': 'DATE',
                'ata': 'DATE',
                'actual_delivered_date': 'DATE',
                'received_by': 'VARCHAR(100)',
                'status': 'VARCHAR(50)',
                'detailed_remarks': 'TEXT',
                'actual_delivery_leadtime': 'INTEGER',
                'received_date_to_pick_up_date': 'INTEGER',
                'year': 'INTEGER',
                'pick_up_month': 'VARCHAR(20)',
                'total_freight_charge': 'FLOAT',
                'billing_date': 'DATE',
                'billing_no': 'VARCHAR(100)',
                'billing_status': 'VARCHAR(50)',
                'team_lead': 'VARCHAR(100)'
            }

            # Filter out columns that already exist
            columns_to_add = {col: dtype for col, dtype in new_columns.items() if col not in columns}

            if not columns_to_add:
                print("\n✅ All new columns already exist. Nothing to add.")
                return True

            print(f"\n➕ Adding {len(columns_to_add)} new columns...")

            # Add each column using ALTER TABLE
            for col_name, col_type in columns_to_add.items():
                try:
                    # Use proper SQL quoting for column names
                    sql = f"ALTER TABLE lcl_summary ADD COLUMN {col_name} {col_type}"
                    if col_name == '3pl':
                        # Special handling for '3pl' column name
                        sql = f'ALTER TABLE lcl_summary ADD COLUMN "3pl" {col_type}'

                    db.session.execute(text(sql))
                    db.session.flush()
                    print(f"  ✓ Added {col_name} ({col_type})")
                except Exception as e:
                    print(f"  ✗ Error adding {col_name}: {e}")
                    raise

            # Commit the changes
            db.session.commit()

            # Verify the new columns were added
            inspector = db.inspect(db.engine)
            updated_columns = [col['name'] for col in inspector.get_columns('lcl_summary')]

            print(f"\n📊 Updated columns in lcl_summary ({len(updated_columns)} total):")
            for col in sorted(updated_columns):
                marker = " 🆕" if col in columns_to_add else ""
                print(f"  - {col}{marker}")

            print("\n" + "=" * 60)
            print("✅ Migration completed successfully!")
            print(f"✅ Added {len(columns_to_add)} new columns")
            print("=" * 60)

            return True

        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Migration failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main function with user confirmation"""
    print("=" * 60)
    print("LCL SUMMARY TABLE MIGRATION")
    print("=" * 60)
    print("\nThis will ADD new columns to the lcl_summary table.")
    print("\nNew columns to be added:")
    print("  • prep_date, waybill_no, 3pl, ref_docs")
    print("  • freight_category, shipping_line, container_no")
    print("  • seal_no, tot_boxes, declared_value")
    print("  • freight_charge, length_width_height, total_kg")
    print("  • remarks, port_of_destination, order_date")
    print("  • booked_date, actual_pickup_date, etd, atd")
    print("  • eta, ata, actual_delivered_date, received_by")
    print("  • status, detailed_remarks, actual_delivery_leadtime")
    print("  • received_date_to_pick_up_date, year, pick_up_month")
    print("  • total_freight_charge, billing_date")
    print("  • billing_no, billing_status, team_lead")
    print("\n⚠️  This action is safe and will not delete existing data.")

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
    success = migrate()

    if success:
        print("\n✨ You can now use the enhanced LCL summary features.")
        return 0
    else:
        print("\n❌ Migration completed with errors")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
