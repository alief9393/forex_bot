import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import pytz

class MT5DataService:
    def __init__(self):
        pass 

    def get_all_historical_data(self, symbol: str, timeframe_str: str, start_date: str) -> pd.DataFrame | None:
        """
        Fetches a large, historical dataset for model training.
        """
        print(f"MT5DataService (Hist): Fetching all data for {symbol} on {timeframe_str} since {start_date}...")
        
        timeframe_map = { 'H4': mt5.TIMEFRAME_H4, 'H1': mt5.TIMEFRAME_H1 }
        if timeframe_str not in timeframe_map: return None
        timeframe = timeframe_map[timeframe_str]

        timezone = pytz.timezone("Etc/UTC")
        start_datetime = timezone.localize(datetime.strptime(start_date, "%Y-%m-%d"))
        
        try:
            now = datetime.now(timezone)
            rates = mt5.copy_rates_range(symbol, timeframe, start_datetime, now)
            if rates is None or len(rates) == 0:
                print("MT5DataService (Hist): No data returned from MT5 terminal.")
                return None

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            df.index = df.index.tz_localize('UTC')
            df = df[df.index >= start_datetime]
            df.rename(columns={'tick_volume': 'volume'}, inplace=True)
            df = df[['open', 'high', 'low', 'close', 'volume']]
            
            print(f"MT5DataService (Hist): Successfully downloaded and processed {len(df)} candles.")
            print(f"MT5DataService (Hist): Data range from {df.index.min()} to {df.index.max()}")
            return df
        except Exception as e:
            print(f"MT5DataService (Hist): An error occurred: {e}")
            return None

    def get_market_data(self, symbol: str, timeframe_str: str, limit: int = 1000, is_startup_run: bool = False) -> pd.DataFrame | None:
        """
        Fetches a recent chunk of market data for LIVE analysis.
        """
        timeframe_map = { 'H4': mt5.TIMEFRAME_H4, 'H1': mt5.TIMEFRAME_H1, 'M1': mt5.TIMEFRAME_M1 }
        if timeframe_str not in timeframe_map: return None
        timeframe = timeframe_map[timeframe_str]

        print(f"MT5DataService (Live): Fetching {limit} recent '{timeframe_str}' klines for {symbol}...")
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, limit)
            if rates is None or len(rates) == 0:
                print("MT5DataService (Live): No data returned from MT5 terminal.")
                return None

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            df.index = df.index.tz_localize('UTC')
            df.rename(columns={'tick_volume': 'volume'}, inplace=True)
            df = df[['open', 'high', 'low', 'close', 'volume']]
            
            print(f"MT5DataService (Live): Successfully fetched {len(df)} candles.")
            print(f"MT5DataService (Live): Most recent candle timestamp is {df.index[-1]}")
            
            if not is_startup_run:
                df = df.iloc[:-1]
                print("MT5DataService (Live): Scheduled run. Removed final (incomplete) candle.")

            return df
        except Exception as e:
            print(f"MT5DataService (Live): An error occurred: {e}")
            return None