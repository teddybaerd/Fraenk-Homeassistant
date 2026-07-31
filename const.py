"""Constants for the fraenk Mobile integration."""

from datetime import timedelta

DOMAIN = "fraenk_mobile"
NAME = "fraenk Mobile"

CONF_CUSTOMER_ID = "customer_id"
CONF_REFRESH_TOKEN = "refresh_token"

DEFAULT_SCAN_INTERVAL = timedelta(minutes=30)

API_BASE_URL = "https://app.fraenk.de/fraenk-rest-service/app/"
API_SCOPE = "app permanent"
APP_VERSION = "2.0.0"

# The API expects plausible Android app headers. They do not identify the HA host.
APP_DEVICE = "SM-S928B"
APP_DEVICE_VENDOR = "samsung"
APP_OS_VERSION = "16"

