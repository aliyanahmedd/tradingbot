"""
backtest/backtest_runner.py

Tests our trading strategy on historical data using the backtesting.py library.

How backtesting works:
  - We feed it 1 year of OHLCV candle data
  - It simulates running our strategy on every candle, in order
  - When our conditions are met, it "opens" a virtual trade
  - When SL or TP is hit, it "closes" the trade and records profit/loss
  - At the end it gives us full performance statistics

This tells us how the strategy WOULD have performed historically.
Past performance doesn't guarantee future results, but it's the best
validation tool we have before risking real money.
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

from core.connector import connect, shutdown
from config.settings import (
    EMA_TREND_FAST, EMA_TREND_SLOW,
    EMA_ENTRY_FAST, EMA_ENTRY_SLOW,
    RSI_PERIOD, ATR_PERIOD,
    RSI_BUY_MIN, RSI_BUY_MAX,
    RSI_SELL_MIN, RSI_SELL_MAX,
    ATR_SL_MULTIPLIER, ATR_TP_MULTIPLIER
)


def fetch_historical_data(symbol, timeframe, bars=5000):
    """
    Fetches a large amount of historical candle data from MT5.

    Parameters:
        symbol    (str): e.g. "EURUSD"
        timeframe     : MT5 timeframe constant e.g. mt5.TIMEFRAME_M15
        bars      (int): number of candles to fetch

    Returns:
        pandas DataFrame formatted for backtesting.py
        backtesting.py requires columns: Open, High, Low, Close, Volume (capitalized)
    """
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)

    if rates is None or len(rates) == 0:
        print(f"[ERROR] No historical data for {symbol}")
        return None

    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df.set_index("time", inplace=True)

    # backtesting.py requires capitalized column names
    df = df.rename(columns={
        "open":        "Open",
        "high":        "High",
        "low":         "Low",
        "close":       "Close",
        "tick_volume": "Volume"
    })

    df = df[["Open", "High", "Low", "Close", "Volume"]]
    return df


class EMARSIStrategy(Strategy):
    """
    Our trading strategy implemented as a backtesting.py Strategy class.

    backtesting.py calls init() once at the start, then calls next() on
    every single candle in order from oldest to newest. We check our
    conditions in next() and call self.buy() or self.sell() to open trades.
    """

    # These can be optimized later — backtesting.py can sweep these values
    ema_fast  = EMA_ENTRY_FAST   # 9
    ema_slow  = EMA_ENTRY_SLOW   # 21
    rsi_period = RSI_PERIOD      # 14
    atr_period = ATR_PERIOD      # 14

    def init(self):
        """
        Called once before the backtest starts.
        Pre-calculates all indicators on the full dataset.
        self.I() wraps an indicator so backtesting.py can track it on the chart.
        """
        close = pd.Series(self.data.Close, index=self.data.index)
        high  = pd.Series(self.data.High,  index=self.data.index)
        low   = pd.Series(self.data.Low,   index=self.data.index)

        # Entry EMAs (M15)
        self.ema9  = self.I(
            lambda c: EMAIndicator(pd.Series(c), window=self.ema_fast).ema_indicator().values,
            close
        )
        self.ema21 = self.I(
            lambda c: EMAIndicator(pd.Series(c), window=self.ema_slow).ema_indicator().values,
            close
        )

        # RSI
        self.rsi = self.I(
            lambda c: RSIIndicator(pd.Series(c), window=self.rsi_period).rsi().values,
            close
        )

        # ATR
        self.atr = self.I(
            lambda h, l, c: AverageTrueRange(
                pd.Series(h), pd.Series(l), pd.Series(c), window=self.atr_period
            ).average_true_range().values,
            high, low, close
        )

        # H4 Trend filter — resample M15 data to H4 and calculate EMAs
        # This replicates the live bot's H4 trend confirmation
        df_h4 = close.resample("4h").last().dropna()
        h4_ema20 = EMAIndicator(df_h4, window=EMA_TREND_FAST).ema_indicator()
        h4_ema50 = EMAIndicator(df_h4, window=EMA_TREND_SLOW).ema_indicator()

        # Reindex back to M15 — forward fill so every M15 candle knows the H4 trend
        self.h4_ema20 = self.I(
            lambda: h4_ema20.reindex(close.index, method="ffill").values
        )
        self.h4_ema50 = self.I(
            lambda: h4_ema50.reindex(close.index, method="ffill").values
        )

    def next(self):
        """
        Called on every candle. This is where we apply our trading rules.
        self.data.Close[-1] = current candle close price
        self.data.Close[-2] = previous candle close price
        """

        # Skip if indicators don't have enough data yet (first N candles)
        if (np.isnan(self.ema9[-1]) or np.isnan(self.ema21[-1]) or
                np.isnan(self.rsi[-1]) or np.isnan(self.atr[-1])):
            return

        # Only one trade at a time
        if self.position:
            return

        current_rsi  = self.rsi[-1]
        current_atr  = self.atr[-1]
        h4_bullish   = self.h4_ema20[-1] > self.h4_ema50[-1]
        h4_bearish   = self.h4_ema20[-1] < self.h4_ema50[-1]

        # Detect EMA crossover on M15
        bull_cross = crossover(self.ema9, self.ema21)
        bear_cross = crossover(self.ema21, self.ema9)

        # BUY — H4 uptrend + M15 crossover + RSI in buy zone
        if h4_bullish and bull_cross and RSI_BUY_MIN <= current_rsi <= RSI_BUY_MAX:
            sl = self.data.Close[-1] - (current_atr * ATR_SL_MULTIPLIER)
            tp = self.data.Close[-1] + (current_atr * ATR_TP_MULTIPLIER)
            self.buy(sl=sl, tp=tp)

        # SELL — H4 downtrend + M15 crossover + RSI in sell zone
        elif h4_bearish and bear_cross and RSI_SELL_MIN <= current_rsi <= RSI_SELL_MAX:
            sl = self.data.Close[-1] + (current_atr * ATR_SL_MULTIPLIER)
            tp = self.data.Close[-1] - (current_atr * ATR_TP_MULTIPLIER)
            self.sell(sl=sl, tp=tp)


def run_backtest(symbol, bars=5000, cash=10000, commission=0.0002):
    """
    Runs the full backtest for one symbol and prints the results.

    Parameters:
        symbol     (str)  : e.g. "EURUSD"
        bars       (int)  : number of M15 candles (~5000 = ~2 months)
        cash       (float): starting virtual balance
        commission (float): cost per trade as a fraction (0.0002 = 0.02%)
    """
    print(f"\n{'='*60}")
    print(f"  Backtesting {symbol} — {bars} M15 candles")
    print(f"{'='*60}")

    # Fetch historical data
    df = fetch_historical_data(symbol, mt5.TIMEFRAME_M15, bars=bars)
    if df is None:
        print(f"[FAILED] Could not fetch data for {symbol}")
        return None

    print(f"Data loaded: {len(df)} candles")
    print(f"From: {df.index[0]}  To: {df.index[-1]}")

    # Run the backtest
    bt = Backtest(
        df,
        EMARSIStrategy,
        cash=cash,
        commission=commission,
        exclusive_orders=True   # Close existing trade before opening new one
    )

    stats = bt.run()

    # Print the key results
    print(f"\n--- RESULTS ---")
    print(f"  Start Balance   : ${cash:,.2f}")
    print(f"  End Balance     : ${stats['Equity Final [$]']:,.2f}")
    print(f"  Total Return    : {stats['Return [%]']:.2f}%")
    print(f"  Total Trades    : {stats['# Trades']}")
    print(f"  Win Rate        : {stats['Win Rate [%]']:.2f}%")
    print(f"  Max Drawdown    : {stats['Max. Drawdown [%]']:.2f}%")
    print(f"  Sharpe Ratio    : {stats['Sharpe Ratio']:.2f}")
    print(f"  Avg Trade       : {stats['Avg. Trade [%]']:.4f}%")
    print(f"  Best Trade      : {stats['Best Trade [%]']:.2f}%")
    print(f"  Worst Trade     : {stats['Worst Trade [%]']:.2f}%")
    print(f"  Avg Trade Duration: {stats['Avg. Trade Duration']}")

    # Show the equity curve chart
    try:
        print(f"\nOpening equity curve chart...")
        bt.plot(open_browser=True)
    except Exception as e:
        print(f"[Chart skipped — bokeh compatibility issue: {e}]")

    return stats


if __name__ == "__main__":
    print("Starting backtester...")

    if not connect():
        print("[FAILED] Could not connect to MT5.")
        exit()

    # Run backtest on EURUSD and XAUUSD
    run_backtest("EURUSD", bars=5000, cash=10000)
    run_backtest("XAUUSD", bars=5000, cash=10000)

    shutdown()
