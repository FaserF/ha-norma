<div align="center">
  <h1>NORMA Offers & Coupons (for Home Assistant) 🛒</h1>
  <p><strong>A secure, robust Home Assistant integration that fetches weekly offers, discounts, and optional user digital coupons for your local NORMA store directly from NORMA endpoints.</strong></p>

  [![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://hacs.xyz)
  [![Downloads (Current release)](https://img.shields.io/github/downloads/FaserF/ha-norma/latest/norma.zip?label=Downloads%20(Current%20release)&style=for-the-badge)](https://github.com/FaserF/ha-norma/releases)
  [![GitHub Release](https://img.shields.io/github/v/release/FaserF/ha-norma?style=for-the-badge)](https://github.com/FaserF/ha-norma/releases)
  [![License](https://img.shields.io/github/license/FaserF/ha-norma?style=for-the-badge)](LICENSE)
</div>

---

## 🧭 Quick Links

| | | | |
| :--- | :--- | :--- | :--- |
| [✨ Features](#-features) | [📦 Installation](#-installation) | [⚙️ Configuration](#️-configuration) | [🛠️ Options](#️-options-flow) |
| [🧑‍💻 Development](#-development) | [💖 Credits](#-credits--acknowledgements) | [📄 License](#-license) | |

### Why use this integration?
Instead of scraping HTML or using broken workarounds, this integration connects to NORMA endpoints using `curl_cffi` for realistic browser impersonation. It fetches structured weekly offers data, valid dates, and optionally authenticates with your user account to track active coupons.

It groups all sensors under a single NORMA store device and implements advanced lock-serialisation, random jitter delays, and backoffs to prevent rate limits and anti-bot bans.

## ✨ Features

- **🛒 Detailed Offers & Coupons Sensors**:
  - **Weekly Offers**: Current week's discounted items count, with attributes detailing titles, base prices, active discount prices, categories, and direct links to product images.
  - **Active Coupons**: Available digital coupons and discount codes (when optional user login is enabled).
  - **Valid Until**: Date string indicating when the current weekly offers cycle ends.
- **🔐 Optional User Account Login**:
  - Store search and offer fetching works **100% anonymously**.
  - Optionally enter email & password to track personal digital coupons.
- **🛡️ Rate-Limiting & Anti-Ban Protections**:
  - **Lock Queueing**: A domain-wide `asyncio.Lock` ensures concurrent updates run sequentially.
  - **Random Jitter**: Introduces a 5–30 second delay between scheduled requests.
  - **Restart-Resistance**: Saves parsed data to HA storage cache to survive HA reboots without unnecessary API calls.
  - **Exponential Backoff**: Backs off for up to 24 hours on 403 or 429 errors.
  - **Browser Impersonation**: Uses `curl_cffi` for anti-fingerprinting.
- **⚙️ Device-Based Grouping**:
  - All sensors and button entities are automatically grouped under a main NORMA Store device.
  - Includes a **Force Update** button entity to trigger manual refreshes on demand.
- **🔍 Diagnostic Downloads**:
  - Full support for Home Assistant UI Diagnostics. Redacts credentials, tokens, and cookies automatically.

## ❤️ Support This Project

> I maintain this integration in my **free time alongside my regular job**.
>
> **This project is and will always remain 100% free.**
>
> Donations are completely voluntary — but they help me stay motivated and dedicate more time to maintaining open-source tools!

<div align="center">

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor%20on-GitHub-%23EA4AAA?style=for-the-badge&logo=github-sponsors&logoColor=white)](https://github.com/sponsors/FaserF)&nbsp;&nbsp;
[![PayPal](https://img.shields.io/badge/Donate%20via-PayPal-%2300457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/FaserF)

</div>

## 📦 Installation

### HACS (Recommended)

This integration is fully compatible with [HACS](https://hacs.xyz/).

1. Open HACS in Home Assistant.
2. Click on the three dots in the top right corner and select **Custom repositories**.
3. Add `FaserF/ha-norma` with category **Integration**.
4. Search for "NORMA Offers & Coupons".
5. Install and restart Home Assistant.

[![Open HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=FaserF&repository=ha-norma&category=integration)

### Manual Installation

1. Download the latest release zip file.
2. Extract the `custom_components/norma` folder into your Home Assistant's `custom_components` directory.
3. Restart Home Assistant.

## ⚙️ Configuration

1. Navigate to **Settings > Devices & Services** in Home Assistant.
2. Click **Add Integration** and search for **NORMA Offers & Coupons**.
3. Enter your ZIP code to search for nearby NORMA stores.
4. (Optional) Enter your NORMA user email and password if you want to track digital coupons.
5. Select your store from the list and submit.

## 🛠️ Options Flow

You can customize the update interval:

1. Go to **Settings > Devices & Services**.
2. Find **NORMA Offers & Coupons** and click **Configure**.
3. Set the **Update Interval** in hours (default is 24 hours, minimum is 12 hours).

## 🛒 Other Supermarket Integrations

- [REWE Discounts](https://github.com/FaserF/ha-rewe)
- [Lidl Offers](https://github.com/FaserF/ha-lidl)
- [EDEKA Offers](https://github.com/FaserF/ha-edeka)
- [Aldi Offers](https://github.com/FaserF/ha-aldi)

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
