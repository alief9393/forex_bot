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

def run_bias_check(config, symbol: str, timeframe: str, data_svc, telegram_svc, heuristic_svc):
    """ The generic "General" function, now called by the dynamic scheduler. """
    status_file = f"{symbol.lower()}_{timeframe.lower()}_status.json"
    model_file = f"models/{symbol.lower()}_{timeframe.lower()}.pkl"

def run_entry_hunt(config, symbol: str, primary_tf: str, entry_tf: str, data_svc, telegram_svc, heuristic_svc):
    """ The generic "Scout" function, now called by the dynamic scheduler. """
    status_file = f"{symbol.lower()}_{primary_tf.lower()}_status.json"
    log_file = f"{symbol.lower()}_{primary_tf.lower()}_log.csv"

if __name__ == '__main__':
    if not mt5.initialize(): quit()
    print("SUCCESS: Connection to MT5 terminal established.")

    config = configparser.ConfigParser()
    config.read('config.ini')

    strategies = {}
    for section in config.sections():
        if section.startswith("strategy_"):
            details = dict(config.items(section))
            strategies[details['symbol']] = details
    
    data_svc = DataService()
    telegram_svc = TelegramService(bot_token=config['telegram']['bot_token'], channel_id=config['telegram']['channel_id'])
    heuristic_svc = HeuristicService()
    
    trade_managers = [
        TradeManagerService(data_svc, telegram_svc, f"{s.lower()}_{v['bias_tf'].lower()}_log.csv", f"{s.lower()}_{v['bias_tf'].lower()}_status.json", s)
        for s, v in strategies.items()
    ]
    
    print(f"\n--- Multi-Strategy MTF Forex Bot Started for: {list(strategies.keys())} ---")
    last_run_times = { "H4": -1, "H1": -1, "M15": -1 }

    try:
        while True:
            now_utc = datetime.now(pytz.utc)
            
            print(f"[{now_utc.strftime('%H:%M:%S')}] Running management cycle...")
            for manager in trade_managers:
                manager.check_open_trade()
            
            for timeframe in ["H4", "H1", "M15"]:
                run_now = False
                if timeframe == "H4" and now_utc.hour % 4 == 0 and now_utc.minute >= 1 and last_run_times["H4"] != now_utc.hour:
                    run_now = True; last_run_times["H4"] = now_utc.hour
                elif timeframe == "H1" and now_utc.minute >= 1 and last_run_times["H1"] != now_utc.hour:
                    run_now = True; last_run_times["H1"] = now_utc.hour
                elif timeframe == "M15" and now_utc.minute % 15 == 0 and last_run_times["M15"] != now_utc.minute:
                    run_now = True; last_run_times["M15"] = now_utc.minute
                
                if run_now:
                    for symbol, strategy_details in strategies.items():
                        status_file = f"{symbol.lower()}_{strategy_details['bias_tf'].lower()}_status.json"
                        with open(status_file, 'r') as f: status = json.load(f)
                        
                        if strategy_details["bias_tf"] == timeframe and status.get('state') == "HUNTING":
                            pass
                        
                        if strategy_details["entry_tf"] == timeframe and status.get('state') == "WATCHING_FOR_ENTRY":
                            pass

            time.sleep(60)

    except (KeyboardInterrupt, SystemExit):
        print("\nBot stopped.")
    finally:
        mt5.shutdown()
        print("Connection to MT5 terminal shut down.")