# forex_bot/main_scheduler.py (The FINAL, Single-Strategy H1/M15 Version)
import configparser, json, time, pytz
from datetime import datetime
import MetaTrader5 as mt5

from services.mt5_data_service import MT5DataService as DataService
from services.indicator_service import IndicatorService
from services.ml_service import MLService
from services.heuristic_service import HeuristicService
from services.telegram_service import TelegramService
from services.trade_logger import TradeLogger
from services.trade_manager import TradeManagerService

def run_h1_bias_check(config, symbol: str, data_svc, telegram_svc, heuristic_svc):
    strategy_name = f"H1 Bias Hunter ({symbol})"
    print(f"\n[{datetime.now()}] --- Running {strategy_name} ---")
    
    # --- FIX: Use correct timeframe-specific filenames ---
    status_file = f"{symbol.lower()}_h1_status.json"
    model_file = f"models/{symbol.lower()}_h1.pkl"

    indicator_svc = IndicatorService()
    ml_svc = MLService(model_path=model_file)
    
    market_df_h1 = data_svc.get_market_data(symbol=symbol, timeframe_str='H1', limit=1000)
    if market_df_h1 is None or market_df_h1.empty: return

    analysis_df_h1 = indicator_svc.add_all_indicators(market_df_h1)
    if analysis_df_h1 is None or analysis_df_h1.empty: return

    prediction = ml_svc.get_prediction(analysis_df_h1)
    result = heuristic_svc.generate_h1_bias(prediction, analysis_df_h1)

    if result['status'] == 'success':
        bias_details = result['bias_details']
        print(f"{strategy_name}: Found a new {bias_details['bias']} bias. Updating state to WATCHING.")
        new_status = {"state": "WATCHING_FOR_ENTRY", "bias_details": bias_details}
        with open(status_file, 'w') as f: json.dump(new_status, f, indent=2)
        telegram_svc.send_bias_alert(bias_details, symbol)

def run_m15_entry_hunt(config, symbol: str, data_svc, telegram_svc, heuristic_svc):
    strategy_name = f"M15 Entry Scout ({symbol})"
    print(f"\n[{datetime.now()}] --- Running {strategy_name} ---")

    # --- FIX: Use correct timeframe-specific filenames ---
    status_file = f"{symbol.lower()}_h1_status.json"
    log_file = f"{symbol.lower()}_h1_log.csv"
    
    market_df_m15 = data_svc.get_market_data(symbol=symbol, timeframe_str='M15', limit=5)
    if market_df_m15 is None or market_df_m15.empty: return
    
    try:
        with open(status_file, 'r') as f: status = json.load(f)
    except FileNotFoundError: return
    
    if status.get('state') != "WATCHING_FOR_ENTRY": return

    bias_details = status['bias_details']
    
    if heuristic_svc.confirm_m15_entry(market_df_m15, bias_details['bias']):
        print(f"{strategy_name}: M15 entry CONFIRMED. Executing trade.")
        final_trade_details = bias_details.copy()
        final_trade_details['entry'] = market_df_m15.iloc[-1]['close']

        telegram_svc.send_execution_alert(final_trade_details, symbol)
        trade_logger = TradeLogger(log_file)
        trade_logger.log_new_signal(symbol, final_trade_details)
            
        new_status = {"state": "IN_TRADE", "trade_details": final_trade_details}
        with open(status_file, 'w') as f: json.dump(new_status, f, indent=2)

if __name__ == '__main__':
    if not mt5.initialize(): quit()
    print("SUCCESS: Connection to MT5 terminal established.")

    config = configparser.ConfigParser()
    config.read('config.ini')
    symbols_to_trade = [symbol.strip() for symbol in config['parameters']['symbols'].split(',')]
    
    data_svc = DataService()
    telegram_svc = TelegramService(bot_token=config['telegram']['bot_token'], channel_id=config['telegram']['channel_id'])
    heuristic_svc = HeuristicService()
    
    # --- FIX: Use correct timeframe-specific filenames ---
    trade_managers = [TradeManagerService(data_svc, telegram_svc, f"{s.lower()}_h1_log.csv", f"{s.lower()}_h1_status.json", s) for s in symbols_to_trade]
    
    print("\n--- MTF H1/M15 Forex Bot Started ---")
    last_h1_run_hour = -1
    last_m15_run_minute = -1

    try:
        while True:
            now_utc = datetime.now(pytz.utc)
            
            print(f"[{now_utc.strftime('%H:%M:%S')}] Running management cycle...")
            for manager in trade_managers:
                manager.check_open_trade()
            
            # H1 Bias Check (every hour)
            if now_utc.minute >= 1 and last_h1_run_hour != now_utc.hour:
                for symbol in symbols_to_trade:
                    status_file = f"{symbol.lower()}_h1_status.json"
                    try:
                        with open(status_file, 'r') as f: status = json.load(f)
                    except FileNotFoundError:
                        status = {"state": "HUNTING"}
                    
                    if status.get('state') == "HUNTING":
                        run_h1_bias_check(config, symbol, data_svc, telegram_svc, heuristic_svc)
                last_h1_run_hour = now_utc.hour

            # M15 Entry Hunt (every 15 mins)
            if now_utc.minute % 15 == 0 and last_m15_run_minute != now_utc.minute:
                for symbol in symbols_to_trade:
                    status_file = f"{symbol.lower()}_h1_status.json"
                    try:
                        with open(status_file, 'r') as f: status = json.load(f)
                        if status.get('state') == "WATCHING_FOR_ENTRY":
                            run_m15_entry_hunt(config, symbol, data_svc, telegram_svc, heuristic_svc)
                    except FileNotFoundError:
                        continue
                last_m15_run_minute = now_utc.minute

            time.sleep(60)

    except (KeyboardInterrupt, SystemExit):
        print("\nBot stopped.")
    finally:
        mt5.shutdown()
        print("Connection to MT5 terminal shut down.")