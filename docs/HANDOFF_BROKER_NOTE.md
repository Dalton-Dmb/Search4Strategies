# AlphaIQ™ Broker Specialisation Handoff

The owner intends AlphaIQ™ to discover evidence-supported instrument/engine specialisation and may later deploy different instruments through different brokers. The architecture already separates canonical symbols from broker aliases/routes.

Treat examples such as XAUUSD on one venue and USDJPY/EURCHF/NZDUSD on others as configuration possibilities, not predetermined winners. Before production routing, compare applicable availability, spread, slippage, latency/fill quality, operational reliability and empirical strategy results. Adding/changing a broker should require an adapter/capability/config change, not a rewrite of strategy logic.
