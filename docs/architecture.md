# Architecture

Search4Strategies uses a research-to-execution pipeline:

1. MT5 candle ingestion
2. Feature engineering
3. Triple-barrier labelling
4. Rule mining and ML classification
5. Validation and reporting
6. Strategy JSON export
7. Later MT5 execution integration

This project deliberately treats SMC concepts as features to be tested, not as assumptions to be blindly trusted.

