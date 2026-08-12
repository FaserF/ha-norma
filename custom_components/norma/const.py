"""Constants for the Norma Offers & Coupons integration."""

from typing import Final

DOMAIN: Final = "norma"
ATTRIBUTION: Final = "Data provided by NORMA Web API"

# Configuration keys
CONF_STORE_ID: Final = "store_id"
CONF_ZIP_CODE: Final = "zip_code"
CONF_CITY: Final = "city"
CONF_STREET: Final = "street"
CONF_STORE_NAME: Final = "store_name"
CONF_UPDATE_INTERVAL: Final = "update_interval"
CONF_USERNAME: Final = "username"
CONF_PASSWORD: Final = "password"
CONF_AUTO_ACTIVATE_COUPONS: Final = "auto_activate_coupons"

# Account device identifier suffix
ACCOUNT_KEY_SUFFIX: Final = "_account"

# Defaults & limits
DEFAULT_UPDATE_INTERVAL: Final = 24  # hours
MIN_UPDATE_INTERVAL: Final = 12  # hours

# Attributes
ATTR_DISCOUNT_TITLE: Final = "title"
ATTR_DISCOUNT_PRICE: Final = "price"
ATTR_BASE_PRICE: Final = "base_price"
ATTR_PICTURE: Final = "picture"
ATTR_VALID_DATE: Final = "valid_date"
ATTR_CATEGORY: Final = "category"
ATTR_COUPON_CODE: Final = "code"
ATTR_DISCOUNT_VALUE: Final = "discount_value"

# Repair issue IDs
ISSUE_ID_CONNECTION: Final = "connection_error"
ISSUE_ID_AUTH: Final = "auth_error"
