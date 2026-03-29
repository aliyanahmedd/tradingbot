"""
main.py

The entry point for the trading bot.
Wires together every module and runs the main trading loop.

Flow each cycle:
  1. Check all risk rules
  2. For each symbol: get signal
  3. If signal: calculate lot size, SL, TP → open trade → log it
  4. Check existing positions for breakeven trailing stop
  5. Wait for next M15 candle close and repeat

Run with: python main.py
Stop with: Ctrl+C
"""

import time
import schedule
import MetaTrader5 as mt5
from loguru import logger

from core.connector import connect, shutdown
from core.data_fetcher import get_candles
from core.indicators import apply_indicators
from core.signal_generator import get_signal
from core.risk_manager import run_all_checks, calculate_lot_size
from core.order_manager import (
    open_trade, get_open_positions,
    calculate_sl_tp, check_breakeven
)
from utils.logger import setup_logger
from utils.trade_log import init_db, log_trade_open
from utils.notifier import notify_bot_start, notify_trade_open, notify_error
from config.settings import SYMBOLS, MAGIC_NUMBER

# Global session start balance — captured once when bot starts
SESSION_START_BALANCE = 0.0


def run_cycle():
    """
    One full trading cycle — runs every 15 minutes.
    Checks every symbol for signals and manages open positions.
    """
    logger.info("=" * 50)
    logger.info("Running trading cycle...")

    account = mt5.account_info()
    if account is None:
        logger.error("Lost connection to MT5. Attempting reconnect...")
        if not connect():
            logger.error("Reconnect failed. Skipping this cycle.")
            return

    balance = account.balance
    logger.info(f"Account balance: ${balance:,.2f}")

    # --- Check existing positions for breakeven trailing stop ---
    all_positions = get_open_positions()
    for position in all_positions:
        symbol = position.symbol
        df = get_candles(symbol, "M15", count=100)
        if df is not None:
            df = apply_indicators(df, mode="entry")
            atr = df["atr"].iloc[-1]
            check_breakeven(position, atr)

    # --- Scan each symbol for new trade signals ---
    for symbol in SYMBOLS:
        logger.info(f"Scanning {symbol}...")

        # Run all risk checks first
        passed, reason = run_all_checks(symbol, SESSION_START_BALANCE)
        if not passed:
            logger.warning(f"{symbol} blocked: {reason}")
            continue

        # Get trading signal
        signal = get_signal(symbol)
        if signal is None:
            logger.info(f"{symbol}: No signal this cycle.")
            continue

        logger.info(f"{symbol}: {signal} signal detected!")

        # Get ATR for SL/TP calculation
        df_m15 = get_candles(symbol, "M15", count=100)
        if df_m15 is None:
            logger.error(f"Could not fetch M15 data for {symbol}")
            continue

        df_m15 = apply_indicators(df_m15, mode="entry")
        atr = df_m15["atr"].iloc[-1]

        # Calculate SL and TP prices
        sl, tp = calculate_sl_tp(symbol, signal, atr)
        if sl is None:
            logger.error(f"Could not calculate SL/TP for {symbol}")
            continue

        # Calculate lot size based on risk settings
        tick = mt5.symbol_info_tick(symbol)
        entry = tick.ask if signal == "BUY" else tick.bid
        lot, lot_reason = calculate_lot_size(symbol, sl, entry)

        if lot is None:
            logger.error(f"Could not calculate lot size for {symbol}: {lot_reason}")
            continue

        logger.info(f"{symbol}: {signal} | Lot: {lot} | Entry: {entry} | SL: {sl} | TP: {tp}")

        # Open the trade
        success, result = open_trade(symbol, signal, lot, sl, tp)

        if success:
            logger.success(f"Trade opened: {signal} {lot} lots {symbol} @ {result.price}")

            # Log to database
            log_trade_open(
                ticket      = result.order,
                symbol      = symbol,
                direction   = signal,
                lot         = lot,
                entry_price = result.price,
                sl_price    = sl,
                tp_price    = tp
            )

            # Send notification
            notify_trade_open(symbol, signal, lot, result.price, sl, tp)

        else:
            logger.error(f"Trade failed for {symbol}: {result}")
            notify_error(f"Trade failed for {symbol}: {result}")

    logger.info("Cycle complete. Waiting for next candle...")


def main():
    """
    Bot startup and main loop.
    """
    global SESSION_START_BALANCE

    # Set up logging first
    setup_logger()
    logger.info("Starting trading bot...")

    # Initialize database
    init_db()
    logger.info("Trade database ready.")

    # Connect to MT5
    if not connect():
        logger.error("Failed to connect to MT5. Exiting.")
        return

    # Capture session start balance for drawdown tracking
    account = mt5.account_info()
    SESSION_START_BALANCE = account.balance
    logger.info(f"Session start balance: ${SESSION_START_BALANCE:,.2f}")

    # Notify bot started
    notify_bot_start(SESSION_START_BALANCE, SYMBOLS)

    # Run one cycle immediately on startup
    run_cycle()

    # Schedule the bot to run every 15 minutes
    # This aligns roughly with M15 candle closes
    schedule.every(15).minutes.do(run_cycle)

    logger.info("Bot is running. Press Ctrl+C to stop.")

    # Main loop — keeps the bot alive and checks the schedule
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)   # Check every second if a scheduled job is due

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Shutting down bot...")

    finally:
        shutdown()
        logger.info("Bot stopped cleanly.")


if __name__ == "__main__":
    main()
