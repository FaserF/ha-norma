"""Sensor platform for the Norma Offers & Coupons integration."""

from __future__ import annotations

import logging
import re
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_BASE_PRICE,
    ATTR_CATEGORY,
    ATTR_DISCOUNT_PRICE,
    ATTR_DISCOUNT_TITLE,
    ATTR_PICTURE,
    ATTR_VALID_DATE,
    ATTRIBUTION,
    DOMAIN,
)
from .coordinator import NormaDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


def _parse_price_value(price_str: Any) -> float:
    """Parse numeric value from price string for sorting."""
    if not price_str:
        return float("inf")
    cleaned = (
        str(price_str)
        .replace("€", "")
        .replace("EUR", "")
        .replace("eur", "")
        .replace("*", "")
        .strip()
        .replace(",", ".")
    )
    match = re.search(r"\d+(?:\.\d+)?", cleaned)
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return float("inf")
    return float("inf")


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

    active_slugs = set()
    for product_filter in coordinator.product_filters:
        clean_filter = product_filter.strip()
        if clean_filter:
            entities.append(NormaProductFilterSensor(coordinator, entry, clean_filter))
            active_slugs.add(
                f"{entry.entry_id}_product_filter_{clean_filter.lower().replace(' ', '_')}"
            )

    # Reconcile entity registry: purge any filter entities belonging to this entry that are no longer configured
    from homeassistant.helpers import entity_registry as er

    ent_reg = er.async_get(hass)
    entry_entities = er.async_entries_for_config_entry(ent_reg, entry.entry_id)
    for ent in entry_entities:
        if (
            ent.domain == "sensor"
            and "_product_filter_" in ent.unique_id
            and ent.unique_id not in active_slugs
        ):
            ent_reg.async_remove(ent.entity_id)
            _LOGGER.debug(
                "NORMA: Removed stale filter entity %s (unique_id=%s)",
                ent.entity_id,
                ent.unique_id,
            )

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


class NormaProductFilterSensor(NormaStoreBaseEntity, SensorEntity):
    """Sensor tracking offers for a specific product search filter."""

    _attr_icon = "mdi:tag-search"

    def __init__(
        self,
        coordinator: NormaDataUpdateCoordinator,
        entry: ConfigEntry,
        product_filter: str,
    ) -> None:
        """Initialize product filter sensor."""
        super().__init__(
            coordinator,
            entry,
            f"product_filter_{product_filter.lower().replace(' ', '_')}",
        )
        self._filter = product_filter
        self._attr_name = f"Angebot {product_filter}"

    def _get_matches(self) -> list[dict[str, Any]]:
        """Calculate matching offers from coordinator discounts."""
        if not self.coordinator.data:
            return []
        discounts: list[dict[str, Any]] = self.coordinator.data.get("discounts", [])
        filter_term = self._filter.lower()
        matches: list[dict[str, Any]] = []
        for discount in discounts:
            title = str(discount.get(ATTR_DISCOUNT_TITLE, "") or "").lower()
            category = str(discount.get(ATTR_CATEGORY, "") or "").lower()
            base_price = str(discount.get(ATTR_BASE_PRICE, "") or "").lower()
            if (
                filter_term in title
                or filter_term in category
                or filter_term in base_price
            ):
                matches.append(discount)
        return matches

    @property
    def native_value(self) -> str:
        """Return best price found or 'Nicht im Angebot'."""
        matches = self._get_matches()
        if not matches:
            return "Nicht im Angebot"
        best = min(
            matches,
            key=lambda m: _parse_price_value(m.get(ATTR_DISCOUNT_PRICE)),
        )
        return str(best.get(ATTR_DISCOUNT_PRICE) or "Nicht im Angebot")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return filter matching details and metadata."""
        matches = self._get_matches()
        on_sale = bool(matches)
        best_match = (
            min(
                matches,
                key=lambda m: _parse_price_value(m.get(ATTR_DISCOUNT_PRICE)),
            )
            if on_sale
            else None
        )

        return {
            "filter": self._filter,
            "on_sale": on_sale,
            "match_count": len(matches),
            "best_price": best_match.get(ATTR_DISCOUNT_PRICE) if best_match else None,
            "base_price": best_match.get(ATTR_BASE_PRICE) if best_match else None,
            "product_title": (
                best_match.get(ATTR_DISCOUNT_TITLE) if best_match else None
            ),
            "category": best_match.get(ATTR_CATEGORY) if best_match else None,
            "valid_until": (
                best_match.get(ATTR_VALID_DATE)
                or (
                    self.coordinator.data.get("valid_until")
                    if self.coordinator.data
                    else None
                )
            )
            if best_match
            else None,
            "picture_link": best_match.get(ATTR_PICTURE) if best_match else None,
            "matches": matches,
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
