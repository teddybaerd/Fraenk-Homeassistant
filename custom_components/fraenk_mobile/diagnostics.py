"""Diagnostics for fraenk Mobile."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.redact import async_redact_data

from .coordinator import FraenkCoordinator

TO_REDACT = {"refresh_token", "customer_id", "contract_id", "_contract_id", "username"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return redacted diagnostics."""
    coordinator: FraenkCoordinator = entry.runtime_data
    return {
        "config_entry": async_redact_data(dict(entry.data), TO_REDACT),
        "data": async_redact_data(coordinator.data, TO_REDACT),
    }
