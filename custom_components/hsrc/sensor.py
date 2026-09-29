from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import HsrcConfigEntry, HsrcCoordinator
from .describe import describe_booked, describe_listed, local_now, to_local_datetime
from .entity import HsrcEntity
from .training import BookedSession, find_unbooked, is_upcoming, session_start


async def async_setup_entry(
    hass: HomeAssistant, entry: HsrcConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities([NextBookedSessionSensor(coordinator), UnbookedSessionsSensor(coordinator)])


class NextBookedSessionSensor(HsrcEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: HsrcCoordinator) -> None:
        super().__init__(coordinator, "next_booked_session")

    @property
    def upcoming_bookings(self) -> list[BookedSession]:
        now = local_now()
        return [session for session in self.coordinator.data.booked if is_upcoming(session.day, now)]

    @property
    def native_value(self) -> datetime | None:
        upcoming = self.upcoming_bookings
        return to_local_datetime(session_start(upcoming[0].day)) if upcoming else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"bookings": [describe_booked(session) for session in self.upcoming_bookings]}


class UnbookedSessionsSensor(HsrcEntity, SensorEntity):
    _attr_native_unit_of_measurement = "sessions"

    def __init__(self, coordinator: HsrcCoordinator) -> None:
        super().__init__(coordinator, "unbooked_sessions")

    @property
    def native_value(self) -> int:
        return len(find_unbooked(self.coordinator.data.listed, self.coordinator.data.booked, local_now()))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        unbooked = find_unbooked(self.coordinator.data.listed, self.coordinator.data.booked, local_now())
        basket_product_ids = self.coordinator.data.basket_product_ids
        return {"sessions": [describe_listed(session, basket_product_ids) for session in unbooked]}
