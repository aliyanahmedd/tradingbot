"""
test_indicators.py

Tests that indicators are calculated correctly on live MT5 data.
Prints the last 5 candles with all indicator values visible.
"""

import pandas as pd
from core.connector import connect, shutdown
from core.data_fetcher import get_candles
from core.indicators import apply_indicators

pd.set_option("display.float_format", "{:.5f}".format)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 120)

print("=" * 70)
print("  Testing Indicators")
print("=" * 70)

if not connect():
    print("[FAILED] Could not connect to MT5.")
    exit()

# --- Test 1: XAUUSD M15 entry indicators ---
print("\n>>> XAUUSD M15 — Entry indicators (EMA 9, EMA 21, RSI, ATR):\n")
df_entry = get_candles("XAUUSD", "M15", count=100)
df_entry = apply_indicators(df_entry, mode="entry")
print(df_entry.tail(5).to_string())

# --- Test 2: EURUSD H4 trend indicators ---
print("\n" + "=" * 70)
print("\n>>> EURUSD H4 — Trend indicators (EMA 20, EMA 50):\n")
df_trend = get_candles("EURUSD", "H4", count=100)
df_trend = apply_indicators(df_trend, mode="trend")
print(df_trend.tail(5).to_string())

# --- Summary of latest values ---
print("\n" + "=" * 70)
print("\n>>> Latest indicator snapshot:\n")

latest = df_entry.iloc[-1]
print(f"  XAUUSD M15:")
print(f"    Close   : {latest['close']:.2f}")
print(f"    EMA 9   : {latest['ema_fast']:.2f}")
print(f"    EMA 21  : {latest['ema_slow']:.2f}")
print(f"    RSI(14) : {latest['rsi']:.2f}")
print(f"    ATR(14) : {latest['atr']:.2f}")

latest_h4 = df_trend.iloc[-1]
print(f"\n  EURUSD H4:")
print(f"    Close   : {latest_h4['close']:.5f}")
print(f"    EMA 20  : {latest_h4['ema_fast']:.5f}")
print(f"    EMA 50  : {latest_h4['ema_slow']:.5f}")
trend = "UPTREND" if latest_h4["ema_fast"] > latest_h4["ema_slow"] else "DOWNTREND"
print(f"    Trend   : {trend}")

shutdown()
