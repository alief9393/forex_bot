# forex_bot/services/heuristic_service.py (The FINAL H1/M15 Version)
import pandas as pd

class HeuristicService:
    def __init__(self):
        print("HeuristicService: Initialized with H1/M15 MTF Logic.")

    def generate_h1_bias(self, prediction: int, df: pd.DataFrame) -> dict:
        if df is None or df.empty or prediction == 0:
            return {"status": "hold"}
    
        latest_candle = df.iloc[-1]
        
        if prediction == 1 and latest_candle['close'] < latest_candle['EMA_50']:
            return {"status": "veto"}
        if prediction == -1 and latest_candle['close'] > latest_candle['EMA_50']:
            return {"status": "veto"}

        atr_value = latest_candle['ATRr_14']
        pullback_level = latest_candle['EMA_21']
        
        if prediction == 1:
            decision = "BUY"
            stop_loss = pullback_level - (1.5 * atr_value)
            take_profit_1 = pullback_level + (2 * atr_value)
            take_profit_2 = pullback_level + (4 * atr_value)
            take_profit_3 = pullback_level + (6 * atr_value)
        else: # SELL
            decision = "SELL"
            stop_loss = pullback_level + (1.5 * atr_value)
            take_profit_1 = pullback_level - (2 * atr_value)
            take_profit_2 = pullback_level - (4 * atr_value)
            take_profit_3 = pullback_level - (6 * atr_value)

        bias_details = {
            "bias": decision,
            "pullback_level": round(pullback_level, 5),
            "sl": round(stop_loss, 5),
            "tp1": round(take_profit_1, 5),
            "tp2": round(take_profit_2, 5),
            "tp3": round(take_profit_3, 5),
        }
        return {"status": "success", "bias_details": bias_details}

    def confirm_m15_entry(self, df: pd.DataFrame, bias: str) -> bool:
        if df is None or len(df) < 2: return False
        last_candle = df.iloc[-1]
        
        if bias == "BUY":
            is_bullish_engulfing = (last_candle['close'] > last_candle['open'] and last_candle['open'] < df.iloc[-2]['close'] and last_candle['close'] > df.iloc[-2]['open'])
            if is_bullish_engulfing: return True
        elif bias == "SELL":
            is_bearish_engulfing = (last_candle['close'] < last_candle['open'] and last_candle['open'] > df.iloc[-2]['close'] and last_candle['close'] < df.iloc[-2]['open'])
            if is_bearish_engulfing: return True
        return False