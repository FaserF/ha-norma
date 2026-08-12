"""Sensor platform for the Norma Offers & Coupons integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NormaDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Norma sensors from a config entry."""
    coordinator: NormaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = [
        NormaOffersSensor(coordinator, entry),
    ]

    if entry.data.get("username"):
        entities.append(NormaCouponsSensor(coordinator, entry))

    async_add_entities(entities)


class NormaBaseEntity(CoordinatorEntity[NormaDataUpdateCoordinator]):
    """Base entity for Norma sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NormaDataUpdateCoordinator,
        entry: ConfigEntry,
        key: str,
    ) -> None:
        """Initialize the base entity."""
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"

        store_name = str(
            entry.data.get("store_name") or entry.data.get("store_id") or "Filiale"
        )
        device_name = (
            store_name
            if store_name.upper().startswith("NORMA")
            else f"NORMA {store_name}"
        )

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=device_name,
            manufacturer="NORMA",
            model="Filiale & Angebote",
            configuration_url=coordinator.configuration_url,
        )


class NormaOffersSensor(NormaBaseEntity, SensorEntity):
    """Sensor tracking total weekly discounts."""

    _attr_translation_key = "offers_count"
    _attr_icon = "mdi:tag-multiple"

    def __init__(
        self, coordinator: NormaDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize offer sensor."""
        super().__init__(coordinator, entry, "offers_count")

    @property
    def native_value(self) -> int:
        """Return total number of discounts."""
        if not self.coordinator.data:
            return 0
        return len(self.coordinator.data.get("discounts", []))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return list of discounts as extra attributes."""
        if not self.coordinator.data:
            return {}
        return {
            "discounts": self.coordinator.data.get("discounts", []),
            "valid_until": self.coordinator.data.get("valid_until"),
            "last_updated": self.coordinator.data.get("last_success"),
        }


class NormaCouponsSensor(NormaBaseEntity, SensorEntity):
    """Sensor tracking active user coupons."""

    _attr_translation_key = "coupons_count"
    _attr_icon = "mdi:ticket-percent"

    def __init__(
        self, coordinator: NormaDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize coupon sensor."""
        super().__init__(coordinator, entry, "coupons_count")

    @property
    def native_value(self) -> int:
        """Return total active coupons."""
        if not self.coordinator.data:
            return 0
        return len(self.coordinator.data.get("coupons", []))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return coupon list attributes."""
        if not self.coordinator.data:
            return {}
        return {
            "coupons": self.coordinator.data.get("coupons", []),
            "is_authenticated": self.coordinator.data.get("is_authenticated", False),
        }


class NormaValidUntilSensor(NormaBaseEntity, SensorEntity):
    """Sensor tracking valid_until date for current offers."""

    _attr_translation_key = "valid_until"
    _attr_icon = "mdi:calendar-clock"

    def __init__(
        self, coordinator: NormaDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize valid until sensor."""
        super().__init__(coordinator, entry, "valid_until")

    @property
    def native_value(self) -> str | None:
        """Return valid_until date string."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("valid_until")
