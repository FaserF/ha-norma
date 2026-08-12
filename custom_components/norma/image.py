"""Image platform for the Norma Offers & Coupons integration."""

from __future__ import annotations

import hashlib
import io
import logging
from typing import Any

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import NormaDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Norma image entities from a config entry."""
    coordinator: NormaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    if entry.data.get("username"):
        async_add_entities([NormaLoyaltyCardQrImage(hass, coordinator, entry)])


class NormaLoyaltyCardQrImage(CoordinatorEntity[NormaDataUpdateCoordinator], ImageEntity):
    """Represents the Norma loyalty customer card QR code image entity."""

    _attr_icon = "mdi:qrcode-scan"
    _attr_has_entity_name = True
    _attr_translation_key = "loyalty_card_qr"

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: NormaDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize loyalty card QR image entity."""
        CoordinatorEntity.__init__(self, coordinator)
        ImageEntity.__init__(self, hass)

        self._attr_unique_id = f"{entry.entry_id}_loyalty_card_qr"
        self._attr_access_token = hashlib.sha256(
            self._attr_unique_id.encode()
        ).hexdigest()[:32]

        store_name = str(entry.data.get("store_name") or entry.data.get("store_id") or "Filiale")
        device_name = store_name if store_name.upper().startswith("NORMA") else f"NORMA {store_name}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=device_name,
            manufacturer="NORMA",
            model="Filiale & Angebote",
            configuration_url=coordinator.configuration_url,
        )
        self._cached_png: bytes | None = None
        self._cached_id: str | None = None

    @property
    def loyalty_id(self) -> str | None:
        """Return loyalty customer card ID from coordinator data."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("loyalty_id", f"NORMA-{self.coordinator.username}")

    @property
    def available(self) -> bool:
        """Return True if coordinator has data and user is authenticated."""
        return self.coordinator.data is not None and bool(
            self.coordinator.data.get("is_authenticated")
        )

    def _generate_qr_png(self, text: str) -> bytes:
        """Generate high-contrast PNG bytes of QR code for checkout scanner."""
        import qrcode

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=12,
            border=4,
        )
        qr.add_data(text)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    async def async_image(self) -> bytes | None:
        """Return bytes of loyalty card QR code image."""
        lid = self.loyalty_id
        if not lid:
            return None

        if self._cached_png is None or self._cached_id != lid:
            self._cached_png = await self.hass.async_add_executor_job(
                self._generate_qr_png, lid
            )
            self._cached_id = lid
            self._attr_image_last_updated = dt_util.now()

        return self._cached_png
