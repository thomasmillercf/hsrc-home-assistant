from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import HsrcConfigEntry, HsrcCoordinator
from .describe import local_now, to_local_datetime
from .entity import HsrcEntity
from .training import find_next_session_day, session_start


async def async_setup_entry(
    hass: HomeAssistant, entry: HsrcConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([NextSessionBookedBinarySensor(entry.runtime_data)])


class NextSessionBookedBinarySensor(HsrcEntity, BinarySensorEntity):
    def __init__(self, coordinator: HsrcCoordinator) -> None:
        super().__init__(coordinator, "next_session_booked")

    @property
    def is_on(self) -> bool | None:
        next_day = find_next_session_day(self.coordinator.data.listed, self.coordinator.data.booked, local_now())
        if next_day is None:
            return None
        return any(session.day == next_day for session in self.coordinator.data.booked)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        next_day = find_next_session_day(self.coordinator.data.listed, self.coordinator.data.booked, local_now())
        if next_day is None:
            return {}
        listing = next((session for session in self.coordinator.data.listed if session.day == next_day), None)
        return {
            "date": next_day.isoformat(),
            "start": to_local_datetime(session_start(next_day)).isoformat(),
            "places_left": listing.places_left if listing else None,
            "url": listing.url if listing else None,
        }
