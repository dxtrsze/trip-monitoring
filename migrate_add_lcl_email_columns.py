#!/usr/bin/env python3
"""
Migration script to add email column to lcl_summary and lcl_detail tables
for visibility control of data.

Run this script: python migrate_add_lcl_email_columns.py
"""

import sys
import os
from flask import Flask
from sqlalchemy import text, inspect

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db

def migrate():
    """Add email column to lcl_summary and lcl_detail tables"""

    with app.app_context():
        inspector = inspect(db.engine)

        # Check existing columns for lcl_summary
        lcl_summary_columns = [col['name'] for col in inspector.get_columns('lcl_summary')]
        lcl_detail_columns = [col['name'] for col in inspector.get_columns('lcl_detail')]

        # Add email column to lcl_summary if it doesn't exist
        if 'email' not in lcl_summary_columns:
            print("Adding 'email' column to lcl_summary table...")
            try:
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE lcl_summary ADD COLUMN email VARCHAR(120)"))
                    conn.commit()
                print("✓ Successfully added 'email' column to lcl_summary")
            except Exception as e:
                print(f"✗ Error adding email to lcl_summary: {e}")
                return False
        else:
            print("⊙ Column 'email' already exists in lcl_summary table")

        # Add email column to lcl_detail if it doesn't exist
        if 'email' not in lcl_detail_columns:
            print("\nAdding 'email' column to lcl_detail table...")
            try:
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE lcl_detail ADD COLUMN email VARCHAR(120)"))
                    conn.commit()
                print("✓ Successfully added 'email' column to lcl_detail")
            except Exception as e:
                print(f"✗ Error adding email to lcl_detail: {e}")
                return False
        else:
            print("⊙ Column 'email' already exists in lcl_detail table")

        # Verify the migration
        print("\n" + "="*50)
        print("Verifying migration...")

        inspector = inspect(db.engine)
        lcl_summary_columns = [col['name'] for col in inspector.get_columns('lcl_summary')]
        lcl_detail_columns = [col['name'] for col in inspector.get_columns('lcl_detail')]

        if 'email' in lcl_summary_columns:
            print("✓ lcl_summary.email column exists")
        else:
            print("✗ lcl_summary.email column missing")

        if 'email' in lcl_detail_columns:
            print("✓ lcl_detail.email column exists")
        else:
            print("✗ lcl_detail.email column missing")

        print("\n" + "="*50)
        print("Migration completed successfully!")
        print("="*50)

        return True

if __name__ == '__main__':
    print("="*50)
    print("LCL Email Columns Migration")
    print("="*50)
    print()

    success = migrate()

    if success:
        print("\n✓ Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n✗ Migration failed!")
        sys.exit(1)
