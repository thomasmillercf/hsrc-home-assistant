from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.util import dt as dt_util

from .training import BookedSession, ListedSession, session_start


def local_now() -> datetime:
    return dt_util.now().replace(tzinfo=None)


def to_local_datetime(naive: datetime) -> datetime:
    return naive.replace(tzinfo=dt_util.get_default_time_zone())


def describe_listed(session: ListedSession, basket_product_ids: set[int]) -> dict[str, Any]:
    return {
        "date": session.day.isoformat(),
        "start": to_local_datetime(session_start(session.day)).isoformat(),
        "name": session.name,
        "code": session.code,
        "places_left": session.places_left,
        "in_basket": session.product_id in basket_product_ids,
        "url": session.url,
    }


def describe_booked(session: BookedSession) -> dict[str, Any]:
    return {
        "date": session.day.isoformat(),
        "start": to_local_datetime(session_start(session.day)).isoformat(),
        "name": session.name,
        "order_id": session.order_id,
        "quantity": session.quantity,
    }
