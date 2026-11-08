"""
Central settings. Edit the MANUAL MACRO INPUTS before you demo the project,
because India's GDP / CPI / RBI repo rate have no free live API.
"""

# ---- How much each of the 3 factors counts in the final score (auto-normalised) ----
WEIGHTS = {"demand": 0.40, "company": 0.30, "macro": 0.30}

# ---- Recommendation thresholds on the final score (-1 .. +1) ----
BUY_THRESHOLD = 0.15
STRONG_THRESHOLD = 0.40
DIRECTION_THRESHOLD = 0.10      # |score| below this -> "SIDEWAYS"

# ---- MANUAL MACRO INPUTS (update from RBI / MoSPI / press releases) ----
REPO_RATE = 5.25                # RBI repo rate in %   (PLACEHOLDER - verify)
REPO_RATE_TREND = 0             # latest RBI move: -1 = cut, 0 = hold, +1 = hike
CPI_INFLATION = 3.0             # latest CPI inflation in %   (PLACEHOLDER - verify)
GDP_GROWTH = 7.0                # latest GDP growth in %      (PLACEHOLDER - verify)

# ---- Live macro series fetched through yfinance ----
MACRO_TICKERS = {
    "Nifty 50": "^NSEI",
    "India VIX": "^INDIAVIX",
    "USD/INR": "INR=X",
    "Brent Crude": "BZ=F",
}

# ---- NSE trading holidays for 2026 (weekends are handled automatically).
# Verify against the official NSE holiday list and edit as needed.
NSE_HOLIDAYS = [
    "2026-01-26", "2026-03-03", "2026-03-26", "2026-03-31", "2026-04-03",
    "2026-04-14", "2026-05-01", "2026-05-28", "2026-06-26", "2026-09-14",
    "2026-10-02", "2026-10-20", "2026-11-10", "2026-11-24", "2026-12-25",
]
