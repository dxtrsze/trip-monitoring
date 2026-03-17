"""
Migration script to add department column to vehicles table
Date: March 17, 2026
"""
import sys
import os

# Add the parent directory to the path to import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Vehicle

def migrate():
    """Add department column to Vehicle table"""
    with app.app_context():
        # Check if dept column already exists
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('vehicle')]

        if 'dept' in columns:
            print("Column 'dept' already exists in vehicle table. Skipping migration.")
            return

        # Add the dept column using raw SQL
        try:
            with db.engine.connect() as conn:
                # For SQLite
                if 'SQLite' in str(db.engine.dialect):
                    # SQLite doesn't support ALTER TABLE ADD COLUMN with CHECK constraints directly
                    # So we'll just add the column without the constraint
                    conn.execute(db.text("ALTER TABLE vehicle ADD COLUMN dept VARCHAR(50)"))
                    conn.commit()
                    print("✓ Column 'dept' added to vehicle table successfully")

                    # Update existing vehicles to have 'Logistics' as default dept
                    conn.execute(db.text("UPDATE vehicle SET dept = 'Logistics' WHERE dept IS NULL"))
                    conn.commit()
                    print("✓ Existing vehicles updated with 'Logistics' as default department")

                # For PostgreSQL
                elif 'PostgreSQL' in str(db.engine.dialect):
                    conn.execute(db.text("ALTER TABLE vehicle ADD COLUMN dept VARCHAR(50)"))
                    conn.execute(db.text("UPDATE vehicle SET dept = 'Logistics' WHERE dept IS NULL"))
                    conn.commit()
                    print("✓ Column 'dept' added to vehicle table successfully")
                    print("✓ Existing vehicles updated with 'Logistics' as default department")

                else:
                    # Generic SQL for other databases
                    conn.execute(db.text("ALTER TABLE vehicle ADD COLUMN dept VARCHAR(50)"))
                    conn.execute(db.text("UPDATE vehicle SET dept = 'Logistics' WHERE dept IS NULL"))
                    conn.commit()
                    print("✓ Column 'dept' added to vehicle table successfully")
                    print("✓ Existing vehicles updated with 'Logistics' as default department")

        except Exception as e:
            print(f"✗ Error adding column: {e}")
            db.session.rollback()
            raise

        # Verify the column was added
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('vehicle')]
        if 'dept' in columns:
            print("✓ Migration verified: 'dept' column exists in vehicle table")
        else:
            print("✗ Migration failed: 'dept' column not found")

if __name__ == '__main__':
    print("=" * 60)
    print("Vehicle Department Migration - March 17, 2026")
    print("=" * 60)
    print()
    migrate()
    print()
    print("=" * 60)
    print("Migration completed!")
    print("=" * 60)
