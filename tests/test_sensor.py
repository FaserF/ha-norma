"""Tests for the Norma sensor platform."""

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.norma.const import CONF_STORE_ID, DOMAIN
from custom_components.norma.coordinator import NormaDataUpdateCoordinator
from custom_components.norma.sensor import (
    NormaActivatedCouponsSensor,
    NormaAvailableCouponsSensor,
    NormaOffersSensor,
)


async def test_sensors_state(hass: HomeAssistant) -> None:
    """Test offer and coupon sensor states."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="NORMA Test",
        data={CONF_STORE_ID: "norma_123", "username": "test@user.de", "password": "secretpassword"},
        options={},
        entry_id="test_entry_id",
    )

    coordinator = NormaDataUpdateCoordinator(hass, entry)
    coordinator.data = {
        "discounts": [{"title": "Test Offer", "price": "1.00 €"}],
        "coupons": [
            {"code": "TEST10", "activated": True},
            {"code": "TEST20", "activated": False},
        ],
        "valid_until": "2026-08-31",
        "is_authenticated": True,
        "last_success": "2026-08-12T12:00:00",
    }

    offers_sensor = NormaOffersSensor(coordinator, entry)
    activated_sensor = NormaActivatedCouponsSensor(coordinator, entry)
    available_sensor = NormaAvailableCouponsSensor(coordinator, entry)

    assert offers_sensor.native_value == 1
    assert offers_sensor.extra_state_attributes["valid_until"] == "2026-08-31"
    assert activated_sensor.native_value == 1
    assert available_sensor.native_value == 1
