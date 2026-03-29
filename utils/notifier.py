"""
utils/notifier.py

Telegram notifications removed. This file is kept as a stub
so other modules that import from it don't break.
All functions do nothing.
"""


def notify_trade_open(symbol, direction, lot, entry, sl, tp):
    pass


def notify_trade_close(symbol, direction, lot, entry, close_price, profit):
    pass


def notify_drawdown_alert(drawdown_pct, current_balance, start_balance):
    pass


def notify_error(error_message):
    pass


def notify_bot_start(balance, symbols):
    pass
