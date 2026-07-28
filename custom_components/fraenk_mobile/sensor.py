"""Sensor platform for fraenk Mobile."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, PERCENTAGE, UnitOfInformation
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FraenkCoordinator

PARALLEL_UPDATES = 0


def _number(value: Any) -> float | None:
    """Extract a decimal number from an API value such as '10.44 GB'."""
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None
    match = re.search(r"-?\d+(?:[.,]\d+)?", value)
    return float(match.group(0).replace(",", ".")) if match else None


def _timestamp(value: Any) -> datetime | None:
    """Convert a millisecond epoch timestamp to UTC."""
    if not isinstance(value, (int, float)) or value <= 0:
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc)


def _remaining(data: dict[str, Any]) -> float | None:
    """Calculate remaining data volume."""
    total = _number(data.get("initialVolume"))
    used = _number(data.get("usedVolume"))
    if total is None or used is None:
        return None
    return max(round(total - used, 3), 0)


@dataclass(frozen=True, kw_only=True)
class FraenkSensorDescription(SensorEntityDescription):
    """Describe a fraenk sensor."""

    value_fn: Callable[[dict[str, Any]], Any]


SENSORS: tuple[FraenkSensorDescription, ...] = (
    FraenkSensorDescription(
        key="used_data",
        translation_key="used_data",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        value_fn=lambda data: _number(data.get("usedVolume")),
    ),
    FraenkSensorDescription(
        key="remaining_data",
        translation_key="remaining_data",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=_remaining,
    ),
    FraenkSensorDescription(
        key="total_data",
        translation_key="total_data",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        value_fn=lambda data: _number(data.get("initialVolume")),
    ),
    FraenkSensorDescription(
        key="consumption_percentage",
        translation_key="consumption_percentage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda data: _number(data.get("percentageConsumption")),
    ),
    FraenkSensorDescription(
        key="expiry",
        translation_key="expiry",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: _timestamp(data.get("expiryTimestamp")),
    ),
    FraenkSensorDescription(
        key="last_update",
        translation_key="last_update",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: _timestamp(data.get("lastUpdateTimestamp")),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up fraenk sensors."""
    coordinator: FraenkCoordinator = entry.runtime_data
    entities: list[FraenkSensor] = []
    for data_pass in coordinator.data:
        entities.extend(
            FraenkSensor(coordinator, entry, data_pass, description)
            for description in SENSORS
        )
    async_add_entities(entities)


class FraenkSensor(CoordinatorEntity[FraenkCoordinator], SensorEntity):
    """A fraenk consumption sensor."""

    entity_description: FraenkSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: FraenkCoordinator,
        entry: ConfigEntry,
        data_pass: dict[str, Any],
        description: FraenkSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._contract_id = data_pass["_contract_id"]
        self._pass_index = data_pass["_pass_index"]
        self._attr_unique_id = (
            f"{entry.unique_id or entry.entry_id}_{self._contract_id}_"
            f"{self._pass_index}_{description.key}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.entry_id}_{self._contract_id}")},
            manufacturer="fraenk",
            model="Mobilfunkvertrag",
            name="fraenk Mobilfunk",
        )

    def _data_pass(self) -> dict[str, Any] | None:
        """Return the current pass matching this entity."""
        return next(
            (
                item
                for item in self.coordinator.data
                if item["_contract_id"] == self._contract_id
                and item["_pass_index"] == self._pass_index
            ),
            None,
        )

    @property
    def native_value(self) -> Any:
        """Return the current value."""
        data_pass = self._data_pass()
        return (
            self.entity_description.value_fn(data_pass)
            if data_pass is not None
            else None
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return useful non-sensitive pass attributes."""
        data_pass = self._data_pass()
        if not data_pass:
            return {}
        return {
            "data_pass": data_pass.get("passName") or None,
            "contract_id": self._contract_id,
            "expected_consumption": data_pass.get("expectedConsumption"),
            "download_bandwidth": data_pass.get("downloadBandwidth"),
            "speed_on": data_pass.get("speedon"),
            "speed_step_down": data_pass.get("speedStepDown"),
            "type": data_pass.get("type"),
        }

