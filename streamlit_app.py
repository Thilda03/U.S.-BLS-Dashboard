import streamlit as st
import pandas as pd

st.set_page_config(page_title="US Labor Market Dashboard", layout="wide")

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("data/bls_data.csv", parse_dates=["date"])
        if df.empty:
            st.warning("Data file exists but contains no data yet.")
            st.stop()
        return df
    except pd.errors.EmptyDataError:
        st.error("Data file is empty. Please wait for the data pipeline to run.")
        st.stop()


df = load_data()

st.title("📊 U.S. Labor Market Dashboard")

latest = df.iloc[-1]

cols = st.columns(3)
cols[0].metric("Unemployment Rate (%)", latest["unemployment_rate"])
cols[1].metric("Nonfarm Employment (Thousands)", latest["nonfarm_employment"])
cols[2].metric("Labor Force Participation (%)", latest["labor_force_participation"])

st.subheader("Time Series Trends")

indicators = st.multiselect(
    "Select indicators",
    options=df.columns.drop("date"),
    default=["unemployment_rate", "nonfarm_employment"]
)

st.line_chart(df.set_index("date")[indicators])

st.caption("Source: U.S. Bureau of Labor Statistics (BLS)")
