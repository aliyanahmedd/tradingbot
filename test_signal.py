"""
test_signal.py

Tests the signal generator on live market data for all configured symbols.
Shows exactly which conditions passed and which failed for each symbol.
"""

from core.connector import connect, shutdown
from core.signal_generator import get_signal
from config.settings import SYMBOLS

print("=" * 60)
print("  Testing Signal Generator")
print("=" * 60)

if not connect():
    print("[FAILED] Could not connect to MT5.")
    exit()

results = {}

for symbol in SYMBOLS:
    signal = get_signal(symbol)
    results[symbol] = signal

print("\n" + "=" * 60)
print("  SIGNAL SUMMARY")
print("=" * 60)
for symbol, signal in results.items():
    status = signal if signal else "NO SIGNAL"
    print(f"  {symbol:<10} : {status}")

shutdown()
