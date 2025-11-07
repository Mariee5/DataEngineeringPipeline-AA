# MySQL Database Integration Guide 

This guide explains how to integrate MySQL database with the Akasa Air Data Pipeline for persistent data storage.

##  Overview

The MySQL integration will:
- Store cleaned customer and order data
- Persist calculated KPIs
- Enable historical data tracking
- Support advanced analytics and queries
- Provide data backup and recovery

##  Database Schema Design

### Tables Structure

```sql
-- 1. Customers Table
CREATE TABLE customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    mobile_number VARCHAR(15) NOT NULL UNIQUE,
    region VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 2. Orders Table
CREATE TABLE orders (
    order_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(20),
    mobile_number VARCHAR(15) NOT NULL,
    order_date_time DATETIME NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    INDEX idx_order_date (order_date_time),
    INDEX idx_customer (customer_id)
);

-- 3. Order Line Items Table
CREATE TABLE order_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL,
    sku_id VARCHAR(20) NOT NULL,
    sku_count INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    INDEX idx_order (order_id),
    INDEX idx_sku (sku_id)
);

-- 4. KPIs Historical Table
CREATE TABLE kpi_snapshots (
    snapshot_id INT AUTO_INCREMENT PRIMARY KEY,
    snapshot_date DATETIME NOT NULL,
    metric_category VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_date (snapshot_date),
    INDEX idx_category (metric_category)
);

-- 5. Data Quality Log Table
CREATE TABLE data_quality_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    pipeline_run_date DATETIME NOT NULL,
    total_customers_loaded INT,
    total_orders_loaded INT,
    valid_orders INT,
    invalid_orders INT,
    issues_detected TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

##  Setup Instructions

### 1. Install MySQL

**Windows:**
- Download MySQL Installer from [mysql.com](https://dev.mysql.com/downloads/installer/)
- Run installer and choose "Developer Default"
- Set root password (remember this!)
- Complete installation

**Verify Installation:**
```powershell
mysql --version
```

### 2. Install Python MySQL Connector

```powershell
pip install mysql-connector-python pymysql sqlalchemy
```

Update `requirements.txt`:
```
pandas==2.1.4
lxml==5.1.0
python-dateutil==2.8.2
mysql-connector-python==8.2.0
pymysql==1.1.0
sqlalchemy==2.0.23
```

### 3. Create Database

```sql
-- Login to MySQL
mysql -u root -p

-- Create database
CREATE DATABASE akasa_data_pipeline;

-- Create user (optional, for security)
CREATE USER 'akasa_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON akasa_data_pipeline.* TO 'akasa_user'@'localhost';
FLUSH PRIVILEGES;

-- Use the database
USE akasa_data_pipeline;

