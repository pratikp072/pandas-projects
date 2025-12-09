# NeoPay Customer Analytics — Pandas-Only Insights

## Project Overview
This project demonstrates a **full customer analytics workflow using Pandas only** (no NumPy for core transformations). The goal is to analyze NeoPay wallet transactions and generate a comprehensive report summarizing customer behavior and business performance across multiple dimensions.

**Key objectives:**
- Analyze month-wise GMV (Gross Merchandise Value) and transaction counts.
- Perform city- and region-level performance analysis.
- Conduct account-level RFM (Recency, Frequency, Monetary) segmentation.
- Investigate night-time and high-value transaction behavior.
- Conduct cohort analysis to track customer retention over time.

**Data Source:** `transactions.csv`  
**Columns:** `account_id, txn_time, amount, txn_type, description, city`  

---

## Analysis Components

### 1. Data Loading & Cleaning
- Load CSV with proper date parsing and dtypes.  
- Deduplicate transactions.  
- Handle missing values and clean string columns.  

### 2. Feature Engineering
- Extract `hour`, `month`, `weekday`, and `weekend` indicator.  
- Flag:
  - **Night-time transactions:** `hour < 6 or hour > 22`  
  - **High-value transactions:** `amount > 200,000`  
- Map `city` to `region` for geographical analysis.  

### 3. Core KPIs & Trends
- **Overall metrics:** total transactions, total amount, median & average amount, percentage of night-time and high-value transactions.  
- **Monthly trends:** GMV, transaction counts, night/high-value counts.  
- **City-level performance:** aggregated metrics by city and region.  

### 4. Pivot Tables
- Month × City transaction amounts.  
- Transaction type trends by month (sum and count).  

### 5. RFM Analysis
- Compute per-account **Recency** (days since last transaction), **Frequency**, and **Monetary value**.  
- Segment accounts into quartiles and generate combined RFM scores.  

### 6. Cohort Analysis
- Identify first month of customer activity.  
- Calculate monthly retention as the fraction of accounts returning in subsequent months.  

### 7. Exports
- Multi-sheet Excel report with sheets: `overall`, `monthly`, `city_perf`, `pivots`, `RFM`, `cohort`.  
- CSV files for downstream analysis.  

---

## Methodology Highlights
- **Pandas-only Transformations:** Use of `groupby`, `resample`, pivot tables, and indexing for all calculations.  
- **RFM Segmentation:** Quantile-based ranking to identify high-value, frequent, and recent customers.  
- **Cohort Retention:** Tracks first-month acquisition and subsequent monthly activity.  
- **Validation:** Totals reconciled between monthly, city-level, and overall metrics.  
