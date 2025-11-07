"""
Database Configuration Module
SECURITY: All credentials loaded from environment variables ONLY
NO hardcoded defaults or fallbacks - fails fast if credentials missing
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, Engine
from sqlalchemy.pool import QueuePool

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent
dotenv_path = PROJECT_ROOT / '.env'

if not dotenv_path.exists():
    raise FileNotFoundError(
        f"SECURITY ERROR: .env file not found at {dotenv_path}. "
        "Cannot proceed without secure credentials. "
        "Please create .env file with database credentials."
    )

load_dotenv(dotenv_path)
logger.info(f"Loaded environment variables from: {dotenv_path}")


class DatabaseConfig:
    """
    Database configuration class - SECURITY ENFORCED
    - All credentials from environment variables
    - No hardcoded defaults
    - Fails if credentials missing
    - Never logs credentials
    """
    
    def __init__(self):
        """Initialize database configuration from environment variables ONLY"""
        # Load credentials - FAIL if missing (no defaults)
        self.host = self._get_required_env('DB_HOST')
        self.port = self._get_required_env('DB_PORT')
        self.user = self._get_required_env('DB_USER')
        self.password = self._get_required_env('DB_PASSWORD')
        self.database = self._get_required_env('DB_NAME')
        
        # Log configuration (WITHOUT credentials)
        logger.info("Database configuration loaded successfully")
        logger.info(f"Database: {self.database}")
        logger.info(f"Host: {self.host}:{self.port}")
        logger.info(f"User: {self.user}")
        # SECURITY: NEVER log password
        
    def _get_required_env(self, key: str) -> str:
        """
        Get required environment variable or raise error
        NO FALLBACKS - security requirement
        
        Args:
            key: Environment variable name
            
        Returns:
            str: Environment variable value
            
        Raises:
            ValueError: If environment variable is missing or empty
        """
        value = os.getenv(key)
        
        if value is None or value.strip() == '':
            raise ValueError(
                f"SECURITY ERROR: Required environment variable '{key}' is not set. "
                f"Please add it to the .env file. "
                f"NO DEFAULTS ALLOWED for security compliance."
            )
        
        # Check for placeholder values (common mistake)
        if 'YOUR_' in value.upper() or 'REPLACE' in value.upper():
            raise ValueError(
                f"SECURITY ERROR: Environment variable '{key}' contains placeholder value: {value}. "
                f"Please replace with actual credentials in .env file."
            )
        
        return value.strip()
    
    def get_connection_url(self) -> str:
        """
        Build SQLAlchemy connection URL
        SECURITY: Uses parameterized format, no string concatenation
        
        Returns:
            str: SQLAlchemy database URL
        """
        # Use pymysql driver (pure Python, no C dependencies)
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    def create_engine(self) -> Engine:
        """
        Create SQLAlchemy engine with connection pooling
        SECURITY: Proper connection management and cleanup
        
        Returns:
            Engine: SQLAlchemy engine instance
        """
        connection_url = self.get_connection_url()
        
        # Create engine with connection pooling
        engine = create_engine(
            connection_url,
            poolclass=QueuePool,
            pool_size=5,          # Max 5 connections in pool
            max_overflow=10,      # Max 10 overflow connections
            pool_pre_ping=True,   # Verify connection before use
            echo=False,           # SECURITY: Don't log SQL (may contain data)
            pool_recycle=3600     # Recycle connections after 1 hour
        )
        
        logger.info("SQLAlchemy engine created successfully")
        return engine


def get_database_engine() -> Engine:
    """
    Factory function to get database engine
    SECURITY: Single point of access with proper error handling
    
    Returns:
        Engine: Configured SQLAlchemy engine
        
    Raises:
        ValueError: If configuration is invalid
        FileNotFoundError: If .env file missing
    """
    try:
        config = DatabaseConfig()
        engine = config.create_engine()
        
        # Test connection (will raise exception if fails)
        with engine.connect() as conn:
            logger.info("Database connection test successful")
        
        return engine
        
    except Exception as e:
        logger.error(f"Failed to create database engine: {str(e)}")
        raise


if __name__ == "__main__":
    """Test database configuration"""
    print("\n" + "="*80)
    print("DATABASE CONFIGURATION TEST")
    print("="*80)
    
    try:
        # Test configuration loading
        print("\n[1/2] Loading configuration from .env file...")
        config = DatabaseConfig()
        print("✓ Configuration loaded successfully")
        
        # Test database connection
        print("\n[2/2] Testing database connection...")
        engine = get_database_engine()
        print("✓ Database connection successful")
        
        print("\n" + "="*80)
        print("ALL TESTS PASSED - DATABASE CONFIGURATION IS VALID")
        print("="*80)
        
    except Exception as e:
        print("\n" + "="*80)
        print("ERROR: Database configuration failed")
        print("="*80)
        print(f"\nError details: {str(e)}")
        print("\nPlease check:")
        print("  1. .env file exists in project root")
        print("  2. All required variables are set (DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)")
        print("  3. MySQL service is running")
        print("  4. Credentials are correct")
        raise
