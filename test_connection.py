"""
test_connection.py

Run this file to verify your MT5 connection is working correctly.
This is a one-time test script — not part of the bot itself.
"""

from core.connector import connect, shutdown

print("=" * 40)
print("  Testing MT5 Connection")
print("=" * 40)

if connect():
    print("\n[SUCCESS] Bot can connect to MT5.")
else:
    print("\n[FAILED] Could not connect to MT5. Check your .env credentials.")

shutdown()
