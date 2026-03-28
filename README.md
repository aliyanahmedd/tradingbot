# tradingbot

A professional algorithmic trading bot for MetaTrader 5 (MT5), built in Python.

## What it does

- Connects to MetaTrader 5 via the official Python bridge
- Trades Forex (EURUSD, GBPUSD) and Commodities (XAUUSD Gold, USOIL)
- Uses a multi-confirmation strategy: EMA crossover + RSI momentum + ATR-based SL/TP
- Multi-timeframe analysis: H4 for trend direction, M15 for entry signals
- Full risk management: position sizing, max drawdown protection, max open positions
- Logs every trade to a SQLite database
- Sends real-time alerts to Telegram
- Includes a backtesting module to validate the strategy on historical data

## Strategy Summary

**BUY when:**
1. H4: EMA 20 > EMA 50 (uptrend on higher timeframe)
2. M15: EMA 9 crosses above EMA 21 (entry signal)
3. M15: RSI between 45–65 (bullish momentum, not overbought)

**SELL when:**
1. H4: EMA 20 < EMA 50 (downtrend on higher timeframe)
2. M15: EMA 9 crosses below EMA 21 (entry signal)
3. M15: RSI between 35–55 (bearish momentum, not oversold)

**Stop Loss / Take Profit:**
- SL = ATR(14) × 1.5
- TP = ATR(14) × 2.5
- Trailing stop to breakeven once 1× ATR in profit

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/aliyanahmedd/tradingbot.git
cd tradingbot
```

### 2. Create a virtual environment
```bash
python -m venv venv
venv\Scripts\activate   # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure your credentials
Copy `.env.example` to `.env` and fill in your real values:
```bash
copy .env.example .env
```

Edit `.env` with your MT5 login details and Telegram bot token.

### 5. Run the bot
```bash
python main.py
```

## Project Structure

```
tradingbot/
├── config/settings.py       # All bot parameters
├── core/connector.py        # MT5 connection
├── core/data_fetcher.py     # Fetch OHLCV candle data
├── core/indicators.py       # EMA, RSI, ATR calculations
├── core/signal_generator.py # Entry signal logic
├── core/risk_manager.py     # Lot sizing, drawdown checks
├── core/order_manager.py    # Open/close/modify orders
├── utils/logger.py          # Loguru logging setup
├── utils/notifier.py        # Telegram alerts
├── utils/trade_log.py       # SQLite trade database
├── backtest/backtest_runner.py  # Strategy backtesting
└── main.py                  # Bot entry point
```

## Risk Warning

This bot is for educational purposes. Trading forex and commodities involves significant risk of loss. Never trade with money you cannot afford to lose. Always test on a demo account first.

## Requirements

- Python 3.8+
- MetaTrader 5 installed on Windows
- A demo or live MT5 account
- A Telegram bot token (optional, for alerts)
