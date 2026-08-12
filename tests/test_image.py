"""Tests for the Norma image platform (Loyalty Card QR Code)."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.norma.const import DOMAIN, CONF_STORE_ID
from custom_components.norma.coordinator import NormaDataUpdateCoordinator
from custom_components.norma.image import NormaLoyaltyCardQrImage


async def test_loyalty_card_qr_image(hass: HomeAssistant) -> None:
    """Test loyalty card QR code image entity generation."""
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
        "is_authenticated": True,
        "loyalty_id": "NORMA-12345678",
    }

    img_entity = NormaLoyaltyCardQrImage(hass, coordinator, entry)

    assert img_entity.loyalty_id == "NORMA-12345678"
    assert img_entity.available is True

    png_bytes = await img_entity.async_image()
    assert png_bytes is not None
    assert len(png_bytes) > 0
    assert png_bytes.startswith(b"\x89PNG")
