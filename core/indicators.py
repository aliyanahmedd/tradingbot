"""
core/indicators.py

Calculates technical indicators on a candle DataFrame.
Takes a raw OHLCV DataFrame (from data_fetcher.py) and adds new columns for
EMA, RSI, and ATR. Returns the same DataFrame with those columns added.
"""

import pandas as pd
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from config.settings import (
    EMA_TREND_FAST, EMA_TREND_SLOW,
    EMA_ENTRY_FAST, EMA_ENTRY_SLOW,
    RSI_PERIOD, ATR_PERIOD
)


def add_ema(df, period, column_name):
    """
    Adds an EMA (Exponential Moving Average) column to the DataFrame.

    Parameters:
        df          : the candle DataFrame
        period      : how many candles to average (e.g. 9, 21, 20, 50)
        column_name : what to name the new column (e.g. "ema_9")

    EMA gives more weight to recent candles than older ones.
    This makes it react faster to price changes than a simple average.
    """
    ema = EMAIndicator(close=df["close"], window=period)
    df[column_name] = ema.ema_indicator()
    return df


def add_rsi(df, period=RSI_PERIOD):
    """
    Adds RSI (Relative Strength Index) column to the DataFrame.

    RSI measures momentum — how fast and how much price is moving.
    It oscillates between 0 and 100:
      - Above 70 = overbought (price may be due for a pullback)
      - Below 30 = oversold (price may be due for a bounce)
      - 45-65 = healthy bullish momentum (our buy zone)
      - 35-55 = healthy bearish momentum (our sell zone)
    """
    rsi = RSIIndicator(close=df["close"], window=period)
    df["rsi"] = rsi.rsi()
    return df


def add_atr(df, period=ATR_PERIOD):
    """
    Adds ATR (Average True Range) column to the DataFrame.

    ATR measures volatility — how much price is moving on average per candle.
    High ATR = market is volatile (big moves). Low ATR = market is calm.
    We use ATR to set SL and TP dynamically so they adapt to current conditions.
    A fixed 20-pip SL on Gold makes no sense — ATR adjusts it automatically.
    """
    atr = AverageTrueRange(
        high=df["high"],
        low=df["low"],
        close=df["close"],
        window=period
    )
    df["atr"] = atr.average_true_range()
    return df


def apply_indicators(df, mode="entry"):
    """
    Applies all indicators to a DataFrame in one call.

    Parameters:
        df   : raw OHLCV DataFrame from get_candles()
        mode : "entry" for M15 timeframe (uses EMA 9 and 21)
               "trend" for H4 timeframe (uses EMA 20 and 50)

    Returns the DataFrame with all indicator columns added.
    """

    if mode == "trend":
        # H4 timeframe — we only need the trend EMAs to confirm direction
        df = add_ema(df, EMA_TREND_FAST, "ema_fast")  # EMA 20
        df = add_ema(df, EMA_TREND_SLOW, "ema_slow")  # EMA 50

    elif mode == "entry":
        # M15 timeframe — we need entry EMAs, RSI for momentum, ATR for SL/TP
        df = add_ema(df, EMA_ENTRY_FAST, "ema_fast")  # EMA 9
        df = add_ema(df, EMA_ENTRY_SLOW, "ema_slow")  # EMA 21
        df = add_rsi(df)
        df = add_atr(df)

    # Drop rows where indicators are NaN (the first N rows before enough data exists)
    df.dropna(inplace=True)

    return df
