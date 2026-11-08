import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_logic import fake_prices
import data, app as webapp

data.fetch_price_history = lambda q, e="NSE": ("RELIANCE.NS", fake_prices())
data.fetch_info = lambda s: {"longName": "Reliance Industries", "earningsGrowth": 0.1, "trailingPE": 24, "profitMargins": 0.09}
data.fetch_macro = lambda: {"Nifty 50": fake_prices(120), "India VIX": fake_prices(120) / 70}

c = webapp.app.test_client()
print("page:", c.get("/").status_code, "| css:", c.get("/static/style.css").status_code, "| js:", c.get("/static/script.js").status_code)
print("status:", c.get("/api/status").get_json()["message"])
r = c.get("/api/analyze?symbol=RELIANCE&exchange=NSE&force=1")
d = r.get_json()
print("analyze:", r.status_code, d["name"], d["prediction"]["direction"], d["prediction"]["recommendation"],
      round(d["prediction"]["predicted_close"], 2), "| chart pts:", len(d["chart"]["close"]))
json.dumps(d, allow_nan=False)    # must be strict-JSON safe
print("no-force on weekend ->", c.get("/api/analyze?symbol=TCS").get_json().get("closed"))
print("empty symbol ->", c.get("/api/analyze?symbol=").status_code)
print("API TEST PASSED")
