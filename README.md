# tradingbot

A professional algorithmic trading bot for MetaTrader 5 (MT5), built in Python.

## What it does

- Connects to MetaTrader 5 via the official Python bridge
- Trades Forex (EURUSD, GBPUSD), Metals (XAUUSD Gold, XAGUSD Silver, XPTUSD Platinum) and Commodities (WTI Oil)
- Uses a multi-confirmation strategy: EMA crossover + RSI momentum + ATR-based SL/TP
- Multi-timeframe analysis: H4 for trend direction, M15 for entry signals
- Full risk management: position sizing, max drawdown protection, max open positions
- Logs every trade to a SQLite database
- Includes a backtesting module to validate the strategy on historical data

## Strategy

**BUY when ALL of these are true:**
1. H4: EMA 20 > EMA 50 (uptrend confirmed)
2. M15: EMA 9 crosses above EMA 21 (entry signal)
3. M15: RSI between 45–65 (bullish momentum, not overbought)
4. No existing position on that symbol

**SELL when ALL of these are true:**
1. H4: EMA 20 < EMA 50 (downtrend confirmed)
2. M15: EMA 9 crosses below EMA 21 (entry signal)
3. M15: RSI between 35–55 (bearish momentum, not oversold)
4. No existing position on that symbol

**Stop Loss / Take Profit:**
- SL = entry price ± (ATR × 1.5)
- TP = entry price ± (ATR × 2.5)
- Trailing stop moves SL to breakeven once 1× ATR in profit

## Risk Management

- Max 1.5% of account balance risked per trade
- Max 3 open positions at once
- Bot stops trading if drawdown exceeds 5% from session start
- Minimum $100 account balance required
- Every order must have SL — no exceptions

## Symbols Traded

| Symbol | Description |
|--------|-------------|
| EURUSD | Euro / US Dollar |
| GBPUSD | British Pound / US Dollar |
| XAUUSD | Gold |
| XAGUSD | Silver |
| XPTUSD | Platinum |
| WTI    | Crude Oil |

## Setup Instructions

### 1. Requirements
- Windows PC (MT5 only runs on Windows)
- MetaTrader 5 installed
- Python 3.8+
- A demo or live MT5 account

### 2. Clone the repository
```bash
git clone https://github.com/aliyanahmedd/tradingbot.git
cd tradingbot
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure credentials
Create a `.env` file in the root folder:
```
MT5_LOGIN=your_account_number
MT5_PASSWORD=your_password
MT5_SERVER=your_broker_server
```

### 5. Enable Algo Trading in MT5
Open MT5 and click the **Algo Trading** button in the toolbar until it turns green.

### 6. Run the bot
```bash
python main.py
```

### 7. Run backtests
```bash
python -m backtest.backtest_runner
```

## Project Structure

```
tradingbot/
├── config/
│   └── settings.py          # All bot parameters — edit this to configure
├── core/
│   ├── connector.py         # MT5 connection
│   ├── data_fetcher.py      # Fetch OHLCV candle data
│   ├── indicators.py        # EMA, RSI, ATR calculations
│   ├── signal_generator.py  # Entry signal logic
│   ├── risk_manager.py      # Lot sizing, drawdown checks
│   └── order_manager.py     # Open/close/modify orders
├── utils/
│   ├── logger.py            # Loguru logging setup
│   ├── notifier.py          # Notification stub
│   └── trade_log.py         # SQLite trade database
├── backtest/
│   └── backtest_runner.py   # Strategy backtesting
├── .env                     # Your secrets (never committed)
├── requirements.txt         # Dependencies
└── main.py                  # Bot entry point
```

## How to Configure

All bot settings are in `config/settings.py`:

```python
SYMBOLS          = ["EURUSD", "GBPUSD", ...]  # Add/remove symbols
RISK_PERCENT     = 1.5    # % of balance to risk per trade
MAX_OPEN_POSITIONS = 3    # Max simultaneous trades
MAX_DRAWDOWN_PERCENT = 5.0  # Stop trading after this % loss
```

## Risk Warning

This bot is for educational purposes. Trading forex and commodities involves
significant risk of loss. Never trade with money you cannot afford to lose.
Always test thoroughly on a demo account before using real money.

## Tech Stack

- Python 3.13
- MetaTrader5 — official MT5 Python bridge
- pandas — candle data as DataFrames
- ta — technical analysis indicators
- schedule — bot loop timing
- sqlite3 — trade logging database
- backtesting.py — strategy backtesting
- python-dotenv — secure credential management
- loguru — structured logging
