import os
from sqlalchemy import create_engine
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

# Create engine
DATABASE_URL = get_database_url()
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("DEBUG", "false").lower() == "true"  # Enable SQL logging in debug mode
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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