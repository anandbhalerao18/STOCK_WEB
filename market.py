"""Market open/closed logic for NSE/BSE (IST, 9:15-15:30, Mon-Fri, minus holidays)."""
from dataclasses import dataclass
from datetime import datetime, time, date
import pytz
import config

IST = pytz.timezone("Asia/Kolkata")
OPEN_T = time(9, 15)
CLOSE_T = time(15, 30)


@dataclass
class MarketStatus:
    state: str      # OPEN, PRE_OPEN, AFTER_CLOSE, WEEKEND, HOLIDAY
    message: str
    now: datetime

    @property
    def closed_all_day(self) -> bool:
        return self.state in ("WEEKEND", "HOLIDAY")


def get_market_status(now: datetime = None) -> MarketStatus:
    now = now or datetime.now(IST)
    d, t = now.date(), now.time()
    day = now.strftime("%A")
    if d.weekday() >= 5:
        return MarketStatus("WEEKEND", f"Today ({day}) the market is closed - it is a weekend.", now)
    if d.isoformat() in config.NSE_HOLIDAYS:
        return MarketStatus("HOLIDAY", f"Today ({day}) the market is closed - it is an exchange holiday.", now)
    if t < OPEN_T:
        return MarketStatus("PRE_OPEN", "Market has not opened yet (opens 9:15 AM IST).", now)
    if t <= CLOSE_T:
        return MarketStatus("OPEN", "Market is open (closes 3:30 PM IST).", now)
    return MarketStatus("AFTER_CLOSE", "Market has closed for today (3:30 PM IST).", now)


def adjust_status_with_data(status: MarketStatus, last_bar_date: date) -> MarketStatus:
    """Catch unlisted holidays: if trading should be under way / finished but
    the stock has no candle for today, the exchange was probably shut."""
    now = status.now
    late_enough = status.state == "AFTER_CLOSE" or (status.state == "OPEN" and now.time() >= time(10, 0))
    if late_enough and last_bar_date < now.date():
        return MarketStatus("HOLIDAY",
                            f"Today ({now.strftime('%A')}) the market is closed - no trading data for today "
                            "(likely an exchange holiday).", now)
    return status