-- Run schema creation (paste all CREATE TABLE statements above)
```

##  Implementation Code

### Create `src/db_manager.py`

```python
import mysql.connector
from mysql.connector import Error
import pandas as pd
import logging
from typing import Dict, Any, Optional
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages MySQL database connections and operations.
    """
    
    def __init__(self, config: Dict[str, str]):
        """
        Initialize database connection.
        
        Args:
            config: Dictionary with connection parameters
                   {host, user, password, database}
        """
        self.config = config
        self.connection = None
        self.cursor = None
        
    def connect(self):
        """Establish database connection."""
        try:
            self.connection = mysql.connector.connect(
                host=self.config['host'],
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database']
            )
            
            if self.connection.is_connected():
                self.cursor = self.connection.cursor()
                logger.info(" MySQL connection established")
                return True
                
        except Error as e:
            logger.error(f" Error connecting to MySQL: {e}")
            return False
    
    def disconnect(self):
        """Close database connection."""
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
            logger.info("MySQL connection closed")
    
    def insert_customers(self, customers_df: pd.DataFrame) -> int:
        """
        Insert customer data into database.
        
        Args:
            customers_df: DataFrame with customer data
            
        Returns:
            Number of records inserted
        """
        query = """
        INSERT INTO customers (customer_id, customer_name, mobile_number, region)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            customer_name = VALUES(customer_name),
            mobile_number = VALUES(mobile_number),
            region = VALUES(region)
        """
        
        try:
            records = customers_df[['customer_id', 'customer_name', 'mobile_number', 'region']].values.tolist()
            self.cursor.executemany(query, records)
            self.connection.commit()
            
            logger.info(f" Inserted/Updated {len(records)} customers")
            return len(records)
            
        except Error as e:
            logger.error(f" Error inserting customers: {e}")
            self.connection.rollback()
            return 0
    
    def insert_orders(self, orders_df: pd.DataFrame) -> int:
        """
        Insert order data into database.
        
        Args:
            orders_df: DataFrame with order data
            
        Returns:
            Number of orders inserted
        """
        # First, insert unique orders
        unique_orders = orders_df.groupby('order_id').agg({
            'customer_id': 'first',
            'mobile_number': 'first',
            'order_date_time': 'first',
            'total_amount': 'first'
        }).reset_index()
        
        order_query = """
        INSERT INTO orders (order_id, customer_id, mobile_number, order_date_time, total_amount)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            total_amount = VALUES(total_amount)
        """
        
        item_query = """
        INSERT INTO order_items (order_id, sku_id, sku_count)
        VALUES (%s, %s, %s)
        """
        
        try:
            # Insert orders
            order_records = unique_orders.values.tolist()
            self.cursor.executemany(order_query, order_records)
            
            # Insert order items
            item_records = orders_df[['order_id', 'sku_id', 'sku_count']].values.tolist()
            self.cursor.executemany(item_query, item_records)
            
            self.connection.commit()
            
            logger.info(f" Inserted {len(order_records)} orders with {len(item_records)} items")
            return len(order_records)
            
        except Error as e:
            logger.error(f" Error inserting orders: {e}")
            self.connection.rollback()
            return 0
    
    def save_kpi_snapshot(self, kpis: Dict[str, Any]) -> bool:
        """
        Save KPI snapshot to database.
        
        Args:
            kpis: Dictionary of KPI metrics
            
        Returns:
            Success status
        """
        query = """
        INSERT INTO kpi_snapshots (snapshot_date, metric_category, metric_name, metric_value)
        VALUES (%s, %s, %s, %s)
        """
        
        try:
            snapshot_date = datetime.now()
            records = []
            
            for category, metrics in kpis.items():
                if isinstance(metrics, dict):
                    for metric_name, metric_value in metrics.items():
                        # Convert complex values to JSON string
                        if isinstance(metric_value, (list, dict)):
                            metric_value = json.dumps(metric_value, default=str)
                        
                        records.append((snapshot_date, category, metric_name, str(metric_value)))
            
            self.cursor.executemany(query, records)
            self.connection.commit()
            
            logger.info(f" Saved {len(records)} KPI metrics")
            return True
            
        except Error as e:
            logger.error(f" Error saving KPIs: {e}")
            self.connection.rollback()
            return False
    
    def log_data_quality(self, stats: Dict[str, Any]) -> bool:
        """
        Log data quality metrics.
        
        Args:
            stats: Dictionary with quality statistics
            
        Returns:
            Success status
        """
        query = """
        INSERT INTO data_quality_log 
        (pipeline_run_date, total_customers_loaded, total_orders_loaded, 
         valid_orders, invalid_orders, issues_detected)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        try:
            record = (
                datetime.now(),
                stats.get('customers', {}).get('final_count', 0),
                stats.get('orders', {}).get('original_count', 0),
                stats.get('orders', {}).get('valid_count', 0),
                stats.get('orders', {}).get('invalid_count', 0),
                json.dumps(stats, default=str)
            )
            
            self.cursor.execute(query, record)
            self.connection.commit()
            
            logger.info(" Data quality metrics logged")
            return True
            
        except Error as e:
            logger.error(f" Error logging data quality: {e}")
            self.connection.rollback()
            return False
    
    def execute_query(self, query: str) -> Optional[pd.DataFrame]:
        """
        Execute custom SQL query and return results as DataFrame.
        
        Args:
            query: SQL query string
            
        Returns:
            DataFrame with query results
        """
        try:
            df = pd.read_sql(query, self.connection)
            logger.info(f"Query executed successfully, returned {len(df)} rows")
            return df
            
        except Error as e:
            logger.error(f" Error executing query: {e}")
            return None


