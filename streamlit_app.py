import streamlit as st
import pandas as pd
import os
import pandas as pd
import ccxt as ccxt

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Retrieve your API Key and Secret ---
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    st.error("API_KEY or API_SECRET not found in environment variables. Please check your .env file.")
    st.stop() # Stop the app if crucial credentials are missing


@st.cache_data(ttl=0) # ttl=0 ensures no caching, data is always refetched
def get_live_trade_data(symbol: str, type: str):
    """Simulates fetching real-time trade data."""
    st.write("Fetching live trade data...")

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
    trades = exchange.fetch_my_trades(symbol=symbol, limit=1000)
    df = pd.DataFrame([trade['info'] for trade in trades])
    df.insert(0, 'datetime', pd.to_datetime(df['time'], unit='ms'))
    # df['datetime'] = pd.to_datetime(df['time'], unit='ms') # For display purposes
    # df['price'] = df['price'].apply(float)
    # df['qty'] = df['qty'].apply(float)
    # df['commission'] = df['commission'].apply(float)
    # df['realizedPnl'] = df['realizedPnl'].apply(float)
    df_sorted = df.sort_values(by='datetime', ascending=False)
    return df_sorted



# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Visiualization of Freedom',
    page_icon=':gem:', # This is an emoji shortcode. Could be a URL too.
)

# --- UI Input for Symbol ---
# Define a list of common symbols. You could also fetch this from the exchange if needed.
selected_symbol = st.selectbox(
    "Select a Trading Symbol:",
    options=['BTCUSDT', 'BTCFDUSD'],
    index=0, # Default to BTCUSDT
    help="Choose the symbol to fetch trade data for."
)

selected_symbol_type = st.selectbox(
    "Select a the Symbol type:",
    options=['future', 'spot'],
    index=0, # Default to future
    help="Choose the type of the symbol."
)

# if 'symbol' not in st.session_state or 'type' not in st.session_state :
#     st.session_state.symbol = 'BTCUSDT' # Default value
#     st.session_state.type = 'future' # Default value


# --- The "Load Data" Button ---
# Data will only load when this button is clicked
if st.button("Load Data", help="Click to fetch trade data for the selected symbol."):
    # Update the session state variable that triggers data loading
    st.session_state.symbol = selected_symbol
    st.session_state.type = selected_symbol_type

    # Check if data should be loaded (only after the button is clicked)
    if 'symbol' in st.session_state and 'type' in st.session_state:
        st.subheader(f"Trade Data for {st.session_state.symbol}")
        df = get_live_trade_data(symbol=st.session_state.symbol, type=st.session_state.type)

        if not df.empty:
            st.dataframe(
                df,
                # column_order=["datetime", "symbol"],
                use_container_width=True
            )
        else:
            # This will be displayed if the DataFrame is empty or an error occurred
            st.info("Please select a symbol and click 'Load Data' to view trades.")

# df = get_live_trade_data(symbol=selected_symbol, type=selected_symbol_type)

# st.dataframe(
#     df,
#     column_order=["datetime", "symbol", "side", "price", "qty", "realizedPnl", "commission", "commissionAsset", "positionSide", "maker", "buyer", "id", "orderId"]
# )

# @st.cache_data
# def get_gdp_data():
#     """Grab GDP data from a CSV file.

#     This uses caching to avoid having to read the file every time. If we were
#     reading from an HTTP endpoint instead of a file, it's a good idea to set
#     a maximum age to the cache with the TTL argument: @st.cache_data(ttl='1d')
#     """

#     # Instead of a CSV on disk, you could read from an HTTP endpoint here too.
#     DATA_FILENAME = Path(__file__).parent/'data/gdp_data.csv'
#     raw_gdp_df = pd.read_csv(DATA_FILENAME)

#     MIN_YEAR = 1960
#     MAX_YEAR = 2022

#     # The data above has columns like:
#     # - Country Name
#     # - Country Code
#     # - [Stuff I don't care about]
#     # - GDP for 1960
#     # - GDP for 1961
#     # - GDP for 1962
#     # - ...
#     # - GDP for 2022
#     #
#     # ...but I want this instead:
#     # - Country Name
#     # - Country Code
#     # - Year
#     # - GDP
#     #
#     # So let's pivot all those year-columns into two: Year and GDP
#     gdp_df = raw_gdp_df.melt(
#         ['Country Code'],
#         [str(x) for x in range(MIN_YEAR, MAX_YEAR + 1)],
#         'Year',
#         'GDP',
#     )

#     # Convert years from string to integers
#     gdp_df['Year'] = pd.to_numeric(gdp_df['Year'])

#     return gdp_df

# gdp_df = get_gdp_data()

# # -----------------------------------------------------------------------------
# # Draw the actual page

# # Set the title that appears at the top of the page.
# '''
# # :earth_americas: GDP dashboard

# Browse GDP data from the [World Bank Open Data](https://data.worldbank.org/) website. As you'll
# notice, the data only goes to 2022 right now, and datapoints for certain years are often missing.
# But it's otherwise a great (and did I mention _free_?) source of data.
# '''

# # Add some spacing
# ''
# ''

# min_value = gdp_df['Year'].min()
# max_value = gdp_df['Year'].max()

# from_year, to_year = st.slider(
#     'Which years are you interested in?',
#     min_value=min_value,
#     max_value=max_value,
#     value=[min_value, max_value])

# countries = gdp_df['Country Code'].unique()

# if not len(countries):
#     st.warning("Select at least one country")

# selected_countries = st.multiselect(
#     'Which countries would you like to view?',
#     countries,
#     ['DEU', 'FRA', 'GBR', 'BRA', 'MEX', 'JPN'])

# ''
# ''
# ''

# # Filter the data
# filtered_gdp_df = gdp_df[
#     (gdp_df['Country Code'].isin(selected_countries))
#     & (gdp_df['Year'] <= to_year)
#     & (from_year <= gdp_df['Year'])
# ]

# st.header('GDP over time', divider='gray')

# ''

# st.line_chart(
#     filtered_gdp_df,
#     x='Year',
#     y='GDP',
#     color='Country Code',
# )

# ''
# ''


# first_year = gdp_df[gdp_df['Year'] == from_year]
# last_year = gdp_df[gdp_df['Year'] == to_year]

# st.header(f'GDP in {to_year}', divider='gray')

# ''

# cols = st.columns(4)

# for i, country in enumerate(selected_countries):
#     col = cols[i % len(cols)]

#     with col:
#         first_gdp = first_year[first_year['Country Code'] == country]['GDP'].iat[0] / 1000000000
#         last_gdp = last_year[last_year['Country Code'] == country]['GDP'].iat[0] / 1000000000

#         if math.isnan(first_gdp):
#             growth = 'n/a'
#             delta_color = 'off'
#         else:
#             growth = f'{last_gdp / first_gdp:,.2f}x'
#             delta_color = 'normal'

#         st.metric(
#             label=f'{country} GDP',
#             value=f'{last_gdp:,.0f}B',
#             delta=growth,
#             delta_color=delta_color
#         )
