"""
Akasa Air Data Pipeline - Interactive Dashboard
Shows ONLY the KPIs actually calculated by the pipeline
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path
import logging

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add src directories to path
sys.path.append(str(Path(__file__).parent / 'src' / 'in_memory'))

# Import pipeline modules
from data_loader import DataLoader
from data_cleaner import DataCleaner
from kpi_calculator import KPICalculator

# Configure logging
logging.basicConfig(level=logging.WARNING)

# Page config
st.set_page_config(
    page_title="Akasa Air Data Pipeline Dashboard",
    page_icon="✈️",
    layout="wide"
)

# Title
st.title("✈️ Akasa Air Data Pipeline Dashboard")
st.markdown("### Real KPIs from In-Memory Processing")

# Cache the pipeline execution
@st.cache_data(show_spinner=False)
def run_pipeline():
    """Run the data pipeline and return results."""
    try:
        loader = DataLoader()
        customers, orders = loader.load_all_data()
        
        cleaner = DataCleaner()
        customers_clean = cleaner.clean_customers(customers)
        orders_clean, orders_invalid = cleaner.clean_orders(orders)
        merged = cleaner.merge_customer_orders(customers_clean, orders_clean)
        
        kpi_calc = KPICalculator()
        kpis = kpi_calc.calculate_all_kpis(merged)
        
        return {'merged': merged, 'kpis': kpis, 'orders_invalid': orders_invalid}
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# Run the pipeline
with st.spinner("Loading data..."):
    results = run_pipeline()

if results is None:
    st.error("Failed to load data.")
    st.stop()

kpis = results['kpis']

# Extract KPIs
customer_metrics = kpis['customer_metrics']
order_metrics = kpis['order_metrics']
revenue_metrics = kpis['revenue_metrics']
product_metrics = kpis['product_metrics']
regional_metrics = kpis['regional_metrics']
temporal_metrics = kpis['temporal_metrics']
top_performers = kpis['top_performers']

# Summary Metrics
st.markdown("## 📊 Key Metrics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Revenue", f"₹{revenue_metrics['total_revenue']:,.0f}")

with col2:
    st.metric("Total Customers", f"{customer_metrics['total_customers']:,}")

with col3:
    st.metric("Avg Revenue/Customer", f"₹{customer_metrics['avg_revenue_per_customer']:,.0f}")

with col4:
    st.metric("Total Orders", f"{order_metrics['total_orders']:,}")

st.markdown("---")

# Regional Analysis
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🌍 Regional Revenue")
    regional_df = pd.DataFrame(regional_metrics['regional_breakdown'])
    
    fig_regional = px.bar(
        regional_df.head(10),
        x='region',
        y='total_revenue',
        title='Top Regions by Revenue',
        labels={'region': 'Region', 'total_revenue': 'Revenue (₹)'},
        color='total_revenue',
        color_continuous_scale='Blues'
    )
    st.plotly_chart(fig_regional, use_container_width=True)

with col2:
    st.markdown("### 👥 Top Customers")
    top_customers_df = pd.DataFrame(top_performers['top_5_customers'])
    
    fig_customers = px.bar(
        top_customers_df,
        x='customer_name',
        y='total_revenue',
        title='Top 5 Customers',
        labels={'customer_name': 'Customer', 'total_revenue': 'Revenue (₹)'},
        color='total_orders',
        color_continuous_scale='Greens'
    )
    st.plotly_chart(fig_customers, use_container_width=True)

# Product Analysis
st.markdown("### 📦 Top Products")

product_df = pd.DataFrame(product_metrics['sku_performance'])

col1, col2 = st.columns(2)

with col1:
    fig_sku_qty = px.bar(
        product_df,
        x='sku_id',
        y='total_quantity_sold',
        title='Top SKUs by Quantity Sold',
        labels={'sku_id': 'SKU', 'total_quantity_sold': 'Quantity'},
        color='total_quantity_sold',
        color_continuous_scale='Reds'
    )
    fig_sku_qty.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_sku_qty, use_container_width=True)

with col2:
    fig_sku_orders = px.bar(
        product_df,
        x='sku_id',
        y='orders_count',
        title='Top SKUs by Number of Orders',
        labels={'sku_id': 'SKU', 'orders_count': 'Number of Orders'},
        color='orders_count',
        color_continuous_scale='Purples'
    )
    fig_sku_orders.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_sku_orders, use_container_width=True)

# Detailed Metrics
st.markdown("## 📋 Detailed Metrics")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### Customer Metrics")
    st.metric("Total Customers", customer_metrics['total_customers'])
    st.metric("Avg Orders/Customer", f"{customer_metrics['avg_orders_per_customer']:.2f}")
    st.metric("Avg Revenue/Customer", f"₹{customer_metrics['avg_revenue_per_customer']:,.0f}")
    st.metric("Avg Items/Customer", f"{customer_metrics['avg_items_per_customer']:.1f}")

with col2:
    st.markdown("### Order Metrics")
    st.metric("Total Orders", order_metrics['total_orders'])
    st.metric("Total Line Items", order_metrics['total_order_line_items'])
    st.metric("Avg Order Value", f"₹{order_metrics['avg_order_value']:,.2f}")
    st.metric("Median Order Value", f"₹{order_metrics['median_order_value']:,.2f}")

with col3:
    st.markdown("### Product Metrics")
    st.metric("Unique SKUs", product_metrics['total_unique_skus'])
    st.metric("Most Sold SKU", product_metrics['most_sold_sku'])
    st.metric("Most Sold Quantity", f"{product_metrics['most_sold_sku_quantity']:.0f}")
    st.metric("Avg Qty/SKU", f"{product_metrics['avg_quantity_per_sku']:.1f}")

# Data Tables
st.markdown("## 📊 Detailed Data")

tab1, tab2, tab3 = st.tabs(["Top Customers", "Top Products", "Regional Breakdown"])

with tab1:
    st.dataframe(top_customers_df, use_container_width=True)

with tab2:
    st.dataframe(product_df, use_container_width=True)

with tab3:
    st.dataframe(regional_df, use_container_width=True)

# Data Quality
if len(results['orders_invalid']) > 0:
    st.markdown("## ⚠️ Data Quality")
    st.warning(f"Found {len(results['orders_invalid'])} invalid orders")
    with st.expander("View Invalid Orders"):
        st.dataframe(results['orders_invalid'][['order_id', 'mobile_number', 'sku_id', 'sku_count', 'total_amount']])

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center'><p>Akasa Air Data Pipeline | Real-Time KPI Dashboard</p></div>", unsafe_allow_html=True)
