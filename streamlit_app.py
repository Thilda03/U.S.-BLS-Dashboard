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

df = df.sort_values("date")

latest = df.iloc[-1]
previous = df.iloc[-2]


st.title("📊 U.S. Labor Market Dashboard")

latest = df.iloc[-1]

st.subheader("Latest on the Labor Market")

col1, col2, col3 = st.columns(3)

col1.metric(
    "Unemployment Rate (%)",
    latest["unemployment_rate"],
    f"{latest['unemployment_rate'] - previous['unemployment_rate']:.2f}"
)

col2.metric(
    "Nonfarm Employment (Thousands)",
    f"{latest['nonfarm_employment']:,.0f}",
    f"{latest['nonfarm_employment'] - previous['nonfarm_employment']:,.0f}"
)

col3.metric(
    "Labor Force Participation (%)",
    latest["labor_force_participation"],
    f"{latest['labor_force_participation'] - previous['labor_force_participation']:.2f}"
)


st.subheader("Labor Market Trends Over Time")

indicators = st.multiselect(
    "Select indicators to display",
    options=df.columns.drop("date"),
    default=["unemployment_rate", "nonfarm_employment"]
)

st.line_chart(df.set_index("date")[indicators])

st.subheader("Latest Month Indicator Comparison")

latest_df = (
    latest.drop("date")
    .rename("value")
    .reset_index()
    .rename(columns={"index": "indicator"})
)
st.bar_chart(latest_df.set_index("indicator"))

st.subheader("Employment vs Unemployment (Normalized)")

dual_df = df[["date", "nonfarm_employment", "unemployment_rate"]].copy()

dual_df["nonfarm_employment_norm"] = (
    dual_df["nonfarm_employment"] / dual_df["nonfarm_employment"].max()
)

dual_df["unemployment_rate_norm"] = (
    dual_df["unemployment_rate"] / dual_df["unemployment_rate"].max()
)

st.line_chart(
    dual_df.set_index("date")[[
        "nonfarm_employment_norm",
        "unemployment_rate_norm"
    ]]
)

st.subheader("Month-over-Month Changes")

mom_df = df.copy()
mom_df["employment_change"] = mom_df["nonfarm_employment"].diff()
mom_df["unemployment_change"] = mom_df["unemployment_rate"].diff()

change_indicator = st.selectbox(
    "Select change metric",
    ["employment_change", "unemployment_change"]
)

st.bar_chart(
    mom_df.set_index("date")[change_indicator]
)


st.caption("Source: U.S. Bureau of Labor Statistics (BLS)")
