"""Config flow for Norma Offers & Coupons integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .api import NormaAPIClient
from .const import (
    CONF_AUTO_ACTIVATE_COUPONS,
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
        self._stores: list[dict[str, Any]] = []
        self._credentials: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Step 1: ZIP code search + optional credentials."""
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
        return NormaOptionsFlowHandler(config_entry)


class NormaOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for Norma — mirrors ha-lidl / ha-rewe pattern."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Main options step: update interval + action selector."""
        if user_input is not None:
            action = user_input.get("action", "save")
            if action == "login":
                return await self.async_step_login()
            if action == "logout":
                new_data = {
                    k: v
                    for k, v in self._config_entry.data.items()
                    if k not in (CONF_USERNAME, CONF_PASSWORD)
                }
                self.hass.config_entries.async_update_entry(
                    self._config_entry, data=new_data
                )
                return self.async_create_entry(
                    title="", data=self._config_entry.options
                )

            # action == "save": persist update_interval
            new_options = {
                **self._config_entry.options,
                CONF_UPDATE_INTERVAL: user_input.get(
                    CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                ),
                CONF_AUTO_ACTIVATE_COUPONS: user_input.get(
                    CONF_AUTO_ACTIVATE_COUPONS, False
                ),
            }
            return self.async_create_entry(title="", data=new_options)

        current_interval = self._config_entry.options.get(
            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
        )
        current_auto_activate = self._config_entry.options.get(
            CONF_AUTO_ACTIVATE_COUPONS, False
        )
        has_account = bool(
            self._config_entry.data.get(CONF_USERNAME)
            and self._config_entry.data.get(CONF_PASSWORD)
        )
        action_choices = {"save": "Save", "login": "Configure Account"}
        if has_account:
            action_choices["logout"] = "Remove Account"

        schema = vol.Schema(
            {
                vol.Optional(CONF_UPDATE_INTERVAL, default=current_interval): vol.All(
                    vol.Coerce(int), vol.Range(min=MIN_UPDATE_INTERVAL)
                ),
                vol.Optional(
                    CONF_AUTO_ACTIVATE_COUPONS, default=current_auto_activate
                ): bool,
                vol.Required("action", default="save"): vol.In(action_choices),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)

    async def async_step_login(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Configure username & password for account features."""
        if user_input is not None:
            username = user_input.get(CONF_USERNAME, "").strip()
            password = user_input.get(CONF_PASSWORD, "").strip()
            # Write credentials directly into entry.data so coordinator picks them up
            new_data = {
                **self._config_entry.data,
                CONF_USERNAME: username,
                CONF_PASSWORD: password,
            }
            self.hass.config_entries.async_update_entry(
                self._config_entry, data=new_data
            )
            new_options = {**self._config_entry.options, **user_input}
            return self.async_create_entry(title="", data=new_options)

        current_username = self._config_entry.options.get(
            CONF_USERNAME,
            self._config_entry.data.get(CONF_USERNAME, ""),
        )
        current_password = self._config_entry.options.get(
            CONF_PASSWORD,
            self._config_entry.data.get(CONF_PASSWORD, ""),
        )
        current_auto_activate = self._config_entry.options.get(
            CONF_AUTO_ACTIVATE_COUPONS, False
        )

        schema = vol.Schema(
            {
                vol.Optional(CONF_USERNAME, default=current_username): str,
                vol.Optional(CONF_PASSWORD, default=current_password): str,
                vol.Optional(
                    CONF_AUTO_ACTIVATE_COUPONS, default=current_auto_activate
                ): bool,
            }
        )

        return self.async_show_form(step_id="login", data_schema=schema)
