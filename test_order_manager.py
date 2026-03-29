"""
test_order_manager.py

Tests opening and closing a real trade on the demo account.
This places an actual order — on demo money only.
"""

import time
import MetaTrader5 as mt5
from core.connector import connect, shutdown
from core.order_manager import (
    open_trade,
    close_trade,
    get_open_positions,
    calculate_sl_tp
)
from core.data_fetcher import get_candles
from core.indicators import apply_indicators

print("=" * 60)
print("  Testing Order Manager (DEMO ACCOUNT)")
print("=" * 60)

if not connect():
    print("[FAILED] Could not connect to MT5.")
    exit()

SYMBOL = "EURUSD"

# Get current ATR to calculate SL/TP
df = get_candles(SYMBOL, "M15", count=100)
df = apply_indicators(df, mode="entry")
atr = df["atr"].iloc[-1]
print(f"\nCurrent ATR for {SYMBOL}: {atr:.5f}")

# Calculate SL and TP for a BUY trade
sl, tp = calculate_sl_tp(SYMBOL, "BUY", atr)
print(f"Calculated SL: {sl} | TP: {tp}")

# --- Open a BUY trade ---
print(f"\n[1] Opening BUY trade on {SYMBOL}...")
success, result = open_trade(
    symbol = SYMBOL,
    signal = "BUY",
    lot    = 0.01,      # Minimum lot size — just for testing
    sl_price = sl,
    tp_price = tp
)

if not success:
    print(f"[FAILED] Could not open trade: {result}")
    shutdown()
    exit()

print(f"[SUCCESS] Trade opened. Ticket: {result.order}")

# Wait 3 seconds so we can see it in MT5
print("\nWaiting 3 seconds... (check MT5 — you should see the open position)")
time.sleep(3)

# --- Check open positions ---
print(f"\n[2] Checking open positions for {SYMBOL}:")
positions = get_open_positions(SYMBOL)
print(f"    Found {len(positions)} bot position(s)")
for p in positions:
    print(f"    Ticket: {p.ticket} | {p.symbol} | {'BUY' if p.type == 0 else 'SELL'} | {p.volume} lots | Open @ {p.price_open}")

# --- Close the trade ---
if positions:
    print(f"\n[3] Closing position ticket {positions[0].ticket}...")
    success, result = close_trade(positions[0])
    if success:
        print(f"[SUCCESS] Trade closed successfully.")
    else:
        print(f"[FAILED] Could not close trade: {result}")

# Verify it's gone
remaining = get_open_positions(SYMBOL)
print(f"\n[4] Remaining open positions: {len(remaining)}")

shutdown()
