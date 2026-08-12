"""Button platform for the Norma Offers & Coupons integration."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import NormaDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Norma button entities from a config entry."""
    coordinator: NormaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    buttons: list[ButtonEntity] = [NormaForceUpdateButton(coordinator, entry)]

    if coordinator.has_account:
        buttons.append(NormaActivateCouponsButton(coordinator, entry))

    async_add_entities(buttons)


class NormaForceUpdateButton(ButtonEntity):
    """Button to trigger an immediate data refresh — attached to store device."""

    _attr_has_entity_name = True
    _attr_translation_key = "force_update"
    _attr_icon = "mdi:refresh"

    def __init__(
        self, coordinator: NormaDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        self.coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_force_update"

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

    async def async_press(self) -> None:
        _LOGGER.info(
            "User pressed force update button for Norma store %s",
            self.coordinator.store_id,
        )
        self.coordinator._force_update = True
        await self.coordinator.async_request_refresh()


class NormaActivateCouponsButton(ButtonEntity):
    """Button to activate all available coupons — attached to account device."""

    _attr_has_entity_name = True
    _attr_translation_key = "activate_coupons"
    _attr_icon = "mdi:ticket-percent-outline"

    def __init__(
        self, coordinator: NormaDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        self.coordinator = coordinator
        self._attr_unique_id = f"{coordinator.account_key}_activate_coupons"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.account_key)},
            name="NORMA Konto",
            manufacturer="NORMA",
            model="NORMA Kundenkonto",
            configuration_url=coordinator.account_configuration_url,
        )

    @property
    def available(self) -> bool:
        return self.coordinator.has_account

    async def async_press(self) -> None:
        _LOGGER.info(
            "User pressed activate coupons button for Norma account %s",
            self.coordinator.username,
        )
        await self.coordinator.async_activate_coupons()
