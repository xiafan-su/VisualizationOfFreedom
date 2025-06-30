# server_b.py
from flask import Flask, request, jsonify
import sqlite3
import os
from datetime import datetime, timezone

app = Flask(__name__)

# Define the SQLite database file name
DATABASE_FILE = 'scores.db'

# def datetime_to_milliseconds(dt_obj):
#     """Converts a datetime object to milliseconds since epoch (UTC)."""
#     # Ensure datetime object is timezone-aware and in UTC for consistent epoch calculation
#     if dt_obj.tzinfo is None: # If timezone-naive, assume UTC
#         dt_obj = dt_obj.replace(tzinfo=timezone.utc)
#     else: # Convert to UTC if it's timezone-aware but not UTC
#         dt_obj = dt_obj.astimezone(timezone.utc)
#     return int(dt_obj.timestamp() * 1000)

# The milliseconds_to_datetime_iso function is no longer needed for API responses
# as timestamps will be returned as raw milliseconds.
# def milliseconds_to_datetime_iso(ms):
#     """Converts milliseconds since epoch to an ISO 8601 string (UTC)."""
#     dt_obj = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
#     return dt_obj.isoformat(timespec='seconds').replace('+00:00', 'Z')

def init_db():
    """Initializes the SQLite database and creates the 'scores' table if it doesn't exist."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        # Create the scores table with symbol, timestamp (now INTEGER), and score columns.
        # (symbol, timestamp) is set as a composite primary key to ensure uniqueness
        # for a given symbol at a specific point in time.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scores (
                symbol TEXT NOT NULL,
                timestamp INTEGER NOT NULL, -- Storing as milliseconds since epoch
                score REAL NOT NULL,
                PRIMARY KEY (symbol, timestamp)
            )
        ''')
        conn.commit()
        print(f"Database '{DATABASE_FILE}' initialized successfully.")
    except sqlite3.Error as e:
        print(f"Database initialization error: {e}")
    finally:
        if conn:
            conn.close()

# Initialize the database when the application starts
init_db()

@app.route('/scores', methods=['POST'])
def add_score():
    """
    Adds one or more score entries to the database.
    Expects a JSON body that is either a single object:
    {"symbol": "AAPL", "timestamp": "2025-06-30T12:00:00Z", "score": 95.5}
    OR a list of objects:
    [
        {"symbol": "AAPL", "timestamp": "2025-06-30T12:00:00Z", "score": 95.5},
        {"symbol": "GOOG", "timestamp": 1678886400000, "score": 120.10}
    ]
    'timestamp' can be either an ISO 8601 string or a raw integer (milliseconds since epoch).
    The 'timestamp' will always be stored as milliseconds.
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request must be JSON"}), 400

    # Ensure data is a list; if not, wrap it in a list for consistent processing
    if not isinstance(data, list):
        data = [data]

    processed_scores = []
    errors = []

    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        for item in data:
            if not isinstance(item, dict):
                errors.append(f"Invalid item format: {item}. Expected an object.")
                continue

            symbol = item.get('symbol')
            timestamp_input = item.get('timestamp') # Can be string or int
            score = item.get('score')

            # Basic validation for each item
            if not all([symbol, timestamp_input is not None, score is not None]):
                errors.append(f"Missing 'symbol', 'timestamp', or 'score' in item: {item}")
                continue

            timestamp_ms = None
            # Determine if timestamp is already milliseconds or needs conversion from ISO 8601 string
            if isinstance(timestamp_input, int):
                timestamp_ms = timestamp_input
            else:
                errors.append(f"'timestamp' for item {item} must be a milliseconds integer.")
                continue
            
            # Validate score type
            if not isinstance(score, (int, float)):
                errors.append(f"'score' for item {item} must be a number.")
                continue

            try:
                cursor.execute(
                    "INSERT OR REPLACE INTO scores (symbol, timestamp, score) VALUES (?, ?, ?)",
                    (symbol, timestamp_ms, score)
                )
                processed_scores.append({"symbol": symbol, "timestamp": timestamp_ms, "score": score})
            except sqlite3.Error as e:
                errors.append(f"Database error for item {item}: {e}")
            except Exception as e:
                errors.append(f"An unexpected error occurred for item {item}: {e}")

        conn.commit() # Commit all successful insertions in one go
        
        response_message = f"Successfully processed {len(processed_scores)} out of {len(data)} items."
        if errors:
            response_message += f" {len(errors)} items had errors."
            return jsonify({
                "message": response_message,
                "successful_inserts": processed_scores,
                "errors": errors
            }), 207 # Multi-Status
        else:
            return jsonify({
                "message": response_message,
                "successful_inserts": processed_scores
            }), 201 # Created

    except sqlite3.Error as e:
        # This catch is for errors before the loop or during connection
        return jsonify({"error": f"Database connection or initial error: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred during batch processing: {e}"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/scores', methods=['GET'])
def get_all_scores():
    """
    Retrieves all scores from the database.
    Returns stored millisecond timestamps directly in the response.
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT symbol, timestamp, score FROM scores ORDER BY symbol, timestamp")
        rows = cursor.fetchall()

        scores = []
        for row in rows:
            scores.append({
                "symbol": row[0],
                "timestamp": row[1], # Return raw milliseconds
                "score": row[2]
            })
        return jsonify(scores), 200
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/scores/<string:symbol>', methods=['GET'])
def get_scores_by_symbol(symbol):
    """
    Retrieves scores for a specific symbol from the database.
    Returns stored millisecond timestamps directly in the response.
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT symbol, timestamp, score FROM scores WHERE symbol = ? ORDER BY timestamp", (symbol,))
        rows = cursor.fetchall()

        if not rows:
            return jsonify({"message": f"No scores found for symbol '{symbol}'"}), 404

        scores = []
        for row in rows:
            scores.append({
                "symbol": row[0],
                "timestamp": row[1], # Return raw milliseconds
                "score": row[2]
            })
        return jsonify(scores), 200
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/scores/<string:symbol>', methods=['DELETE'])
def delete_scores_by_symbol(symbol):
    """Deletes all scores for a specific symbol from the database."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scores WHERE symbol = ?", (symbol,))
        rows_affected = cursor.rowcount
        conn.commit()

        if rows_affected > 0:
            return jsonify({"message": f"Successfully deleted {rows_affected} scores for symbol '{symbol}'"}), 200
        else:
            return jsonify({"message": f"No scores found for symbol '{symbol}' to delete"}), 404
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # When running locally for testing, host='0.0.0.0' makes it accessible
    # from other machines on the same network. In a production environment,
    # you would typically use a WSGI server like Gunicorn or uWSGI
    # and a reverse proxy like Nginx.
    app.run(host='0.0.0.0', port=5000, debug=False) # debug=True for development, set to False in production
