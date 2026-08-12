from unittest.mock import AsyncMock

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.norma.button import (
    NormaActivateCouponsButton,
    NormaForceUpdateButton,
)
from custom_components.norma.const import CONF_STORE_ID, DOMAIN
from custom_components.norma.coordinator import NormaDataUpdateCoordinator


async def test_button_presses(hass: HomeAssistant) -> None:
    """Test button entity presses."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="NORMA Test",
        data={CONF_STORE_ID: "norma_123", "username": "test@user.de"},
        options={},
        entry_id="test_entry_id",
    )

    coordinator = NormaDataUpdateCoordinator(hass, entry)
    coordinator.async_request_refresh = AsyncMock()
    coordinator.async_activate_coupons = AsyncMock()

    force_btn = NormaForceUpdateButton(coordinator, entry)
    activate_btn = NormaActivateCouponsButton(coordinator, entry)

    await force_btn.async_press()
    assert coordinator._force_update is True
    coordinator.async_request_refresh.assert_called_once()

    await activate_btn.async_press()
    coordinator.async_activate_coupons.assert_called_once()
