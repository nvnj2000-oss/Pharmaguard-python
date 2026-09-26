"""
analysis.py
-----------
All the Pandas + NumPy logic for PharmaGuard lives here.
Both app.py (Streamlit) and flask_app.py (Flask) import functions
from this file, so the calculations are written only once.
"""

import pandas as pd
import numpy as np
from datetime import datetime


def load_data(file):
    """Read a CSV file into a Pandas DataFrame."""
    df = pd.read_csv(file)
    return df


def clean_data(df):
    """Basic cleaning: fix types, drop empty rows, remove duplicates."""
    df = df.dropna(subset=["Medicine_Name", "Expiry_Date"])
    df = df.drop_duplicates()

    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce").fillna(0)
    df["Daily_Sales"] = pd.to_numeric(df["Daily_Sales"], errors="coerce").fillna(0)
    df["Expiry_Date"] = pd.to_datetime(df["Expiry_Date"], errors="coerce")

    df = df.dropna(subset=["Expiry_Date"])
    return df


def add_expiry_analysis(df):
    """Add Days_Remaining and Expiry_Status columns."""
    today = pd.Timestamp(datetime.now().date())

    # NumPy: vectorized subtraction across the whole column at once
    df["Days_Remaining"] = (df["Expiry_Date"] - today).dt.days

    conditions = [
        df["Days_Remaining"] < 0,
        df["Days_Remaining"] <= 30,
    ]
    choices = ["Expired", "Expiring Soon"]
    df["Expiry_Status"] = np.select(conditions, choices, default="Safe")

    return df


def add_inventory_analysis(df):
    """Add NumPy-based numeric calculations."""
    # Estimated Sales Before Expiry = Daily_Sales * Days_Until_Expiry
    days_until_expiry = np.clip(df["Days_Remaining"].to_numpy(), 0, None)
    daily_sales = df["Daily_Sales"].to_numpy()

    estimated_sales = daily_sales * days_until_expiry
    df["Estimated_Sales_Before_Expiry"] = estimated_sales

    # Potential Expired Quantity = Quantity - Estimated Sales (never negative)
    quantity = df["Quantity"].to_numpy()
    potential_expired = quantity - estimated_sales
    df["Potential_Expired_Quantity"] = np.clip(potential_expired, 0, None)

    # Inventory value per medicine
    df["Inventory_Value"] = df["Quantity"] * df["Price"]

    return df


def process_dataframe(df):
    """Run the full pipeline: clean -> expiry analysis -> inventory analysis."""
    df = clean_data(df)
    df = add_expiry_analysis(df)
    df = add_inventory_analysis(df)
    return df


def get_dashboard_summary(df):
    """Calculate the top-level dashboard numbers using NumPy/Pandas."""
    summary = {
        "total_medicines": int(len(df)),
        "total_stock": int(np.sum(df["Quantity"].to_numpy())),
        "total_inventory_value": float(np.sum(df["Inventory_Value"].to_numpy())),
        "average_stock": float(np.mean(df["Quantity"].to_numpy())) if len(df) else 0,
        "expired_count": int((df["Expiry_Status"] == "Expired").sum()),
        "expiring_soon_count": int((df["Expiry_Status"] == "Expiring Soon").sum()),
        "safe_count": int((df["Expiry_Status"] == "Safe").sum()),
    }
    return summary


def get_category_summary(df):
    """Group medicines by category and calculate totals/averages."""
    grouped = df.groupby("Category").agg(
        Medicine_Count=("Medicine_Name", "count"),
        Total_Quantity=("Quantity", "sum"),
        Average_Price=("Price", "mean"),
        Total_Value=("Inventory_Value", "sum"),
    ).reset_index()
    return grouped
