import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime
import numpy as np, pandas as pd
import market, scoring, predict


def fake_prices(n=250, drift=0.001, seed=1):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(end="2026-11-06", periods=n, tz="Asia/Kolkata")
    close = 1000 * np.cumprod(1 + rng.normal(drift, 0.012, n))
    return pd.DataFrame({"Open": close * 0.998, "High": close * 1.01, "Low": close * 0.99,
                         "Close": close, "Volume": rng.integers(1e6, 2e6, n)}, index=idx)


def test_market():
    ist = market.IST
    assert market.get_market_status(ist.localize(datetime(2026, 11, 8, 11, 0))).state == "WEEKEND"   # Sunday
    assert market.get_market_status(ist.localize(datetime(2026, 11, 7, 11, 0))).state == "WEEKEND"   # Saturday
    assert market.get_market_status(ist.localize(datetime(2026, 11, 10, 11, 0))).state == "HOLIDAY"
    assert market.get_market_status(ist.localize(datetime(2026, 11, 9, 8, 0))).state == "PRE_OPEN"
    assert market.get_market_status(ist.localize(datetime(2026, 11, 9, 11, 0))).state == "OPEN"
    assert market.get_market_status(ist.localize(datetime(2026, 11, 9, 16, 0))).state == "AFTER_CLOSE"


def test_pipeline():
    for drift in (0.004, -0.004):
        df = fake_prices(drift=drift)
        macro = {"Nifty 50": fake_prices(120, drift, 2), "India VIX": fake_prices(120, 0, 3) / 70,
                 "USD/INR": fake_prices(120, 0, 4) / 12, "Brent Crude": fake_prices(120, 0, 5) / 14}
        info = {"earningsGrowth": 0.2, "revenueGrowth": 0.1, "profitMargins": 0.15,
                "returnOnEquity": 0.18, "trailingPE": 22, "forwardPE": 19}
        f = {"demand": scoring.demand_score(df), "company": scoring.company_score(info), "macro": scoring.macro_score(macro)}
        st_ = market.get_market_status(market.IST.localize(datetime(2026, 11, 9, 11, 0)))
        p = predict.build_prediction(df, st_, f)
        print(f"drift {drift:+}: scores", {k: round(v.score, 2) for k, v in f.items()},
              "->", p.direction, p.recommendation, round(p.predicted_close, 2), p.confidence)
        assert all(-1 <= v.score <= 1 for v in f.values())


def test_new_listing_and_missing_data():
    df = fake_prices(8)                       # IPO with 8 days of history
    f = {"demand": scoring.demand_score(df), "company": scoring.company_score({}), "macro": scoring.macro_score({})}
    st_ = market.get_market_status(market.IST.localize(datetime(2026, 11, 8, 11, 0)))
    p = predict.build_prediction(df, st_, f)
    assert p.predicted_close > 0 and f["company"].note


if __name__ == "__main__":
    test_market(); test_pipeline(); test_new_listing_and_missing_data()
    print("ALL TESTS PASSED")
