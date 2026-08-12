"""Diagnostics support for Norma Offers & Coupons."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_PASSWORD, CONF_USERNAME, DOMAIN
from .coordinator import NormaDataUpdateCoordinator

TO_REDACT = {CONF_USERNAME, CONF_PASSWORD, "token", "auth_token", "cookies"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: NormaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    diagnostics_data = {
        "config_entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "coordinator": {
            "store_id": coordinator.store_id,
            "last_success": (
                coordinator._last_success.isoformat()
                if coordinator._last_success
                else None
            ),
            "consecutive_failures": coordinator._consecutive_failures,
            "backoff_until": (
                coordinator._backoff_until.isoformat()
                if coordinator._backoff_until
                else None
            ),
            "data": async_redact_data(coordinator.data or {}, TO_REDACT),
        },
    }

    return diagnostics_data
