import pandas as pd
import numpy as np
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class KPICalculator:
    """
    Calculate various Key Performance Indicators (KPIs) from the data.
    """
    
    def __init__(self):
        logger.info("KPICalculator initialized")
        self.kpis = {}
    
    def calculate_all_kpis(self, merged_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate all KPIs from the merged customer-order data.
        
        Args:
            merged_df: DataFrame with merged customer and order data
            
        Returns:
            Dict containing all calculated KPIs
        """
        logger.info("Calculating all KPIs...")
        
        self.kpis = {
            'customer_metrics': self._calculate_customer_metrics(merged_df),
            'order_metrics': self._calculate_order_metrics(merged_df),
            'revenue_metrics': self._calculate_revenue_metrics(merged_df),
            'product_metrics': self._calculate_product_metrics(merged_df),
            'regional_metrics': self._calculate_regional_metrics(merged_df),
            'temporal_metrics': self._calculate_temporal_metrics(merged_df),
            'top_performers': self._calculate_top_performers(merged_df)
        }
        
        logger.info("All KPIs calculated successfully")
        return self.kpis
    
    def _calculate_customer_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate customer-related KPIs."""
        logger.info("Calculating customer metrics...")
        
        # Group by customer
        customer_stats = df.groupby('customer_id').agg({
            'order_id': 'nunique',  # Number of unique orders
            'total_amount': lambda x: df[df['customer_id'] == x.name].groupby('order_id')['total_amount'].first().sum(),  # Total revenue per customer
            'sku_id': 'count'  # Total items purchased
        }).reset_index()
        
        customer_stats.columns = ['customer_id', 'total_orders', 'total_revenue', 'total_items']
        
        # Calculate average order value per customer
        customer_stats['avg_order_value'] = customer_stats['total_revenue'] / customer_stats['total_orders']
        
        metrics = {
            'total_customers': df['customer_id'].nunique(),
            'avg_orders_per_customer': customer_stats['total_orders'].mean(),
            'avg_revenue_per_customer': customer_stats['total_revenue'].mean(),
            'avg_items_per_customer': customer_stats['total_items'].mean(),
            'customer_details': customer_stats.to_dict('records')
        }
        
        return metrics
    
    def _calculate_order_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate order-related KPIs."""
        logger.info("Calculating order metrics...")
        
        # Group by order_id to get order-level metrics
        order_stats = df.groupby('order_id').agg({
            'total_amount': 'first',  # Order total (same for all items in order)
            'sku_id': 'count',  # Number of SKUs per order
            'sku_count': 'sum',  # Total quantity in order
            'order_date_time': 'first'
        }).reset_index()
        
        order_stats.columns = ['order_id', 'order_value', 'unique_skus', 'total_quantity', 'order_date']
        
        metrics = {
            'total_orders': df['order_id'].nunique(),
            'total_order_line_items': len(df),
            'avg_items_per_order': order_stats['unique_skus'].mean(),
            'avg_quantity_per_order': order_stats['total_quantity'].mean(),
            'avg_order_value': order_stats['order_value'].mean(),
            'min_order_value': order_stats['order_value'].min(),
            'max_order_value': order_stats['order_value'].max(),
            'median_order_value': order_stats['order_value'].median()
        }
        
        return metrics
    
    def _calculate_revenue_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate revenue-related KPIs."""
        logger.info("Calculating revenue metrics...")
        
        # Get unique orders with their amounts
        order_revenue = df.groupby('order_id')['total_amount'].first()
        
        metrics = {
            'total_revenue': order_revenue.sum(),
            'avg_revenue_per_order': order_revenue.mean(),
            'total_items_sold': df['sku_count'].sum(),
            'avg_revenue_per_item': order_revenue.sum() / df['sku_count'].sum() if df['sku_count'].sum() > 0 else 0
        }
        
        return metrics
    
    def _calculate_product_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate product/SKU-related KPIs."""
        logger.info("Calculating product metrics...")
        
        # SKU analysis
        sku_stats = df.groupby('sku_id').agg({
            'sku_count': 'sum',  # Total quantity sold
            'order_id': 'nunique',  # Number of orders containing this SKU
            'total_amount': lambda x: len(x)  # Frequency in order lines
        }).reset_index()
        
        sku_stats.columns = ['sku_id', 'total_quantity_sold', 'orders_count', 'line_items']
        sku_stats = sku_stats.sort_values('total_quantity_sold', ascending=False)
        
        metrics = {
            'total_unique_skus': df['sku_id'].nunique(),
            'most_sold_sku': sku_stats.iloc[0]['sku_id'] if len(sku_stats) > 0 else None,
            'most_sold_sku_quantity': sku_stats.iloc[0]['total_quantity_sold'] if len(sku_stats) > 0 else 0,
            'avg_quantity_per_sku': sku_stats['total_quantity_sold'].mean(),
            'sku_performance': sku_stats.head(10).to_dict('records')  # Top 10 SKUs
        }
        
        return metrics
    
    def _calculate_regional_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate region-based KPIs."""
        logger.info("Calculating regional metrics...")
        
        # Get unique orders per region
        regional_orders = df.groupby('region').agg({
            'order_id': 'nunique',
            'customer_id': 'nunique'
        }).reset_index()
        
        # Calculate revenue per region (sum unique order amounts)
        regional_revenue = []
        for region in df['region'].unique():
            region_df = df[df['region'] == region]
            region_order_revenue = region_df.groupby('order_id')['total_amount'].first().sum()
            regional_revenue.append({
                'region': region,
                'revenue': region_order_revenue
            })
        
        regional_revenue_df = pd.DataFrame(regional_revenue)
        
        # Merge with order stats
        regional_stats = regional_orders.merge(regional_revenue_df, on='region')
        regional_stats.columns = ['region', 'total_orders', 'total_customers', 'total_revenue']
        regional_stats['avg_revenue_per_customer'] = regional_stats['total_revenue'] / regional_stats['total_customers']
        regional_stats = regional_stats.sort_values('total_revenue', ascending=False)
        
        metrics = {
            'regions_count': df['region'].nunique(),
            'top_revenue_region': regional_stats.iloc[0]['region'] if len(regional_stats) > 0 else None,
            'regional_breakdown': regional_stats.to_dict('records')
        }
        
        return metrics
    
    def _calculate_temporal_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate time-based KPIs."""
        logger.info("Calculating temporal metrics...")
        
        # Orders by month
        monthly_orders = df.groupby(['order_year', 'order_month']).agg({
            'order_id': 'nunique'
        }).reset_index()
        monthly_orders.columns = ['year', 'month', 'order_count']
        
        # Orders by weekday
        weekday_orders = df.groupby('order_weekday')['order_id'].nunique().reset_index()
        weekday_orders.columns = ['weekday', 'order_count']
        
        # Orders by hour
        hourly_orders = df.groupby('order_hour')['order_id'].nunique().reset_index()
        hourly_orders.columns = ['hour', 'order_count']
        
        metrics = {
            'date_range': {
                'first_order': df['order_date_time'].min().strftime('%Y-%m-%d %H:%M:%S') if pd.notna(df['order_date_time'].min()) else None,
                'last_order': df['order_date_time'].max().strftime('%Y-%m-%d %H:%M:%S') if pd.notna(df['order_date_time'].max()) else None
            },
            'monthly_breakdown': monthly_orders.to_dict('records'),
            'weekday_breakdown': weekday_orders.to_dict('records'),
            'hourly_breakdown': hourly_orders.to_dict('records'),
            'busiest_hour': hourly_orders.loc[hourly_orders['order_count'].idxmax(), 'hour'] if len(hourly_orders) > 0 else None,
            'busiest_weekday': weekday_orders.loc[weekday_orders['order_count'].idxmax(), 'weekday'] if len(weekday_orders) > 0 else None
        }
        
        return metrics
    
    def _calculate_top_performers(self, df: pd.DataFrame) -> Dict:
        """Identify top performing customers, products, etc."""
        logger.info("Calculating top performers...")
        
        # Top customers by revenue
        customer_revenue = []
        for customer in df['customer_id'].unique():
            customer_df = df[df['customer_id'] == customer]
            revenue = customer_df.groupby('order_id')['total_amount'].first().sum()
            customer_revenue.append({
                'customer_id': customer,
                'customer_name': customer_df['customer_name'].iloc[0],
                'region': customer_df['region'].iloc[0],
                'total_revenue': revenue,
                'total_orders': customer_df['order_id'].nunique()
            })
        
        top_customers_df = pd.DataFrame(customer_revenue).sort_values('total_revenue', ascending=False)
        
        metrics = {
            'top_5_customers': top_customers_df.head(5).to_dict('records'),
            'top_customer_revenue': top_customers_df.iloc[0]['total_revenue'] if len(top_customers_df) > 0 else 0
        }
        
        return metrics
    
    def print_kpi_summary(self):
        """Print a formatted summary of all KPIs."""
        if not self.kpis:
            logger.warning("No KPIs calculated yet. Run calculate_all_kpis() first.")
            return
        
        print("\n" + "="*80)
        print("KPI DASHBOARD - SUMMARY REPORT")
        print("="*80)
        
        # Customer Metrics
        print("\n📊 CUSTOMER METRICS")
        print("-" * 80)
        cm = self.kpis['customer_metrics']
        print(f"Total Customers: {cm['total_customers']}")
        print(f"Avg Orders per Customer: {cm['avg_orders_per_customer']:.2f}")
        print(f"Avg Revenue per Customer: ₹{cm['avg_revenue_per_customer']:.2f}")
        print(f"Avg Items per Customer: {cm['avg_items_per_customer']:.2f}")
        
        # Order Metrics
        print("\n📦 ORDER METRICS")
        print("-" * 80)
        om = self.kpis['order_metrics']
        print(f"Total Orders: {om['total_orders']}")
        print(f"Total Order Line Items: {om['total_order_line_items']}")
        print(f"Avg Items per Order: {om['avg_items_per_order']:.2f}")
        print(f"Avg Order Value: ₹{om['avg_order_value']:.2f}")
        print(f"Order Value Range: ₹{om['min_order_value']:.2f} - ₹{om['max_order_value']:.2f}")
        
        # Revenue Metrics
        print("\n💰 REVENUE METRICS")
        print("-" * 80)
        rm = self.kpis['revenue_metrics']
        print(f"Total Revenue: ₹{rm['total_revenue']:.2f}")
        print(f"Total Items Sold: {rm['total_items_sold']}")
        print(f"Avg Revenue per Item: ₹{rm['avg_revenue_per_item']:.2f}")
        
        # Product Metrics
        print("\n🏷️  PRODUCT METRICS")
        print("-" * 80)
        pm = self.kpis['product_metrics']
        print(f"Total Unique SKUs: {pm['total_unique_skus']}")
        print(f"Most Sold SKU: {pm['most_sold_sku']} (Qty: {pm['most_sold_sku_quantity']})")
        
        # Regional Metrics
        print("\n🌍 REGIONAL METRICS")
        print("-" * 80)
        reg = self.kpis['regional_metrics']
        print(f"Regions: {reg['regions_count']}")
        print(f"Top Revenue Region: {reg['top_revenue_region']}")
        print("\nRegional Breakdown:")
        for region_data in reg['regional_breakdown']:
            print(f"  {region_data['region']}: ₹{region_data['total_revenue']:.2f} "
                  f"({region_data['total_orders']} orders, {region_data['total_customers']} customers)")
        
        # Temporal Metrics
        print("\n⏰ TEMPORAL METRICS")
        print("-" * 80)
        tm = self.kpis['temporal_metrics']
        print(f"Date Range: {tm['date_range']['first_order']} to {tm['date_range']['last_order']}")
        print(f"Busiest Hour: {tm['busiest_hour']}:00")
        print(f"Busiest Weekday: {tm['busiest_weekday']}")
        
        # Top Performers
        print("\n🏆 TOP PERFORMERS")
        print("-" * 80)
        tp = self.kpis['top_performers']
        print("Top 5 Customers by Revenue:")
        for i, customer in enumerate(tp['top_5_customers'], 1):
            print(f"  {i}. {customer['customer_name']} ({customer['customer_id']}): "
                  f"₹{customer['total_revenue']:.2f} ({customer['total_orders']} orders)")
        
        print("\n" + "="*80)


# Example usage
if __name__ == "__main__":
    from data_loader import DataLoader
    from data_cleaner import DataCleaner
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load and clean data
    loader = DataLoader()
    customers, orders = loader.load_all_data()
    
    cleaner = DataCleaner()
    customers_clean = cleaner.clean_customers(customers)
    orders_clean, orders_invalid = cleaner.clean_orders(orders)
    merged = cleaner.merge_customer_orders(customers_clean, orders_clean)
    
    # Calculate KPIs
    kpi_calc = KPICalculator()
    kpis = kpi_calc.calculate_all_kpis(merged)
    
    # Print summary
    kpi_calc.print_kpi_summary()
    
    # Access specific KPIs
    print("\n\nDetailed Customer Metrics:")
    print(kpi_calc.kpis['customer_metrics']['customer_details'])
