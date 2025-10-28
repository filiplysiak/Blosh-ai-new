#!/usr/bin/env python3
"""
Blosh AI Database Creation Script

This script creates the database tables and adds the default user.
Run with: python createdb.py
"""

import os
import sys
from db_helper import create_tables, add_user, check_user_exists, list_users

def main():
    print("🚀 Blosh AI Database Setup")
    print("=" * 40)
    
    # Create tables
    print("\n1️⃣ Creating database tables...")
    if not create_tables():
        print("❌ Failed to create tables. Exiting.")
        sys.exit(1)
    
    # Add default user
    print("\n2️⃣ Adding default user...")
    default_username = "blosh"
    default_password = "blosh12!"
    
    if check_user_exists(default_username):
        print(f"ℹ️  User '{default_username}' already exists, skipping...")
    else:
        if add_user(default_username, default_password):
            print(f"✅ Default user created successfully!")
            print(f"   Username: {default_username}")
            print(f"   Password: {default_password}")
        else:
            print("❌ Failed to create default user")
            sys.exit(1)
    
    # List all users
    print("\n3️⃣ Current users in database:")
    list_users()
    
    print("\n🎉 Database setup completed successfully!")
    print("\nYou can now start the Flask server with:")
    print("   cd server && python app.py")

if __name__ == "__main__":
    main()
