#!/usr/bin/env python3
"""
Create default admin user.
Run this after migrating the users table.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, User

def create_admin():
    with app.app_context():
        # Check if admin already exists
        existing_admin = User.query.filter_by(email='admin@example.com').first()
        if existing_admin:
            print("Admin user already exists!")
            return

        # Create default admin user
        admin = User(
            name='Admin',
            email='admin@example.com',
            position='admin',
            status='active'
        )
        admin.set_password('admin123')

        db.session.add(admin)
        db.session.commit()

        print("Default admin user created successfully!")
        print("\nLogin credentials:")
        print("  Email: admin@example.com")
        print("  Password: admin123")
        print("\nPlease change the password after first login!")

if __name__ == '__main__':
    create_admin()
