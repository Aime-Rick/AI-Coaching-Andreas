"""
Database migration script to add performance indexes
Run this script to update existing database with new indexes
"""
import os
import sys

# Add parent directory to path to import backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database.connection import engine, create_tables
from backend.database.models import Base
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """Apply database migrations for performance improvements"""
    logger.info("Starting database migration...")
    
    try:
        # Create all tables (will skip existing ones)
        create_tables()
        logger.info("✓ Tables verified")
        
        # Add indexes if they don't exist (for SQLite and PostgreSQL compatibility)
        with engine.connect() as conn:
            # Check database type
            db_url = str(engine.url)
            is_sqlite = 'sqlite' in db_url
            
            logger.info(f"Database type: {'SQLite' if is_sqlite else 'PostgreSQL'}")
            
            # For SQLite, we need to check if indexes exist before creating
            if is_sqlite:
                # Get existing indexes
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='index'"))
                existing_indexes = {row[0] for row in result}
                
                indexes_to_create = [
                    ("idx_user_active_updated", 
                     "CREATE INDEX IF NOT EXISTS idx_user_active_updated ON chat_sessions(user_id, is_active, updated_at)"),
                    ("idx_vector_store", 
                     "CREATE INDEX IF NOT EXISTS idx_vector_store ON chat_sessions(vector_store_id)"),
                    ("idx_session_type_timestamp", 
                     "CREATE INDEX IF NOT EXISTS idx_session_type_timestamp ON chat_messages(session_id, message_type, timestamp)"),
                    ("idx_session_timestamp", 
                     "CREATE INDEX IF NOT EXISTS idx_session_timestamp ON chat_messages(session_id, timestamp)"),
                ]
                
                for idx_name, idx_sql in indexes_to_create:
                    if idx_name not in existing_indexes:
                        logger.info(f"Creating index: {idx_name}")
                        conn.execute(text(idx_sql))
                        conn.commit()
                        logger.info(f"✓ Created index: {idx_name}")
                    else:
                        logger.info(f"○ Index already exists: {idx_name}")
            else:
                # For PostgreSQL, use CREATE INDEX IF NOT EXISTS
                indexes_to_create = [
                    ("idx_user_active_updated", 
                     "CREATE INDEX IF NOT EXISTS idx_user_active_updated ON chat_sessions(user_id, is_active, updated_at)"),
                    ("idx_vector_store", 
                     "CREATE INDEX IF NOT EXISTS idx_vector_store ON chat_sessions(vector_store_id)"),
                    ("idx_session_type_timestamp", 
                     "CREATE INDEX IF NOT EXISTS idx_session_type_timestamp ON chat_messages(session_id, message_type, timestamp)"),
                    ("idx_session_timestamp", 
                     "CREATE INDEX IF NOT EXISTS idx_session_timestamp ON chat_messages(session_id, timestamp)"),
                ]
                
                for idx_name, idx_sql in indexes_to_create:
                    logger.info(f"Creating index: {idx_name}")
                    conn.execute(text(idx_sql))
                    conn.commit()
                    logger.info(f"✓ Created index: {idx_name}")
        
        logger.info("✓ Database migration completed successfully!")
        logger.info("\nPerformance improvements applied:")
        logger.info("  - Added composite indexes for common query patterns")
        logger.info("  - Optimized session and message lookups")
        logger.info("  - Improved vector store queries")
        
    except Exception as e:
        logger.error(f"✗ Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    migrate_database()
