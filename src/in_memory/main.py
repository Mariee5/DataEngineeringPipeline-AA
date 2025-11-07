"""
Akasa Air Data Engineering Pipeline - Main Execution Script

This script orchestrates the entire data pipeline:
1. Load data from CSV and XML files
2. Clean and validate data
3. Calculate KPIs
4. Generate reports
5. (Future) Store results in MySQL database

Author: Data Engineering Team
Date: November 2025
"""

import sys
import pandas as pd

# Fix Windows console encoding for special characters
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
import logging
from pathlib import Path
from datetime import datetime
import json

from data_loader import DataLoader
from data_cleaner import DataCleaner
from kpi_calculator import KPICalculator


# Configure logging
def setup_logging():
    """Setup logging configuration."""
    # Create logs directory
    Path('logs').mkdir(exist_ok=True)
    
    # Get current timestamp for log file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'logs/pipeline_{timestamp}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)


def save_results(customers_clean, orders_clean, orders_invalid, merged, kpis):
    """
    Save processing results to files (CSV, JSON, Excel).
    
    Args:
        customers_clean: Cleaned customer DataFrame
        orders_clean: Cleaned orders DataFrame
        orders_invalid: Invalid orders DataFrame
        merged: Merged customer-order DataFrame
        kpis: Dictionary of calculated KPIs
    """
    # Create outputs directory (use project root)
    from pathlib import Path
    PROJECT_ROOT = Path(__file__).parent.parent
    outputs_dir = PROJECT_ROOT / 'outputs'
    outputs_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save cleaned data as CSV
    customers_clean.to_csv(outputs_dir / f'customers_clean_{timestamp}.csv', index=False)
    orders_clean.to_csv(outputs_dir / f'orders_clean_{timestamp}.csv', index=False)
    
    if len(orders_invalid) > 0:
        orders_invalid.to_csv(outputs_dir / f'orders_invalid_{timestamp}.csv', index=False)
    
    merged.to_csv(outputs_dir / f'merged_data_{timestamp}.csv', index=False)
    
    # Save KPIs as JSON
    # Convert DataFrames in KPIs to serializable format
    kpis_serializable = {}
    for category, data in kpis.items():
        if isinstance(data, dict):
            kpis_serializable[category] = data
        else:
            kpis_serializable[category] = str(data)
    
    with open(outputs_dir / f'kpis_{timestamp}.json', 'w') as f:
        json.dump(kpis_serializable, f, indent=2, default=str)
    
    # Save KPIs to Excel with multiple sheets
    try:
        excel_path = outputs_dir / f'in_memory_kpis_{timestamp}.xlsx'
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Create summary sheet with key metrics
            summary_data = {
                'Metric': [
                    'Total Customers',
                    'Avg Orders per Customer',
                    'Avg Revenue per Customer',
                    'Total Orders',
                    'Avg Order Value',
                    'Total Revenue',
                    'Total Items Sold',
                    'Total Unique SKUs',
                    'Most Sold SKU'
                ],
                'Value': [
                    kpis.get('customer_metrics', {}).get('total_customers', 'N/A'),
                    f"{kpis.get('customer_metrics', {}).get('avg_orders_per_customer', 0):.2f}",
                    f"₹{kpis.get('customer_metrics', {}).get('avg_revenue_per_customer', 0):.2f}",
                    kpis.get('order_metrics', {}).get('total_orders', 'N/A'),
                    f"₹{kpis.get('order_metrics', {}).get('avg_order_value', 0):.2f}",
                    f"₹{kpis.get('revenue_metrics', {}).get('total_revenue', 0):.2f}",
                    kpis.get('revenue_metrics', {}).get('total_items_sold', 'N/A'),
                    kpis.get('product_metrics', {}).get('total_unique_skus', 'N/A'),
                    kpis.get('product_metrics', {}).get('most_sold_sku', 'N/A')
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Add detailed sheets for nested data
            if 'customer_metrics' in kpis and 'customer_details' in kpis['customer_metrics']:
                cust_details_df = pd.DataFrame(kpis['customer_metrics']['customer_details'])
                cust_details_df.to_excel(writer, sheet_name='Customer Details', index=False)
            
            if 'product_metrics' in kpis and 'sku_performance' in kpis['product_metrics']:
                sku_df = pd.DataFrame(kpis['product_metrics']['sku_performance'])
                sku_df.to_excel(writer, sheet_name='SKU Performance', index=False)
            
            if 'regional_metrics' in kpis and 'revenue_by_region' in kpis['regional_metrics']:
                regional_df = pd.DataFrame(kpis['regional_metrics']['revenue_by_region'])
                regional_df.to_excel(writer, sheet_name='Regional Revenue', index=False)
            
            if 'top_performers' in kpis and 'top_5_customers' in kpis['top_performers']:
                top_cust_df = pd.DataFrame(kpis['top_performers']['top_5_customers'])
                top_cust_df.to_excel(writer, sheet_name='Top Customers', index=False)
            
            # Auto-adjust column widths for all sheets
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
        
        logging.info(f"Excel report saved to {excel_path}")
    except Exception as e:
        logging.warning(f"Failed to save Excel file: {e}")
    
    logging.info(f"Results saved to {outputs_dir}/")
    
    return outputs_dir


def generate_summary_report(cleaner, kpis, output_dir):
    """
    Generate a human-readable summary report.
    
    Args:
        cleaner: DataCleaner instance with cleaning stats
        kpis: Dictionary of calculated KPIs
        output_dir: Directory to save the report
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    report_lines = [
        "="*80,
        "AKASA AIR - DATA PIPELINE SUMMARY REPORT",
        "="*80,
        f"Generated: {timestamp}",
        "",
        "DATA QUALITY SUMMARY",
        "-"*80,
    ]
    
    # Add cleaning stats
    cleaning_stats = cleaner.get_cleaning_summary()
    
    report_lines.extend([
        "",
        "Customer Data:",
        f"  Original Records: {cleaning_stats['customers'].get('original_count', 'N/A')}",
        f"  Clean Records: {cleaning_stats['customers'].get('final_count', 'N/A')}",
        f"  Duplicates Removed: {cleaning_stats['customers'].get('duplicates_removed', 'N/A')}",
        "",
        "Order Data:",
        f"  Original Records: {cleaning_stats['orders'].get('original_count', 'N/A')}",
        f"  Valid Records: {cleaning_stats['orders'].get('valid_count', 'N/A')}",
        f"  Invalid Records: {cleaning_stats['orders'].get('invalid_count', 'N/A')}",
        f"    - Missing SKU Count: {cleaning_stats['orders'].get('rows_with_missing_sku_count', 'N/A')}",
        f"    - Negative Count: {cleaning_stats['orders'].get('rows_with_negative_count', 'N/A')}",
        f"    - Negative Amount: {cleaning_stats['orders'].get('rows_with_negative_amount', 'N/A')}",
        "",
        "="*80,
        "KEY PERFORMANCE INDICATORS",
        "="*80,
        ""
    ])
    
    # Add KPI summary
    cm = kpis.get('customer_metrics', {})
    om = kpis.get('order_metrics', {})
    rm = kpis.get('revenue_metrics', {})
    pm = kpis.get('product_metrics', {})
    reg = kpis.get('regional_metrics', {})
    tm = kpis.get('temporal_metrics', {})
    tp = kpis.get('top_performers', {})
    
    report_lines.extend([
        "CUSTOMER METRICS:",
        f"  Total Customers: {cm.get('total_customers', 'N/A')}",
        f"  Avg Orders per Customer: {cm.get('avg_orders_per_customer', 0):.2f}",
        f"  Avg Revenue per Customer: ₹{cm.get('avg_revenue_per_customer', 0):.2f}",
        "",
        "ORDER METRICS:",
        f"  Total Orders: {om.get('total_orders', 'N/A')}",
        f"  Avg Order Value: ₹{om.get('avg_order_value', 0):.2f}",
        f"  Order Value Range: ₹{om.get('min_order_value', 0):.2f} - ₹{om.get('max_order_value', 0):.2f}",
        "",
        "REVENUE METRICS:",
        f"  Total Revenue: ₹{rm.get('total_revenue', 0):.2f}",
        f"  Total Items Sold: {rm.get('total_items_sold', 'N/A')}",
        "",
        "PRODUCT METRICS:",
        f"  Total Unique SKUs: {pm.get('total_unique_skus', 'N/A')}",
        f"  Most Sold SKU: {pm.get('most_sold_sku', 'N/A')} (Qty: {pm.get('most_sold_sku_quantity', 0)})",
        "",
        "REGIONAL METRICS:",
        f"  Top Revenue Region: {reg.get('top_revenue_region', 'N/A')}",
        "",
        "TEMPORAL METRICS:",
        f"  Busiest Hour: {tm.get('busiest_hour', 'N/A')}:00",
        f"  Busiest Weekday: {tm.get('busiest_weekday', 'N/A')}",
        "",
        "TOP CUSTOMER:",
    ])
    
    if tp.get('top_5_customers'):
        top_cust = tp['top_5_customers'][0]
        report_lines.append(
            f"  {top_cust.get('customer_name', 'N/A')} - "
            f"₹{top_cust.get('total_revenue', 0):.2f} ({top_cust.get('total_orders', 0)} orders)"
        )
    
    report_lines.extend([
        "",
        "="*80,
        "END OF REPORT",
        "="*80
    ])
    
    # Write to file
    report_file = output_dir / f'summary_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    # Also print to console
    print('\n'.join(report_lines))
    
    logging.info(f"Summary report saved to {report_file}")


def main():
    """Main pipeline execution function."""
    
    logger = setup_logging()
    
    logger.info("="*80)
    logger.info("STARTING AKASA AIR DATA PIPELINE")
    logger.info("="*80)
    
    try:
        # Step 1: Load Data
        logger.info("\n[STEP 1/4] Loading data...")
        loader = DataLoader()
        customers, orders = loader.load_all_data()
        
        logger.info(f"Loaded {len(customers)} customers and {len(orders)} order line items")
        
        # Step 2: Clean Data
        logger.info("\n[STEP 2/4] Cleaning data...")
        cleaner = DataCleaner()
        
        customers_clean = cleaner.clean_customers(customers)
        orders_clean, orders_invalid = cleaner.clean_orders(orders)
        
        logger.info(f"Cleaning complete: {len(customers_clean)} clean customers, "
                   f"{len(orders_clean)} clean orders, {len(orders_invalid)} invalid orders")
        
        if len(orders_invalid) > 0:
            logger.warning(f"WARNING: Found {len(orders_invalid)} invalid order records:")
            print("\nInvalid Orders:")
            print(orders_invalid[['order_id', 'mobile_number', 'sku_id', 'sku_count', 'total_amount']])
        
        # Step 3: Merge Data
        logger.info("\n[STEP 3/4] Merging customer and order data...")
        merged = cleaner.merge_customer_orders(customers_clean, orders_clean)
        
        logger.info(f"Merged dataset created: {merged.shape[0]} rows, {merged.shape[1]} columns")
        
        # Step 4: Calculate KPIs
        logger.info("\n[STEP 4/4] Calculating KPIs...")
        kpi_calc = KPICalculator()
        kpis = kpi_calc.calculate_all_kpis(merged)
        
        logger.info("All KPIs calculated successfully")
        
        # Display KPI Dashboard
        # kpi_calc.print_kpi_summary()  # Commented out due to Windows console encoding issues
        print("\n✓ KPIs calculated successfully - see outputs directory for details")
        
        # Save Results
        logger.info("\nSaving results...")
        output_dir = save_results(customers_clean, orders_clean, orders_invalid, merged, kpis)
        
        # Generate Summary Report
        logger.info("\nGenerating summary report...")
        generate_summary_report(cleaner, kpis, output_dir)
        
        logger.info("\n" + "="*80)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY!")
        logger.info("="*80)
        
        # Future: MySQL integration
        logger.info("\nNext Steps:")
        logger.info("  - Results saved to 'outputs/' directory")
        logger.info("  - Review invalid orders in 'orders_invalid_*.csv'")
        logger.info("  - (Future) Integrate MySQL database for persistent storage")
        
        return {
            'customers_clean': customers_clean,
            'orders_clean': orders_clean,
            'orders_invalid': orders_invalid,
            'merged': merged,
            'kpis': kpis
        }
        
    except Exception as e:
        logger.error(f"❌ Pipeline failed with error: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    results = main()
