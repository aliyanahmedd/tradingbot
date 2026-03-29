"""
core/risk_manager.py

Enforces all risk management rules before any trade is opened.
Every function returns a tuple: (bool, str)
  - bool : True = allowed, False = blocked
  - str  : reason message explaining the decision (for logging)

The bot checks ALL of these before placing any order.
If any check returns False, the trade is rejected.
"""

import MetaTrader5 as mt5
from config.settings import (
    RISK_PERCENT,
    MAX_OPEN_POSITIONS,
    MAX_DRAWDOWN_PERCENT,
    MIN_BALANCE,
    MAGIC_NUMBER
)


def get_account_info():
    """
    Fetches current account details from MT5.
    Returns the account info object, or None if MT5 is not connected.
    """
    info = mt5.account_info()
    if info is None:
        return None
    return info


def check_minimum_balance():
    """
    Checks that the account balance is above the minimum required to trade.
    Prevents the bot from trading on a nearly-wiped account.

    Returns:
        (True, reason)  if balance is sufficient
        (False, reason) if balance is too low
    """
    info = get_account_info()
    if info is None:
        return False, "Could not retrieve account info from MT5"

    balance = info.balance

    if balance < MIN_BALANCE:
        return False, f"Balance ${balance:.2f} is below minimum ${MIN_BALANCE:.2f}"

    return True, f"Balance ${balance:.2f} is above minimum ${MIN_BALANCE:.2f}"


def check_drawdown(session_start_balance):
    """
    Checks if the account has dropped more than MAX_DRAWDOWN_PERCENT
    from the balance at the start of the trading session.

    If it has, the bot stops trading for the day to protect remaining capital.

    Parameters:
        session_start_balance (float): balance recorded when the bot started today

    Returns:
        (True, reason)  if drawdown is within limits
        (False, reason) if drawdown limit has been breached
    """
    info = get_account_info()
    if info is None:
        return False, "Could not retrieve account info from MT5"

    current_balance = info.balance

    # Calculate how much the account has dropped as a percentage
    drawdown = ((session_start_balance - current_balance) / session_start_balance) * 100

    if drawdown >= MAX_DRAWDOWN_PERCENT:
        return False, (
            f"Drawdown limit reached: {drawdown:.2f}% drop from session start "
            f"(${session_start_balance:.2f} → ${current_balance:.2f}). "
            f"Max allowed: {MAX_DRAWDOWN_PERCENT}%"
        )

    return True, f"Drawdown OK: {drawdown:.2f}% (limit: {MAX_DRAWDOWN_PERCENT}%)"


def check_max_positions():
    """
    Checks that the number of currently open positions is below the maximum.
    We only count positions opened by THIS bot (matched by MAGIC_NUMBER),
    not manual trades the user may have placed.

    Returns:
        (True, reason)  if we can open more positions
        (False, reason) if the limit has been reached
    """
    # Get all open positions from MT5
    positions = mt5.positions_get()

    if positions is None:
        # No positions exist at all — that's fine
        return True, "No open positions"

    # Count only positions opened by this bot using our magic number
    bot_positions = [p for p in positions if p.magic == MAGIC_NUMBER]
    count = len(bot_positions)

    if count >= MAX_OPEN_POSITIONS:
        return False, f"Max positions reached: {count}/{MAX_OPEN_POSITIONS} open"

    return True, f"Position count OK: {count}/{MAX_OPEN_POSITIONS} open"


def check_existing_position(symbol):
    """
    Checks if the bot already has an open position on this specific symbol.
    We never open two trades on the same symbol at the same time.

    Parameters:
        symbol (str): e.g. "EURUSD"

    Returns:
        (True, reason)  if no existing position on this symbol
        (False, reason) if a position already exists
    """
    positions = mt5.positions_get(symbol=symbol)

    if positions is None or len(positions) == 0:
        return True, f"No existing position on {symbol}"

    # Filter for only bot positions on this symbol
    bot_positions = [p for p in positions if p.magic == MAGIC_NUMBER]

    if len(bot_positions) > 0:
        return False, f"Already have an open position on {symbol}"

    return True, f"No existing bot position on {symbol}"


def calculate_lot_size(symbol, sl_price, entry_price):
    """
    Calculates the correct lot size to risk exactly RISK_PERCENT of balance.

    Formula:
        risk_amount = balance * (RISK_PERCENT / 100)
        sl_distance = |entry_price - sl_price|  (in price units)
        lot = risk_amount / (sl_distance * contract_size * tick_value)

    We use MT5's symbol info to get the exact contract size and tick value
    for each symbol — they are different for Forex vs Gold vs Oil.

    Parameters:
        symbol     (str)  : trading symbol
        sl_price   (float): stop loss price level
        entry_price(float): entry price level

    Returns:
        (lot_size, reason) where lot_size is rounded to allowed step
        Returns (None, reason) if calculation fails
    """
    info = get_account_info()
    if info is None:
        return None, "Could not retrieve account info"

    balance = info.balance

    # How much money we are willing to lose on this trade
    risk_amount = balance * (RISK_PERCENT / 100)

    # Get symbol trading specs from MT5
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        return None, f"Could not get symbol info for {symbol}"

    # The distance between entry and stop loss in price units
    sl_distance = abs(entry_price - sl_price)
    if sl_distance == 0:
        return None, "SL distance is zero — cannot calculate lot size"

    # Contract size = how many units one lot represents
    # For EURUSD: 100,000 units. For XAUUSD: 100 oz. MT5 provides this.
    contract_size = symbol_info.trade_contract_size

    # Tick value = how much 1 tick of price movement is worth in account currency
    tick_value = symbol_info.trade_tick_value
    tick_size  = symbol_info.trade_tick_size

    # Value of 1 lot moving by sl_distance
    value_per_lot = (sl_distance / tick_size) * tick_value

    if value_per_lot == 0:
        return None, "Value per lot is zero — symbol data may be unavailable"

    # Raw lot size from the risk formula
    raw_lot = risk_amount / value_per_lot

    # Round to the nearest allowed lot step (e.g. 0.01 for most brokers)
    lot_step  = symbol_info.volume_step
    lot_min   = symbol_info.volume_min
    lot_max   = symbol_info.volume_max

    # Round down to nearest step to never exceed risk
    lot = round(int(raw_lot / lot_step) * lot_step, 8)

    # Clamp between min and max allowed lot sizes
    lot = max(lot_min, min(lot_max, lot))

    reason = (
        f"Balance: ${balance:.2f} | Risk: {RISK_PERCENT}% = ${risk_amount:.2f} | "
        f"SL distance: {sl_distance:.5f} | Lot: {lot}"
    )

    return lot, reason


def run_all_checks(symbol, session_start_balance):
    """
    Runs every risk check in sequence before a trade is opened.
    Stops at the first failure — no point checking further.

    Parameters:
        symbol               (str)  : trading symbol
        session_start_balance(float): balance at bot session start

    Returns:
        (True, "All checks passed")   if all checks pass
        (False, reason)               if any check fails
    """
    checks = [
        ("Minimum Balance",   lambda: check_minimum_balance()),
        ("Drawdown Limit",    lambda: check_drawdown(session_start_balance)),
        ("Max Positions",     lambda: check_max_positions()),
        ("Existing Position", lambda: check_existing_position(symbol)),
    ]

    for name, check_fn in checks:
        passed, reason = check_fn()
        if not passed:
            return False, f"[BLOCKED] {name}: {reason}"

    return True, "All risk checks passed"
