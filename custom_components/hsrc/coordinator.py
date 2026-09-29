from __future__ import annotations

import logging
from dataclasses import dataclass, field

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import HsrcApiError, HsrcClient
from .const import DOMAIN, SCAN_INTERVAL
from .describe import local_now
from .parsing import OrderItem
from .training import BookedSession, ListedSession, build_booked_sessions, find_sessions_to_add_to_basket

_LOGGER = logging.getLogger(__name__)

type HsrcConfigEntry = ConfigEntry[HsrcCoordinator]


@dataclass
class HsrcData:
    listed: list[ListedSession] = field(default_factory=list)
    booked: list[BookedSession] = field(default_factory=list)
    basket_product_ids: set[int] = field(default_factory=set)


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
            basket_product_ids = await self.client.async_get_basket_product_ids()
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
        return HsrcData(
            listed=listed,
            booked=sorted(booked, key=lambda session: session.day),
            basket_product_ids=basket_product_ids,
        )

    async def async_add_unbooked_to_basket(self) -> list[ListedSession]:
        await self.async_refresh()
        if not self.last_update_success:
            raise HomeAssistantError(f"Could not read hsrc.info: {self.last_exception}")
        sessions = find_sessions_to_add_to_basket(
            self.data.listed, self.data.booked, self.data.basket_product_ids, local_now()
        )
        try:
            for session in sessions:
                await self.client.async_add_to_basket(session.url)
        except (HsrcApiError, aiohttp.ClientError) as error:
            raise HomeAssistantError(f"Could not add to the hsrc.info basket: {error}") from error
        finally:
            await self.async_refresh()
        return sessions
