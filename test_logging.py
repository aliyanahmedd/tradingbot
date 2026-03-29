"""
test_logging.py

Tests logger, SQLite trade database, and Telegram notifier together.
"""

from utils.logger import setup_logger
from utils.trade_log import init_db, log_trade_open, log_trade_close, get_all_trades, get_trade_summary
from utils.notifier import notify_trade_open, notify_trade_close, notify_bot_start

# --- Test 1: Logger ---
print("=" * 60)
print("  Testing Logger")
print("=" * 60)

logger = setup_logger()
logger.info("This is an INFO message — normal bot activity")
logger.warning("This is a WARNING — something needs attention")
logger.error("This is an ERROR — something went wrong")
logger.debug("This is a DEBUG message — only saved to file, not shown in console")
print("Check your logs/ folder — a log file should have been created.\n")

# --- Test 2: SQLite Database ---
print("=" * 60)
print("  Testing SQLite Trade Database")
print("=" * 60)

init_db()
logger.info("Database initialized.")

# Simulate opening a trade
log_trade_open(
    ticket      = 99999001,
    symbol      = "EURUSD",
    direction   = "BUY",
    lot         = 0.5,
    entry_price = 1.15071,
    sl_price    = 1.14962,
    tp_price    = 1.15344
)
logger.info("Trade open recorded in database.")

# Simulate closing that trade with a profit
log_trade_close(
    ticket      = 99999001,
    close_price = 1.15300,
    profit      = 114.50
)
logger.info("Trade close recorded in database.")

# Show all trades
trades = get_all_trades()
print(f"\nAll trades in database ({len(trades)} records):")
for t in trades:
    print(f"  #{t['id']} | {t['symbol']} | {t['direction']} | {t['lot']} lots | "
          f"Entry: {t['entry_price']} | Close: {t['close_price']} | "
          f"P&L: ${t['profit']} | Status: {t['status']}")

# Show summary
summary = get_trade_summary()
print(f"\nPerformance Summary:")
print(f"  Total trades : {summary['total_trades']}")
print(f"  Wins         : {summary['wins']}")
print(f"  Losses       : {summary['losses']}")
print(f"  Win rate     : {summary['win_rate']}%")
print(f"  Total P&L    : ${summary['total_profit']}")

logger.info("Phase 9 test complete.")
