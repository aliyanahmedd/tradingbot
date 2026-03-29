"""
utils/logger.py

Sets up Loguru — a modern logging library that replaces Python's built-in logging.

Why Loguru instead of Python's built-in logging?
  - Built-in logging requires 10+ lines of boilerplate to configure properly.
  - Loguru does it in 2 lines with better formatting, colors, and file rotation.
  - Loguru automatically rotates log files (starts a new file each day or when
    the file gets too big) so your logs folder never fills up your disk.
  - It shows the exact file, function, and line number where each log came from.
  - Colors in the console make it easy to spot errors at a glance.
"""

import sys
from loguru import logger


def setup_logger():
    """
    Configures Loguru with two output destinations:
      1. Console (terminal) — colored, human-readable output
      2. File (logs/tradingbot.log) — full structured log saved to disk

    Call this once at the start of main.py before anything else runs.
    After calling this, use logger.info(), logger.error(), etc. anywhere in the bot.
    """

    # Remove the default Loguru handler so we can set our own format
    logger.remove()

    # --- Console handler ---
    # Shows logs in the terminal with color-coded levels
    # {time} = timestamp, {level} = INFO/ERROR/etc, {message} = your log text
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        colorize=True
    )

    # --- File handler ---
    # Saves every log to a file, rotates daily, keeps 7 days of history
    logger.add(
        "logs/tradingbot_{time:YYYY-MM-DD}.log",  # New file each day
        level="DEBUG",                             # Capture everything including debug
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="00:00",                          # Rotate at midnight
        retention="7 days",                        # Delete logs older than 7 days
        compression="zip",                         # Compress old logs to save space
        encoding="utf-8"
    )

    logger.info("Logger initialized — console and file logging active.")
    return logger
