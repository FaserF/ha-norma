"""Sensor platform for the Norma Offers & Coupons integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
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

    if coordinator.has_account:
        entities.extend(
            [
                NormaActivatedCouponsSensor(coordinator, entry),
                NormaAvailableCouponsSensor(coordinator, entry),
            ]
        )

    async_add_entities(entities)


# ---------------------------------------------------------------------------
# Store device sensors
# ---------------------------------------------------------------------------


class NormaStoreBaseEntity(CoordinatorEntity[NormaDataUpdateCoordinator]):
    """Base entity attached to the NORMA store device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NormaDataUpdateCoordinator,
        entry: ConfigEntry,
        key: str,
    ) -> None:
        super().__init__(coordinator)
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


class NormaOffersSensor(NormaStoreBaseEntity, SensorEntity):
    """Sensor tracking total weekly discounts."""

    _attr_translation_key = "offers_count"
    _attr_icon = "mdi:tag-multiple"
    _attr_native_unit_of_measurement = "items"

    def __init__(
        self, coordinator: NormaDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry, "offers_count")

    @property
    def native_value(self) -> int:
        if not self.coordinator.data:
            return 0
        return len(self.coordinator.data.get("discounts", []))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coordinator.data:
            return {ATTR_ATTRIBUTION: ATTRIBUTION}
        return {
            "discounts": self.coordinator.data.get("discounts", []),
            "valid_until": self.coordinator.data.get("valid_until"),
            "last_updated": self.coordinator.data.get("last_success"),
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }


# ---------------------------------------------------------------------------
# Account device sensors
# ---------------------------------------------------------------------------


class NormaAccountBaseEntity(CoordinatorEntity[NormaDataUpdateCoordinator]):
    """Base entity attached to the NORMA account device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NormaDataUpdateCoordinator,
        entry: ConfigEntry,
        key: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.account_key}_{key}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.account_key)},
            name="NORMA Konto",
            manufacturer="NORMA",
            model="NORMA Kundenkonto",
            configuration_url=coordinator.account_configuration_url,
        )

    @property
    def available(self) -> bool:
        return self.coordinator.data is not None and self.coordinator.has_account


class NormaActivatedCouponsSensor(NormaAccountBaseEntity, SensorEntity):
    """Sensor tracking activated NORMA coupons."""

    _attr_translation_key = "activated_coupons"
    _attr_icon = "mdi:ticket-confirmation"
    _attr_native_unit_of_measurement = "items"

    def __init__(
        self, coordinator: NormaDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry, "activated_coupons")

    @property
    def native_value(self) -> int:
        if not self.coordinator.data:
            return 0
        coupons: list[dict[str, Any]] = self.coordinator.data.get("coupons", [])
        return len([c for c in coupons if c.get("activated", False)])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coordinator.data:
            return {ATTR_ATTRIBUTION: ATTRIBUTION}
        coupons = self.coordinator.data.get("coupons", [])
        return {
            "coupons": [c for c in coupons if c.get("activated", False)],
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }


class NormaAvailableCouponsSensor(NormaAccountBaseEntity, SensorEntity):
    """Sensor tracking available (non-activated) NORMA coupons."""

    _attr_translation_key = "available_coupons"
    _attr_icon = "mdi:ticket-percent"
    _attr_native_unit_of_measurement = "items"

    def __init__(
        self, coordinator: NormaDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry, "available_coupons")

    @property
    def native_value(self) -> int:
        if not self.coordinator.data:
            return 0
        coupons: list[dict[str, Any]] = self.coordinator.data.get("coupons", [])
        return len([c for c in coupons if not c.get("activated", False)])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coordinator.data:
            return {ATTR_ATTRIBUTION: ATTRIBUTION}
        coupons = self.coordinator.data.get("coupons", [])
        return {
            "coupons": [c for c in coupons if not c.get("activated", False)],
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }
