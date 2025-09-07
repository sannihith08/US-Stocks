# ==========================================
# CPR + Breakout Strategy - Streamlit App
# ==========================================
import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go

st.set_page_config(page_title="CPR + Breakout Strategy", layout="wide")

st.title("📊 CPR Previous Day + Intraday + Breakout Strategy")

# --------------------------
# User Inputs


uploaded_file = st.file_uploader("📂 Upload your stock list CSV", type=["csv"])

if uploaded_file is not None:

    stocks_df = pd.read_csv(uploaded_file)
    stocks = stocks_df["Symbol"].tolist()

    # Results list
    qualified_stocks = []

    # Today's date
    today = datetime.today().date()

    progress_bar = st.progress(0)
    total = len(stocks)

    for idx, ticker in enumerate(stocks):
        try:
            # --------------------------
            # Step 1: Daily Data for CPR
            # --------------------------
            daily = yf.download(ticker, period="15d", interval="1d")
            daily = daily[daily.index.date < today]

            if len(daily) < 2:
                continue  # not enough data

            # Yesterday's OHLC
            yday_high = float(daily["High"].iloc[-2])
            yday_low = float(daily["Low"].iloc[-2])
            yday_close = float(daily["Close"].iloc[-2])

            # CPR Calculation
            P = (yday_high + yday_low + yday_close) / 3
            BC = (yday_high + yday_low) / 2
            TC = 2 * P - BC

            # Check ascending CPR
            if not (BC < P < TC):
                continue

            # --------------------------
            # Step 2: Intraday 5-min Data
            # --------------------------
            intraday = yf.download(
                ticker,
                start=daily.index[-1].date(),
                end=daily.index[-1].date() + timedelta(days=1),
                interval="5m"
            ).reset_index()

            if intraday.empty:
                continue

            # First 5-min candle
            first_candle = intraday.iloc[0]
            first_open = float(first_candle["Open"])
            first_close = float(first_candle["Close"])

            # Check condition
            if (first_close > first_open) and (first_close > yday_high):
                qualified_stocks.append(ticker)

        except Exception as e:
            st.warning(f"⚠️ Error processing {ticker}: {e}")
            continue

        progress_bar.progress((idx + 1) / total)

    # --------------------------
    # Step 3: Results
    # --------------------------
    if qualified_stocks:
        st.success("✅ Stocks satisfying conditions:")
        result_df = pd.DataFrame(qualified_stocks, columns=["Qualified Stocks"])
        st.dataframe(result_df)

        # Save to CSV
        csv_file = "qualified_stocks.csv"
        result_df.to_csv(csv_file, index=False)

        # Download link
        st.download_button(
            label="📥 Download Qualified Stocks CSV",
            data=result_df.to_csv(index=False).encode("utf-8"),
            file_name="qualified_stocks.csv",
            mime="text/csv"
        )
    else:
        st.error("❌ No stocks satisfied the conditions today.")
else:
    st.info("👆 Please upload a stock list CSV file (with a 'Symbol' column).")    
# Put input widgets inside col1
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
with col1:
    ticker = st.text_input("Enter Stock Symbol (e.g., ASIANPAINT.NS):", "ASIANPAINT.NS")
with col2:
     period = st.text_input("Enter Daily Data Period (e.g., 30d):", "30d")
with col3:
     intraday_interval = st.selectbox("Intraday Interval:", ["5m", "15m", "30m", "60m"], index=0)
with col4:
     vol_filter = st.selectbox("Apply Volume Breakout Filter?", ["No", "Yes"], index=0)


