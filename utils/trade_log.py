"""
utils/trade_log.py

SQLite database for recording every trade the bot opens and closes.
SQLite is a file-based database — no server needed, just a .db file on disk.

The trades table stores:
  - When the trade was opened and closed
  - Which symbol, direction (BUY/SELL), and lot size
  - Entry, SL, and TP prices
  - Final profit/loss
  - The MT5 ticket number for cross-referencing
"""

import sqlite3
from datetime import datetime

DB_PATH = "trades.db"


def init_db():
    """
    Creates the database file and the trades table if they don't exist yet.
    Safe to call every time the bot starts — it won't overwrite existing data.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket      INTEGER,
            symbol      TEXT,
            direction   TEXT,
            lot         REAL,
            entry_price REAL,
            sl_price    REAL,
            tp_price    REAL,
            close_price REAL,
            profit      REAL,
            open_time   TEXT,
            close_time  TEXT,
            status      TEXT DEFAULT 'OPEN'
        )
    """)

    conn.commit()
    conn.close()


def log_trade_open(ticket, symbol, direction, lot, entry_price, sl_price, tp_price):
    """
    Records a newly opened trade in the database.

    Parameters:
        ticket      (int)  : MT5 ticket/order number
        symbol      (str)  : e.g. "EURUSD"
        direction   (str)  : "BUY" or "SELL"
        lot         (float): lot size
        entry_price (float): price the trade was opened at
        sl_price    (float): stop loss price
        tp_price    (float): take profit price
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO trades
            (ticket, symbol, direction, lot, entry_price, sl_price, tp_price, open_time, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OPEN')
    """, (
        ticket,
        symbol,
        direction,
        lot,
        entry_price,
        sl_price,
        tp_price,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()


def log_trade_close(ticket, close_price, profit):
    """
    Updates an existing trade record when it is closed.

    Parameters:
        ticket      (int)  : MT5 ticket number to find the record
        close_price (float): price the trade was closed at
        profit      (float): final profit or loss in account currency
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE trades
        SET close_price = ?,
            profit      = ?,
            close_time  = ?,
            status      = 'CLOSED'
        WHERE ticket = ?
    """, (
        close_price,
        profit,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ticket
    ))

    conn.commit()
    conn.close()


def get_all_trades():
    """
    Returns all trades from the database as a list of dictionaries.
    Useful for reviewing performance or building reports.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # Makes rows accessible as dicts
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM trades ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_open_trades():
    """
    Returns only the currently open trades from the database.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM trades WHERE status = 'OPEN' ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_trade_summary():
    """
    Returns a quick performance summary:
      - Total trades closed
      - Win count and loss count
      - Win rate percentage
      - Total profit/loss
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM trades WHERE status = 'CLOSED'")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM trades WHERE status = 'CLOSED' AND profit > 0")
    wins = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(profit) FROM trades WHERE status = 'CLOSED'")
    total_profit = cursor.fetchone()[0] or 0.0

    conn.close()

    losses   = total - wins
    win_rate = (wins / total * 100) if total > 0 else 0.0

    return {
        "total_trades" : total,
        "wins"         : wins,
        "losses"       : losses,
        "win_rate"     : round(win_rate, 2),
        "total_profit" : round(total_profit, 2)
    }
