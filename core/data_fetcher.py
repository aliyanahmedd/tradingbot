"""
core/data_fetcher.py

Fetches OHLCV candle data from MT5 for any symbol and timeframe.
Returns a clean pandas DataFrame ready for indicator calculations.
"""

import MetaTrader5 as mt5
import pandas as pd
from config.settings import CANDLE_COUNT


# Map human-readable timeframe strings to MT5's internal integer constants.
# MT5 doesn't understand "M15" as a string — it needs the exact integer value.
# This dictionary lets us write TIMEFRAME_MAP["M15"] and get mt5.TIMEFRAME_M15.
TIMEFRAME_MAP = {
    "M1":  mt5.TIMEFRAME_M1,
    "M5":  mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1":  mt5.TIMEFRAME_H1,
    "H4":  mt5.TIMEFRAME_H4,
    "D1":  mt5.TIMEFRAME_D1,
    "W1":  mt5.TIMEFRAME_W1,
    "MN1": mt5.TIMEFRAME_MN1,
}


def get_candles(symbol, timeframe_str, count=CANDLE_COUNT):
    """
    Fetch the most recent 'count' candles for a symbol on a given timeframe.

    Parameters:
        symbol       (str): e.g. "EURUSD", "XAUUSD"
        timeframe_str(str): e.g. "M15", "H4"
        count        (int): number of candles to fetch (default from settings)

    Returns:
        pandas DataFrame with columns: time, open, high, low, close, volume
        Returns None if the fetch fails.
    """

    # Convert the string timeframe to the MT5 integer constant
    timeframe = TIMEFRAME_MAP.get(timeframe_str)
    if timeframe is None:
        print(f"[ERROR] Unknown timeframe: {timeframe_str}. Use M1, M5, M15, M30, H1, H4, D1.")
        return None

    # Ask MT5 for the last 'count' candles, starting from the most recent one (index 0)
    # mt5.copy_rates_from_pos() returns a numpy structured array
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)

    if rates is None or len(rates) == 0:
        print(f"[ERROR] No data returned for {symbol} {timeframe_str}. Error: {mt5.last_error()}")
        return None

    # Convert the numpy structured array into a pandas DataFrame
    df = pd.DataFrame(rates)

    # MT5 returns time as a Unix timestamp (seconds since 1970-01-01).
    # We convert it to a human-readable datetime object.
    df["time"] = pd.to_datetime(df["time"], unit="s")

    # Set the time column as the index — this is standard for time series data
    df.set_index("time", inplace=True)

    # MT5 returns these columns: time, open, high, low, close, tick_volume, spread, real_volume
    # We only keep the ones we actually use
    df = df[["open", "high", "low", "close", "tick_volume"]]

    # Rename tick_volume to volume — cleaner and more standard
    df.rename(columns={"tick_volume": "volume"}, inplace=True)

    return df
