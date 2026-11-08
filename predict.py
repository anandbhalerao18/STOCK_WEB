"""Combine the 3 factor scores into direction, recommendation and expected closing price."""
from dataclasses import dataclass
import numpy as np
import config


@dataclass
class Prediction:
    base_price: float
    base_label: str
    target_label: str
    predicted_close: float
    change_pct: float
    low: float
    high: float
    final_score: float
    direction: str
    recommendation: str
    confidence: str
    sigma: float


def _norm_weights(w):
    t = sum(w.values()) or 1
    return {k: v / t for k, v in w.items()}


def build_prediction(df, status, factors: dict, weights: dict = None) -> Prediction:
    w = _norm_weights(weights or config.WEIGHTS)
    final = sum(w[k] * factors[k].score for k in w)

    close = df["Close"]
    base = float(close.iloc[-1])
    sigma = float(close.pct_change().tail(20).std())
    if np.isnan(sigma) or sigma == 0:
        sigma = 0.015

    exp_pct = final * sigma            # a score of +1 means "expect a 1-sigma daily move"
    pred = base * (1 + exp_pct)

    labels = {
        "OPEN": ("Current price", "Predicted closing price for today"),
        "PRE_OPEN": ("Previous close", "Predicted closing price for today"),
        "AFTER_CLOSE": ("Today's close", "Predicted closing price for the next session"),
    }
    base_label, target_label = labels.get(
        status.state, ("Last session close", "Predicted close for the next trading session"))

    if final >= config.DIRECTION_THRESHOLD:
        direction = "UP"
    elif final <= -config.DIRECTION_THRESHOLD:
        direction = "DOWN"
    else:
        direction = "SIDEWAYS"

    if final >= config.STRONG_THRESHOLD:
        rec = "STRONG BUY"
    elif final >= config.BUY_THRESHOLD:
        rec = "BUY"
    elif final <= -config.STRONG_THRESHOLD:
        rec = "STRONG SELL"
    elif final <= -config.BUY_THRESHOLD:
        rec = "SELL"
    else:
        rec = "HOLD"

    scores = [f.score for f in factors.values() if abs(f.score) > 0.02]
    agree = np.mean([np.sign(s) == np.sign(final) for s in scores]) if scores and final != 0 else 0.0
    conf_val = 0.6 * min(1.0, abs(final) / 0.5) + 0.4 * agree
    confidence = "High" if conf_val >= 0.7 else "Medium" if conf_val >= 0.4 else "Low"

    return Prediction(base, base_label, target_label, pred, exp_pct * 100,
                      pred * (1 - sigma), pred * (1 + sigma), final, direction, rec, confidence, sigma)
