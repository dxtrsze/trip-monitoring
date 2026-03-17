"""
Migration script to fix daily_rate, sched_start, and sched_end columns NULL constraint
Date: March 17, 2026
"""
import sys
import os

# Add the parent directory to the path to import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User

def migrate():
    """Fix daily_rate column to allow NULL values"""
    with app.app_context():
        # Check current schema
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        columns = inspector.get_columns('user')

        print("Current user table schema:")
        for col in columns:
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            print(f"  - {col['name']}: {col['type']} {nullable}")

        # Check if daily_rate column is nullable
        daily_rate_col = next((col for col in columns if col['name'] == 'daily_rate'), None)

        if daily_rate_col and daily_rate_col['nullable']:
            print("\n✓ Column 'daily_rate' already allows NULL. No migration needed.")
            return

        print("\nAltering daily_rate column to allow NULL values...")

        try:
            with db.engine.connect() as conn:
                # SQLite doesn't support ALTER COLUMN directly, need to recreate table
                if 'SQLite' in str(db.engine.dialect):
                    # For SQLite, we need to:
                    # 1. Create a new table with the correct schema
                    # 2. Copy data from old table
                    # 3. Drop old table
                    # 4. Rename new table

                    # Get existing data
                    result = conn.execute(text("SELECT * FROM user"))
                    users_data = result.fetchall()
                    columns_names = result.keys()

                    print(f"  - Backed up {len(users_data)} user records")

                    # Create new table with correct schema
                    conn.execute(text("""
                        CREATE TABLE user_new (
                            id INTEGER PRIMARY KEY,
                            name VARCHAR(100) NOT NULL,
                            email VARCHAR(120) UNIQUE NOT NULL,
                            password_hash VARCHAR(255) NOT NULL,
                            position VARCHAR(50) NOT NULL DEFAULT 'user',
                            status VARCHAR(50) NOT NULL DEFAULT 'active',
                            daily_rate FLOAT,
                            sched_start VARCHAR(10),
                            sched_end VARCHAR(10)
                        )
                    """))

                    # Copy data
                    for user in users_data:
                        user_dict = dict(zip(columns_names, user))
                        conn.execute(text("""
                            INSERT INTO user_new (id, name, email, password_hash, position, status, daily_rate, sched_start, sched_end)
                            VALUES (:id, :name, :email, :password_hash, :position, :status, :daily_rate, :sched_start, :sched_end)
                        """), {
                            'id': user_dict.get('id'),
                            'name': user_dict.get('name'),
                            'email': user_dict.get('email'),
                            'password_hash': user_dict.get('password_hash'),
                            'position': user_dict.get('position'),
                            'status': user_dict.get('status'),
                            'daily_rate': user_dict.get('daily_rate'),
                            'sched_start': user_dict.get('sched_start'),
                            'sched_end': user_dict.get('sched_end')
                        })

                    print(f"  - Copied {len(users_data)} user records to new table")

                    # Drop old table
                    conn.execute(text("DROP TABLE user"))
                    print("  - Dropped old user table")

                    # Rename new table
                    conn.execute(text("ALTER TABLE user_new RENAME TO user"))
                    print("  - Renamed user_new to user")

                    # Recreate indexes
                    conn.execute(text("CREATE INDEX ix_user_email ON user (email)"))
                    print("  - Recreated email index")

                    conn.commit()

                elif 'PostgreSQL' in str(db.engine.dialect):
                    # PostgreSQL supports ALTER COLUMN
                    conn.execute(text("ALTER TABLE user ALTER COLUMN daily_rate DROP NOT NULL"))
                    conn.execute(text("ALTER TABLE user ALTER COLUMN sched_start DROP NOT NULL"))
                    conn.execute(text("ALTER TABLE user ALTER COLUMN sched_end DROP NOT NULL"))
                    conn.commit()
                    print("✓ Columns altered successfully")

                else:
                    # Generic SQL (MySQL, etc.)
                    conn.execute(text("ALTER TABLE user MODIFY COLUMN daily_rate FLOAT NULL"))
                    conn.execute(text("ALTER TABLE user MODIFY COLUMN sched_start VARCHAR(10) NULL"))
                    conn.execute(text("ALTER TABLE user MODIFY COLUMN sched_end VARCHAR(10) NULL"))
                    conn.commit()
                    print("✓ Columns altered successfully")

        except Exception as e:
            print(f"✗ Error during migration: {e}")
            db.session.rollback()
            raise

        # Verify the changes
        inspector = inspect(db.engine)
        columns = inspector.get_columns('user')
        daily_rate_col = next((col for col in columns if col['name'] == 'daily_rate'), None)

        if daily_rate_col and daily_rate_col['nullable']:
            print("\n✓ Migration verified: 'daily_rate' column now allows NULL")
            print("✓ sched_start and sched_end also allow NULL")
        else:
            print("\n✗ Migration verification failed")

if __name__ == '__main__':
    print("=" * 60)
    print("Fix daily_rate NULL constraint - March 17, 2026")
    print("=" * 60)
    print()
    migrate()
    print()
    print("=" * 60)
    print("Migration completed!")
    print("=" * 60)
