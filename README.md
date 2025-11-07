# Akasa Air Data Engineering Pipeline

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

A production-ready data engineering pipeline for processing customer and order data with comprehensive KPI analytics. Implements dual validation through both in-memory (Pandas) and database (MySQL) approaches.

---

##  Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Output](#output)
- [Documentation](#documentation)
- [Project Structure](#project-structure)
- [Results](#results)
- [Contributing](#contributing)

---

##  Overview

This project implements a complete ETL (Extract, Transform, Load) pipeline that:

- **Extracts** data from CSV (customers) and XML (orders) sources
- **Transforms** data through validation, cleaning, and enrichment
- **Loads** results into multiple output formats (CSV, JSON, Excel, TXT)
- **Calculates** 20+ business KPIs across multiple dimensions
- **Validates** correctness through two independent implementations

### Key Highlights

-  **91% Data Quality Score** - Automated validation and cleaning
-  **100% Accuracy Verified** - Dual approach validation (In-Memory vs Database)
-  **Sub-second Processing** - Optimized for performance
-  **Production Ready** - Comprehensive error handling and logging
-  **Multi-format Reports** - TXT, CSV, JSON, and Excel outputs

---

##  Features

### Data Processing
- Multi-source data ingestion (CSV, XML)
- Automated data validation and quality checks
- Duplicate detection and removal
- Missing value handling
- Invalid record segregation
- Temporal feature enrichment

### Analytics & KPIs
- **Customer Metrics**: Total customers, repeat customers, lifetime value
- **Order Metrics**: Order counts, average order value, order trends
- **Revenue Metrics**: Total revenue, revenue by region, revenue trends
- **Product Metrics**: SKU performance, bestsellers, inventory insights
- **Regional Analysis**: Geographic performance breakdown
- **Temporal Analysis**: Time-based patterns and trends
- **Top Performers**: Identification of key customers and products

### Dual Implementation
- **In-Memory Approach** (Pandas): Fast prototyping and analysis
- **Database Approach** (MySQL): Scalable production deployment
- Both approaches independently calculate identical results for validation

---

##  Architecture

```

   Data Sources  
   CSV Files   
   XML Files   

         
         

   Data Loading     
  (DataLoader)      

         
         

   Data Cleaning    
  (DataCleaner)     

         
         

                                 
                                 
        
  In-Memory              Database   
  (Pandas)               (MySQL)    
        
                              
       
                   
          
           KPI Calculation
          
                   
          
           Report Output  
           (CSV/JSON/XLSX)
          
```

---

##  Installation

### Prerequisites

- **Python**: 3.11 or higher
- **MySQL**: 8.0+ (optional, for database approach)
- **Git**: For version control

### Setup

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/akasa-air-pipeline.git
cd akasa-air-pipeline
```

2. **Create virtual environment**

```bash
python -m venv venv
```

3. **Activate virtual environment**

```bash
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Windows Command Prompt
.\venv\Scripts\activate.bat

# Linux/macOS
source venv/bin/activate
```

4. **Install dependencies**

```bash
pip install -r requirements.txt
```

### Dependencies

- `pandas==2.1.4` - Data manipulation and analysis
- `lxml==5.1.0` - XML parsing
- `pymysql==1.1.1` - MySQL database driver
- `sqlalchemy==2.0.23` - SQL toolkit and ORM
- `python-dotenv==1.0.0` - Environment variable management
- `openpyxl==3.1.2` - Excel file generation

---

##  Quick Start

### Option 1: In-Memory Approach (Recommended for First Run)

No database setup required!

```bash
python src/in_memory/main.py
```

**Expected Output:**
```
 Loaded 5 customers and 22 order line items
 Cleaning complete: 5 clean customers, 20 clean orders
 Total Revenue: ₹51,727.00
 Pipeline completed successfully!
```

### Option 2: Database Approach

Requires MySQL setup. See [MYSQL_INTEGRATION.md](MYSQL_INTEGRATION.md) for configuration.

```bash
# First run: Reset and initialize database
python database/main_db.py --reset

# Subsequent runs
python database/main_db.py
```

### Option 3: Interactive Dashboard (Streamlit)

Visualize KPIs in real-time with an interactive web dashboard!

```bash
# Install Streamlit (if not already installed)
pip install streamlit plotly

# Run the dashboard
streamlit run streamlit_app.py
```

The dashboard will open in your browser at `http://localhost:8501` and display:
- Real-time KPI metrics (Revenue, Customers, Orders)
- Interactive charts (Regional Revenue, Top Customers, Top Products)
- Detailed data tables
- Automatic data refresh on reload

---

##  Usage

### Running the Pipeline

```bash
# In-Memory approach
python src/in_memory/main.py

# Database approach (with existing data)
python database/main_db.py

# Database approach (fresh start)
python database/main_db.py --reset
```

### Viewing Results

```bash
# List generated files (In-Memory)
ls src/outputs/

# List generated files (Database)
ls outputs/database/

# Open Excel report
start src/outputs/in_memory_kpis_*.xlsx
```

---

##  Output

### Generated Files

Both approaches generate multiple output formats:

| Format | Description | Location |
|--------|-------------|----------|
| **Excel (.xlsx)** | Multi-sheet KPI dashboard with charts | `*_kpis_*.xlsx` |
| **Text (.txt)** | Human-readable summary report | `summary_report_*.txt` |
| **CSV (.csv)** | Individual KPI tables and clean data | `*.csv` |
| **JSON (.json)** | Structured KPI data for API integration | `kpis_*.json` |

### Excel Report Structure

- **Summary Sheet**: Overview of key metrics
- **Customer Details**: Per-customer performance analysis
- **SKU Performance**: Product-level metrics and trends
- **Regional Revenue**: Geographic breakdown
- **Top Customers**: High-value customer identification

### Output Locations

- **In-Memory**: `src/outputs/`
- **Database**: `outputs/database/`
- **Logs**: `logs/`

---

##  Documentation

Comprehensive documentation is available in the following files:

| Document | Description | Read Time |
|----------|-------------|-----------|
| [README.md](README.md) | This file - Quick start guide | 5 min |
| [DOCUMENTATION.md](DOCUMENTATION.md) | Complete technical guide | 20 min |
| [RESULTS_VISUALIZATION.md](RESULTS_VISUALIZATION.md) | Charts, graphs, and visual analysis | 15 min |
| [REVENUE_DISCREPANCY_ANALYSIS.md](REVENUE_DISCREPANCY_ANALYSIS.md) | Technical deep-dive on validation | 10 min |
| [MYSQL_INTEGRATION.md](MYSQL_INTEGRATION.md) | Database setup guide | 12 min |

---

##  Project Structure

```
akasa-air-pipeline/

 data/                              # Input data files
    task_DE_new_customers.csv      # Customer master data
    task_DE_new_orders.xml         # Order transaction data

 src/in_memory/                     # In-Memory implementation
    __init__.py
    main.py                        # Pipeline orchestrator
    data_loader.py                 # CSV/XML data loader
    data_cleaner.py                # Data validation & cleaning
    kpi_calculator.py              # KPI calculation engine

 database/                          # Database implementation
    main_db.py                     # Pipeline orchestrator
    db_config.py                   # MySQL connection config
    db_schema.py                   # SQLAlchemy ORM models
    db_loader.py                   # Data ingestion
    db_queries.py                  # KPI SQL queries

 outputs/                           # Generated reports
    database/                      # Database outputs

 src/outputs/                       # In-memory outputs

 logs/                              # Application logs

 .env                               # Environment variables (not in git)
 .gitignore                         # Git ignore rules
 requirements.txt                   # Python dependencies
 README.md                          # This file
```

---

##  Results

### Key Performance Indicators

| Metric | Value | Status |
|--------|-------|--------|
| **Total Revenue** | ₹51,727 |  Verified |
| **Total Customers** | 5 |  |
| **Total Orders** | 8 |  |
| **Valid Order Items** | 20 |  |
| **Data Quality Score** | 91% |  Excellent |
| **Processing Time** | <1s |  Fast |

### Business Insights

- **Top Customer**: Aarav Mehta (₹15,748 revenue, 3 orders)
- **Top Region**: West (39.3% of total revenue)
- **Peak Month**: October 2025 (₹21,999)
- **Repeat Customer Rate**: 40%
- **Most Sold Product**: SKU-1003 (7 units)

### Validation Results

Both implementations (In-Memory and Database) produce identical results:

```
 Total Revenue:      ₹51,727.00  (100% match)
 Customer Count:     5           (100% match)
 Order Count:        8           (100% match)
 Monthly Breakdown:              (100% match)
 Regional Analysis:              (100% match)
 Top Customers:                  (100% match)
```

---

##  Configuration

### Database Setup (Optional)

Create a `.env` file in the project root for database credentials:

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=akasa_air_db
DB_USER=your_username
DB_PASSWORD=your_password
```

** Security Note**: Never commit the `.env` file to version control.

---

##  Troubleshooting

### Common Issues

#### Issue: Module not found
```bash
# Ensure you're in the project root
cd /path/to/akasa-air-pipeline
python src/in_memory/main.py
```

#### Issue: Data files not found
```bash
# Verify data files exist
ls data/
# Should show: task_DE_new_customers.csv, task_DE_new_orders.xml
```

#### Issue: Revenue mismatch
```bash
# Reset database (if using database approach)
python database/main_db.py --reset
```

### Getting Help

1. Check the [DOCUMENTATION.md](DOCUMENTATION.md) troubleshooting section
2. Review log files in the `logs/` directory
3. Examine invalid records in `orders_invalid_*.csv`

---

##  Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests (if available)
pytest tests/

# Check code style
flake8 src/ database/
```

---

##  Future Enhancements

Given more time, the following improvements would be considered:

### 1. **Automated Scheduling & Orchestration**
- **Apache Airflow Integration**: Implement DAGs for daily/hourly data ingestion workflows
- **Cron Jobs**: Set up scheduled pipeline execution with monitoring
- **Real-time Monitoring**: Dashboard for pipeline status and data freshness tracking

### 2. **Advanced Data Processing**
- **Incremental Loading**: Process only new/changed records since last run
- **Data Versioning**: Track historical changes and maintain audit trail
- **Partitioning**: Implement date-based table partitioning for large datasets
- **Caching Layer**: Redis integration for frequently accessed KPIs

### 3. **Enhanced Analytics & ML**
- **Predictive Analytics**: Machine learning models for customer churn prediction
- **Anomaly Detection**: Identify unusual order patterns and fraudulent activities
- **Real-time Dashboards**: Power BI/Tableau integration for business stakeholders
- **Time Series Forecasting**: Revenue and demand forecasting models

### 4. **Scalability Improvements**
- **Distributed Processing**: Apache Spark for handling big data workloads
- **Cloud Deployment**: Containerized deployment on AWS/Azure/GCP
- **Message Queue**: Apache Kafka for real-time data streaming
- **REST API Layer**: FastAPI/Flask endpoints for programmatic KPI access

### 5. **Data Quality & Governance**
- **Data Quality Framework**: Great Expectations for automated data validation
- **Data Lineage Tracking**: OpenLineage implementation for complete traceability
- **Metadata Management**: Data catalog with business glossary
- **Automated Testing**: pytest suite with 80%+ code coverage

### 6. **Security Enhancements**
- **Encryption**: Data encryption at rest and in transit
- **RBAC**: Role-based access control for multi-user environments
- **Audit Logging**: Comprehensive tracking of all data access and modifications
- **PII Protection**: Data masking and anonymization for sensitive information

### 7. **Operational Excellence**
- **CI/CD Pipeline**: GitHub Actions for automated testing and deployment
- **Containerization**: Docker and Kubernetes for scalable deployment
- **Monitoring**: Prometheus + Grafana for metrics and alerting
- **Incident Management**: Automated alerting via Slack/Email on failures

### 8. **Performance Optimization**
- **Query Optimization**: Advanced indexing strategies and query plan analysis
- **Connection Pooling**: Efficient database connection management
- **Parallel Processing**: Multi-threading for concurrent data processing
- **Result Caching**: Materialized views for frequently accessed aggregations

---

##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

##  Author

**Your Name**

- GitHub: [@yMariee5](https://github.com/Mariee5)
- LinkedIn: [Shobha Mary](www.linkedin.com/in/shobha-mary-388388249https://linkedin.com/in/ShobhaMary)

---

##  Acknowledgments

- Built for Akasa Air data engineering assessment
- Inspired by real-world ETL pipeline requirements
- Uses industry-standard tools and best practices

---



** If you find this project useful, please consider giving it a star!**

---

*Last Updated: November 2025*
