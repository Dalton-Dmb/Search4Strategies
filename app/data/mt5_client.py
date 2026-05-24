from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
import pandas as pd

log = logging.getLogger(__name__)

_TIMEFRAMES = {
    "M1": "TIMEFRAME_M1",
    "M5": "TIMEFRAME_M5",
    "M15": "TIMEFRAME_M15",
    "M30": "TIMEFRAME_M30",
    "H1": "TIMEFRAME_H1",
    "H4": "TIMEFRAME_H4",
    "D1": "TIMEFRAME_D1",
}

@dataclass
class MT5Client:
    path: str | None = None
    login: str | None = None
    password: str | None = None
    server: str | None = None

    def _mt5(self):
        try:
            import MetaTrader5 as mt5
            return mt5
        except ImportError as exc:
            raise RuntimeError("MetaTrader5 package is not installed. Run pip install -r requirements.txt") from exc

    def connect(self) -> None:
        mt5 = self._mt5()
        kwargs = {}
        if self.path:
            kwargs["path"] = self.path
        if self.login and self.password and self.server:
            kwargs.update(login=int(self.login), password=self.password, server=self.server)
        if not mt5.initialize(**kwargs):
            raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
        log.info("Connected to MetaTrader 5")

    def shutdown(self) -> None:
        self._mt5().shutdown()

    def fetch_rates(self, symbol: str, timeframe: str, bars: int) -> pd.DataFrame:
        mt5 = self._mt5()
        tf_name = _TIMEFRAMES.get(timeframe.upper())
        if not tf_name:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        tf = getattr(mt5, tf_name)
        if not mt5.symbol_select(symbol, True):
            raise RuntimeError(f"Could not select symbol {symbol}")
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, bars)
        if rates is None or len(rates) == 0:
            raise RuntimeError(f"No rates returned for {symbol} {timeframe}: {mt5.last_error()}")
        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
        df["symbol"] = symbol
        df["timeframe"] = timeframe.upper()
        return df[["time","symbol","timeframe","open","high","low","close","tick_volume","spread","real_volume"]]

