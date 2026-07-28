"""Data coordinator for fraenk Mobile."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    FraenkApi,
    FraenkAuthenticationError,
    FraenkConnectionError,
    FraenkError,
)
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class FraenkCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Coordinate fraenk API updates."""

    config_entry: ConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, api: FraenkApi
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
            config_entry=entry,
        )
        self.api = api

    async def _async_update_data(self) -> list[dict[str, Any]]:
        """Fetch consumption data."""
        try:
            data = await self.api.async_get_consumption()
        except FraenkAuthenticationError as err:
            raise ConfigEntryAuthFailed from err
        except (FraenkConnectionError, FraenkError) as err:
            raise UpdateFailed(str(err)) from err

        if self.api.refresh_token != self.config_entry.data.get("refresh_token"):
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={
                    **self.config_entry.data,
                    "refresh_token": self.api.refresh_token,
                },
            )
        return data
