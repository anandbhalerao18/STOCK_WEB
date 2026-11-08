"""Live data fetching with yfinance. No database everything is fetched on demand."""
import pandas as pd
import yfinance as yf
import config


class SymbolNotFound(Exception):
    pass


def _candidates(query: str, exchange: str):
    s = query.strip().upper().replace(" ", "")
    if s.startswith("^") or s.endswith((".NS", ".BO")):
        return [s]
    order = (".NS", ".BO") if exchange == "NSE" else (".BO", ".NS")
    return [s + order[0], s + order[1]]


def _search_by_name(query: str, exchange: str):
    """Fallback: let the user type a company name, e.g. 'tata motors'."""
    try:
        quotes = yf.Search(query, max_results=10).quotes
    except Exception:
        return []
    want = (".NS", ".BO") if exchange == "NSE" else (".BO", ".NS")
    syms = [q.get("symbol", "") for q in quotes]
    out = []
    for suffix in want:
        out += [s for s in syms if s.endswith(suffix)]
    return out[:3]


def _history(symbol: str, period: str = "1y"):
    try:
        df = yf.Ticker(symbol).history(period=period, auto_adjust=False)
    except Exception:
        return None
    if df is None or df.empty:
        return None
    df = df.dropna(subset=["Close"]).copy()
    return df if len(df) >= 5 else None


def fetch_price_history(query: str, exchange: str = "NSE"):
    """Returns (resolved_symbol, dataframe). Works for old and newly listed stocks."""
    tried = _candidates(query, exchange)
    for sym in tried:
        df = _history(sym)
        if df is not None:
            return sym, df
    for sym in _search_by_name(query, exchange):
        df = _history(sym)
        if df is not None:
            return sym, df
    raise SymbolNotFound(f"No data found for '{query}'. Tried: {', '.join(tried)}")


def fetch_info(symbol: str) -> dict:
    try:
        return yf.Ticker(symbol).info or {}
    except Exception:
        return {}


def fetch_macro() -> dict:
    out = {}
    for name, tk in config.MACRO_TICKERS.items():
        df = _history(tk, "6mo")
        if df is not None:
            out[name] = df
    return out
