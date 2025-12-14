import streamlit as st
import pandas as pd
import numpy as np

# --- Configuration ---
DATA_FILE = "data/bls_data.csv"
st.set_page_config(layout="wide", page_title="BLS Labor Market Dashboard")

# --- Function to load data (with caching for speed) ---
# Tell Streamlit to re-run this function only when the file changes.
@st.cache_data(ttl=3600) 
def load_data():
    try:
        df = pd.read_csv(DATA_FILE, index_col='Date', parse_dates=True)
        
        # Final cleanup and calculations for the dashboard
        df['Nonfarm Employment Change (Thousands)'] = df['Total Nonfarm Employment (Thousands)'].diff()
        df['Nonfarm Employment (Millions)'] = df['Total Nonfarm Employment (Thousands)'] / 1000
        df['Avg Weekly Earnings'] = df['Avg Hourly Earnings of All Employees: Total Private'] * df['Avg Weekly Hours of All Employees: Total Private']

        return df
    except FileNotFoundError:
        st.error(f"Data file not found at {DATA_FILE}. Please ensure the GitHub Action has run and committed the data.")
        return pd.DataFrame()

df = load_data()

# --- Streamlit Dashboard Layout ---
st.title("🇺🇸 U.S. Labor Market Dashboard (BLS Data)")
st.caption(f"Data powered by the BLS API and automatically updated via GitHub Actions. Last data point: **{df.index.max().strftime('%b %Y')}**")
st.write("---")

if not df.empty:
    
    # Get latest values for metric boxes
    latest_data = df.iloc[-1]
    prev_data = df.iloc[-2]
    
    # --- Row 1: Key Metrics ---
    col1, col2, col3, col4 = st.columns(4)

    # Unemployment Rate (LNS14000000)
    col1.metric(
        label="Unemployment Rate (SA)",
        value=f"{latest_data['Unemployment Rate']:.1f}%",
        delta=f"{latest_data['Unemployment Rate'] - prev_data['Unemployment Rate']:.1f} pts"
    )

    # Nonfarm Employment (CES0000000001)
    col2.metric(
        label="Total Nonfarm Jobs (SA)",
        value=f"{latest_data['Nonfarm Employment (Millions)']:.1f}M",
        delta=f"{latest_data['Nonfarm Employment Change (Thousands)']:.0f}K (MoM)"
    )
    
    # Average Hourly Earnings (CES0500000003)
    col3.metric(
        label="Avg Hourly Earnings",
        value=f"${latest_data['Avg Hourly Earnings of All Employees: Total Private']:.2f}",
        delta=f"${latest_data['Avg Hourly Earnings of All Employees: Total Private'] - prev_data['Avg Hourly Earnings of All Employees: Total Private']:.2f}"
    )
    
    # Average Weekly Hours (CES0500000002)
    col4.metric(
        label="Avg Weekly Hours",
        value=f"{latest_data['Avg Weekly Hours of All Employees: Total Private']:.1f}",
        delta=f"{latest_data['Avg Weekly Hours of All Employees: Total Private'] - prev_data['Avg Weekly Hours of All Employees: Total Private']:.1f} hrs"
    )

    st.write("---")

    # --- Row 2: Charts ---
    
    # Chart 1: Unemployment vs. Employment
    st.header("Joblessness and Job Creation")
    chart_data = df[['Unemployment Rate', 'Nonfarm Employment Change (Thousands)']]
    st.line_chart(chart_data)

    st.write("---")

    # Chart 2: Wages and Hours
    st.header("Wage and Hour Trends")
    wage_data = df[['Avg Hourly Earnings of All Employees: Total Private', 'Avg Weekly Hours of All Employees: Total Private']]
    st.line_chart(wage_data)

    st.write("---")
    
    # Optional: Display the raw data
    if st.checkbox('Show Raw Data Table'):
        st.subheader('Raw Data')
        st.dataframe(df.tail(24)) # Show last 2 years