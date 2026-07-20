import logging
import aiohttp
from datetime import datetime

_LOGGER = logging.getLogger(__name__)


class AxleApi:
    """
    Production API client for Axle Energy VPP events.

    Fetches real event data from Axle and normalises it to a list of event dicts
    regardless of whether the API returns a single object, a bare list, or an
    {"events": [...]} envelope.
    """

    BASE_URL = "https://api.axle.energy/vpp/home-assistant/event"

    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        }

    async def async_get_events(self) -> list[dict]:
        """
        Fetch VPP events from Axle.

        Returns a (possibly empty) list of event dicts, each with keys:
            start_time, end_time, import_export, updated_at
        Raises:
            Exception on network or API errors.
        """
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(self.BASE_URL) as resp:
                    if resp.status != 200:
                        raise Exception(f"Axle API returned status {resp.status}")
                    data = await resp.json()
        except Exception as err:
            raise Exception(f"Error fetching Axle API: {err}") from err

        _LOGGER.debug("Raw API response: %s", data)
        events = self._normalise(data)
        _LOGGER.debug("Normalised to %d event(s): %s", len(events), events)
        return events

    def _normalise(self, data) -> list[dict]:
        """Normalise any API response shape to a list of event dicts."""
        if not data:
            _LOGGER.debug("Empty response from API")
            return []

        # Unwrap {"events": [...]} envelope
        if isinstance(data, dict) and "events" in data:
            _LOGGER.debug("Unwrapping 'events' envelope")
            data = data["events"]

        # Single-event flat dict
        if isinstance(data, dict):
            if "start_time" not in data:
                _LOGGER.debug("Single dict response has no 'start_time', ignoring")
                return []
            data = [data]

        if not isinstance(data, list):
            _LOGGER.debug("Unexpected response type %s, ignoring", type(data))
            return []

        now_iso = datetime.utcnow().isoformat() + "Z"
        events = []
        for item in data:
            if not isinstance(item, dict) or "start_time" not in item:
                _LOGGER.debug("Skipping item with no 'start_time': %s", item)
                continue
            events.append({
                "start_time": item.get("start_time"),
                "end_time": item.get("end_time"),
                "import_export": item.get("import_export", 0),
                "updated_at": item.get("updated_at", now_iso),
            })

        return events
