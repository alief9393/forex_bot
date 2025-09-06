import MetaTrader5 as mt5

print("--- Attempting to connect to MetaTrader 5 ---")

# Establish connection to the MetaTrader 5 terminal
if not mt5.initialize():
    print("FATAL: initialize() failed, error code =", mt5.last_error())
    print("\nTroubleshooting:")
    print("1. Is the MetaTrader 5 terminal running?")
    print("2. In MT5, is 'Tools -> Options -> Expert Advisors -> Allow algorithmic trading' enabled?")
    quit()

print("\nSUCCESS: Connection to MetaTrader 5 terminal is established.")

# Display some data about the connection status
terminal_info = mt5.terminal_info()
if terminal_info:
    print(f"\n- Terminal Info -")
    print(f"  Connected to: {terminal_info.name}")
    print(f"  Broker: {terminal_info.company}")
    
account_info = mt5.account_info()
if account_info:
    print(f"\n- Account Info -")
    print(f"  Logged in to Account: {account_info.login}")
    print(f"  Account Holder: {account_info.name}")
    print(f"  Account Server: {account_info.server}")
    print(f"  Account Equity: {account_info.equity}")

# Shut down connection to the MetaTrader 5 terminal
mt5.shutdown()
print("\n--- Connection shut down. Test Complete. ---")