"""The 3 factor models. Each returns a FactorResult with a score from -1 (bearish) to +1 (bullish)."""
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
import config


def _clip(x, lo=-1.0, hi=1.0):
    return float(max(lo, min(hi, x)))


@dataclass
class FactorResult:
    name: str
    score: float = 0.0
    details: list = field(default_factory=list)   # (indicator, value text, sub-score)
    note: str = ""

    def add(self, indicator, value, sub):
        self.details.append((indicator, value, _clip(sub)))

    def finalize(self):
        if self.details:
            self.score = _clip(float(np.mean([d[2] for d in self.details])))
        return self


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    delta = close.diff()
    up = delta.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    down = (-delta.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = up / down.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(50)


# ------------------------------------------------------------------ 1. SUPPLY & DEMAND
def demand_score(df: pd.DataFrame) -> FactorResult:
    r = FactorResult("Supply & Demand")
    if len(df) < 20:
        r.note = "Less than 20 trading days of history (new listing) - limited demand signals."
    c, h, l, v = df["Close"], df["High"], df["Low"], df["Volume"]
    last = float(c.iloc[-1])

    if len(df) >= 20:
        sma20 = float(c.tail(20).mean())
        r.add("Price vs 20-day average", f"{last:.2f} vs {sma20:.2f}", (last / sma20 - 1) / 0.05)
    if len(df) >= 50:
        sma50 = float(c.tail(50).mean())
        r.add("Price vs 50-day average", f"{last:.2f} vs {sma50:.2f}", (last / sma50 - 1) / 0.10)
    if len(df) >= 15:
        rv = float(rsi(c).iloc[-1])
        sub = 0.5 if rv < 30 else -0.5 if rv > 70 else (rv - 50) / 40
        r.add("RSI (14)", f"{rv:.1f}", sub)
    if len(df) >= 6:
        mom = float(c.iloc[-1] / c.iloc[-6] - 1)
        r.add("5-day momentum", f"{mom * 100:+.2f}%", mom / 0.05)
    if len(df) >= 22 and v.tail(21).iloc[:-1].mean() > 0:
        ratio = float(v.iloc[-1] / v.tail(21).iloc[:-1].mean())
        ret = float(c.iloc[-1] / c.iloc[-2] - 1)
        sub = float(np.sign(ret)) * _clip((ratio - 0.5) / 1.5, 0, 1)
        r.add("Volume vs 20-day avg (x direction)", f"{ratio:.2f}x, price {ret * 100:+.2f}%", sub)
    rng = (h - l).replace(0, np.nan)
    clv = (((c - l) - (h - c)) / rng).fillna(0)          # +1 = closed at high (buyers), -1 = at low (sellers)
    vt = v.tail(10)
    if vt.sum() > 0:
        mf = float((clv.tail(10) * vt).sum() / vt.sum())
        r.add("Buy/Sell pressure (money flow, 10d)", f"{mf:+.2f}", mf * 1.5)
    return r.finalize()


# ------------------------------------------------------------------ 2. COMPANY PERFORMANCE
def _num(info, key):
    x = info.get(key)
    return float(x) if isinstance(x, (int, float)) and not np.isnan(x) else None


def company_score(info: dict) -> FactorResult:
    r = FactorResult("Company Performance")
    eg, rg = _num(info, "earningsGrowth"), _num(info, "revenueGrowth")
    pm, roe = _num(info, "profitMargins"), _num(info, "returnOnEquity")
    pe, fpe = _num(info, "trailingPE"), _num(info, "forwardPE")
    if eg is not None:
        r.add("Earnings growth", f"{eg * 100:+.1f}%", eg / 0.30)
    if rg is not None:
        r.add("Revenue growth", f"{rg * 100:+.1f}%", rg / 0.20)
    if pm is not None:
        r.add("Profit margin", f"{pm * 100:.1f}%", (pm - 0.10) / 0.15)
    if roe is not None:
        r.add("Return on equity", f"{roe * 100:.1f}%", (roe - 0.12) / 0.15)
    if pe is not None and pe > 0:
        r.add("P/E ratio (25 = fair)", f"{pe:.1f}", 0.5 * (25 - pe) / 25)
    if pe is not None and fpe is not None and pe > 0 and fpe > 0:
        r.add("Forward vs trailing P/E (earnings expected to grow?)", f"{fpe:.1f} vs {pe:.1f}", (pe - fpe) / pe / 0.2)
    if not r.details:
        r.note = "No fundamentals available (very new listing / data missing) - this factor is neutral."
    return r.finalize()


# ------------------------------------------------------------------ 3. MACROECONOMIC
def macro_score(macro: dict) -> FactorResult:
    r = FactorResult("Macroeconomic")
    n = macro.get("Nifty 50")
    if n is not None and len(n) >= 20:
        c = n["Close"]
        r.add("Nifty 50 vs 50-day avg", f"{c.iloc[-1]:.0f}", (c.iloc[-1] / c.tail(50).mean() - 1) / 0.04)
        r.add("Nifty 5-day return", f"{(c.iloc[-1] / c.iloc[-6] - 1) * 100:+.2f}%", (c.iloc[-1] / c.iloc[-6] - 1) / 0.02)
    vx = macro.get("India VIX")
    if vx is not None and len(vx) >= 6:
        c = vx["Close"]
        r.add("India VIX level (fear gauge)", f"{c.iloc[-1]:.1f}", (16 - c.iloc[-1]) / 6)
        r.add("India VIX 5-day change", f"{(c.iloc[-1] / c.iloc[-6] - 1) * 100:+.1f}%", -(c.iloc[-1] / c.iloc[-6] - 1) / 0.15)
    fx = macro.get("USD/INR")
    if fx is not None and len(fx) >= 6:
        c = fx["Close"]
        ch = c.iloc[-1] / c.iloc[-6] - 1
        r.add("USD/INR 5-day change (rupee weakness = bad)", f"{c.iloc[-1]:.2f} ({ch * 100:+.2f}%)", -ch / 0.01)
    cr = macro.get("Brent Crude")
    if cr is not None and len(cr) >= 6:
        c = cr["Close"]
        ch = c.iloc[-1] / c.iloc[-6] - 1
        r.add("Crude oil 5-day change (India imports oil)", f"{c.iloc[-1]:.1f} ({ch * 100:+.1f}%)", -ch / 0.05)

    # manual inputs from config.py (RBI / MoSPI)
    r.add("RBI repo rate move", f"{config.REPO_RATE:.2f}% ({['cut', 'hold', 'hike'][config.REPO_RATE_TREND + 1]})",
          -0.7 * config.REPO_RATE_TREND)
    cpi = config.CPI_INFLATION
    r.add("CPI inflation (RBI target 4%, band 2-6%)", f"{cpi:.1f}%",
          -0.8 if cpi > 6 else -0.3 if cpi > 4.5 else 0.3 if cpi >= 2 else 0.0)
    r.add("GDP growth", f"{config.GDP_GROWTH:.1f}%", (config.GDP_GROWTH - 6) / 2)
    if not macro:
        r.note = "Live macro data unavailable - only manual RBI/CPI/GDP inputs were used."
    return r.finalize()
