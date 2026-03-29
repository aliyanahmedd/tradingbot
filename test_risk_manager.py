"""
test_risk_manager.py

Tests all risk management functions against the live demo account.
"""

import MetaTrader5 as mt5
from core.connector import connect, shutdown
from core.risk_manager import (
    check_minimum_balance,
    check_drawdown,
    check_max_positions,
    check_existing_position,
    calculate_lot_size,
    run_all_checks
)

print("=" * 60)
print("  Testing Risk Manager")
print("=" * 60)

if not connect():
    print("[FAILED] Could not connect to MT5.")
    exit()

# Record session start balance (normally done once at bot startup)
account = mt5.account_info()
session_start_balance = account.balance
print(f"\nSession start balance: ${session_start_balance:,.2f}")

# --- Test 1: Minimum balance ---
print("\n[1] Minimum Balance Check:")
passed, reason = check_minimum_balance()
print(f"    Result : {'PASS' if passed else 'FAIL'}")
print(f"    Reason : {reason}")

# --- Test 2: Drawdown check ---
print("\n[2] Drawdown Check:")
passed, reason = check_drawdown(session_start_balance)
print(f"    Result : {'PASS' if passed else 'FAIL'}")
print(f"    Reason : {reason}")

# Simulate a drawdown scenario
print("\n[2b] Drawdown Check (simulated 6% loss scenario):")
simulated_start = session_start_balance * 1.065  # pretend we started 6.5% higher
passed, reason = check_drawdown(simulated_start)
print(f"    Result : {'PASS' if passed else 'BLOCKED'}")
print(f"    Reason : {reason}")

# --- Test 3: Max positions ---
print("\n[3] Max Positions Check:")
passed, reason = check_max_positions()
print(f"    Result : {'PASS' if passed else 'FAIL'}")
print(f"    Reason : {reason}")

# --- Test 4: Existing position on EURUSD ---
print("\n[4] Existing Position Check (EURUSD):")
passed, reason = check_existing_position("EURUSD")
print(f"    Result : {'PASS' if passed else 'FAIL'}")
print(f"    Reason : {reason}")

# --- Test 5: Lot size calculation ---
print("\n[5] Lot Size Calculation:")

# EURUSD example: entry at 1.15071, SL 30 pips below (buy trade)
entry  = 1.15071
sl     = 1.14771  # 30 pips SL
lot, reason = calculate_lot_size("EURUSD", sl, entry)
print(f"    EURUSD  entry={entry}, SL={sl}")
print(f"    Lot     : {lot}")
print(f"    Details : {reason}")

# XAUUSD example: entry at 4493, SL based on ATR x 1.5 (~24 points)
entry_xau = 4493.00
sl_xau    = 4493.00 - (16.17 * 1.5)  # ATR from earlier test
lot_xau, reason_xau = calculate_lot_size("XAUUSD", sl_xau, entry_xau)
print(f"\n    XAUUSD  entry={entry_xau}, SL={sl_xau:.2f}")
print(f"    Lot     : {lot_xau}")
print(f"    Details : {reason_xau}")

# --- Test 6: Full check sequence ---
print("\n[6] Full Risk Check for EURUSD:")
passed, reason = run_all_checks("EURUSD", session_start_balance)
print(f"    Result : {'PASS — trade allowed' if passed else 'BLOCKED'}")
print(f"    Reason : {reason}")

shutdown()
