"""The fraenk Mobile integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import FraenkApi
from .const import CONF_CUSTOMER_ID, CONF_REFRESH_TOKEN
from .coordinator import FraenkCoordinator

PLATFORMS = [Platform.SENSOR]
type FraenkConfigEntry = ConfigEntry[FraenkCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: FraenkConfigEntry) -> bool:
    """Set up fraenk Mobile from a config entry."""
    api = FraenkApi(
        async_get_clientsession(hass),
        refresh_token=entry.data[CONF_REFRESH_TOKEN],
        customer_id=entry.data[CONF_CUSTOMER_ID],
    )
    coordinator = FraenkCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: FraenkConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
