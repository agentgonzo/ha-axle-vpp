from __future__ import annotations

from datetime import timedelta, datetime
import logging
import homeassistant.util.dt as dt_util

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(hours=1)


class AxleCoordinator(DataUpdateCoordinator):
    """Coordinator for fetching Axle events."""

    def __init__(self, hass: HomeAssistant, api) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.api = api

    async def _async_update_data(self) -> list[dict]:
        """Fetch the latest event list from the Axle API."""
        try:
            return await self.api.async_get_events()
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Axle API: {err}") from err

    @property
    def current_event(self) -> dict | None:
        """Return the active event, or the next upcoming one, or None."""
        events: list[dict] = self.data or []
        now = dt_util.utcnow()
        upcoming = []

        for event in events:
            start_raw = event.get("start_time")
            end_raw = event.get("end_time")
            if not start_raw or not end_raw:
                continue
            try:
                start = datetime.fromisoformat(start_raw.replace("Z", "+00:00"))
                end = datetime.fromisoformat(end_raw.replace("Z", "+00:00"))
            except Exception:
                continue
            if start <= now <= end:
                return event
            if now < start:
                upcoming.append((start, event))

        if not upcoming:
            return None
        upcoming.sort(key=lambda x: x[0])
        return upcoming[0][1]
