from __future__ import annotations

from datetime import datetime

import homeassistant.util.dt as dt_util
from homeassistant.components.calendar import (
    CalendarEntity,
    CalendarEvent,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

DEVICE_INFO = DeviceInfo(
    identifiers={(DOMAIN, "axle_vpp")},
    name="Axle VPP",
    manufacturer="Axle Energy",
    model="Virtual Power Plant",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AxleNextEventCalendar(coordinator)])


class AxleNextEventCalendar(CoordinatorEntity, CalendarEntity):
    _attr_name = "Axle Next Event"
    _attr_unique_id = "axle_vpp_next_event"
    _attr_device_info = DEVICE_INFO

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)

    @property
    def event(self) -> CalendarEvent | None:
        """The active or next upcoming event, shown on the calendar tile."""
        return self._event_from_dict(self.coordinator.current_event)

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return all events that overlap the requested date range."""
        events = []
        for event_dict in (self.coordinator.data or []):
            cal_event = self._event_from_dict(event_dict)
            if cal_event is None:
                continue
            if cal_event.end < start_date or cal_event.start > end_date:
                continue
            events.append(cal_event)
        return events

    def _event_from_dict(self, data: dict | None) -> CalendarEvent | None:
        if not data:
            return None
        start_raw = data.get("start_time")
        end_raw = data.get("end_time")
        if not start_raw or not end_raw:
            return None
        try:
            start = datetime.fromisoformat(start_raw.replace("Z", "+00:00"))
            end = datetime.fromisoformat(end_raw.replace("Z", "+00:00"))
        except Exception:
            return None
        import_export = data.get("import_export", "Dispatch")
        return CalendarEvent(
            summary=f"Axle {import_export} Event",
            start=dt_util.as_local(start),
            end=dt_util.as_local(end),
        )

    @property
    def extra_state_attributes(self):
        data = self.coordinator.current_event or {}
        return {
            "import_export": data.get("import_export"),
            "updated_at": data.get("updated_at"),
        }
