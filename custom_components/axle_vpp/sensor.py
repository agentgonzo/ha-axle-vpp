from __future__ import annotations

from datetime import datetime
import homeassistant.util.dt as dt_util

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

DEVICE_INFO = DeviceInfo(
    identifiers={(DOMAIN, "axle_vpp")},
    name="Axle VPP",
    manufacturer="Axle Energy",
    model="Virtual Power Plant",
)

FRIENDLY_SENSORS = {
    "start_time_friendly": "Axle Start Time (Friendly)",
    "end_time_friendly":   "Axle End Time (Friendly)",
    "updated_at_friendly": "Axle Updated At (Friendly)",
}

_KEY_MAP = {
    "start_time_friendly": "start_time",
    "end_time_friendly":   "end_time",
    "updated_at_friendly": "updated_at",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AxleFriendlySensor(coordinator, key, name)
        for key, name in FRIENDLY_SENSORS.items()
    )


class AxleFriendlySensor(SensorEntity):
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator, key: str, name: str) -> None:
        self.coordinator = coordinator
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"axle_vpp_{key}"
        self._attr_device_info = DEVICE_INFO

    @property
    def available(self):
        return self.coordinator.last_update_success

    async def async_added_to_hass(self):
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    @property
    def native_value(self):
        raw = (self.coordinator.current_event or {}).get(_KEY_MAP[self._key])
        if not raw:
            return None
        try:
            return dt_util.as_local(datetime.fromisoformat(raw.replace("Z", "+00:00")))
        except Exception:
            return None
