from typing import List, Dict, Optional, Tuple
from services.logger import get_logger
from services.metaapi_client import MetaApiClient
from config import METAAPI_TOKEN
import math

logger = get_logger("engine")

# --- Strategy Rules per Planner ---
# - HTF Structural Analysis (4H, 1D, 1W, 1M)
# - Pattern recognition (breakout only)
# - Looking Left for structure alignment
# - Multi-timeframe refinement (HTF -> 1D/4H -> M15)
# - Final trigger: M15 Pin Bar

class TradingEngine:
    def __init__(self):
        self.meta = MetaApiClient(METAAPI_TOKEN)

    @staticmethod
    def _is_pin_bar(candle) -> Optional[str]:
        """Detect M15 pin bar: return 'buy' (inverted pin) / 'sell' (standard) or None."""
        o, h, l, c = candle['open'], candle['high'], candle['low'], candle['close']
        body = abs(c - o)
        rng = h - l if (h - l) != 0 else 1e-9
        upper_wick = h - max(c, o)
        lower_wick = min(c, o) - l
        # Pin bar heuristic: small body, long wick (> 2x body)
        if body / rng < 0.3:
            if lower_wick > 2 * body and (max(c, o) - l) / rng > 0.6:
                return "buy"   # inverted pin, long lower wick
            if upper_wick > 2 * body and (h - min(c, o)) / rng > 0.6:
                return "sell"  # standard pin, long upper wick
        return None

    @staticmethod
    def _pips(symbol: str, price_diff: float) -> float:
        # Approx pip calculation for FX and metals (simplified)
        if "JPY" in symbol.replace("/", ""):
            return round(price_diff * 100, 1)
        if "XAU" in symbol:
            return round(price_diff * 10, 1)
        if "BTC" in symbol:
            return round(price_diff, 1)
        return round(price_diff * 10000, 1)

    async def analyze_and_signal(self, connection, symbol: str) -> Optional[Dict]:
        """
        Returns a signal dict or None if no setup. High-level approximation
        (robustly wrapped, no silent failures).
        """
        try:
            # 1) HTF context: look for structure using 4H and 1D swings (simple pivot-based)
            h4 = await self.meta.get_candles(connection, symbol, '4h', 300)
            d1 = await self.meta.get_candles(connection, symbol, '1d', 200)
            if not h4 or not d1:
                logger.info("Insufficient HTF candles for %s", symbol); return None

            # Simple trend context: compare last closes
            trend_up = d1[-1]['close'] > d1[-50]['close'] if len(d1) > 50 else False
            trend_down = d1[-1]['close'] < d1[-50]['close'] if len(d1) > 50 else False

            # 2) Pattern / breakout heuristic: recent range and breakout
            recent = h4[-40:]
            hh = max(c['high'] for c in recent)
            ll = min(c['low'] for c in recent)
            last = recent[-1]
            breakout_up = last['close'] > hh * 0.999
            breakout_dn = last['close'] < ll * 1.001

            # 3) Looking left: align with past swing zones (using d1 highs/lows)
            levels = sorted(list({round(c['high'], 3) for c in d1[-150:]} | {round(c['low'], 3) for c in d1[-150:]}))
            price = last['close']
            nearby_level = min(levels, key=lambda x: abs(x - price)) if levels else None
            aligned = abs(price - (nearby_level or price)) / price < 0.004 if nearby_level else False

            # 4) M15 trigger pin bar
            m15 = await self.meta.get_candles(connection, symbol, '15m', 200)
            if not m15: return None
            trigger = None
            for c in reversed(m15[-10:]):  # check last 10 candles
                tag = self._is_pin_bar(c)
                if tag:
                    trigger = tag
                    break
            if not trigger:
                return None

            # Gate by trend/breakout/alignment
            if trigger == "buy" and not (trend_up or breakout_up) and not aligned:
                return None
            if trigger == "sell" and not (trend_down or breakout_dn) and not aligned:
                return None

            entry = m15[-1]['close']
            # Risk model (SL 30-50 pips) approximate
            sl_pips = 40
            if trigger == "buy":
                sl = entry - (sl_pips / 10000 if "JPY" not in symbol else sl_pips / 100)
            else:
                sl = entry + (sl_pips / 10000 if "JPY" not in symbol else sl_pips / 100)

            # TPs (3, within max pips constraints)
            tp1_pips = 30
            tp2_pips = 60
            tp3_pips = 90
            if trigger == "buy":
                tp1 = entry + (tp1_pips / 10000 if "JPY" not in symbol else tp1_pips / 100)
                tp2 = entry + (tp2_pips / 10000 if "JPY" not in symbol else tp2_pips / 100)
                tp3 = entry + (tp3_pips / 10000 if "JPY" not in symbol else tp3_pips / 100)
            else:
                tp1 = entry - (tp1_pips / 10000 if "JPY" not in symbol else tp1_pips / 100)
                tp2 = entry - (tp2_pips / 10000 if "JPY" not in symbol else tp2_pips / 100)
                tp3 = entry - (tp3_pips / 10000 if "JPY" not in symbol else tp3_pips / 100)

            return {
                "symbol": symbol,
                "direction": "BUY" if trigger == "buy" else "SELL",
                "entry": round(entry, 5),
                "tp1": round(tp1, 5), "tp2": round(tp2, 5), "tp3": round(tp3, 5),
                "sl": round(sl, 5),
                "tp1_pips": tp1_pips, "tp2_pips": tp2_pips, "tp3_pips": tp3_pips,
                "sl_pips": sl_pips
            }
        except Exception as e:
            logger.exception("Engine analyze error for %s: %s", symbol, e)
            return None
