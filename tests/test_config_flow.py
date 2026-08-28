"""Tests for the Norma Offers & Coupons config flow."""

from unittest.mock import patch

from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.norma.const import (
    CONF_PASSWORD,
    CONF_STORE_ID,
    CONF_USERNAME,
    CONF_ZIP_CODE,
    DOMAIN,
)


async def test_flow_user_init(hass: HomeAssistant) -> None:
    """Test initial user step rendering."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_flow_user_missing_zip(hass: HomeAssistant) -> None:
    """Test user step with missing zip code."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ZIP_CODE: ""},
    )
    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "missing_zip"}


async def test_flow_user_search_and_select_store(hass: HomeAssistant) -> None:
    """Test user step search and store selection."""
    with patch(
        "custom_components.norma.api.NormaAPIClient.store_search",
        return_value=[
            {
                "id": "norma_123",
                "name": "NORMA Test Store",
                "street": "Teststraße 1",
                "zip": "80331",
                "city": "München",
            }
        ],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result_stores = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ZIP_CODE: "80331",
                CONF_USERNAME: "seitzf1@yahoo.de",
                CONF_PASSWORD: "testpassword",
            },
        )
        assert result_stores["type"] == data_entry_flow.FlowResultType.FORM
        assert result_stores["step_id"] == "select_store"

        result_entry = await hass.config_entries.flow.async_configure(
            result_stores["flow_id"],
            {CONF_STORE_ID: "norma_123"},
        )
        assert result_entry["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result_entry["data"][CONF_STORE_ID] == "norma_123"
        assert result_entry["data"][CONF_USERNAME] == "seitzf1@yahoo.de"


from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_options_flow(hass: HomeAssistant) -> None:
    """Test options flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="NORMA Test",
        data={CONF_STORE_ID: "norma_123"},
        options={},
        entry_id="test_entry_id",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"

    result_save = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"update_interval": 14, "product_filters": ["Milch", "Butter"]},
    )
    assert result_save["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result_save["data"]["update_interval"] == 14
    assert result_save["data"]["product_filters"] == ["Milch", "Butter"]
