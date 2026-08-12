from custom_components.norma.binary_sensor import (
    NormaLoginStatusBinarySensor,
    NormaOffersAvailableBinarySensor,
)
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.norma.const import CONF_STORE_ID, DOMAIN
from custom_components.norma.coordinator import NormaDataUpdateCoordinator


async def test_binary_sensors_state(hass: HomeAssistant) -> None:
    """Test binary sensor on/off states."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="NORMA Test",
        data={CONF_STORE_ID: "norma_123", "username": "test@user.de"},
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
