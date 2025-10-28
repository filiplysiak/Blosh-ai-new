import sqlite3
import hashlib
import os

DATABASE = 'blosh_ai.db'

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_tables():
    """Create all tables from schema.sql"""
    try:
        conn = get_db_connection()
        
        # Read and execute schema
        with open('schema.sql', 'r') as f:
            schema = f.read()
        
        conn.executescript(schema)
        conn.commit()
        conn.close()
        
        print("✅ Database tables created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def add_user(username, password):
    """Add a new user to the database"""
    try:
        conn = get_db_connection()
        hashed_password = hash_password(password)
        
        conn.execute(
            'INSERT INTO users (username, password) VALUES (?, ?)',
            (username, hashed_password)
        )
        conn.commit()
        conn.close()
        
        print(f"✅ User '{username}' added successfully")
        return True
        
    except sqlite3.IntegrityError:
        print(f"❌ User '{username}' already exists")
        return False
    except Exception as e:
        print(f"❌ Error adding user: {e}")
        return False

def check_user_exists(username):
    """Check if a user exists in the database"""
    try:
        conn = get_db_connection()
        user = conn.execute(
            'SELECT username FROM users WHERE username = ?',
            (username,)
        ).fetchone()
        conn.close()
        
        return user is not None
        
    except Exception as e:
        print(f"❌ Error checking user: {e}")
        return False

def list_users():
    """List all users in the database"""
    try:
        conn = get_db_connection()
        users = conn.execute(
            'SELECT id, username, created_at FROM users ORDER BY created_at'
        ).fetchall()
        conn.close()
        
        print("\n📋 Users in database:")
        for user in users:
            print(f"  ID: {user['id']}, Username: {user['username']}, Created: {user['created_at']}")
        
        return users
        
    except Exception as e:
        print(f"❌ Error listing users: {e}")
        return []
