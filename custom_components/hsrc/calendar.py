from __future__ import annotations

from datetime import datetime

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import HsrcConfigEntry, HsrcCoordinator
from .describe import local_now, to_local_datetime
from .entity import HsrcEntity
from .training import BookedSession, is_upcoming, session_end, session_start


async def async_setup_entry(
    hass: HomeAssistant, entry: HsrcConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([BookedTrainingCalendar(entry.runtime_data)])


def to_calendar_event(session: BookedSession) -> CalendarEvent:
    return CalendarEvent(
        start=to_local_datetime(session_start(session.day)),
        end=to_local_datetime(session_end(session.day)),
        summary="HSRC early training",
        description=f"{session.name} (order {session.order_id})",
        location="The Snow Centre, Hemel Hempstead",
    )


class BookedTrainingCalendar(HsrcEntity, CalendarEntity):
    def __init__(self, coordinator: HsrcCoordinator) -> None:
        super().__init__(coordinator, "booked_training")

    @property
    def event(self) -> CalendarEvent | None:
        now = local_now()
        upcoming = [session for session in self.coordinator.data.booked if is_upcoming(session.day, now)]
        return to_calendar_event(upcoming[0]) if upcoming else None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        events = [to_calendar_event(session) for session in self.coordinator.data.booked]
        return [event for event in events if event.end > start_date and event.start < end_date]
