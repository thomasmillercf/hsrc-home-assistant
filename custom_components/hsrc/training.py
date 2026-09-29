from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from .const import EARLY_END, EARLY_START
from .parsing import ListingRow, OrderItem, OrderSummary

EARLY_SESSION = re.compile(
    r"^EARLY - Training - (?P<weekday>[A-Za-z]+) (?P<day>\d{1,2}) (?P<month>[A-Za-z]+)\s*$", re.IGNORECASE
)
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
MONTHS = [
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
]
CANCELLED_ORDER_STATUSES = {"refunded", "cancelled", "canceled"}
BOOKING_LEAD_TIME = timedelta(days=14)


@dataclass(frozen=True)
class ListedSession:
    day: date
    name: str
    code: str
    places_left: int
    url: str


@dataclass(frozen=True)
class BookedSession:
    day: date
    name: str
    order_id: int
    quantity: int


def read_early_session_day(name: str, earliest: date) -> date | None:
    match = EARLY_SESSION.match(name.strip())
    if match is None or match["month"].casefold() not in MONTHS:
        return None
    month = MONTHS.index(match["month"].casefold()) + 1
    for year in (earliest.year, earliest.year + 1):
        try:
            day = date(year, month, int(match["day"]))
        except ValueError:
            continue
        if day >= earliest and WEEKDAYS[day.weekday()] == match["weekday"].casefold():
            return day
    return None


def build_listed_sessions(rows: list[ListingRow], year: int) -> list[ListedSession]:
    sessions: list[ListedSession] = []
    for row in rows:
        day = read_early_session_day(row.name, date(year, 1, 1))
        if day is not None:
            sessions.append(ListedSession(day, row.name, row.code, row.places_left, row.url))
    return sessions


def build_booked_sessions(order: OrderSummary, items: list[OrderItem]) -> list[BookedSession]:
    if order.status.casefold() in CANCELLED_ORDER_STATUSES:
        return []
    sessions: list[BookedSession] = []
    for item in items:
        day = read_early_session_day(item.name, order.placed_on - BOOKING_LEAD_TIME)
        if day is not None:
            sessions.append(BookedSession(day, item.name, order.order_id, item.quantity))
    return sessions


def session_start(day: date) -> datetime:
    return datetime.combine(day, EARLY_START)


def session_end(day: date) -> datetime:
    return datetime.combine(day, EARLY_END)


def is_upcoming(day: date, now: datetime) -> bool:
    return session_end(day) > now


def find_unbooked(listed: list[ListedSession], booked: list[BookedSession], now: datetime) -> list[ListedSession]:
    booked_days = {session.day for session in booked}
    return sorted(
        (session for session in listed if is_upcoming(session.day, now) and session.day not in booked_days),
        key=lambda session: session.day,
    )


def find_next_session_day(listed: list[ListedSession], booked: list[BookedSession], now: datetime) -> date | None:
    upcoming = [session.day for session in [*listed, *booked] if is_upcoming(session.day, now)]
    return min(upcoming, default=None)
