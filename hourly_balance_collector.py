import ccxt
import os
import sqlite3
import datetime
import time
import pandas as pd # Used for pd.to_datetime and general data handling
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from dotenv import load_dotenv
from db_manager import fetch_symbols, fetch_scores
from ccxt_helper import get_balance_in_usdt

# Load environment variables from .env file
load_dotenv()

# --- Retrieve your API Key and Secret ---
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")


DATABASE_FILE = "scores.db"

# --- Database Functions ---
def initialize_db():
    """Initializes the SQLite database and creates the table if it doesn't exist."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS balance_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER NOT NULL,
                total_usdt_value REAL NOT NULL
            )
        """)
        conn.commit()
        conn.close()
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Database '{DATABASE_FILE}' initialized.")
    except Exception as e:
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error initializing database: {e}")

def save_balance_to_db(timestamp, total_usdt_value):
    """Saves the balance snapshot to the database."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO balance_snapshots (timestamp, total_usdt_value) VALUES (?, ?)",
                       (timestamp, total_usdt_value))
        conn.commit()
        conn.close()
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Saved: {timestamp} - {total_usdt_value:.2f} USDT to DB.")
    except Exception as e:
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error saving balance to DB: {e}")

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

# --- Binance Balance Fetching Function ---
def get_binance_total_usdt_balance_combined():
    """
    Fetches balances from both Binance Spot and USD-M Futures accounts,
    converts all assets to their USDT equivalent, and returns the total sum as a float.
    """
    total_usdt_value = 0
    for type in ['spot', 'future']:
        exchange = get_exchange(type)
        total_usdt_value += get_balance_in_usdt(exchange)

    return total_usdt_value

# --- Main Scheduled Task ---
def collect_and_save_balance():
    """
    The task to be scheduled: fetches balance and saves it to the database.
    """
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting balance collection...")
    current_time = datetime.datetime.utcnow().timestamp() * 1000
    total_balance = get_binance_total_usdt_balance_combined()

    if total_balance is not None:
        save_balance_to_db(current_time, total_balance)
    else:
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Failed to get balance at {current_time}. Not saving to DB.")
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Balance collection finished.")

# --- Script Entry Point ---
if __name__ == "__main__":
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Binance Balance Collector Script.")

    # Initialize the database
    initialize_db()

    # Set up the scheduler
    scheduler = BackgroundScheduler()
    # Add the job to run every 1 hour
    scheduler.add_job(
        collect_and_save_balance,
        trigger=IntervalTrigger(hours=1),
        id='binance_balance_job',
        name='Binance Hourly Balance Collection',
        replace_existing=True # Ensures only one instance of this job runs
    )

    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scheduler started. Next collection in 1 hour.")
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] The first collection will run shortly after startup.")

    # Run the first collection immediately
    collect_and_save_balance()

    # Start the scheduler
    scheduler.start()

    try:
        # Keep the main thread alive so the scheduler can run in the background
        while True:
            time.sleep(10) # Sleep for a short interval to avoid busy-waiting
    except (KeyboardInterrupt, SystemExit):
        # Gracefully shut down the scheduler on Ctrl+C or system exit
        scheduler.shutdown()
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scheduler shut down.")
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Script terminated.")