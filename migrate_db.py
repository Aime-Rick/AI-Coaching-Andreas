"""
Database Migration Script

Run this script to initialize or migrate your database.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database.connection import create_tables, get_database_url, engine
from sqlalchemy import text

def check_database_connection():
    """Test database connection"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def initialize_database():
    """Initialize database with tables"""
    try:
        print("🔄 Creating database tables...")
        create_tables()
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False

def main():
    print("🚀 AI Coaching Database Migration")
    print("=" * 40)
    
    db_url = get_database_url()
    print(f"📊 Database URL: {db_url}")
    
    # Check connection
    if not check_database_connection():
        print("💡 Make sure your database is running and credentials are correct.")
        return
    
    print("✅ Database connection successful!")
    
    # Initialize tables
    if initialize_database():
        print("\n🎉 Database migration completed successfully!")
        print("\n📋 What's been created:")
        print("   • chat_sessions table - stores chat session metadata")
        print("   • chat_messages table - stores individual messages")
        print("\n🔗 You can now use the chat memory features!")
    else:
        print("\n❌ Migration failed. Please check the error messages above.")

if __name__ == "__main__":
    main()