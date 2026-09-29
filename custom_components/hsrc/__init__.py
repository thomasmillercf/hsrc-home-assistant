from __future__ import annotations

import aiohttp
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import HsrcApiError, HsrcAuthError, HsrcClient
from .coordinator import HsrcConfigEntry, HsrcCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.CALENDAR, Platform.SENSOR]


def create_client(hass: HomeAssistant, entry_data: dict) -> HsrcClient:
    return HsrcClient(
        async_create_clientsession(hass, cookie_jar=aiohttp.CookieJar()),
        entry_data[CONF_EMAIL],
        entry_data[CONF_PASSWORD],
    )


async def async_setup_entry(hass: HomeAssistant, entry: HsrcConfigEntry) -> bool:
    client = create_client(hass, dict(entry.data))
    try:
        await client.async_login()
    except HsrcAuthError as error:
        raise ConfigEntryAuthFailed(str(error)) from error
    except (HsrcApiError, aiohttp.ClientError) as error:
        raise ConfigEntryNotReady(str(error)) from error

    coordinator = HsrcCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: HsrcConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
