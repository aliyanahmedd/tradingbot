"""
core/signal_generator.py

Applies the full multi-timeframe, multi-confirmation entry logic.
Returns "BUY", "SELL", or None for each symbol checked.

Strategy rules:
  BUY  : H4 EMA20 > EMA50  AND  M15 EMA9 crosses above EMA21  AND  RSI 45-65
  SELL : H4 EMA20 < EMA50  AND  M15 EMA9 crosses below EMA21  AND  RSI 35-55
"""

from core.data_fetcher import get_candles
from core.indicators import apply_indicators
from config.settings import (
    TIMEFRAME_TREND, TIMEFRAME_ENTRY,
    RSI_BUY_MIN, RSI_BUY_MAX,
    RSI_SELL_MIN, RSI_SELL_MAX
)


def _check_crossover(df):
    """
    Detects whether a crossover happened on the most recent completed candle.

    A crossover is NOT just "EMA9 is above EMA21 right now".
    That would be true for hundreds of candles in a trend — we'd get signals constantly.

    A crossover means:
      - On the PREVIOUS candle: EMA9 was BELOW EMA21
      - On the CURRENT candle:  EMA9 is ABOVE EMA21
    That transition — from below to above — is the cross event.

    We use iloc[-1] for the current (last) candle
    and  iloc[-2] for the previous candle.

    Returns:
        "BUY"  if EMA9 just crossed above EMA21
        "SELL" if EMA9 just crossed below EMA21
        None   if no crossover happened
    """
    # Current candle values
    ema_fast_now  = df["ema_fast"].iloc[-1]
    ema_slow_now  = df["ema_slow"].iloc[-1]

    # Previous candle values
    ema_fast_prev = df["ema_fast"].iloc[-2]
    ema_slow_prev = df["ema_slow"].iloc[-2]

    # Bullish crossover: was below, now above
    if ema_fast_prev < ema_slow_prev and ema_fast_now > ema_slow_now:
        return "BUY"

    # Bearish crossover: was above, now below
    if ema_fast_prev > ema_slow_prev and ema_fast_now < ema_slow_now:
        return "SELL"

    return None


def get_signal(symbol):
    """
    Runs the full strategy check for one symbol.

    Steps:
      1. Fetch H4 data and check trend direction (EMA 20 vs EMA 50)
      2. Fetch M15 data and check for EMA crossover
      3. Check RSI is in the correct zone
      4. If all 3 conditions align → return "BUY" or "SELL"
      5. If any condition fails → return None (no trade)

    Parameters:
        symbol (str): e.g. "EURUSD", "XAUUSD"

    Returns:
        "BUY", "SELL", or None
    """

    print(f"\n--- Checking signal for {symbol} ---")

    # -------------------------------------------------------------------------
    # STEP 1: Fetch H4 data and determine trend direction
    # -------------------------------------------------------------------------
    df_h4 = get_candles(symbol, TIMEFRAME_TREND, count=100)
    if df_h4 is None:
        print(f"  [SKIP] Could not fetch H4 data for {symbol}")
        return None

    df_h4 = apply_indicators(df_h4, mode="trend")

    h4_ema_fast = df_h4["ema_fast"].iloc[-1]  # EMA 20
    h4_ema_slow = df_h4["ema_slow"].iloc[-1]  # EMA 50

    h4_bullish = h4_ema_fast > h4_ema_slow    # True = uptrend
    h4_bearish = h4_ema_fast < h4_ema_slow    # True = downtrend

    print(f"  H4 EMA20: {h4_ema_fast:.5f}  |  EMA50: {h4_ema_slow:.5f}")
    print(f"  H4 Trend : {'UPTREND (bullish)' if h4_bullish else 'DOWNTREND (bearish)'}")

    # -------------------------------------------------------------------------
    # STEP 2: Fetch M15 data and check for EMA crossover
    # -------------------------------------------------------------------------
    df_m15 = get_candles(symbol, TIMEFRAME_ENTRY, count=100)
    if df_m15 is None:
        print(f"  [SKIP] Could not fetch M15 data for {symbol}")
        return None

    df_m15 = apply_indicators(df_m15, mode="entry")

    crossover = _check_crossover(df_m15)

    m15_ema_fast = df_m15["ema_fast"].iloc[-1]  # EMA 9
    m15_ema_slow = df_m15["ema_slow"].iloc[-1]  # EMA 21
    rsi          = df_m15["rsi"].iloc[-1]
    atr          = df_m15["atr"].iloc[-1]

    print(f"  M15 EMA9 : {m15_ema_fast:.5f}  |  EMA21: {m15_ema_slow:.5f}")
    print(f"  M15 RSI  : {rsi:.2f}")
    print(f"  M15 ATR  : {atr:.5f}")
    print(f"  Crossover: {crossover if crossover else 'None — no cross on this candle'}")

    # -------------------------------------------------------------------------
    # STEP 3: BUY conditions — all three must be true
    # -------------------------------------------------------------------------
    if h4_bullish and crossover == "BUY" and RSI_BUY_MIN <= rsi <= RSI_BUY_MAX:
        print(f"  [SIGNAL] BUY signal confirmed on {symbol}")
        return "BUY"

    # -------------------------------------------------------------------------
    # STEP 4: SELL conditions — all three must be true
    # -------------------------------------------------------------------------
    if h4_bearish and crossover == "SELL" and RSI_SELL_MIN <= rsi <= RSI_SELL_MAX:
        print(f"  [SIGNAL] SELL signal confirmed on {symbol}")
        return "SELL"

    # -------------------------------------------------------------------------
    # STEP 5: No signal — explain which condition(s) failed
    # -------------------------------------------------------------------------
    print(f"  [NO SIGNAL] Conditions not met:")

    if not h4_bullish and not h4_bearish:
        print(f"    - H4 EMAs are equal (rare edge case)")
    if crossover is None:
        print(f"    - No EMA crossover on the latest M15 candle")
    if crossover == "BUY" and not h4_bullish:
        print(f"    - BUY crossover found but H4 trend is bearish (no confirmation)")
    if crossover == "SELL" and not h4_bearish:
        print(f"    - SELL crossover found but H4 trend is bullish (no confirmation)")
    if crossover == "BUY" and not (RSI_BUY_MIN <= rsi <= RSI_BUY_MAX):
        print(f"    - RSI {rsi:.2f} outside BUY zone ({RSI_BUY_MIN}-{RSI_BUY_MAX})")
    if crossover == "SELL" and not (RSI_SELL_MIN <= rsi <= RSI_SELL_MAX):
        print(f"    - RSI {rsi:.2f} outside SELL zone ({RSI_SELL_MIN}-{RSI_SELL_MAX})")

    return None
