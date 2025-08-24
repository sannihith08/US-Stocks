# CPR Strategy Streamlit App
# ==============================
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
from datetime import date, timedelta

# ==============================
# Function to calculate CPR
# ==============================
def calculate_cpr(df):
    df["Pivot"] = (df["High"].shift(1) + df["Low"].shift(1) + df["Close"].shift(1)) / 3
    df["BC"] = (df["High"].shift(1) + df["Low"].shift(1)) / 2
    df["TC"] = 2 * df["Pivot"] - df["BC"]
    return df

def bulk_volume_breakout(symbols, period="60d", interval="1d"):
    results = []
    for symbol in symbols:
        try:
            df = yf.download(symbol, period=period, interval=interval, auto_adjust=True)
            df.columns = df.columns.get_level_values(0)

            # Condition 1: Volume spike (e.g., > 1.5x average of last 20)
            df["Avg_Volume_20"] = df["Volume"].rolling(20).mean()
            df["Bulk_Volume"] = df["Volume"] >  df["Avg_Volume_20"]

            # Condition 2: Close > Previous High
            df["Prev_High"] = df["High"].shift(1)
            df["Prev_Close"] = df["Close"].shift(1)
            df["Breakout"] = (df["Close"] > df["Prev_Close"])

            if df["Breakout"].iloc[-1]:
                results.append(symbol)

        except Exception as e:
            st.error(f"Could not fetch {symbol}: {e}")
    
    return results


# ==============================
# Streamlit UI
# ==============================
st.set_page_config(page_title="CPR Strategy", layout="wide")
st.title("📊 CPR (Central Pivot Range) Strategy")

ticker = st.text_input("Enter Stock Symbol (e.g. RELIANCE.NS, TCS.NS, INFY.NS):", "RELIANCE.NS")
period = st.selectbox("Select Period:", ["5d", "1mo", "3mo", "6mo", "1y"])
interval = st.selectbox("Select Interval:", ["15m", "30m", "1h", "1d"])
uploaded_file = st.file_uploader("Upload a stock list file (CSV or TXT)", type=["csv", "txt"])

if uploaded_file:
    df_symbols = pd.read_csv(uploaded_file)
    # Expecting the file to have a column named "Symbol"
    if "Symbol" in df_symbols.columns:
        stock_list = df_symbols["Symbol"].dropna().tolist()
    else:
        st.error("CSV must contain a column named 'Symbol'")
        stock_list = []
else:
    # Default fallback
    stock_list = [
        "RELIANCE.NS", "SBILIFE.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
        "VEDL.NS", "AXISBANK.NS", "LT.NS", "ITC.NS", "HINDUNILVR.NS",
        "BHARTIARTL.NS", "KOTAKBANK.NS", "ONGC.NS", "ADANIENT.NS", "TATAMOTORS.NS"
    ]

    # Show multiselect with all loaded tickers
    stocks = st.multiselect(
        "Select stocks",
        options=stock_list,
        default=stock_list  # preselect all
    )

    st.write("✅ Selected Stocks:", stocks)




if st.button("Get Data & Plot CPR"):
    try:
        # Download stock data
        df = yf.download(ticker, period=period, interval=interval, auto_adjust=True)
        df = df.dropna()

        if df.empty:
            st.error("No data found. Please check ticker/interval.")
        else:
            df = calculate_cpr(df)

            # Show DataFrame
            st.subheader("Stock Data with CPR Levels")
            st.dataframe(df.tail(20))

            # Plot using Plotly
            fig = go.Figure()

            # Candlestick
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                 name='Candlestick'
            ))

            # CPR Levels
            fig.add_trace(go.Scatter(x=df.index, y=df["Pivot"], mode="lines", name="Pivot", line=dict(color="blue", dash="dot")))
            fig.add_trace(go.Scatter(x=df.index, y=df["BC"], mode="lines", name="BC", line=dict(color="red", dash="dot")))
            fig.add_trace(go.Scatter(x=df.index, y=df["TC"], mode="lines", name="TC", line=dict(color="green", dash="dot")))

            fig.update_layout(title=f"{ticker} CPR Chart", xaxis_rangeslider_visible=False)

            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
st.subheader("📈 Bulk Volume + Price Breakout Scanner")

# Predefined stock list (you can expand this)
default_stocks = [
    "RELIANCE.NS", "ABB.NS", "BAJFINANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "VEDL.NS", "AXISBANK.NS", "LT.NS", "ITC.NS", "HINDUNILVR.NS",
    "BHARTIARTL.NS", "KOTAKBANK.NS", "ONGC.NS", "ADANIENT.NS", "TATAMOTORS.NS"
]

if st.button("Run Breakout Scanner on 15 Stocks"):
    results = []
    try:
        # use your bulk_volume_breakout function to scan all at once
        breakout_stocks = bulk_volume_breakout(stocks, period="60d", interval="1d")

        for stock in breakout_stocks:
            df = yf.download(stock, period="60d", interval="1d", auto_adjust=True)
            df = df.dropna()

            results.append({
                "Stock": stock,
                "Last Close": df["Close"].iloc[-1],
                "Prev High": df["High"].shift(1).iloc[-1],
                "Volume": df["Volume"].iloc[-1]
            })
    except Exception as e:
        st.warning(f"Error while scanning: {e}")

    if results:
        st.success("✅ Breakout signals found!")
        st.dataframe(pd.DataFrame(results))
    else:
        st.warning("No breakout signals found for selected stocks.")
