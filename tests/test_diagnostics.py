from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.norma.const import CONF_STORE_ID, DOMAIN
from custom_components.norma.coordinator import NormaDataUpdateCoordinator
from custom_components.norma.diagnostics import async_get_config_entry_diagnostics


async def test_diagnostics(hass: HomeAssistant) -> None:
    """Test diagnostics data redaction."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="NORMA Test",
        data={
            CONF_STORE_ID: "norma_123",
            "username": "secret@user.de",
            "password": "secretpassword",
        },
        options={},
        entry_id="test_entry_id",
    )

    coordinator = NormaDataUpdateCoordinator(hass, entry)
    coordinator.data = {"discounts": [], "cookies": {"session": "secret"}}

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["config_entry"]["data"]["username"] == "**REDACTED**"
    assert diag["config_entry"]["data"]["password"] == "**REDACTED**"
    assert (
        "cookies" not in diag["coordinator"]["data"]
        or diag["coordinator"]["data"]["cookies"] == "**REDACTED**"
    )
