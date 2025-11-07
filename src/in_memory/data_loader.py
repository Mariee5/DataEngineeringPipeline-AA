import pandas as pd
import xml.etree.ElementTree as ET
import logging
from pathlib import Path
from typing import Tuple

# Get the project root directory (parent of src folder)
# From src/in_memory/data_loader.py, go up 2 levels to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Ensure logs directory exists
(PROJECT_ROOT / 'logs').mkdir(exist_ok=True)

#Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(PROJECT_ROOT / 'logs' / 'data_pipeline.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class DataLoader:
    
    def __init__(self, data_dir: str = 'data'):
        # If relative path, make it relative to project root
        if not Path(data_dir).is_absolute():
            self.data_dir = PROJECT_ROOT / data_dir
        else:
            self.data_dir = Path(data_dir)
        logger.info(f"DataLoader initialized with directory: {self.data_dir}")
    
    def load_customers_csv(self, filename: str = 'task_DE_new_customers.csv') -> pd.DataFrame:
    
        file_path = self.data_dir / filename
        
        try:
            logger.info(f"Loading customer data from: {file_path}")
            
            # Read CSV file
            df = pd.read_csv(file_path)
            
            logger.info(f"Successfully loaded {len(df)} customer records")
            logger.debug(f"Columns: {df.columns.tolist()}")
            
            return df
            
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading CSV file: {str(e)}")
            raise
    
    def load_orders_xml(self, filename: str = 'task_DE_new_orders.xml') -> pd.DataFrame:
        
        #Load order data from XML file and convert to DataFrame.
        file_path = self.data_dir / filename
        
        try:
            logger.info(f"Loading order data from: {file_path}")
            
            # Parse XML file
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Extract data from each order element
            orders_data = []
            for order in root.findall('order'):
                try:
                    # Safely extract data, allowing for missing/invalid values
                    sku_count_text = order.find('sku_count').text
                    total_amount_text = order.find('total_amount').text
                    
                    order_dict = {
                        'order_id': order.find('order_id').text,
                        'mobile_number': order.find('mobile_number').text,
                        'order_date_time': order.find('order_date_time').text,
                        'sku_id': order.find('sku_id').text,
                        'sku_count': sku_count_text,  # Keep as string, will convert in data_cleaner
                        'total_amount': total_amount_text  # Keep as string, will convert in data_cleaner
                    }
                    orders_data.append(order_dict)
                except Exception as e:
                    logger.warning(f"Skipping malformed order: {e}")
                    continue
            
            # Convert to DataFrame
            df = pd.DataFrame(orders_data)
            
            logger.info(f"Successfully loaded {len(df)} order line items")
            logger.info(f"Unique orders: {df['order_id'].nunique()}")
            logger.debug(f"Columns: {df.columns.tolist()}")
            
            return df
            
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error loading XML file: {str(e)}")
            raise
    
    def load_all_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load both customer and order data.
        
        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: (customers_df, orders_df)
        """
        logger.info("Loading all data sources...")
        
        customers_df = self.load_customers_csv()
        orders_df = self.load_orders_xml()
        
        logger.info("All data loaded successfully")
        
        return customers_df, orders_df


# Example usage
if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    Path('logs').mkdir(exist_ok=True)
    
    # Initialize loader
    loader = DataLoader()
    
    # Load data
    customers, orders = loader.load_all_data()
    
    # Display sample data
    print("\n=== CUSTOMERS DATA ===")
    print(customers.head())
    print(f"\nShape: {customers.shape}")
    
    print("\n=== ORDERS DATA ===")
    print(orders.head(10))
    print(f"\nShape: {orders.shape}")
    print(f"Unique Orders: {orders['order_id'].nunique()}")