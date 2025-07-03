import streamlit as st
import pandas as pd
import os
import pandas as pd
import plotly.graph_objects as go
import ccxt as ccxt
import sqlite3

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Retrieve your API Key and Secret ---
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    st.error("API_KEY or API_SECRET not found in environment variables. Please check your .env file.")
    st.stop() # Stop the app if crucial credentials are missing

# --- Initialize CCXT Exchange (cached for efficiency) ---
@st.cache_resource
def get_exchange(type):
    """Initializes and returns the CCXT Binance exchange object."""
    exchange = ccxt.binance(
        {
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {
                'defaultType': type,  # spot, margin, future, delivery
                'adjustForTimeDifference': True,
            }
        }
    )
    return exchange

@st.cache_data(ttl=0) # ttl=0 ensures no caching, data is always refetched
def get_live_trade_data(symbol: str, type: str):
    """Simulates fetching real-time trade data."""
    exchange = get_exchange(type)

    trades = exchange.fetch_my_trades(symbol=symbol, limit=1000)
    df = pd.DataFrame([trade['info'] for trade in trades])
    if not df.empty:
        df.insert(0, 'datetime', pd.to_datetime(df['time'], unit='ms'))
        df = df.sort_values(by='datetime', ascending=False)
    return df

# --- Function to fetch K-line data ---
@st.cache_data(ttl=0) # ttl=0 ensures no caching, data is always refetched
def fetch_klines(symbol: str, type: str, timeframe='1m', limit=1440, since=None):
    """
    Fetches OHLCV (K-line) data from Binance using CCXT.
    Handles pagination if `limit` exceeds single request max (Binance max ~1000-1500).
    """
    exchange = get_exchange(type)
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since, limit)

    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['merge_key'] = df['timestamp'].dt.floor('min')
    df.set_index('timestamp', inplace=True)
    df.sort_index(inplace=True) # Ensure chronological order

    return df

# --- Function to fetch scores data ---
@st.cache_data(ttl=0) # ttl=0 ensures no caching, data is always refetched
def fetch_scores(symbol: str):
    DATABASE_FILE = 'scores.db'
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT symbol, timestamp, score FROM scores WHERE symbol = ? ORDER BY timestamp", (symbol,))
        rows = cursor.fetchall()

        scores = []
        for row in rows:
            scores.append([row[0], row[1], row[2]])
        scores_df = pd.DataFrame(scores, columns=['symbol', 'timestamp', 'score'])
        scores_df['merge_key'] = pd.to_datetime(scores_df['timestamp'], unit='ms')
        scores_df['merge_key'] = scores_df['merge_key'].dt.floor('min')
        return scores_df
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None
    finally:
        if conn:
            conn.close()

# --- Function to fetch all symbols list ---
@st.cache_data(ttl=0) # ttl=0 ensures no caching, data is always refetched
def fetch_symbols():
    DATABASE_FILE = 'scores.db'
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT symbol FROM scores")
        rows = cursor.fetchall()
        symbols = []
        for row in rows:
            symbols.append(row[0])
        return symbols
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []
    finally:
        if conn:
            conn.close()

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Visiualization of Freedom',
    page_icon=':gem:', # This is an emoji shortcode. Could be a URL too.
)

st.header(f"Visiualization of Freedom")

all_symbols = fetch_symbols()

# --- UI Input for Symbol ---
# Define a list of common symbols. You could also fetch this from the exchange if needed.
selected_symbol = st.selectbox(
    "Select a Trading Symbol:",
    #options=['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'BNBUSDT', 'DOGEUSDT'],
    options=all_symbols,
    index=0, # Default to BTCUSDT
    help="Choose the symbol to fetch trade data for."
)

selected_symbol_type = st.selectbox(
    "Select a the Symbol type:",
    options=['future', 'spot'],
    index=0, # Default to future
    help="Choose the type of the symbol."
)

# --- The "Load Data" Button ---
# Data will only load when this button is clicked
if st.button("Load Data", help="Click to fetch trade data for the selected symbol."):
    # Update the session state variable that triggers data loading
    st.session_state.symbol = selected_symbol
    st.session_state.type = selected_symbol_type

    # Check if data should be loaded (only after the button is clicked)
    if 'symbol' in st.session_state and 'type' in st.session_state:
        st.subheader(f"Trade Data for {st.session_state.symbol}")
        with st.spinner("Fetching live trade data..."):
            df = get_live_trade_data(symbol=st.session_state.symbol, type=st.session_state.type)
        if not df.empty:
            st.dataframe(
                df,
                # column_order=["datetime", "symbol"],
                use_container_width=True
            )
        else:
            # This will be displayed if the DataFrame is empty or an error occurred
            st.info("Trades info are empty.")
        
        st.subheader(f"{selected_symbol} K-line Chart")
        with st.spinner(f"Fetching 1m klines data..."):
            df_klines = fetch_klines(symbol=st.session_state.symbol, type=st.session_state.type)
        with st.spinner("Fetching scores data..."):
            df_scores = fetch_scores(symbol=st.session_state.symbol)
        df_klines = pd.merge(df_klines, df_scores[['merge_key', 'score']],
                on='merge_key', how='left')
        df_klines.set_index('merge_key', inplace=True)
        df_klines = df_klines.sort_index()

        if not df_klines.empty:
            # Create Candlestick chart
            fig = go.Figure(data=[go.Candlestick(
                x=df_klines.index,
                open=df_klines['open'],
                high=df_klines['high'],
                low=df_klines['low'],
                close=df_klines['close'],
                name='Candlesticks',
            )])

            # Add Volume bars
            fig.add_trace(go.Bar(
                x=df_klines.index,
                y=df_klines['volume'],
                name='Volume',
                marker_color='rgba(0, 150, 0, 0.5)',  # Green for up, red for down (simple)
                yaxis='y2', # Assign to secondary y-axis
            ))

            # --- Workaround: Add an invisible Scatter trace for custom hover info ---
            # This trace will carry all the hover data you want.
            # Make sure it uses the same x-axis values as your candlesticks.
            fig.add_trace(go.Scatter(
                x=df_klines.index,
                y=(df_klines['high'] + df_klines['low']) / 2, # Plot at the middle of the candle
                mode='markers', # We need markers for hover, but we'll make them invisible
                marker=dict(size=1, opacity=0), # Make markers tiny and fully transparent
                name='Score', # This name might appear if hoverinfo is not 'none'
                hoverinfo='text', # Crucial: Tell plotly to use text from hovertemplate
                # Prepare customdata for the Scatter trace
                customdata=df_klines[['score']].fillna('N/A').values,
                hovertemplate=(
                    "<b>Score:</b> %{customdata[0]:.6f}<extra></extra>"
                )
            ))

            # Update layout for better appearance
            fig.update_layout(
                xaxis_rangeslider_visible=False, # Hide the default range slider for cleaner look
                xaxis_title="Time",
                yaxis_title="Price",
                title=f"{selected_symbol} K-line Chart",
                hovermode="x unified",
                height=600,
                # Add secondary y-axis for volume
                yaxis=dict(domain=[0.3, 1]), # Price axis occupies top 70%
                yaxis2=dict(domain=[0, 0.25], anchor='x', overlaying='y', side='right', showgrid=False, title='Volume'), # Volume axis occupies bottom 25%
                template="plotly_dark", # Or "plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data fetched for the selected parameters. Please try different settings.")

        

