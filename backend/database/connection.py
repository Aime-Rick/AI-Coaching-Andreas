import os
from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import sessionmaker
from backend.database.models import Base
from dotenv import load_dotenv

load_dotenv()

def get_database_url():
    """Get database URL based on environment"""
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        # PostgreSQL for production
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "ai_coaching")
        
        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    else:
        # SQLite for development
        db_path = os.getenv("SQLITE_DB_PATH", "ai_coaching.db")
        return f"sqlite:///{db_path}"

# Create engine with optimized connection pooling
DATABASE_URL = get_database_url()
env = os.getenv("ENVIRONMENT", "development")

# Configure connection pool settings
if env == "production":
    # PostgreSQL production settings with connection pooling
    engine = create_engine(
        DATABASE_URL,
        echo=os.getenv("DEBUG", "false").lower() == "true",
        pool_size=10,  # Keep 10 connections in pool
        max_overflow=20,  # Allow up to 20 additional connections
        pool_pre_ping=True,  # Verify connections before using them
        pool_recycle=3600,  # Recycle connections after 1 hour
        connect_args={
            "connect_timeout": 10,
            "options": "-c statement_timeout=30000"  # 30 second query timeout
        }
    )
else:
    # SQLite development settings with optimizations
    engine = create_engine(
        DATABASE_URL,
        echo=os.getenv("DEBUG", "false").lower() == "true",
        connect_args={
            "check_same_thread": False,
            "timeout": 30  # 30 second timeout for SQLite
        },
        poolclass=pool.StaticPool  # Use static pool for SQLite
    )
    
    # Enable SQLite optimizations
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for better concurrency
        cursor.execute("PRAGMA synchronous=NORMAL")  # Balance between safety and speed
        cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
        cursor.execute("PRAGMA temp_store=MEMORY")  # Store temp tables in memory
        cursor.close()

# Create session factory with optimized settings
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False  # Prevent unnecessary queries after commit
)

def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()