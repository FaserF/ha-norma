"""Binary sensor platform for the Norma Offers & Coupons integration."""

from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
)
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
    """Set up Norma binary sensors from a config entry."""
    coordinator: NormaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[BinarySensorEntity] = [
        NormaOffersAvailableBinarySensor(coordinator, entry),
    ]

    if entry.data.get("username"):
        entities.append(NormaLoginStatusBinarySensor(coordinator, entry))

    async_add_entities(entities)


class NormaBaseBinaryEntity(
    CoordinatorEntity[NormaDataUpdateCoordinator], BinarySensorEntity
):
    """Base binary sensor for Norma."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NormaDataUpdateCoordinator,
        entry: ConfigEntry,
        key: str,
    ) -> None:
        """Initialize binary sensor."""
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


class NormaOffersAvailableBinarySensor(NormaBaseBinaryEntity):
    """Binary sensor indicating if current offers are active."""

    _attr_translation_key = "offers_available"
    _attr_icon = "mdi:store-check"

    def __init__(
        self, coordinator: NormaDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize offers available binary sensor."""
        super().__init__(coordinator, entry, "offers_available")

    @property
    def is_on(self) -> bool:
        """Return True if offers exist in payload."""
        if not self.coordinator.data:
            return False
        return len(self.coordinator.data.get("discounts", [])) > 0


class NormaLoginStatusBinarySensor(NormaBaseBinaryEntity):
    """Binary sensor indicating if optional user login is valid."""

    _attr_translation_key = "login_status"
    _attr_icon = "mdi:account-check"

    def __init__(
        self, coordinator: NormaDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize login status binary sensor."""
        super().__init__(coordinator, entry, "login_status")

    @property
    def is_on(self) -> bool:
        """Return True if user authentication is active."""
        if not self.coordinator.data:
            return False
        return self.coordinator.data.get("is_authenticated", False)
