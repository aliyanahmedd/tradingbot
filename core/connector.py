"""
core/connector.py

Handles everything related to connecting and disconnecting from MetaTrader 5.
This is the first thing the bot runs at startup, and the last thing it runs on shutdown.
"""

import MetaTrader5 as mt5
from config.settings import MT5_LOGIN, MT5_PASSWORD, MT5_SERVER


def initialize():
    """
    Step 1: Start the MT5 application bridge.
    This launches the MT5 terminal process in the background and opens
    the communication channel between Python and MT5.
    Returns True if successful, False if MT5 is not installed or can't start.
    """
    if not mt5.initialize():
        print(f"[ERROR] MT5 initialize() failed. Error code: {mt5.last_error()}")
        return False

    print("[OK] MT5 initialized successfully.")
    return True


def login():
    """
    Step 2: Log into your MT5 account using credentials from .env.
    Must be called AFTER initialize() — the bridge must be open before logging in.
    Returns True if login succeeds, False if credentials are wrong or server unreachable.
    """
    authorized = mt5.login(
        login=MT5_LOGIN,
        password=MT5_PASSWORD,
        server=MT5_SERVER
    )

    if not authorized:
        print(f"[ERROR] MT5 login() failed. Error code: {mt5.last_error()}")
        mt5.shutdown()
        return False

    # Pull account info to confirm we're connected and show key details
    account = mt5.account_info()
    print(f"[OK] Logged in successfully.")
    print(f"     Account : {account.login}")
    print(f"     Name    : {account.name}")
    print(f"     Server  : {account.server}")
    print(f"     Balance : ${account.balance:,.2f}")
    print(f"     Currency: {account.currency}")
    print(f"     Leverage: 1:{account.leverage}")

    return True


def shutdown():
    """
    Cleanly closes the connection to MT5.
    Always call this when the bot stops — whether normally or after an error.
    Leaving the connection open can cause issues on the next run.
    """
    mt5.shutdown()
    print("[OK] MT5 connection closed.")


def connect():
    """
    Convenience function that runs initialize() and login() together.
    This is what the main bot loop will call at startup.
    Returns True only if BOTH steps succeed.
    """
    if not initialize():
        return False
    if not login():
        return False
    return True
