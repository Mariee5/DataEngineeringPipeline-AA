"""
Database Query Module - KPI Calculations
SECURITY: Uses SQLAlchemy ORM and parameterized queries ONLY - NO string concatenation
All KPIs calculated using secure SQL queries from MySQL database
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd
from sqlalchemy import func, and_, extract, desc
from sqlalchemy.exc import SQLAlchemyError

from db_config import get_database_engine
from db_schema import Customer, Order, get_session

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KPICalculator:
    """
    Calculate KPIs from database using secure SQL queries
    SECURITY: All queries use SQLAlchemy ORM - fully parameterized
    """
    
    def __init__(self, engine=None):
        """
        Initialize KPI calculator
        
        Args:
            engine: SQLAlchemy engine (optional, will create if not provided)
        """
        self.engine = engine if engine else get_database_engine()
        self.session = get_session(self.engine)
        logger.info("KPICalculator initialized")
    
    def get_repeat_customers(self) -> pd.DataFrame:
        """
        KPI 1: Identify customers with more than one order
        SECURITY: Uses SQLAlchemy ORM with parameterized filtering
        
        Returns:
            DataFrame: Customers with order count > 1
        """
        try:
            logger.info("Calculating repeat customers...")
            
            # SECURITY: SQLAlchemy query() with func.count() - fully parameterized
            # No string concatenation
            query = (
                self.session.query(
                    Customer.customer_id,
                    Customer.customer_name,
                    Customer.region,
                    func.count(func.distinct(Order.order_id)).label('order_count')
                )
                .join(Order, Customer.mobile_number == Order.mobile_number)
                .group_by(Customer.customer_id, Customer.customer_name, Customer.region)
                .having(func.count(func.distinct(Order.order_id)) > 1)
                .order_by(desc('order_count'))
            )
            
            # Convert to DataFrame
            df = pd.read_sql(query.statement, self.session.bind)
            
            logger.info(f"Found {len(df)} repeat customers")
            return df
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to calculate repeat customers: {str(e)}")
            raise
    
    def get_monthly_order_trends(self) -> pd.DataFrame:
        """
        KPI 2: Aggregate orders by month to observe trends
        SECURITY: Uses SQLAlchemy extract() and func - fully parameterized
        
        FIXED: Deduplicates by order_id to avoid counting same order total multiple times
        (XML has total_amount repeated across line items of same order)
        
        Returns:
            DataFrame: Order counts and revenue by month
        """
        try:
            logger.info("Calculating monthly order trends...")
            
            # SECURITY: Create subquery to get one row per order_id (deduplication)
            # This handles the XML structure where total_amount is repeated for all line items
            from sqlalchemy import distinct
            from sqlalchemy.sql import select
            
            # Subquery: Get distinct orders with their total_amount (take MIN to get first value)
            subquery = (
                self.session.query(
                    Order.order_id,
                    func.min(Order.order_date_time).label('order_date_time'),
                    func.min(Order.total_amount).label('total_amount')  # Take first occurrence
                )
                .group_by(Order.order_id)
                .subquery()
            )
            
            # Main query: Aggregate by month using deduplicated orders
            query = (
                self.session.query(
                    extract('year', subquery.c.order_date_time).label('year'),
                    extract('month', subquery.c.order_date_time).label('month'),
                    func.count(subquery.c.order_id).label('order_count'),
                    func.sum(subquery.c.total_amount).label('total_revenue'),
                    func.avg(subquery.c.total_amount).label('avg_order_value')
                )
                .group_by('year', 'month')
                .order_by('year', 'month')
            )
            
            # Convert to DataFrame
            df = pd.read_sql(query.statement, self.session.bind)
            
            # Format year-month for readability
            if not df.empty:
                df['year_month'] = df['year'].astype(int).astype(str) + '-' + df['month'].astype(int).astype(str).str.zfill(2)
            
            logger.info(f"Calculated trends for {len(df)} months (deduplicated by order_id)")
            return df
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to calculate monthly trends: {str(e)}")
            raise
    
    def get_regional_revenue(self) -> pd.DataFrame:
        """
        KPI 3: Sum of total_amount grouped by region
        SECURITY: Uses SQLAlchemy join and aggregation - fully parameterized
        
        FIXED: Deduplicates by order_id to avoid counting same order total multiple times
        (XML has total_amount repeated across line items of same order)
        
        Returns:
            DataFrame: Revenue metrics by region
        """
        try:
            logger.info("Calculating regional revenue...")
            
            # SECURITY: Create subquery to deduplicate orders first
            subquery = (
                self.session.query(
                    Order.order_id,
                    Order.mobile_number,
                    func.min(Order.total_amount).label('total_amount')  # Take first occurrence per order
                )
                .group_by(Order.order_id, Order.mobile_number)
                .subquery()
            )
            
            # Main query: Join with customers and aggregate by region
            query = (
                self.session.query(
                    Customer.region,
                    func.count(func.distinct(Customer.customer_id)).label('customer_count'),
                    func.count(subquery.c.order_id).label('order_count'),
                    func.sum(subquery.c.total_amount).label('total_revenue'),
                    func.avg(subquery.c.total_amount).label('avg_order_value')
                )
                .join(subquery, Customer.mobile_number == subquery.c.mobile_number)
                .group_by(Customer.region)
                .order_by(desc('total_revenue'))
            )
            
            # Convert to DataFrame
            df = pd.read_sql(query.statement, self.session.bind)
            
            logger.info(f"Calculated revenue for {len(df)} regions (deduplicated by order_id)")
            return df
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to calculate regional revenue: {str(e)}")
            raise
    
    def get_top_customers_last_30_days(self, days: int = 30) -> pd.DataFrame:
        """
        KPI 4: Rank customers by total spend in the last N days
        SECURITY: Uses SQLAlchemy parameterized date filtering
        
        FIXED: Deduplicates by order_id to avoid counting same order total multiple times
        (XML has total_amount repeated across line items of same order)
        
        Args:
            days: Number of days to look back (default 30)
            
        Returns:
            DataFrame: Top customers by spending in last N days
        """
        try:
            logger.info(f"Calculating top customers (last {days} days)...")
            
            # Calculate cutoff date
            # SECURITY: Using Python datetime, not SQL string concatenation
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # SECURITY: Create subquery to deduplicate orders first
            subquery = (
                self.session.query(
                    Order.order_id,
                    Order.mobile_number,
                    func.min(Order.order_date_time).label('order_date_time'),
                    func.min(Order.total_amount).label('total_amount')
                )
                .filter(Order.order_date_time >= cutoff_date)
                .group_by(Order.order_id, Order.mobile_number)
                .subquery()
            )
            
            # Main query: Join with customers and aggregate
            query = (
                self.session.query(
                    Customer.customer_id,
                    Customer.customer_name,
                    Customer.region,
                    func.count(subquery.c.order_id).label('order_count'),
                    func.sum(subquery.c.total_amount).label('total_spent'),
                    func.avg(subquery.c.total_amount).label('avg_order_value'),
                    func.max(subquery.c.order_date_time).label('last_order_date')
                )
                .join(subquery, Customer.mobile_number == subquery.c.mobile_number)
                .group_by(Customer.customer_id, Customer.customer_name, Customer.region)
                .order_by(desc('total_spent'))
            )
            
            # Convert to DataFrame
            df = pd.read_sql(query.statement, self.session.bind)
            
            logger.info(f"Found {len(df)} customers with orders in last {days} days (deduplicated by order_id)")
            return df
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to calculate top customers: {str(e)}")
            raise
    
    def get_all_kpis(self) -> Dict[str, pd.DataFrame]:
        """
        Calculate all KPIs
        SECURITY: All queries use parameterized SQLAlchemy methods
        
        Returns:
            Dict[str, DataFrame]: All KPI results
        """
        try:
            logger.info("Calculating all KPIs from database...")
            
            kpis = {
                'repeat_customers': self.get_repeat_customers(),
                'monthly_trends': self.get_monthly_order_trends(),
                'regional_revenue': self.get_regional_revenue(),
                'top_customers_30_days': self.get_top_customers_last_30_days(30)
            }
            
            logger.info("All KPIs calculated successfully")
            return kpis
            
        except Exception as e:
            logger.error(f"Failed to calculate KPIs: {str(e)}")
            raise
    
    def print_kpi_summary(self, kpis: Dict[str, pd.DataFrame]):
        """
        Print KPI summary to console
        
        Args:
            kpis: Dictionary of KPI DataFrames
        """
        print("\n" + "="*80)
        print("KPI DASHBOARD - DATABASE RESULTS")
        print("="*80)
        
        # Repeat Customers
        print("\n1. REPEAT CUSTOMERS (Customers with >1 order):")
        print("-" * 80)
        if not kpis['repeat_customers'].empty:
            print(kpis['repeat_customers'].to_string(index=False))
        else:
            print("No repeat customers found")
        
        # Monthly Trends
        print("\n2. MONTHLY ORDER TRENDS:")
        print("-" * 80)
        if not kpis['monthly_trends'].empty:
            print(kpis['monthly_trends'][['year_month', 'order_count', 'total_revenue', 'avg_order_value']].to_string(index=False))
        else:
            print("No monthly trends data")
        
        # Regional Revenue
        print("\n3. REGIONAL REVENUE:")
        print("-" * 80)
        if not kpis['regional_revenue'].empty:
            print(kpis['regional_revenue'].to_string(index=False))
        else:
            print("No regional revenue data")
        
        # Top Customers
        print("\n4. TOP CUSTOMERS (Last 30 Days):")
        print("-" * 80)
        if not kpis['top_customers_30_days'].empty:
            print(kpis['top_customers_30_days'].head(10).to_string(index=False))
        else:
            print("No customers with orders in last 30 days")
        
        print("\n" + "="*80)
    
    def close(self):
        """Close database session"""
        if self.session:
            self.session.close()
            logger.info("Database session closed")


if __name__ == "__main__":
    """Test KPI calculations"""
    print("\n" + "="*80)
    print("DATABASE KPI CALCULATOR")
    print("="*80)
    
    try:
        # Calculate KPIs
        print("\nCalculating KPIs from MySQL database...")
        calculator = KPICalculator()
        
        kpis = calculator.get_all_kpis()
        
        # Print summary
        calculator.print_kpi_summary(kpis)
        
        # Save KPIs to files
        print("\nSaving KPI results to files...")
        output_dir = calculator.engine.url.database + "_kpis"
        
        # Save each KPI to CSV
        kpis['repeat_customers'].to_csv(f'repeat_customers.csv', index=False)
        kpis['monthly_trends'].to_csv(f'monthly_trends.csv', index=False)
        kpis['regional_revenue'].to_csv(f'regional_revenue.csv', index=False)
        kpis['top_customers_30_days'].to_csv(f'top_customers_30_days.csv', index=False)
        
        print("✓ KPI results saved to CSV files")
        
        # Close session
        calculator.close()
        
        print("\n" + "="*80)
        print("KPI CALCULATION COMPLETED SUCCESSFULLY")
        print("="*80)
        print("\nNext steps:")
        print("  1. Review KPI results above")
        print("  2. Run main_db.py to execute complete pipeline with reports")
        print("="*80)
        
    except Exception as e:
        print("\n" + "="*80)
        print("ERROR: KPI calculation failed")
        print("="*80)
        print(f"\nError details: {str(e)}")
        raise
