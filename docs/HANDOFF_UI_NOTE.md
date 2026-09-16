# AlphaIQ™ Human UI / Machine Logic Separation

TradingView/Pine indicators may display dashboards, labels, circles, necklines, boxes, POIs and other visual navigation aids. Those visuals are not the authoritative machine implementation unless the exact underlying rule is separately specified and certified.

Python/MQL5/backend components should consume deterministic features/states/coordinates and evidence, not screen drawings. Keep the user's compact human dashboard/visual preferences separate from automated decision contracts so visualization can evolve without altering historical strategy semantics.
