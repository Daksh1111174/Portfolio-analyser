import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import datetime as dt
import plotly.express as px

st.set_page_config(page_title="Portfolio Analyzer", layout="wide")

# ---------------------------- FUNCTIONS ---------------------------------

def calculate_cagr(start_value, end_value, years):
    return (end_value / start_value) ** (1/years) - 1 if start_value > 0 else 0

def calculate_xirr(cashflows, dates):
    try:
        return np.irr(cashflows)
    except:
        return None

def calculate_drawdown(series):
    cummax = series.cummax()
    drawdown = (series - cummax) / cummax
    return drawdown.min()

def get_live_price(symbol):
    data = yf.Ticker(symbol).history(period="1d")
    return data["Close"].iloc[-1] if not data.empty else None

def get_sector(symbol):
    try:
        return yf.Ticker(symbol).info.get("sector", "Unknown")
    except:
        return "Unknown"


# ---------------------------- UI SECTION ---------------------------------

st.title("📊 Portfolio Analyzer (Live Stock Analysis)")

uploaded_file = st.file_uploader("Upload your Portfolio CSV file", type=["csv", "xlsx"])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith("csv") else pd.read_excel(uploaded_file)

    st.success("File uploaded successfully!")

    # FETCH LIVE PRICES
    st.subheader("📌 Fetching Live Prices...")
    df["LivePrice"] = df["Symbol"].apply(get_live_price)

    # Current Value
    df["CurrentValue"] = df["LivePrice"] * df["Quantity"]
    df["InvestedValue"] = df["BuyPrice"] * df["Quantity"]
    df["P/L"] = df["CurrentValue"] - df["InvestedValue"]
    df["Returns %"] = (df["P/L"] / df["InvestedValue"]) * 100

    # CAGR
    st.subheader("📈 CAGR & Portfolio Returns")
    today = dt.datetime.today()
    df["Years"] = ((today - pd.to_datetime(df["BuyDate"])).dt.days) / 365
    df["CAGR"] = df.apply(lambda x: calculate_cagr(x["BuyPrice"], x["LivePrice"], x["Years"]), axis=1)

    # Sector Allocation
    df["Sector"] = df["Symbol"].apply(get_sector)

    # Display updated table
    st.dataframe(df, use_container_width=True)

    # ----------------- Portfolio Summary -------------------------

    st.header("📊 Portfolio Summary")

    total_invested = df["InvestedValue"].sum()
    total_current = df["CurrentValue"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Invested", f"₹{total_invested:,.2f}")
    col2.metric("Current Value", f"₹{total_current:,.2f}")
    col3.metric("Total P/L", f"₹{total_current - total_invested:,.2f}")

    # ----------------- Sector Allocation Chart -------------------

    st.subheader("📌 Sector Allocation")
    sector_data = df.groupby("Sector")["CurrentValue"].sum()
    fig = px.pie(sector_data, values=sector_data.values, names=sector_data.index, title="Sector Breakdown")
    st.plotly_chart(fig, use_container_width=True)

    # ----------------- Volatility & Risk -------------------------

    st.subheader("📌 Volatility & Risk Analysis")

    returns_data = []
    for symbol in df["Symbol"]:
        hist = yf.Ticker(symbol).history(period="1y")
        if not hist.empty:
            hist["DailyReturn"] = hist["Close"].pct_change()
            vol = hist["DailyReturn"].std() * np.sqrt(252)
            avg_return = hist["DailyReturn"].mean() * 252
            returns_data.append([symbol, vol, avg_return])

    if returns_data:
        risk_df = pd.DataFrame(returns_data, columns=["Symbol", "Volatility", "AnnualReturn"])

        st.dataframe(risk_df)

        fig = px.scatter(
            risk_df, x="Volatility", y="AnnualReturn", text="Symbol",
            title="Risk vs Return Chart", trendline="ols"
        )
        st.plotly_chart(fig, use_container_width=True)

    # ----------------- Benchmark Comparison -------------------------

    st.subheader("📌 Portfolio vs NIFTY 50 Comparison")

    nifty = yf.Ticker("^NSEI").history(period="1y")["Close"]
    portfolio_value = df["CurrentValue"].sum()

    nifty_return = (nifty.iloc[-1] - nifty.iloc[0]) / nifty.iloc[0] * 100
    portfolio_return = (total_current - total_invested) / total_invested * 100

    col1, col2 = st.columns(2)
    col1.metric("Portfolio Return (1Y)", f"{portfolio_return:.2f}%")
    col2.metric("NIFTY 50 Return (1Y)", f"{nifty_return:.2f}%")


# -------------------------------------------------------------------------

st.info("Upload your CSV to begin portfolio analysis.")
