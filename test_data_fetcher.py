"""
test_data_fetcher.py

Tests that we can pull live candle data from MT5.
Prints the last 10 candles of XAUUSD on M15 and EURUSD on H4.
"""

from core.connector import connect, shutdown
from core.data_fetcher import get_candles

print("=" * 60)
print("  Testing Data Fetcher")
print("=" * 60)

if not connect():
    print("[FAILED] Could not connect to MT5.")
    exit()

# --- Test 1: XAUUSD on M15 ---
print("\n>>> XAUUSD — Last 10 candles on M15:\n")
df = get_candles("XAUUSD", "M15", count=10)

if df is not None:
    print(df.to_string())
    print(f"\nShape: {df.shape[0]} rows x {df.shape[1]} columns")
    print(f"Columns: {list(df.columns)}")
else:
    print("[FAILED] Could not fetch XAUUSD data.")

# --- Test 2: EURUSD on H4 ---
print("\n" + "=" * 60)
print("\n>>> EURUSD — Last 10 candles on H4:\n")
df2 = get_candles("EURUSD", "H4", count=10)

if df2 is not None:
    print(df2.to_string())
else:
    print("[FAILED] Could not fetch EURUSD data.")

shutdown()
