"""
Database Loader Module
SECURITY: Uses SQLAlchemy ORM for all database operations - NO string concatenation
Loads CSV/XML data into MySQL using parameterized queries only
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Tuple
import pandas as pd
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.mysql import insert

# Add parent directory to path to import from src/
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT / 'src'))

from data_loader import DataLoader
from data_cleaner import DataCleaner
from db_config import get_database_engine
from db_schema import Customer, Order, get_session, get_table_info

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseLoader:
    """
    Load data into MySQL database
    SECURITY: All operations use SQLAlchemy ORM - fully parameterized
    """
    
    def __init__(self, engine=None):
        """
        Initialize database loader
        
        Args:
            engine: SQLAlchemy engine (optional, will create if not provided)
        """
        self.engine = engine if engine else get_database_engine()
        self.session = get_session(self.engine)
        logger.info("DatabaseLoader initialized")
    
    def load_customers(self, customers_df: pd.DataFrame) -> int:
        """
        Load customer data into database
        SECURITY: Uses SQLAlchemy ORM bulk operations - fully parameterized
        
        Args:
            customers_df: DataFrame with customer data
            
        Returns:
            int: Number of customers inserted/updated
        """
        try:
            logger.info(f"Loading {len(customers_df)} customers into database...")
            
            # Convert DataFrame to list of dictionaries
            customers_data = customers_df.to_dict('records')
            
            # SECURITY: Using SQLAlchemy's insert() with ON DUPLICATE KEY UPDATE
            # Fully parameterized - no string concatenation
            stmt = insert(Customer).values(customers_data)
            
            # Handle duplicates: update existing records
            stmt = stmt.on_duplicate_key_update(
                customer_name=stmt.inserted.customer_name,
                mobile_number=stmt.inserted.mobile_number,
                region=stmt.inserted.region,
                updated_at=datetime.utcnow()
            )
            
            # Execute the statement
            result = self.session.execute(stmt)
            self.session.commit()
            
            rows_affected = result.rowcount
            logger.info(f"Successfully loaded {rows_affected} customer records")
            
            return rows_affected
            
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Failed to load customers: {str(e)}")
            raise
    
    def load_orders(self, orders_df: pd.DataFrame) -> int:
        """
        Load order data into database
        SECURITY: Uses SQLAlchemy ORM bulk operations - fully parameterized
        
        Args:
            orders_df: DataFrame with order data
            
        Returns:
            int: Number of orders inserted
        """
        try:
            logger.info(f"Loading {len(orders_df)} orders into database...")
            
            # Convert DataFrame to list of Order objects
            # SECURITY: SQLAlchemy ORM handles all parameterization
            orders = []
            for _, row in orders_df.iterrows():
                order = Order(
                    order_id=row['order_id'],
                    mobile_number=row['mobile_number'],
                    order_date_time=row['order_date_time'],
                    sku_id=row['sku_id'],
                    sku_count=int(row['sku_count']),
                    total_amount=float(row['total_amount'])
                )
                orders.append(order)
            
            # SECURITY: bulk_save_objects uses parameterized queries
            self.session.bulk_save_objects(orders)
            self.session.commit()
            
            logger.info(f"Successfully loaded {len(orders)} order records")
            
            return len(orders)
            
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Failed to load orders: {str(e)}")
            raise
    
    def clear_tables(self):
        """
        Clear all data from tables (for testing/reset)
        SECURITY: Uses SQLAlchemy delete() - fully parameterized
        """
        try:
            logger.warning("Clearing all table data...")
            
            # SECURITY: SQLAlchemy handles DELETE statements safely
            self.session.query(Order).delete()
            self.session.query(Customer).delete()
            self.session.commit()
            
            logger.info("All table data cleared")
            
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Failed to clear tables: {str(e)}")
            raise
    
    def get_row_counts(self) -> dict:
        """
        Get row counts for all tables
        SECURITY: Uses SQLAlchemy count() - fully parameterized
        
        Returns:
            dict: Table name -> row count mapping
        """
        try:
            # SECURITY: SQLAlchemy query().count() is parameterized
            customer_count = self.session.query(Customer).count()
            order_count = self.session.query(Order).count()
            
            return {
                'customers': customer_count,
                'orders': order_count
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get row counts: {str(e)}")
            raise
    
    def close(self):
        """Close database session"""
        if self.session:
            self.session.close()
            logger.info("Database session closed")


def load_data_to_database(data_dir: Path = None) -> Tuple[int, int]:
    """
    Complete data loading pipeline: Load CSV/XML -> Clean -> Insert to MySQL
    SECURITY: All database operations use parameterized queries
    
    Args:
        data_dir: Path to data directory (optional)
        
    Returns:
        Tuple[int, int]: (customers_loaded, orders_loaded)
    """
    try:
        # Step 1: Load data from CSV/XML files
        logger.info("="*80)
        logger.info("STEP 1: Loading data from files...")
        logger.info("="*80)
        
        if data_dir is None:
            data_dir = PROJECT_ROOT / 'data'
        
        loader = DataLoader(str(data_dir))
        customers, orders = loader.load_all_data()
        
        logger.info(f"Loaded {len(customers)} customers and {len(orders)} order line items")
        
        # Step 2: Clean data
        logger.info("\n" + "="*80)
        logger.info("STEP 2: Cleaning data...")
        logger.info("="*80)
        
        cleaner = DataCleaner()
        customers_clean = cleaner.clean_customers(customers)
        orders_clean, orders_invalid = cleaner.clean_orders(orders)
        
        logger.info(f"Cleaned: {len(customers_clean)} customers, {len(orders_clean)} valid orders")
        logger.info(f"Invalid orders: {len(orders_invalid)}")
        
        # Step 3: Load into database
        logger.info("\n" + "="*80)
        logger.info("STEP 3: Loading data into MySQL database...")
        logger.info("="*80)
        
        db_loader = DatabaseLoader()
        
        # Load customers
        customers_loaded = db_loader.load_customers(customers_clean)
        
        # Load orders
        orders_loaded = db_loader.load_orders(orders_clean)
        
        # Get final counts
        counts = db_loader.get_row_counts()
        logger.info(f"\nDatabase row counts:")
        logger.info(f"  - customers: {counts['customers']}")
        logger.info(f"  - orders: {counts['orders']}")
        
        # Close session
        db_loader.close()
        
        return customers_loaded, orders_loaded
        
    except Exception as e:
        logger.error(f"Failed to load data to database: {str(e)}")
        raise


if __name__ == "__main__":
    """Test data loading"""
    print("\n" + "="*80)
    print("DATABASE DATA LOADER")
    print("="*80)
    
    try:
        # Load data to database
        print("\nLoading data from CSV/XML files into MySQL database...")
        customers_loaded, orders_loaded = load_data_to_database()
        
        print("\n" + "="*80)
        print("DATA LOADING COMPLETED SUCCESSFULLY")
        print("="*80)
        print(f"\nRecords loaded:")
        print(f"  - Customers: {customers_loaded}")
        print(f"  - Orders: {orders_loaded}")
        
        # Verify data
        print("\nVerifying data in database...")
        db_loader = DatabaseLoader()
        counts = db_loader.get_row_counts()
        
        print(f"\nCurrent database state:")
        print(f"  - customers table: {counts['customers']} rows")
        print(f"  - orders table: {counts['orders']} rows")
        
        db_loader.close()
        
        print("\n" + "="*80)
        print("Next steps:")
        print("  1. Run db_queries.py to calculate KPIs from database")
        print("  2. Run main_db.py to execute complete pipeline")
        print("="*80)
        
    except Exception as e:
        print("\n" + "="*80)
        print("ERROR: Data loading failed")
        print("="*80)
        print(f"\nError details: {str(e)}")
        raise
