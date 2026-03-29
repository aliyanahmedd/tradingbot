"""
core/order_manager.py

Handles all trade execution: opening, closing, and modifying positions in MT5.
Every function that touches MT5 orders validates inputs first and
returns a clear result so the bot knows exactly what happened.
"""

import MetaTrader5 as mt5
from config.settings import MAGIC_NUMBER, MAX_DEVIATION, ATR_SL_MULTIPLIER, ATR_TP_MULTIPLIER


def get_open_positions(symbol=None):
    """
    Returns all open positions opened by this bot.

    Parameters:
        symbol (str, optional): if provided, only returns positions for that symbol.
                                if None, returns all bot positions.

    Returns:
        List of position objects, or empty list if none exist.
    """
    if symbol:
        positions = mt5.positions_get(symbol=symbol)
    else:
        positions = mt5.positions_get()

    if positions is None:
        return []

    # Filter to only return positions opened by this bot (our magic number)
    return [p for p in positions if p.magic == MAGIC_NUMBER]


def open_trade(symbol, signal, lot, sl_price, tp_price):
    """
    Opens a new market order (BUY or SELL) on the given symbol.

    Parameters:
        symbol   (str)  : e.g. "EURUSD"
        signal   (str)  : "BUY" or "SELL"
        lot      (float): position size from risk manager
        sl_price (float): stop loss price level
        tp_price (float): take profit price level

    Returns:
        (True, result)  if order was filled successfully
        (False, reason) if order was rejected
    """

    # Get current market price from MT5
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return False, f"Could not get tick data for {symbol}"

    # For a BUY we enter at the Ask price (what the broker sells to us at)
    # For a SELL we enter at the Bid price (what the broker buys from us at)
    if signal == "BUY":
        order_type = mt5.ORDER_TYPE_BUY
        price      = tick.ask
    elif signal == "SELL":
        order_type = mt5.ORDER_TYPE_SELL
        price      = tick.bid
    else:
        return False, f"Invalid signal: {signal}. Must be BUY or SELL."

    # Validate that SL is on the correct side of the entry price
    if signal == "BUY" and sl_price >= price:
        return False, f"Invalid SL for BUY: SL {sl_price} must be below entry {price}"
    if signal == "SELL" and sl_price <= price:
        return False, f"Invalid SL for SELL: SL {sl_price} must be above entry {price}"

    # Build the order request dictionary — this is what MT5 expects
    request = {
        "action":      mt5.TRADE_ACTION_DEAL,       # Immediate market execution
        "symbol":      symbol,                       # Which instrument to trade
        "volume":      lot,                          # Lot size
        "type":        order_type,                   # BUY or SELL
        "price":       price,                        # Entry price (current market)
        "sl":          sl_price,                     # Stop loss price
        "tp":          tp_price,                     # Take profit price
        "deviation":   MAX_DEVIATION,                # Max slippage allowed in points
        "magic":       MAGIC_NUMBER,                 # Our bot's unique identifier
        "comment":     "tradingbot",                 # Label visible in MT5 history
        "type_time":   mt5.ORDER_TIME_GTC,           # Good Till Cancelled
        "type_filling": mt5.ORDER_FILLING_FOK,       # Fill entire order or cancel
    }

    # Send the order to MT5
    result = mt5.order_send(request)

    if result is None:
        return False, f"order_send() returned None. MT5 error: {mt5.last_error()}"

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        return False, (
            f"Order rejected. Retcode: {result.retcode} | "
            f"Comment: {result.comment}"
        )

    print(f"  [ORDER OPENED] {signal} {lot} lots of {symbol} @ {result.price}")
    print(f"  SL: {sl_price} | TP: {tp_price} | Ticket: {result.order}")

    return True, result


