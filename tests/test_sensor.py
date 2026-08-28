"""Tests for the Norma sensor platform."""

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.norma.const import CONF_STORE_ID, DOMAIN
from custom_components.norma.coordinator import NormaDataUpdateCoordinator
from custom_components.norma.sensor import (
    NormaActivatedCouponsSensor,
    NormaAvailableCouponsSensor,
    NormaOffersSensor,
    NormaProductFilterSensor,
)


async def test_sensors_state(hass: HomeAssistant) -> None:
    """Test offer and coupon sensor states."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="NORMA Test",
        data={
            CONF_STORE_ID: "norma_123",
            "username": "test@user.de",
            "password": "secretpassword",
        },
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


async def test_product_filter_sensor(hass: HomeAssistant) -> None:
    """Test product filter sensor matching, states and attributes."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="NORMA Test",
        data={CONF_STORE_ID: "norma_123"},
        options={"product_filters": ["Milch", "Kaffee", "Butter"]},
        entry_id="test_entry_id",
    )

    coordinator = NormaDataUpdateCoordinator(hass, entry)
    coordinator.data = {
        "discounts": [
            {
                "title": "Bio Vollmilch 3.8%",
                "base_price": "1 Liter",
                "price": "1,49 €",
                "picture": "https://norma.de/milch1.jpg",
                "valid_date": "2026-08-31",
                "category": "Molkereiprodukte",
            },
            {
                "title": "H-Milch 1.5%",
                "base_price": "1 Liter",
                "price": "1,19 €",
                "picture": "https://norma.de/milch2.jpg",
                "valid_date": "2026-08-31",
                "category": "Milch & mehr",
            },
            {
                "title": "Röstkaffee Espresso",
                "base_price": "500g Packung",
                "price": "5,99 €",
                "picture": "https://norma.de/kaffee.jpg",
                "valid_date": "2026-08-31",
                "category": "Kaffee & Tee",
            },
        ],
        "coupons": [],
        "valid_until": "2026-08-31",
        "last_success": "2026-08-12T12:00:00",
    }

    milch_sensor = NormaProductFilterSensor(coordinator, entry, "Milch")
    kaffee_sensor = NormaProductFilterSensor(coordinator, entry, "Kaffee")
    butter_sensor = NormaProductFilterSensor(coordinator, entry, "Butter")

    # Milch has 2 matches, best price 1,19 €
    assert milch_sensor.native_value == "1,19 €"
    milch_attrs = milch_sensor.extra_state_attributes
    assert milch_attrs["filter"] == "Milch"
    assert milch_attrs["on_sale"] is True
    assert milch_attrs["match_count"] == 2
    assert milch_attrs["best_price"] == "1,19 €"
    assert milch_attrs["product_title"] == "H-Milch 1.5%"
    assert milch_attrs["picture_link"] == "https://norma.de/milch2.jpg"
    assert len(milch_attrs["matches"]) == 2

    # Kaffee has 1 match
    assert kaffee_sensor.native_value == "5,99 €"
    kaffee_attrs = kaffee_sensor.extra_state_attributes
    assert kaffee_attrs["filter"] == "Kaffee"
    assert kaffee_attrs["on_sale"] is True
    assert kaffee_attrs["match_count"] == 1
    assert kaffee_attrs["best_price"] == "5,99 €"

    # Butter has 0 matches
    assert butter_sensor.native_value == "Nicht im Angebot"
    butter_attrs = butter_sensor.extra_state_attributes
    assert butter_attrs["filter"] == "Butter"
    assert butter_attrs["on_sale"] is False
    assert butter_attrs["match_count"] == 0
    assert butter_attrs["best_price"] is None
    assert butter_attrs["matches"] == []
