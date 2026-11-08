"""Backend (Flask) - serves the HTML/CSS/JS page and a small JSON API.
Run:  python app.py   then open  http://127.0.0.1:5000
(A backend is needed because browsers block direct calls to Yahoo Finance - CORS.)"""
import math
import time

import numpy as np
from flask import Flask, jsonify, request, send_from_directory

import config, data, market, scoring, predict

app = Flask(__name__, static_folder="static", static_url_path="/static")
_cache = {}


def cached(key, ttl, fn):
    """Tiny in-memory cache (no database). Failures are never cached."""
    now = time.time()
    if key in _cache and now - _cache[key][0] < ttl:
        return _cache[key][1]
    val = fn()
    _cache[key] = (now, val)
    return val


def clean(o):
    """Make everything JSON-safe (NaN -> null, numpy -> python)."""
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (float, np.floating)):
        return float(o) if math.isfinite(o) else None
    if isinstance(o, np.integer):
        return int(o)
    return o


def status_dict(s):
    return {"state": s.state, "message": s.message, "closed_all_day": s.closed_all_day,
            "clock": s.now.strftime("%A, %d %b %Y, %I:%M %p IST")}


@app.route("/")
def home():
    return send_from_directory("static", "index.html")


@app.route("/api/status")
def api_status():
    return jsonify(status_dict(market.get_market_status()))


@app.route("/api/analyze")
def api_analyze():
    query = request.args.get("symbol", "").strip()
    exchange = "BSE" if request.args.get("exchange", "NSE").upper() == "BSE" else "NSE"
    force = request.args.get("force") == "1"
    if not query:
        return jsonify({"error": "Please enter a stock symbol or company name."}), 400
    try:
        weights = {"demand": float(request.args.get("wd", config.WEIGHTS["demand"] * 100)),
                   "company": float(request.args.get("wc", config.WEIGHTS["company"] * 100)),
                   "macro": float(request.args.get("wm", config.WEIGHTS["macro"] * 100))}
    except ValueError:
        weights = dict(config.WEIGHTS)

    status = market.get_market_status()
    if status.closed_all_day and not force:
        return jsonify({"closed": True, "status": status_dict(status)})

    try:
        symbol, df = cached(("px", query.upper(), exchange), 300, lambda: data.fetch_price_history(query, exchange))
    except data.SymbolNotFound as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Could not fetch data: {e}"}), 502

    info = cached(("info", symbol), 3600, lambda: data.fetch_info(symbol))
    macro_data = cached("macro", 600, data.fetch_macro)

    status = market.adjust_status_with_data(status, df.index[-1].date())
    if status.closed_all_day and not force:
        return jsonify({"closed": True, "status": status_dict(status)})

    factors = {"demand": scoring.demand_score(df), "company": scoring.company_score(info),
               "macro": scoring.macro_score(macro_data)}
    p = predict.build_prediction(df, status, factors, weights)

    return jsonify(clean({
        "closed": False,
        "symbol": symbol,
        "name": info.get("longName") or info.get("shortName") or symbol,
        "status": status_dict(status),
        "last_session": df.index[-1].strftime("%d %b %Y"),
        "prediction": p.__dict__,
        "factors": {k: {"name": f.name, "score": f.score, "note": f.note,
                        "details": [{"indicator": a, "value": b, "score": s} for a, b, s in f.details]}
                    for k, f in factors.items()},
        "settings": {"repo": config.REPO_RATE, "cpi": config.CPI_INFLATION, "gdp": config.GDP_GROWTH},
    }))


if __name__ == "__main__":
    print("\n  Stock Recommender running ->  http://127.0.0.1:5000\n")
    app.run(host="127.0.0.1", port=5000, debug=False)
