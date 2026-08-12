"""Tests for the Norma sensor platform."""

from unittest.mock import patch
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.norma.const import DOMAIN, CONF_STORE_ID
from custom_components.norma.sensor import NormaOffersSensor, NormaCouponsSensor, NormaValidUntilSensor
from custom_components.norma.coordinator import NormaDataUpdateCoordinator


async def test_sensors_state(hass: HomeAssistant) -> None:
    """Test offer, coupon, and valid_until sensor states."""
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
        "discounts": [{"title": "Test Offer", "price": "1.00 €"}],
        "coupons": [{"code": "TEST10"}],
        "valid_until": "2026-08-31",
        "is_authenticated": True,
        "last_success": "2026-08-12T12:00:00",
    }

    offers_sensor = NormaOffersSensor(coordinator, entry)
    coupons_sensor = NormaCouponsSensor(coordinator, entry)
    valid_until_sensor = NormaValidUntilSensor(coordinator, entry)

    assert offers_sensor.native_value == 1
    assert coupons_sensor.native_value == 1
    assert valid_until_sensor.native_value == "2026-08-31"
