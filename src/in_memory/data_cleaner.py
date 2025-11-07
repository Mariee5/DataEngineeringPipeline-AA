import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import Tuple, Dict

logger = logging.getLogger(__name__)


class DataCleaner:
    """
    Handles data cleaning and transformation for customers and orders.
    """
    
    def __init__(self):
        logger.info("DataCleaner initialized")
        self.cleaning_stats = {
            'customers': {},
            'orders': {}
        }
    
    def clean_customers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean customer data:
        - Remove duplicates
        - Validate required fields
        - Standardize formats
        """
        logger.info("Starting customer data cleaning...")
        original_count = len(df)
        
        #Creating a copy to avoid modifying original
        df_clean = df.copy()
        
        #1.Removing duplicates based on customer_id
        duplicates = df_clean.duplicated(subset=['customer_id'], keep='first')
        df_clean = df_clean[~duplicates]
        logger.info(f"Removed {duplicates.sum()} duplicate customers")
        
        #2.Checking for missing values
        missing_before = df_clean.isnull().sum().to_dict()
        logger.info(f"Missing values before cleaning: {missing_before}")
        
        #Remove rows with missing critical fields
        df_clean = df_clean.dropna(subset=['customer_id', 'mobile_number'])
        
        #Fill missing names with 'Unknown'
        df_clean['customer_name'] = df_clean['customer_name'].fillna('Unknown')
        
        #Fill missing regions with 'Unknown'
        df_clean['region'] = df_clean['region'].fillna('Unknown')
        
        #3.Standardizing mobile numbers (remove spaces, ensure 10 digits)
        df_clean['mobile_number'] = df_clean['mobile_number'].astype(str).str.strip()
        
        #4.Standardizing region names (capitalize)
        df_clean['region'] = df_clean['region'].str.strip().str.title()
        
        #Store cleaning stats
        self.cleaning_stats['customers'] = {
            'original_count': original_count,
            'final_count': len(df_clean),
            'duplicates_removed': duplicates.sum(),
            'rows_dropped': original_count - len(df_clean)
        }
        
        logger.info(f"Customer cleaning complete: {original_count} -> {len(df_clean)} records")
        return df_clean
    
    def clean_orders(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Clean order data:
        - Validate data types
        - Handle missing/invalid values
        - Parse dates
        - Identify invalid records
        
        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: (clean_orders, invalid_orders)
        """
        logger.info("Starting order data cleaning...")
        original_count = len(df)
        
        # Create a copy
        df_clean = df.copy()
        
        # Track invalid records
        invalid_records = []
        
        # 1. Convert data types and handle errors
        # Handle sku_count (should be integer)
        df_clean['sku_count'] = pd.to_numeric(df_clean['sku_count'], errors='coerce')
        
        # Handle total_amount (should be float)
        df_clean['total_amount'] = pd.to_numeric(df_clean['total_amount'], errors='coerce')
        
        # 2. Identify invalid records
        # Empty/missing sku_count
        invalid_sku_count = df_clean['sku_count'].isna()
        if invalid_sku_count.any():
            logger.warning(f"Found {invalid_sku_count.sum()} orders with missing/invalid sku_count")
            invalid_records.append(df_clean[invalid_sku_count].copy())
        
        # Negative or zero sku_count
        invalid_negative_count = (df_clean['sku_count'] <= 0) & (~df_clean['sku_count'].isna())
        if invalid_negative_count.any():
            logger.warning(f"Found {invalid_negative_count.sum()} orders with negative/zero sku_count")
            invalid_records.append(df_clean[invalid_negative_count].copy())
        
        # Negative total_amount (refunds/returns - flag for review)
        invalid_negative_amount = (df_clean['total_amount'] < 0) & (~df_clean['total_amount'].isna())
        if invalid_negative_amount.any():
            logger.warning(f"Found {invalid_negative_amount.sum()} orders with negative total_amount")
            invalid_records.append(df_clean[invalid_negative_amount].copy())
        
        # Missing critical fields
        invalid_missing = df_clean[['order_id', 'mobile_number', 'sku_id']].isna().any(axis=1)
        if invalid_missing.any():
            logger.warning(f"Found {invalid_missing.sum()} orders with missing critical fields")
            invalid_records.append(df_clean[invalid_missing].copy())
        
        # Combine all invalid records
        invalid_mask = (invalid_sku_count | invalid_negative_count | 
                       invalid_negative_amount | invalid_missing)
        
        df_invalid = df_clean[invalid_mask].copy()
        df_clean = df_clean[~invalid_mask].copy()
        
        # 3. Parse dates
        df_clean['order_date_time'] = pd.to_datetime(
            df_clean['order_date_time'], 
            errors='coerce'
        )
        
        # Check for invalid dates
        invalid_dates = df_clean['order_date_time'].isna()
        if invalid_dates.any():
            logger.warning(f"Found {invalid_dates.sum()} orders with invalid dates")
        
        # 4. Extract date components for analysis
        df_clean['order_date'] = df_clean['order_date_time'].dt.date
        df_clean['order_year'] = df_clean['order_date_time'].dt.year
        df_clean['order_month'] = df_clean['order_date_time'].dt.month
        df_clean['order_day'] = df_clean['order_date_time'].dt.day
        df_clean['order_hour'] = df_clean['order_date_time'].dt.hour
        df_clean['order_weekday'] = df_clean['order_date_time'].dt.day_name()
        
        # 5. Ensure correct data types
        df_clean['sku_count'] = df_clean['sku_count'].astype(int)
        df_clean['mobile_number'] = df_clean['mobile_number'].astype(str).str.strip()
        
        # Store cleaning stats
        self.cleaning_stats['orders'] = {
            'original_count': original_count,
            'valid_count': len(df_clean),
            'invalid_count': len(df_invalid),
            'rows_with_missing_sku_count': invalid_sku_count.sum(),
            'rows_with_negative_count': invalid_negative_count.sum(),
            'rows_with_negative_amount': invalid_negative_amount.sum(),
            'rows_with_invalid_dates': invalid_dates.sum()
        }
        
        logger.info(f"Order cleaning complete: {original_count} -> {len(df_clean)} valid, {len(df_invalid)} invalid")
        
        return df_clean, df_invalid
    
    def merge_customer_orders(self, customers_df: pd.DataFrame, 
                             orders_df: pd.DataFrame) -> pd.DataFrame:
        """
        Merge customer and order data.
        
        Returns:
            pd.DataFrame: Merged dataset with customer and order information
        """
        logger.info("Merging customer and order data...")
        
        # Merge on mobile_number
        merged_df = orders_df.merge(
            customers_df,
            on='mobile_number',
            how='left',
            suffixes=('_order', '_customer')
        )
        
        # Check for orders without matching customers
        unmatched = merged_df['customer_id'].isna().sum()
        if unmatched > 0:
            logger.warning(f"Found {unmatched} orders without matching customers")
        
        logger.info(f"Merged dataset shape: {merged_df.shape}")
        
        return merged_df
    
    def get_cleaning_summary(self) -> Dict:
        """Return summary of cleaning operations."""
        return self.cleaning_stats


# Example usage
if __name__ == "__main__":
    from data_loader import DataLoader
    from pathlib import Path
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load data
    loader = DataLoader()
    customers, orders = loader.load_all_data()
    
    # Clean data
    cleaner = DataCleaner()
    
    customers_clean = cleaner.clean_customers(customers)
    orders_clean, orders_invalid = cleaner.clean_orders(orders)
    
    print("\n=== CLEANING SUMMARY ===")
    print(cleaner.get_cleaning_summary())
    
    print("\n=== CLEAN CUSTOMERS ===")
    print(customers_clean.head())
    
    print("\n=== CLEAN ORDERS ===")
    print(orders_clean.head())
    
    print("\n=== INVALID ORDERS (for review) ===")
    print(orders_invalid)
    
    # Merge data
    merged = cleaner.merge_customer_orders(customers_clean, orders_clean)
    print("\n=== MERGED DATA ===")
    print(merged.head())
    print(f"\nMerged shape: {merged.shape}")
