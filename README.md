# EquityLens — Indian Stock Analysis (NSE / BSE)

A minimal, dark, evidence-first web app that analyses Indian listed stocks using three transparent factor groups:
- **Supply & demand:** moving-average position, RSI, 5-day momentum, relative volume/price direction, and money-flow proxy.
- **Company performance:** earnings/revenue growth, profit margin, ROE, trailing/forward P/E (where Yahoo Finance supplies them).
- **Macro:** Nifty trend, India VIX, USD/INR, Brent crude, plus explicitly manual RBI/CPI/GDP inputs.

The interface intentionally contains **no charts or decorative/fake data visualisations**. It presents the factor score, indicator values, recommendation, model assumptions and data date.

## Run locally
Python 3.10+ recommended.
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

## Data and limitations (read this)
- Price/fundamental/macro data are fetched on demand from Yahoo Finance via `yfinance`; network access is required. Yahoo data can be delayed, incomplete, or rate-limited.
- NSE/BSE cash-market hours are represented as 09:15–15:30 Asia/Kolkata, weekdays, minus the configured holiday list. Exchange calendars can change; verify holidays.
- RBI repo rate, CPI inflation and GDP are **manual config inputs** (`config.py`) because no dependable free real-time endpoint is configured. Values in the file are examples/placeholders—update from official releases before relying on them.
- On weekends/holidays, the UI can show last-session analysis when explicitly enabled. It does not pretend this is a live quote.
- The “predicted close” is a **model scenario**, not an observed quote: weighted factor score × recent daily volatility. It is not trained or backtested and should not be treated as a reliable forecast or trading advice.
- Company name search and symbols depend on Yahoo Finance's search coverage. Use NSE ticker names (e.g. `RELIANCE`, `TCS`) or BSE symbols when possible.

## Tests (offline synthetic data)
```bash
python tests/test_logic.py
python tests/test_api.py
```
