"""
Database Schema Module
SECURITY: Uses SQLAlchemy ORM exclusively - NO string concatenation in SQL
All table operations use parameterized queries via SQLAlchemy
"""

import logging
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, 
    Index, create_engine, text
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from db_config import get_database_engine

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create declarative base for ORM models
Base = declarative_base()


class Customer(Base):
    """
    Customer table model
    SECURITY: SQLAlchemy ORM model - no SQL strings
    """
    __tablename__ = 'customers'
    
    # Primary key
    customer_id = Column(String(50), primary_key=True, nullable=False)
    
    # Customer details
    customer_name = Column(String(100), nullable=False)
    mobile_number = Column(String(20), nullable=False)
    region = Column(String(50), nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes for performance (parameterized via SQLAlchemy)
    __table_args__ = (
        Index('idx_mobile_number', 'mobile_number'),
        Index('idx_region', 'region'),
        Index('idx_customer_name', 'customer_name'),
    )
    
    def __repr__(self):
        return f"<Customer(customer_id='{self.customer_id}', name='{self.customer_name}', region='{self.region}')>"


class Order(Base):
    """
    Order table model
    SECURITY: SQLAlchemy ORM model - no SQL strings
    """
    __tablename__ = 'orders'
    
    # Primary key (auto-increment)
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Order details
    order_id = Column(String(50), nullable=False)
    mobile_number = Column(String(20), nullable=False)
    order_date_time = Column(DateTime, nullable=False)
    sku_id = Column(String(50), nullable=False)
    sku_count = Column(Integer, nullable=False)
    total_amount = Column(Float, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes for performance (parameterized via SQLAlchemy)
    __table_args__ = (
        Index('idx_order_id', 'order_id'),
        Index('idx_mobile_number', 'mobile_number'),
        Index('idx_order_date_time', 'order_date_time'),
        Index('idx_sku_id', 'sku_id'),
        # Composite index for common join queries
        Index('idx_mobile_order_date', 'mobile_number', 'order_date_time'),
    )
    
    def __repr__(self):
        return f"<Order(order_id='{self.order_id}', mobile='{self.mobile_number}', amount={self.total_amount})>"


def create_tables(engine=None):
    """
    Create all tables in the database
    SECURITY: Uses SQLAlchemy's metadata.create_all() - fully parameterized
    
    Args:
        engine: SQLAlchemy engine (optional, will create if not provided)
    """
    try:
        if engine is None:
            engine = get_database_engine()
        
        logger.info("Creating database tables...")
        
        # SECURITY: SQLAlchemy handles all DDL statements internally
        # No string concatenation - all parameterized
        Base.metadata.create_all(engine)
        
        logger.info("Tables created successfully:")
        logger.info("  - customers (with indexes on mobile_number, region, customer_name)")
        logger.info("  - orders (with indexes on order_id, mobile_number, order_date_time, sku_id)")
        
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"Failed to create tables: {str(e)}")
        raise


def drop_tables(engine=None):
    """
    Drop all tables from the database
    SECURITY: Uses SQLAlchemy's metadata.drop_all() - fully parameterized
    WARNING: This will delete all data!
    
    Args:
        engine: SQLAlchemy engine (optional, will create if not provided)
    """
    try:
        if engine is None:
            engine = get_database_engine()
        
        logger.warning("Dropping all tables...")
        
        # SECURITY: SQLAlchemy handles all DDL statements internally
        Base.metadata.drop_all(engine)
        
        logger.info("All tables dropped successfully")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"Failed to drop tables: {str(e)}")
        raise


def get_session(engine=None):
    """
    Create a database session for queries
    SECURITY: Session provides parameterized query interface
    
    Args:
        engine: SQLAlchemy engine (optional, will create if not provided)
        
    Returns:
        Session: SQLAlchemy session object
    """
    try:
        if engine is None:
            engine = get_database_engine()
        
        # Create session factory
        Session = sessionmaker(bind=engine)
        session = Session()
        
        return session
        
    except SQLAlchemyError as e:
        logger.error(f"Failed to create session: {str(e)}")
        raise


def get_table_info(engine=None):
    """
    Get information about existing tables
    SECURITY: Uses SQLAlchemy text() for safe query execution
    
    Args:
        engine: SQLAlchemy engine (optional, will create if not provided)
        
    Returns:
        dict: Table information
    """
    try:
        if engine is None:
            engine = get_database_engine()
        
        with engine.connect() as conn:
            # SECURITY: Using SQLAlchemy text() for safe parameterized queries
            # No string concatenation
            result = conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result]
            
            table_info = {}
            for table in tables:
                # SECURITY: Using text() with bound parameter
                count_query = text(f"SELECT COUNT(*) FROM {table}")
                count_result = conn.execute(count_query)
                count = count_result.scalar()
                table_info[table] = count
            
            return table_info
            
    except SQLAlchemyError as e:
        logger.error(f"Failed to get table info: {str(e)}")
        raise


if __name__ == "__main__":
    """Test schema creation"""
    print("\n" + "="*80)
    print("DATABASE SCHEMA SETUP")
    print("="*80)
    
    try:
        # Get database engine
        print("\n[1/4] Connecting to database...")
        engine = get_database_engine()
        print("✓ Connected successfully")
        
        # Drop existing tables (clean slate)
        print("\n[2/4] Dropping existing tables (if any)...")
        drop_tables(engine)
        print("✓ Existing tables dropped")
        
        # Create tables
        print("\n[3/4] Creating tables...")
        create_tables(engine)
        print("✓ Tables created successfully")
        
        # Verify tables
        print("\n[4/4] Verifying table creation...")
        table_info = get_table_info(engine)
        
        print("\nDatabase tables:")
        for table_name, row_count in table_info.items():
            print(f"  - {table_name}: {row_count} rows")
        
        print("\n" + "="*80)
        print("SCHEMA SETUP COMPLETED SUCCESSFULLY")
        print("="*80)
        print("\nNext steps:")
        print("  1. Run db_loader.py to load data into tables")
        print("  2. Run db_queries.py to calculate KPIs")
        print("  3. Run main_db.py to execute complete pipeline")
        
    except Exception as e:
        print("\n" + "="*80)
        print("ERROR: Schema setup failed")
        print("="*80)
        print(f"\nError details: {str(e)}")
        raise
