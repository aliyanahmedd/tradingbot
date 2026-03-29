"""
config/settings.py

Central configuration file for the trading bot.
All parameters that control bot behavior live here.
To change how the bot works, you edit this file — not the core logic files.
"""

import os
from dotenv import load_dotenv

# Load the .env file so all os.getenv() calls below can read from it
load_dotenv()

# ==============================================================================
# MT5 ACCOUNT CREDENTIALS
# These are loaded from your .env file — never hardcoded here
# ==============================================================================

MT5_LOGIN    = int(os.getenv("MT5_LOGIN", 0))       # Your MT5 account number
MT5_PASSWORD = os.getenv("MT5_PASSWORD", "")         # Your MT5 account password
MT5_SERVER   = os.getenv("MT5_SERVER", "")           # Your broker's server name

# ==============================================================================
# TRADING SYMBOLS
# Each symbol in this list will be scanned for signals every cycle
# ==============================================================================

SYMBOLS = [
    "EURUSD",
    "GBPUSD",
    "XAUUSD",  # Gold
    "WTI",     # Crude Oil (WTI on MetaQuotes-Demo)
]

# ==============================================================================
# TIMEFRAMES
# MT5 uses integer constants for timeframes — we import them in the files
# that need them. Here we just store the string names for display/logging.
# ==============================================================================

TIMEFRAME_TREND = "H4"   # Higher timeframe — used to confirm trend direction
TIMEFRAME_ENTRY = "M15"  # Lower timeframe — used for entry signal detection

# ==============================================================================
# INDICATOR PARAMETERS
# ==============================================================================

# EMA periods for the H4 trend confirmation
EMA_TREND_FAST = 20   # If EMA20 > EMA50 on H4 = uptrend
EMA_TREND_SLOW = 50

# EMA periods for the M15 entry signal (crossover)
EMA_ENTRY_FAST = 9    # If EMA9 crosses above EMA21 = buy signal
EMA_ENTRY_SLOW = 21

# RSI settings
RSI_PERIOD = 14
RSI_BUY_MIN  = 45     # RSI must be above this for a buy
RSI_BUY_MAX  = 65     # RSI must be below this for a buy (not overbought)
RSI_SELL_MIN = 35     # RSI must be above this for a sell (not oversold)
RSI_SELL_MAX = 55     # RSI must be below this for a sell

# ATR settings
ATR_PERIOD = 14
ATR_SL_MULTIPLIER = 1.5   # SL = entry +/- (ATR x 1.5)
ATR_TP_MULTIPLIER = 2.5   # TP = entry +/- (ATR x 2.5)
ATR_BE_MULTIPLIER = 1.0   # Move SL to breakeven when profit reaches 1x ATR

# ==============================================================================
# RISK MANAGEMENT
# ==============================================================================

RISK_PERCENT         = 1.5   # Maximum % of account balance to risk per trade
MAX_OPEN_POSITIONS   = 3     # Maximum number of simultaneous open trades
MAX_DRAWDOWN_PERCENT = 5.0   # If account drops 5% from session start, stop trading
MIN_BALANCE          = 100.0 # Minimum account balance required to allow trading ($)

# ==============================================================================
# BOT BEHAVIOR
# ==============================================================================

# How many candles to fetch when pulling data (more = more history for indicators)
CANDLE_COUNT = 200

# Magic number — a unique ID stamped on every order this bot places.
# Lets you identify bot trades vs manual trades in MT5's trade history.
MAGIC_NUMBER = 20240101

# Maximum slippage allowed on order execution (in points)
# If price moves more than this between signal and execution, order is rejected
MAX_DEVIATION = 20
