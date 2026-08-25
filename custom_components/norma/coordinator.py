"""Data Update Coordinator for the Norma Offers & Coupons integration.

Anti-ban strategies (ported from ha-rewe):
- Random jitter delay (5–30 s) before each scheduled API request
- Domain-wide asyncio.Lock to serialise concurrent fetches
- Exponential backoff on 403/429 (up to 24 h)
- Restart-resistance: last_success persisted via HA Storage
"""

from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Any

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers import storage
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import NormaAPIClient
from .const import (
    ACCOUNT_KEY_SUFFIX,
    ATTR_BASE_PRICE,
    ATTR_CATEGORY,
    ATTR_DISCOUNT_PRICE,
    ATTR_DISCOUNT_TITLE,
    ATTR_PICTURE,
    ATTR_VALID_DATE,
    CONF_AUTO_ACTIVATE_COUPONS,
    CONF_PASSWORD,
    CONF_STORE_ID,
    CONF_UPDATE_INTERVAL,
    CONF_USERNAME,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    ISSUE_ID_CONNECTION,
    MIN_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class NormaDataUpdateCoordinator(DataUpdateCoordinator):
    """Manage fetching Norma offer & coupon data from the API."""

    config_entry: config_entries.ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: config_entries.ConfigEntry) -> None:
        config = {**entry.data, **entry.options}
        self.store_id: str = config[CONF_STORE_ID]
        self.username: str | None = config.get(CONF_USERNAME)
        self.password: str | None = config.get(CONF_PASSWORD)
        self.auto_activate_coupons: bool = config.get(CONF_AUTO_ACTIVATE_COUPONS, False)
        self.config_entry = entry

        # Account device identifiers (mirrors ha-lidl / ha-rewe pattern)
        self.account_key: str = f"{self.store_id}{ACCOUNT_KEY_SUFFIX}"
        self.account_configuration_url: str = (
            "https://www.norma-online.de/de/mein-konto/"
        )

        # Anti-ban state tracking
        self._backoff_until: datetime | None = None
        self._consecutive_failures: int = 0
        self._last_success: datetime | None = None
        self._issue_created: bool = False
        self._force_update: bool = False

        # HA persistent storage for restart-resistance
        self.store: storage.Store = storage.Store(hass, 1, f"{DOMAIN}_{self.store_id}")

        interval_hours = max(
            MIN_UPDATE_INTERVAL,
            config.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
        )
        interval_minutes = interval_hours * 60

        _LOGGER.debug(
            "Initializing Norma update coordinator for store %s (interval: %d h)",
            self.store_id,
            interval_hours,
        )

        self.configuration_url = (
            f"https://www.norma-online.de/de/angebote/?storeId={self.store_id}"
        )

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"Norma {self.store_id}",
            update_interval=timedelta(minutes=interval_minutes),
        )

    @property
    def is_data_valid(self) -> bool:
        """Return True if cached data is fresh and valid."""
        if not self.data or not self._last_success:
            return False

        now = dt_util.now()
        current_monday = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return self._last_success >= current_monday

    @property
    def has_account(self) -> bool:
        """Return True if user credentials are configured."""
        return bool(self.username and self.password)

    async def async_load_cache(self) -> None:
        """Load cached data from HA storage (restart-resistance)."""
        _LOGGER.debug(
            "Attempting to load cached Norma data for store %s", self.store_id
        )
        cache = await self.store.async_load()
        if cache:
            required_keys = {"discounts", "valid_until", "coupons"}
            if not required_keys.issubset(cache.keys()):
                _LOGGER.info(
                    "Norma cache for store %s is outdated – discarding", self.store_id
                )
                await self.store.async_remove()
                return

            _LOGGER.debug(
                "Successfully loaded cached Norma data for store %s", self.store_id
            )
            self.data = cache
            if "last_success" in cache:
                try:
                    self._last_success = dt_util.parse_datetime(cache["last_success"])
                except ValueError, TypeError:
                    self._last_success = None
        else:
            _LOGGER.debug("No cached Norma data found for store %s", self.store_id)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch offer data on schedule with anti-ban protections."""
        _LOGGER.debug(
            "Starting Norma update cycle for store %s (force_update=%s)",
            self.store_id,
            self._force_update,
        )

        # Backoff guard
        if (
            not self._force_update
            and self._backoff_until
            and dt_util.now() < self._backoff_until
        ):
            _LOGGER.debug(
                "Skipping Norma update for store %s – backoff active until %s",
                self.store_id,
                self._backoff_until,
            )
            return self.data

        # Restart resistance check
        if not self._force_update and self._last_success is not None:
            time_since = dt_util.now() - self._last_success
            effective_interval = self.update_interval or timedelta(
                hours=DEFAULT_UPDATE_INTERVAL
            )
            if time_since < (effective_interval - timedelta(minutes=5)):
                _LOGGER.info(
                    "Skipping Norma update for store %s: last success was %d min ago",
                    self.store_id,
                    int(time_since.total_seconds() / 60),
                )
                return self.data

        try:
            domain_data = self.hass.data.setdefault(DOMAIN, {})
            fetch_lock: asyncio.Lock = domain_data.setdefault(
                "fetch_lock", asyncio.Lock()
            )

            _LOGGER.debug(
                "Norma store %s: requesting domain-wide fetch lock", self.store_id
            )
            async with fetch_lock:
                _LOGGER.debug(
                    "Norma store %s: acquired domain-wide fetch lock", self.store_id
                )
                is_first_fetch = self._last_success is None
                if not self._force_update and not is_first_fetch:
                    jitter = random.uniform(5.0, 30.0)
                    _LOGGER.debug(
                        "Norma store %s: waiting %.1f s jitter before fetch",
                        self.store_id,
                        jitter,
                    )
                    await asyncio.sleep(jitter)
                elif is_first_fetch:
                    _LOGGER.debug(
                        "Norma store %s: first fetch – skipping jitter", self.store_id
                    )
                else:
                    self._force_update = False

                async with asyncio.timeout(90):
                    existing_cookies = self.config_entry.data.get("cookies", {})
                    data, new_cookies = await self.hass.async_add_executor_job(
                        self._fetch_sync, existing_cookies
                    )

            self._last_success = dt_util.now()
            self._consecutive_failures = 0
            data["last_success"] = self._last_success.isoformat()
            await self.store.async_save(data)

            if new_cookies != existing_cookies:
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data={**self.config_entry.data, "cookies": new_cookies},
                )

            if self._issue_created:
                ir.async_delete_issue(self.hass, DOMAIN, ISSUE_ID_CONNECTION)
                self._issue_created = False

            return data

        except Exception as err:
            self._consecutive_failures += 1
            _LOGGER.warning(
                "Norma store %s: fetch attempt failed (consecutive failures: %d): %s",
                self.store_id,
                self._consecutive_failures,
                err,
            )

            if (
                self._last_success
                and (dt_util.now() - self._last_success) > timedelta(hours=24)
                and not self._issue_created
            ):
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    ISSUE_ID_CONNECTION,
                    is_fixable=False,
                    severity=ir.IssueSeverity.WARNING,
                    translation_key="connection_error",
                    learn_more_url="https://github.com/FaserF/ha-norma/issues",
                )
                self._issue_created = True

            status = getattr(err, "status", None)
            err_str = str(err).lower()
            if status in (403, 429) or "403" in err_str or "429" in err_str:
                backoff_hours = min(24, self._consecutive_failures * 2)
                self._backoff_until = dt_util.now() + timedelta(hours=backoff_hours)
                _LOGGER.error(
                    "Norma store %s: rate-limited / blocked. Backing off %d h.",
                    self.store_id,
                    backoff_hours,
                )
            else:
                backoff_minutes = min(240, self._consecutive_failures * 30)
                self._backoff_until = dt_util.now() + timedelta(minutes=backoff_minutes)
                _LOGGER.error(
                    "Norma store %s: fetch error (failure #%d). Backing off %d min.",
                    self.store_id,
                    self._consecutive_failures,
                    backoff_minutes,
                )

            raise UpdateFailed(
                f"Error fetching Norma offers for store {self.store_id}: {err}"
            ) from err

    def _fetch_sync(
        self, cookies: dict[str, str]
    ) -> tuple[dict[str, Any], dict[str, str]]:
        """Fetch offers and user coupons synchronously in executor thread."""
        client = NormaAPIClient(
            username=self.username, password=self.password, cookies=cookies
        )
        if self.username and self.password:
            client.authenticate()

        raw_offers = client.get_offers(self.store_id)
        raw_coupons = client.get_coupons()

        parsed = self._parse_offers(raw_offers)
        parsed["coupons"] = raw_coupons
        parsed["is_authenticated"] = bool(client.auth_token)

        cookies = client.cookies if isinstance(client.cookies, dict) else {}
        return parsed, cookies

    async def async_activate_coupons(self) -> int:
        """Activate all available digital coupons for the user account."""
        _LOGGER.info("Requesting coupon activation for Norma store %s", self.store_id)
        client = NormaAPIClient(
            username=self.username,
            password=self.password,
            cookies=self.config_entry.data.get("cookies", {}),
        )
        activated_count = await self.hass.async_add_executor_job(
            client.activate_all_coupons
        )
        await self.async_request_refresh()
        return activated_count

    def _parse_offers(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Parse raw offer payload into Home Assistant structure."""
        discounts: list[dict[str, Any]] = []
        valid_until = raw.get("valid_until")

        for category in raw.get("categories", []):
            cat_title = category.get("title", "Angebote")
            for offer in category.get("offers", []):
                discounts.append(
                    {
                        ATTR_DISCOUNT_TITLE: offer.get("title", "").strip(),
                        ATTR_BASE_PRICE: offer.get("subtitle", "").strip(),
                        ATTR_DISCOUNT_PRICE: offer.get("price", "").strip(),
                        ATTR_PICTURE: offer.get("image"),
                        ATTR_VALID_DATE: valid_until,
                        ATTR_CATEGORY: cat_title,
                    }
                )

        return {
            "discounts": discounts,
            "valid_until": valid_until,
            "store_id": self.store_id,
        }