def close_trade(position):
    """
    Closes a specific open position.

    Parameters:
        position: an MT5 position object from get_open_positions()

    Returns:
        (True, result)  if closed successfully
        (False, reason) if close failed
    """

    symbol = position.symbol
    lot    = position.volume
    ticket = position.ticket

    # Get current price to close at
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return False, f"Could not get tick data for {symbol}"

    # To close a BUY position, we place a SELL order (and vice versa)
    if position.type == mt5.ORDER_TYPE_BUY:
        close_type = mt5.ORDER_TYPE_SELL
        price      = tick.bid   # We sell at the bid to close our buy
    else:
        close_type = mt5.ORDER_TYPE_BUY
        price      = tick.ask   # We buy at the ask to close our sell

    request = {
        "action":       mt5.TRADE_ACTION_DEAL,
        "symbol":       symbol,
        "volume":       lot,
        "type":         close_type,
        "position":     ticket,              # The ticket ID of the position to close
        "price":        price,
        "deviation":    MAX_DEVIATION,
        "magic":        MAGIC_NUMBER,
        "comment":      "tradingbot close",
        "type_time":    mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }

    result = mt5.order_send(request)

    if result is None:
        return False, f"order_send() returned None. MT5 error: {mt5.last_error()}"

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        return False, (
            f"Close failed. Retcode: {result.retcode} | "
            f"Comment: {result.comment}"
        )

    print(f"  [ORDER CLOSED] Ticket {ticket} | {symbol} | {lot} lots @ {result.price}")

    return True, result


def modify_sl(position, new_sl):
    """
    Modifies the stop loss of an open position (used for breakeven trailing stop).

    Parameters:
        position: an MT5 position object
        new_sl  : the new stop loss price to set

    Returns:
        (True, result)  if modified successfully
        (False, reason) if modification failed
    """

    request = {
        "action":   mt5.TRADE_ACTION_SLTP,   # Modify SL/TP only (no new order)
        "symbol":   position.symbol,
        "position": position.ticket,
        "sl":       new_sl,
        "tp":       position.tp,             # Keep existing TP unchanged
    }

    result = mt5.order_send(request)

    if result is None:
        return False, f"order_send() returned None. MT5 error: {mt5.last_error()}"

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        return False, (
            f"Modify SL failed. Retcode: {result.retcode} | "
            f"Comment: {result.comment}"
        )

    print(f"  [SL MODIFIED] Ticket {position.ticket} | New SL: {new_sl}")

    return True, result


def check_breakeven(position, atr):
    """
    Checks if a trade has moved 1x ATR in profit and should be moved to breakeven.
    If yes, calls modify_sl() to move SL to the entry price.

    Parameters:
        position: MT5 position object
        atr     : current ATR value for this symbol/timeframe

    Returns:
        True if breakeven was applied, False if not needed yet
    """

    entry = position.price_open
    tick  = mt5.symbol_info_tick(position.symbol)
    if tick is None:
        return False

    current_price = tick.bid if position.type == mt5.ORDER_TYPE_BUY else tick.ask

    if position.type == mt5.ORDER_TYPE_BUY:
        profit_distance = current_price - entry
        # Only move to breakeven if SL hasn't already been moved above entry
        if profit_distance >= atr and position.sl < entry:
            print(f"  [BREAKEVEN] Moving SL to entry {entry} for ticket {position.ticket}")
            modify_sl(position, entry)
            return True

    elif position.type == mt5.ORDER_TYPE_SELL:
        profit_distance = entry - current_price
        if profit_distance >= atr and position.sl > entry:
            print(f"  [BREAKEVEN] Moving SL to entry {entry} for ticket {position.ticket}")
            modify_sl(position, entry)
            return True

    return False


def calculate_sl_tp(symbol, signal, atr):
    """
    Calculates the stop loss and take profit price levels using ATR.

    Parameters:
        symbol (str)  : trading symbol
        signal (str)  : "BUY" or "SELL"
        atr    (float): current ATR value

    Returns:
        (sl_price, tp_price) tuple, or (None, None) if price fetch fails
    """

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return None, None

    if signal == "BUY":
        entry  = tick.ask
        sl     = entry - (atr * ATR_SL_MULTIPLIER)
        tp     = entry + (atr * ATR_TP_MULTIPLIER)
    else:  # SELL
        entry  = tick.bid
        sl     = entry + (atr * ATR_SL_MULTIPLIER)
        tp     = entry - (atr * ATR_TP_MULTIPLIER)

    # Round to symbol's price precision
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info:
        digits = symbol_info.digits
        sl = round(sl, digits)
        tp = round(tp, digits)

    return sl, tp
