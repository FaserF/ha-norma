"""Tests for the Norma binary sensor platform."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.norma.binary_sensor import (
    NormaLoginStatusBinarySensor,
    NormaOffersAvailableBinarySensor,
)
from custom_components.norma.const import CONF_STORE_ID, DOMAIN
from custom_components.norma.coordinator import NormaDataUpdateCoordinator


async def test_binary_sensors_state(hass: HomeAssistant) -> None:
    """Test binary sensor on/off states."""
    entry = ConfigEntry(
        version=1,
        minor_version=0,
        domain=DOMAIN,
        title="NORMA Test",
        data={CONF_STORE_ID: "norma_123", "username": "test@user.de"},
        source="user",
        options={},
        entry_id="test_entry_id",
    )

    coordinator = NormaDataUpdateCoordinator(hass, entry)
    coordinator.data = {
        "discounts": [{"title": "Test Offer"}],
        "is_authenticated": True,
    }

    offers_bs = NormaOffersAvailableBinarySensor(coordinator, entry)
    login_bs = NormaLoginStatusBinarySensor(coordinator, entry)

    assert offers_bs.is_on is True
    assert login_bs.is_on is True
