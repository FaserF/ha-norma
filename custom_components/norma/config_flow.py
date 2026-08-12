"""Config flow for Norma Offers & Coupons integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .api import NormaAPIClient
from .const import (
    CONF_CITY,
    CONF_PASSWORD,
    CONF_STORE_ID,
    CONF_STORE_NAME,
    CONF_STREET,
    CONF_UPDATE_INTERVAL,
    CONF_USERNAME,
    CONF_ZIP_CODE,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MIN_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class NormaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Norma."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow."""
        self._stores: list[dict[str, Any]] = []
        self._credentials: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Step 1: Optional Login credentials & ZIP code search."""
        errors: dict[str, str] = {}

        if user_input is not None:
            zip_code = user_input.get(CONF_ZIP_CODE, "").strip()
            username = user_input.get(CONF_USERNAME, "").strip()
            password = user_input.get(CONF_PASSWORD, "").strip()

            if username and password:
                self._credentials = {
                    CONF_USERNAME: username,
                    CONF_PASSWORD: password,
                }

            if not zip_code:
                errors["base"] = "missing_zip"
            else:
                client = NormaAPIClient(username=username, password=password)
                stores = await self.hass.async_add_executor_job(
                    client.store_search, zip_code
                )

                if not stores:
                    errors["base"] = "no_stores_found"
                else:
                    self._stores = stores
                    return await self.async_step_select_store()

        schema = vol.Schema(
            {
                vol.Required(CONF_ZIP_CODE): str,
                vol.Optional(CONF_USERNAME): str,
                vol.Optional(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_select_store(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Step 2: Select store from search results."""
        errors: dict[str, str] = {}

        if user_input is not None:
            store_id = user_input[CONF_STORE_ID]
            selected = next(
                (s for s in self._stores if str(s.get("id")) == str(store_id)), None
            )
            if selected:
                await self.async_set_unique_id(str(store_id))
                self._abort_if_unique_id_configured()

                title = selected.get("name") or f"NORMA Store {store_id}"
                data = {
                    CONF_STORE_ID: str(store_id),
                    CONF_STORE_NAME: title,
                    CONF_ZIP_CODE: selected.get("zip", ""),
                    CONF_CITY: selected.get("city", ""),
                    CONF_STREET: selected.get("street", ""),
                    **self._credentials,
                }
                return self.async_create_entry(title=title, data=data)

        store_options = {
            str(
                s.get("id")
            ): f"{s.get('name', 'NORMA')} - {s.get('street', '')}, {s.get('zip', '')} {s.get('city', '')}"
            for s in self._stores
        }

        schema = vol.Schema({vol.Required(CONF_STORE_ID): vol.In(store_options)})

        return self.async_show_form(
            step_id="select_store",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get options flow."""
        return NormaOptionsFlowHandler()


class NormaOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for Norma."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage integration options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self.config_entry.options.get(
            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
        )

        schema = vol.Schema(
            {
                vol.Optional(CONF_UPDATE_INTERVAL, default=current_interval): vol.All(
                    vol.Coerce(int), vol.Range(min=MIN_UPDATE_INTERVAL)
                )
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )
