"""Tests for the Norma data update coordinator."""

from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.norma.const import CONF_STORE_ID, DOMAIN
from custom_components.norma.coordinator import NormaDataUpdateCoordinator


async def test_coordinator_update_data(hass: HomeAssistant) -> None:
    """Test coordinator data fetch."""
    entry = ConfigEntry(
        version=1,
        minor_version=0,
        domain=DOMAIN,
        title="NORMA Test Store",
        data={CONF_STORE_ID: "norma_123"},
        source="user",
        options={},
        entry_id="test_entry_id",
    )

    coordinator = NormaDataUpdateCoordinator(hass, entry)

    mock_offers = {
        "valid_until": "2026-08-18",
        "categories": [
            {
                "title": "Angebote",
                "offers": [
                    {
                        "title": "Bio Bananen",
                        "subtitle": "1 kg",
                        "price": "1.29 €",
                        "image": None,
                    }
                ],
            }
        ],
    }

    with (
        patch(
            "custom_components.norma.api.NormaAPIClient.get_offers",
            return_value=mock_offers,
        ),
        patch(
            "custom_components.norma.api.NormaAPIClient.get_coupons",
            return_value=[],
        ),
    ):
        data = await coordinator._async_update_data()
        assert len(data["discounts"]) == 1
        assert data["discounts"][0]["title"] == "Bio Bananen"
        assert data["valid_until"] == "2026-08-18"


async def test_coordinator_activate_coupons(hass: HomeAssistant) -> None:
    """Test coordinator activate coupons method."""
    entry = ConfigEntry(
        version=1,
        minor_version=0,
        domain=DOMAIN,
        title="NORMA Test Store",
        data={CONF_STORE_ID: "norma_123", "username": "test@user.de"},
        source="user",
        options={},
        entry_id="test_entry_id",
    )

    coordinator = NormaDataUpdateCoordinator(hass, entry)

    with (
        patch(
            "custom_components.norma.api.NormaAPIClient.activate_all_coupons",
            return_value=2,
        ),
        patch.object(coordinator, "async_request_refresh", new=AsyncMock()),
    ):
        count = await coordinator.async_activate_coupons()
        assert count == 2
