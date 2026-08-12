"""The Norma Offers & Coupons integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN
from .coordinator import NormaDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BUTTON,
    Platform.IMAGE,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Norma from a config entry."""
    _LOGGER.debug("Setting up Norma entry for store: %s", entry.title)

    coordinator = NormaDataUpdateCoordinator(hass, entry)
    await coordinator.async_load_cache()

    await coordinator.async_config_entry_first_refresh()

    domain_data = hass.data.setdefault(DOMAIN, {})
    domain_data[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Remove orphaned account device when credentials were cleared (logout)
    if not coordinator.has_account:
        dev_reg = dr.async_get(hass)
        account_device = dev_reg.async_get_device(
            identifiers={(DOMAIN, coordinator.account_key)}
        )
        if account_device:
            dev_reg.async_remove_device(account_device.id)
            _LOGGER.debug(
                "NORMA: removed orphaned account device for store %s",
                coordinator.store_id,
            )

    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Norma entry for store: %s", entry.title)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        domain_data = hass.data.get(DOMAIN, {})
        domain_data.pop(entry.entry_id, None)

    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
