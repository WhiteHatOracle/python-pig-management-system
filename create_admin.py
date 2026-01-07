#!/usr/bin/env python3
"""
Script to create the first admin user.
Run this once after setting up the admin panel.

Usage: python create_admin.py
"""

from app import app, db
from models import AdminUser
from getpass import getpass

def create_first_admin():
    with app.app_context():
        # Check if any admin exists
        existing = AdminUser.query.first()
        if existing:
            print("⚠️  Admin users already exist!")
            print(f"   Existing admin: {existing.username}")
            
            create_another = input("\nCreate another admin? (y/n): ").lower()
            if create_another != 'y':
                return
        
        print("\n🔐 Create Admin User\n" + "="*40)
        
        # Get admin details
        username = input("Username: ").strip()
        email = input("Email: ").strip()
        password = getpass("Password: ")
        confirm_password = getpass("Confirm Password: ")
        
        # Validation
        if not username or not email or not password:
            print("❌ All fields are required!")
            return
        
        if password != confirm_password:
            print("❌ Passwords do not match!")
            return
        
        if len(password) < 8:
            print("❌ Password must be at least 8 characters!")
            return
        
        # Check if username/email exists
        if AdminUser.query.filter((AdminUser.username == username) | (AdminUser.email == email)).first():
            print("❌ Username or email already exists!")
            return
        
        # Ask if super admin
        is_super = input("Make this a Super Admin? (y/n): ").lower() == 'y'
        
        # Create admin
        admin = AdminUser(
            username=username,
            email=email,
            is_super_admin=is_super,
            is_active=True
        )
        admin.set_password(password)
        
        db.session.add(admin)
        db.session.commit()
        
        print("\n" + "="*40)
        print("✅ Admin created successfully!")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        print(f"   Super Admin: {'Yes' if is_super else 'No'}")
        print(f"\n🔗 Login at: http://localhost:5000/admin/login")

if __name__ == '__main__':
    create_first_admin()