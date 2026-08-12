from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.norma.const import CONF_STORE_ID, DOMAIN
from custom_components.norma.coordinator import NormaDataUpdateCoordinator
from custom_components.norma.image import NormaLoyaltyCardQrImage


async def test_loyalty_card_qr_image(hass: HomeAssistant) -> None:
    """Test loyalty card QR code image entity generation."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="NORMA Test",
        data={CONF_STORE_ID: "norma_123", "username": "test@user.de"},
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
