from pathlib import Path
import pandas as pd

# Determine the base directory depending on whether we're in a notebook or a .py file
BASE_DIR = Path(__file__).parent.parent if '__file__' in globals() else Path.cwd().parent

# Path to the CSV file
CSV_PATH = BASE_DIR / "data" / "transactions.csv"

# Check if the CSV exists
if not CSV_PATH.exists():
    raise FileNotFoundError(f"CSV file not found: {CSV_PATH}")

OUT_DIR = BASE_DIR / "outputs" 
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Load the CSV
df = pd.read_csv(
    CSV_PATH,
    dtype={
        "account_id": "int64",
        "amount": "float64",
        "txn_type": "string",
        "description": "string",
        "city": "string"
    },
    parse_dates=["txn_time"],
    dayfirst=True  # because format is DD-MM-YYYY
)

print(df.head())
print(df.info())

# Basic Data Cleaning
# Check for duplicates and missing values:

# Remove duplicates
df = df.drop_duplicates(subset=["account_id", "txn_time", "amount", "txn_type", "description", "city"])

# Check missing values
print(df.isna().sum())

# Clean string columns
for col in ["txn_type", "description", "city"]:
    df[col] = df[col].str.strip()

# Feature Engineering
# We create new columns needed for analysis.

df = df.sort_values("txn_time").set_index("txn_time")

# Derived columns
df["hour"] = df.index.hour
df["month"] = df.index.to_period("M").astype(str)  # e.g., '2024-01'
df["weekday"] = df.index.day_name()
df["is_weekend"] = df.index.weekday >= 5
df["is_night"] = (df["hour"] < 6) | (df["hour"] > 22)
df["is_high"] = df["amount"] > 200_000

# Map city to region
city_to_region = {
    "Mumbai":"West","Pune":"West","Delhi":"North","Bengaluru":"South",
    "Hyderabad":"South","Chennai":"South","Kolkata":"East"
}
df["region"] = df["city"].map(city_to_region).fillna("Unknown")

# Core KPIs & Aggregations

# Overall KPIs:
overall = pd.DataFrame({
    "total_txns": [len(df)],
    "total_amount": [df["amount"].sum()],
    "median_amount": [df["amount"].median()],
    "avg_amount": [df["amount"].mean()],
    "pct_night": [df["is_night"].mean()*100],
    "pct_high": [df["is_high"].mean()*100],
})

# Month-wise summary:
monthly = df.resample("ME").agg(
    total_amount=("amount","sum"),
    txns=("amount","count"),
    high_txns=("is_high","sum"),
    night_txns=("is_night","sum")
).reset_index()
monthly["month"] = monthly["txn_time"].dt.to_period("M").astype(str)

# City-wise summary:
city_perf = df.groupby("city", as_index=False).agg(
    total_amount=("amount","sum"),
    txns=("amount","count"),
    high_txns=("is_high","sum"),
    night_txns=("is_night","sum")
).sort_values("total_amount", ascending=False)

# Pivot Tables
# Month x City
pivot_month_city = pd.pivot_table(df.reset_index(), index="month", columns="city", values="amount", aggfunc="sum", fill_value=0)

# Transaction type per month
pivot_month_type = pd.pivot_table(df.reset_index(), index="month", columns="txn_type", values="amount", aggfunc=["sum","count"], fill_value=0)

# RFM Analysis
max_date = df.index.max().normalize()  # last date in dataset

rfm = df.groupby("account_id").agg(
    last_txn=("amount", lambda s: s.index.max()),  # last transaction
    frequency=("amount","count"),
    monetary=("amount","sum")
)
rfm["recency_days"] = (max_date - rfm["last_txn"].dt.normalize()).dt.days

# Quartile segmentation
rfm["R_quart"] = pd.qcut(-rfm["recency_days"], 4, labels=[1,2,3,4])
rfm["F_quart"] = pd.qcut(rfm["frequency"].rank(method="first"), 4, labels=[1,2,3,4])
rfm["M_quart"] = pd.qcut(rfm["monetary"].rank(method="first"), 4, labels=[1,2,3,4])

rfm["RFM_score"] = rfm[["R_quart","F_quart","M_quart"]].astype(int).sum(axis=1)

# Cohort Analysis
x = df.reset_index()[["txn_time","account_id"]].copy()
x["cohort_month"] = x["txn_time"].dt.to_period("M").astype(str)

# First month per account
first_month = x.groupby("account_id")["cohort_month"].min().rename("first_month")
x = x.merge(first_month, on="account_id", how="left")

# Cohort index (months since first transaction)
x["cohort_index"] = x.apply(lambda row: (pd.Period(row["cohort_month"]).year - pd.Period(row["first_month"]).year)*12 + (pd.Period(row["cohort_month"]).month - pd.Period(row["first_month"]).month), axis=1)

# Cohort retention table
cohort_base = x.groupby("first_month")["account_id"].nunique()
cohort_counts = x.groupby(["first_month","cohort_index"])["account_id"].nunique().unstack(fill_value=0)
cohort_retention = (cohort_counts.T / cohort_base).T.round(3)

# Export Results
excel_path = OUT_DIR / "neopay_pandas_report.xlsx"
with pd.ExcelWriter(excel_path, engine="xlsxwriter") as xl:
    overall.to_excel(xl, sheet_name="00_overall", index=False)
    monthly.to_excel(xl, sheet_name="01_monthly", index=False)
    city_perf.to_excel(xl, sheet_name="02_city_perf", index=False)
    pivot_month_city.to_excel(xl, sheet_name="03_pivot_month_city")
    pivot_month_type.to_excel(xl, sheet_name="04_pivot_month_type")
    rfm.reset_index().to_excel(xl, sheet_name="05_rfm", index=False)
    cohort_retention.to_excel(xl, sheet_name="06_cohort_retention")

# Optional CSVs for downstream teams
monthly.to_csv(OUT_DIR / "monthly_metrics.csv", index=False)
city_perf.to_csv(OUT_DIR / "city_performance.csv", index=False)
rfm.reset_index().to_csv(OUT_DIR / "rfm_scores.csv", index=False)
cohort_retention.to_csv(OUT_DIR / "cohort_retention.csv")
print("Saved:", excel_path)
