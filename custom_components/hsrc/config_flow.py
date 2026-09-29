from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType

from . import create_client
from .api import HsrcApiError, HsrcAuthError
from .const import DOMAIN

CREDENTIALS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): TextSelector(TextSelectorConfig(type=TextSelectorType.EMAIL)),
        vol.Required(CONF_PASSWORD): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
    }
)


class HsrcConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def _async_check_login(self, user_input: dict[str, Any]) -> str | None:
        try:
            await create_client(self.hass, user_input).async_login()
        except HsrcAuthError:
            return "invalid_auth"
        except (HsrcApiError, aiohttp.ClientError):
            return "cannot_connect"
        return None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_EMAIL].casefold())
            self._abort_if_unique_id_configured()
            if error := await self._async_check_login(user_input):
                errors["base"] = error
            else:
                return self.async_create_entry(title=user_input[CONF_EMAIL], data=user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(CREDENTIALS_SCHEMA, user_input),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            credentials = {**entry.data, CONF_PASSWORD: user_input[CONF_PASSWORD]}
            if error := await self._async_check_login(credentials):
                errors["base"] = error
            else:
                return self.async_update_reload_and_abort(entry, data=credentials)
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {vol.Required(CONF_PASSWORD): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))}
            ),
            description_placeholders={"email": entry.data[CONF_EMAIL]},
            errors=errors,
        )
