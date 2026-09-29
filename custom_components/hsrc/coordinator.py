from __future__ import annotations

import logging
from dataclasses import dataclass, field

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import HsrcApiError, HsrcClient
from .const import DOMAIN, SCAN_INTERVAL
from .parsing import OrderItem
from .training import BookedSession, ListedSession, build_booked_sessions

_LOGGER = logging.getLogger(__name__)

type HsrcConfigEntry = ConfigEntry[HsrcCoordinator]


@dataclass
class HsrcData:
    listed: list[ListedSession] = field(default_factory=list)
    booked: list[BookedSession] = field(default_factory=list)


class HsrcCoordinator(DataUpdateCoordinator[HsrcData]):
    config_entry: HsrcConfigEntry

    def __init__(self, hass: HomeAssistant, entry: HsrcConfigEntry, client: HsrcClient) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self.client = client
        self._items_by_order: dict[int, list[OrderItem]] = {}

    async def _async_update_data(self) -> HsrcData:
        try:
            listed = await self.client.async_get_listed_sessions()
            orders = await self.client.async_get_orders()
            for order in orders:
                if order.order_id not in self._items_by_order:
                    self._items_by_order[order.order_id] = await self.client.async_get_order_items(order.order_id)
        except (HsrcApiError, aiohttp.ClientError) as error:
            raise UpdateFailed(str(error)) from error
        booked = [
            session
            for order in orders
            for session in build_booked_sessions(order, self._items_by_order[order.order_id])
        ]
        return HsrcData(listed=listed, booked=sorted(booked, key=lambda session: session.day))
