# Search4Strategies

Search4Strategies is a research-first trading discovery engine for MetaTrader 5 data.

It is designed to:
- collect historical OHLCV data from MT5;
- engineer candle, session, volatility and structure features;
- label candidate trades using triple-barrier logic;
- search for repeatable bullish and bearish conditions;
- validate findings with walk-forward testing;
- rank setups by expectancy, R-multiple performance and stability;
- export approved strategy rules for later MT5 execution.

## Quick start

```powershell
cd C:\Projects\Search4Strategies
.\scripts\setup_venv.ps1
.\.venv\Scripts\Activate.ps1
python -m app.cli doctor
python -m app.cli collect --symbol EURUSD --timeframe M30 --bars 5000
python -m app.cli discover --symbol EURUSD --timeframe M30
```

## Configure

Copy `.env.example` to `.env` and fill in private values.

No broker passwords, API keys, or webhooks are hardcoded.

