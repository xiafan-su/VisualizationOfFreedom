import sqlite3
import pandas as pd

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

def fetch_balance_history():
    """
    Loads all balance snapshots from the SQLite database.
    Converts the 'timestamp_ms' column to UTC-aware datetime objects.
    """
    DATABASE_FILE = 'scores.db'
    conn = None # Initialize conn to None
    df = pd.DataFrame() # Initialize df as an empty DataFrame
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        # Fetch all records, ordered by timestamp (descending for latest first)
        df = pd.read_sql_query("SELECT * FROM balance_snapshots ORDER BY timestamp DESC", conn)
    except Exception as e:
       print(f"An unexpected error occurred while loading data: {e}")
    finally:
        if conn:
            conn.close()

    if not df.empty:
        # Convert milliseconds timestamp (INTEGER) to UTC-aware datetime objects
        # 'unit='ms'' tells pandas the integer is in milliseconds
        # 'utc=True' makes the resulting datetime objects timezone-aware and set to UTC
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
    return df