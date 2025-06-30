# client_a.py
import requests
import json
from datetime import datetime, timedelta, timezone

# Replace with the actual IP address or hostname of Server B
# If running on the same machine, '127.0.0.1' or 'localhost' is fine.
# If on a different server, use its network IP (e.g., '192.168.1.100').
SERVER_B_URL = "http://20.187.91.140:5000" # Assuming Server B runs on the same machine for this example

def datetime_to_milliseconds(dt_obj):
    """Converts a datetime object to milliseconds since epoch (UTC)."""
    if dt_obj.tzinfo is None:
        dt_obj = dt_obj.replace(tzinfo=timezone.utc)
    else:
        dt_obj = dt_obj.astimezone(timezone.utc)
    return int(dt_obj.timestamp() * 1000)

def add_scores(scores_list):
    """
    Adds one or more score entries to Server B.
    'scores_list' should be a list of dictionaries, where each dictionary
    contains 'symbol', 'timestamp' (ISO 8601 string or milliseconds int), and 'score'.
    """
    url = f"{SERVER_B_URL}/scores"
    headers = {'Content-Type': 'application/json'}
    print(f"\n--- Adding scores ---")
    try:
        response = requests.post(url, json=scores_list, headers=headers)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        print("Response:", json.dumps(response.json(), indent=2))
    except requests.exceptions.RequestException as e:
        print(f"Error adding scores: {e}")
        if e.response is not None:
            print("Server response:", e.response.text)

def get_all_scores():
    """Retrieves all scores from Server B."""
    url = f"{SERVER_B_URL}/scores"
    print("\n--- Getting all scores ---")
    try:
        response = requests.get(url)
        response.raise_for_status()
        print("Response:", json.dumps(response.json(), indent=2))
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting all scores: {e}")
        if e.response is not None:
            print("Server response:", e.response.text)
        return None

def get_scores_by_symbol(symbol):
    """Retrieves scores for a specific symbol from Server B."""
    url = f"{SERVER_B_URL}/scores/{symbol}"
    print(f"\n--- Getting scores for symbol: {symbol} ---")
    try:
        response = requests.get(url)
        response.raise_for_status()
        print("Response:", json.dumps(response.json(), indent=2))
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting scores for {symbol}: {e}")
        if e.response is not None:
            print("Server response:", e.response.text)
        return None

def delete_scores_by_symbol(symbol):
    """Deletes all scores for a specific symbol on Server B."""
    url = f"{SERVER_B_URL}/scores/{symbol}"
    print(f"\n--- Deleting scores for symbol: {symbol} ---")
    try:
        response = requests.delete(url)
        response.raise_for_status()
        print("Response:", json.dumps(response.json(), indent=2))
    except requests.exceptions.RequestException as e:
        print(f"Error deleting scores for {symbol}: {e}")
        if e.response is not None:
            print("Server response:", e.response.text)

if __name__ == '__main__':
    # --- Demonstrate adding scores ---

    # Get current time in milliseconds for testing raw timestamp input
    current_ms = datetime_to_milliseconds(datetime.now())

    # Example 1: Add a single score with ISO 8601 timestamp
    add_scores([
        {"symbol": "AAPL", "timestamp": datetime_to_milliseconds(datetime.now() - timedelta(minutes=5)), "score": 175.25}
    ])

    # Example 2: Add a single score with raw millisecond timestamp
    add_scores([
        {"symbol": "GOOG", "timestamp": current_ms, "score": 120.10}
    ])

    # Example 3: Add multiple scores in one request, mixing timestamp formats
    batch_scores = [
        {"symbol": "MSFT", "timestamp": datetime_to_milliseconds(datetime.now() - timedelta(minutes=2)), "score": 420.00},
        {"symbol": "AAPL", "timestamp": datetime_to_milliseconds(datetime.now() - timedelta(minutes=10)), "score": 176.00}, # Older timestamp for AAPL
        {"symbol": "GOOG", "timestamp": datetime_to_milliseconds(datetime.now() + timedelta(minutes=1)), "score": 121.50}, # Future timestamp for GOOG
        {"symbol": "AMZN", "timestamp": datetime_to_milliseconds(datetime.now() + timedelta(minutes=2)), "score": 150.75}
    ]
    add_scores(batch_scores)

    # --- Demonstrate getting all scores ---
    get_all_scores()

    # --- Demonstrate getting scores by symbol ---
    get_scores_by_symbol("AAPL")
    get_scores_by_symbol("GOOG")
    get_scores_by_symbol("AMZN")
    get_scores_by_symbol("NONEXISTENT") # Should show "No scores found"

    # --- Demonstrate deleting scores ---
    delete_scores_by_symbol("MSFT")
    get_all_scores() # Verify MSFT is gone
    delete_scores_by_symbol("NONEXISTENT") # Should show "No scores found to delete"