if st.button("Run Analysis"):
    # --------------------------
    # Step 1: Get Daily Data
    # --------------------------
    daily = yf.download(ticker, period=period, interval="1d")

    if daily.empty:
        st.error("No data found. Please check symbol or period.")
        st.stop()

    # Drop today's partial candle if exists
    today = datetime.today().date()
    daily = daily[daily.index.date < today]

    if len(daily) < 3:
        st.error("Not enough historical daily data to calculate CPR.")
        st.stop()

    # Yesterday & Day-before data (backtest mode)
    yday_high = float(daily["High"].iloc[-1])
    yday_low = float(daily["Low"].iloc[-1])
    yday_close = float(daily["Close"].iloc[-1])

    prev_high = float(daily["High"].iloc[-2])
    prev_low = float(daily["Low"].iloc[-2])
    prev_close = float(daily["Close"].iloc[-2])

    last_trading_day = daily.index[-1].date()

    # --------------------------
    # Step 2: Calculate CPR
    # --------------------------
    # pivot = (yday_high + yday_low + yday_close) / 3
    # bc = (yday_high + yday_low) / 2
    # tc = 2 * pivot - bc

    # Support/Resistance
    # r1 = tc + (tc - bc)
    # r2 = tc + 2 * (tc - bc)
    # s1 = bc - (tc - bc)
    # s2 = bc - 2 * (tc - bc)

    # Previous day CPR for trend comparison
    p_pivot = (prev_high + prev_low + prev_close) / 3
    p_bc = (prev_high + prev_low) / 2
    p_tc = 2 * p_pivot - p_bc

    pivot = (yday_high + yday_low + yday_close) / 3
    bc = (yday_high + yday_low) / 2
    tc = 2 * pivot - bc

    #Classic pivot supports/resistances
    r1 = (2 * pivot) - yday_low
    s1 = (2 * pivot) - yday_high
    r2 = pivot + (yday_high - yday_low)
    s2 = pivot - (yday_high - yday_low)

        # CPR Trend
    if pivot > p_pivot:
        cpr_trend = "Ascending CPR (Bullish Bias)"
        bullish_cpr = True
    elif pivot < p_pivot:
        cpr_trend = "Descending CPR (Bearish Bias)"
        bullish_cpr = False
    elif (bc >= p_bc) and (tc <= p_tc):
        cpr_trend = "Inside Value CPR (Consolidation)"
        bullish_cpr = False
    elif (bc < p_bc) and (tc > p_tc):
        cpr_trend = "Outside Value CPR (Volatility Expansion)"
        bullish_cpr = False
    else:
        cpr_trend = "Neutral CPR"
        bullish_cpr = False


  

    # # CPR Trend
    # if pivot > p_pivot:
    #     cpr_trend = "Ascending CPR (Bullish Bias)"
    # elif pivot < p_pivot:
    #     cpr_trend = "Descending CPR (Bearish Bias)"
    # elif (bc >= p_bc) and (tc <= p_tc):
    #     cpr_trend = "Inside Value CPR (Consolidation)"
    # elif (bc < p_bc) and (tc > p_tc):
    #     cpr_trend = "Outside Value CPR (Volatility Expansion)"
    # else:
    #     cpr_trend = "Neutral CPR"

    st.success(f"**CPR Trend:** {cpr_trend}")
    st.write(f"**Pivot:** {pivot:.2f}, **BC:** {bc:.2f}, **TC:** {tc:.2f}, **R1:** {r1:.2f}, **R2:** {r2:.2f}, **S1:** {s1:.2f}, **S2:** {s2:.2f}")

    # --------------------------
    # Step 3: Get Intraday Data
    # --------------------------
    intraday = yf.download(
        ticker,
        start=last_trading_day,
        end=last_trading_day + timedelta(days=1),
        interval=intraday_interval
    ).reset_index()

    if intraday.empty:
        st.error("No intraday data found for this ticker/interval.")
        st.stop()

    if isinstance(intraday.columns, pd.MultiIndex):
        intraday.columns = intraday.columns.get_level_values(0)

    intraday = intraday.dropna(subset=["Open", "High", "Low", "Close"])

    # Ensure datetime column is proper datetime type
    # # Fix timezone (yfinance gives UTC, convert to IST)
    # if "Datetime" in intraday.columns:
    #     intraday["Datetime"] = pd.to_datetime(intraday["Datetime"], utc=True).dt.tz_convert("Asia/Kolkata")
    # else:
    #     intraday.rename(columns={"Date": "Datetime"}, inplace=True)
    #     intraday["Datetime"] = pd.to_datetime(intraday["Datetime"], utc=True).dt.tz_convert("Asia/Kolkata")

        # Auto-detect timezone
    if ticker.endswith(".NS"):
        tz = "Asia/Kolkata"       # NSE India
    else:
        tz = "America/New_York"   # US stocks

    # Convert UTC → Local trading timezone
    if "Datetime" in intraday.columns:
        intraday["Datetime"] = pd.to_datetime(intraday["Datetime"], utc=True).dt.tz_convert(tz)
    else:
        intraday.rename(columns={"Date": "Datetime"}, inplace=True)
        intraday["Datetime"] = pd.to_datetime(intraday["Datetime"], utc=True).dt.tz_convert(tz)

       # --------------------------
    # Step 4: Breakout Detection with Volume Filter
    # --------------------------
    #avg_vol_10d = daily["Volume"].tail(10).mean()
        # Calculate 10-day avg volume once from daily data

    if "Volume" in daily.columns:
            avg_vol_10d = float(daily["Volume"].tail(7).mean())
           
    else:
            avg_vol_10d = 0.0
  

    # if "Volume" in daily.columns and not daily["Volume"].isna().all():
    #     #avg_vol_10d = daily["Volume"].rolling(window=10).mean().iloc[-1]  # ✅ single float
    #     avg_vol_10d = float(daily["Volume"].tail(10).mean())  
    # else:
    #     avg_vol_10d = 0
    # #st.info(f"10-Day Avg Volume: {avg_vol_10d:.0f}")

    # if vol_filter == "Yes":
    #     #breakouts = intraday[(intraday["Close"] > yday_high) & (intraday["Volume"] > avg_vol_10d)]
    #     # Breakout condition with volume filter
    #     st.write(f"🔎 10-Day Avg Volume Threshold: {avg_vol_10d:,.0f}")
    #     st.write(f"🔎 Current Day Volume: {intraday['Volume'].sum():,.0f}")
    #     breakouts = intraday[
    #         (intraday["Close"] > yday_high) & 
    #         (intraday["Volume"] > avg_vol_10d)
    #     ]
        
    # else:
    #     breakouts = intraday[intraday["Close"] > yday_high]   

    if vol_filter == "Yes":
        # Show thresholds
        st.write(f"🔎 10-Day Avg Volume Threshold: {avg_vol_10d:,.0f}")
        st.write(f"🔎 Current Day Volume (sum of intraday): {intraday['Volume'].sum():,.0f}")

        # Condition satisfied only if today's total volume > 10-day average
        if intraday["Volume"].sum() > avg_vol_10d:
            breakouts = intraday[intraday["Close"] > yday_high]
            st.success("✅ Volume breakout condition satisfied!")
        else:
            breakouts = pd.DataFrame()  # empty, no breakout
            st.warning("⚠️ Volume breakout condition NOT satisfied")
    else:
        breakouts = intraday[intraday["Close"] > yday_high]
        # --------------------------
    # Step 4: Breakout Detection
    # --------------------------
    #breakouts = intraday[intraday["Close"] > yday_high]
    entry_candle = None
    breakout_candle = None

    if not breakouts.empty:
        breakout_candle = breakouts.iloc[0]
        breakout_index = intraday.index.get_loc(breakouts.index[0])

        # Confirmation with next candle
        if breakout_index + 1 < len(intraday):
            next_candle = intraday.iloc[breakout_index + 1]
            if next_candle["Low"] >= breakout_candle["Low"] and next_candle["High"] <= breakout_candle["High"]:
                greens = intraday.iloc[breakout_index + 2:]
                green_candles = greens[greens["Close"] > greens["Open"]]
                if not green_candles.empty:
                    entry_candle = green_candles.iloc[0]

    # --------------------------
    # Step 5: Plotly Graph
    # --------------------------
    fig = go.Figure()

    # Candlesticks
    fig.add_trace(go.Candlestick(
        x=intraday["Datetime"],
        open=intraday['Open'],
        high=intraday['High'],
        low=intraday['Low'],
        close=intraday['Close'],
        name="Candles"
    ))

    # Yesterday High
    fig.add_hline(
        y=yday_high,
        line=dict(color="blue", dash="dash"),
        annotation_text=f"Yday High: {yday_high:.2f}"
    )

    # CPR Zone
    # fig.add_shape(
    #     type="rect",
    #     x0=intraday["Datetime"].iloc[0], x1=intraday["Datetime"].iloc[-1],
    #     y0=bc, y1=tc,
    #     fillcolor="yellow", opacity=0.2, layer="below", line_width=0
    # )
     # CPR Zone (Green if bullish, Yellow otherwise)
    cpr_color = "green" if bullish_cpr else "yellow"
    fig.add_shape(
        type="rect",
        x0=intraday["Datetime"].iloc[0], x1=intraday["Datetime"].iloc[-1],
        y0=bc, y1=tc,
        fillcolor=cpr_color, opacity=0.2, layer="below", line_width=0
    )

    # Pivot, R1, R2, S1, S2
    fig.add_hline(y=pivot, line=dict(color="yellow", dash="dot"), annotation_text=f"Pivot: {pivot:.2f}")
    fig.add_hline(y=r1, line=dict(color="green", dash="dash"), annotation_text=f"R1: {r1:.2f}")
    fig.add_hline(y=r2, line=dict(color="green", dash="dot"), annotation_text=f"R2: {r2:.2f}")
    fig.add_hline(y=s1, line=dict(color="red", dash="dash"), annotation_text=f"S1: {s1:.2f}")
    fig.add_hline(y=s2, line=dict(color="red", dash="dot"), annotation_text=f"S2: {s2:.2f}")

    # Mark Breakout Candle
    if breakout_candle is not None:
        fig.add_trace(go.Scatter(
            x=[breakout_candle["Datetime"]],
            y=[breakout_candle["Close"]],
            mode="markers",
            marker=dict(color="orange", size=12, symbol="star"),
            name="Breakout"
        ))

    # Mark Entry Candle
    if entry_candle is not None:
        fig.add_trace(go.Scatter(
            x=[entry_candle["Datetime"]],
            y=[entry_candle["Close"]],
            mode="markers",
            marker=dict(color="green", size=18, symbol="triangle-up"),
            name="Entry ✅"
        ))

    fig.update_layout(
        title=f"{ticker} - CPR + Breakout Strategy ({cpr_trend})",
        xaxis_title=f"Time ({tz})",
        yaxis_title="Price",
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        height=700,
        xaxis=dict(
            type="date",
            tickformat="%H:%M",  # show 09:30, 10:00, etc.
            tickangle=0
        )
    )
    st.plotly_chart(fig, use_container_width=True)