# Example usage
if __name__ == "__main__":
    # Database configuration
    db_config = {
        'host': 'localhost',
        'user': 'akasa_user',  # or 'root'
        'password': 'your_password',
        'database': 'akasa_data_pipeline'
    }
    
    # Test connection
    db = DatabaseManager(db_config)
    if db.connect():
        print(" Database connection successful!")
        
        # Example query
        query = "SELECT COUNT(*) as customer_count FROM customers"
        result = db.execute_query(query)
        if result is not None:
            print(result)
        
        db.disconnect()
    else:
        print(" Database connection failed!")
```

### Update `src/main.py` to Include Database

Add to the imports:
```python
from db_manager import DatabaseManager
import os
```

Add after calculating KPIs:
```python
# Optional: Save to MySQL
use_database = os.getenv('USE_DATABASE', 'false').lower() == 'true'

if use_database:
    logger.info("\nSaving to MySQL database...")
    
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'akasa_data_pipeline')
    }
    
    db = DatabaseManager(db_config)
    if db.connect():
        # Insert data
        db.insert_customers(customers_clean)
        db.insert_orders(merged)
        db.save_kpi_snapshot(kpis)
        db.log_data_quality(cleaner.get_cleaning_summary())
        
        logger.info(" Data saved to MySQL successfully!")
        db.disconnect()
    else:
        logger.warning("  Database connection failed, skipping database storage")
```

##  Environment Variables

Create `.env` file in project root:

```
# Database Configuration
USE_DATABASE=true
DB_HOST=localhost
DB_USER=akasa_user
DB_PASSWORD=your_secure_password
DB_NAME=akasa_data_pipeline
```

Install python-dotenv:
```powershell
pip install python-dotenv
```

Load in main.py:
```python
from dotenv import load_dotenv
load_dotenv()
```

##  Useful SQL Queries

### 1. Customer Revenue Report
```sql
SELECT 
    c.customer_id,
    c.customer_name,
    c.region,
    COUNT(DISTINCT o.order_id) as total_orders,
    SUM(o.total_amount) as total_revenue,
    AVG(o.total_amount) as avg_order_value
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.customer_name, c.region
ORDER BY total_revenue DESC;
```

### 2. Top Selling Products
```sql
SELECT 
    sku_id,
    COUNT(DISTINCT order_id) as orders_count,
    SUM(sku_count) as total_quantity_sold
FROM order_items
GROUP BY sku_id
ORDER BY total_quantity_sold DESC
LIMIT 10;
```

### 3. Monthly Revenue Trend
```sql
SELECT 
    DATE_FORMAT(order_date_time, '%Y-%m') as month,
    COUNT(DISTINCT order_id) as total_orders,
    SUM(total_amount) as total_revenue
FROM orders
GROUP BY month
ORDER BY month;
```

### 4. Regional Performance
```sql
SELECT 
    c.region,
    COUNT(DISTINCT c.customer_id) as customers,
    COUNT(DISTINCT o.order_id) as orders,
    SUM(o.total_amount) as revenue
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.region
ORDER BY revenue DESC;
```

##  Testing Database Integration

```powershell
# Set environment variable
$env:USE_DATABASE="true"

# Run pipeline
cd src
python main.py
```

Verify data:
```sql
-- Check record counts
SELECT 'customers' as table_name, COUNT(*) as count FROM customers
UNION ALL
SELECT 'orders', COUNT(*) FROM orders
UNION ALL
SELECT 'order_items', COUNT(*) FROM order_items
UNION ALL
SELECT 'kpi_snapshots', COUNT(*) FROM kpi_snapshots;
```

##  Troubleshooting

### Connection Issues
```python
# Test connection
import mysql.connector

try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='your_password'
    )
    print(" Connected!")
    conn.close()
except Exception as e:
    print(f" Error: {e}")
```

### Common Errors

**Error: Access denied**
- Check username/password
- Verify user privileges

**Error: Database doesn't exist**
- Run CREATE DATABASE command first

**Error: Table doesn't exist**
- Run schema creation script

##  Performance Optimization

1. **Indexes:** Already added in schema
2. **Batch Inserts:** Use executemany() for bulk operations
3. **Connection Pooling:** For high-volume applications
4. **Caching:** Cache frequently accessed KPIs

##  Next Steps

1.  Set up MySQL server
2.  Create database and schema
3.  Install Python MySQL libraries
4.  Create db_manager.py
5.  Update main.py
6.  Test connection
7.  Run pipeline with database
8.  Create analytics dashboards
9.  Set up automated backups

---

**Database Setup Complete! **

Your pipeline now supports persistent storage in MySQL!
