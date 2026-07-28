"""Config flow for fraenk Mobile."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    FraenkApi,
    FraenkAuthenticationError,
    FraenkConnectionError,
    FraenkError,
    FraenkMfaError,
    FraenkMfaRequired,
    FraenkTokens,
)
from .const import CONF_CUSTOMER_ID, CONF_REFRESH_TOKEN, DOMAIN

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)
STEP_MFA_SCHEMA = vol.Schema({vol.Required("mtan"): str})


class FraenkConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for fraenk Mobile."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self._username = ""
        self._password = ""
        self._mfa_token = ""

    def _api(self) -> FraenkApi:
        """Create an API client."""
        return FraenkApi(async_get_clientsession(self.hass))

    async def _finish(
        self, tokens: FraenkTokens, *, reauth: bool = False
    ) -> ConfigFlowResult:
        """Create or update the config entry."""
        data = {
            CONF_USERNAME: self._username,
            CONF_REFRESH_TOKEN: tokens.refresh_token,
            CONF_CUSTOMER_ID: tokens.customer_id,
        }
        if reauth:
            entry = self._get_reauth_entry()
            await self.async_set_unique_id(self._username.casefold())
            self._abort_if_unique_id_mismatch(reason="wrong_account")
            return self.async_update_reload_and_abort(
                entry,
                data_updates=data,
            )

        await self.async_set_unique_id(self._username.casefold())
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=f"fraenk ({self._username})", data=data)

    async def _login(
        self, user_input: dict[str, Any], *, reauth: bool
    ) -> ConfigFlowResult:
        """Handle username/password login."""
        self._username = user_input[CONF_USERNAME].strip()
        self._password = user_input[CONF_PASSWORD]
        errors: dict[str, str] = {}
        try:
            tokens = await self._api().async_login(self._username, self._password)
        except FraenkMfaRequired as err:
            self._mfa_token = err.mfa_token
            return await self.async_step_reauth_mfa() if reauth else await self.async_step_mfa()
        except FraenkAuthenticationError:
            errors["base"] = "invalid_auth"
        except FraenkConnectionError:
            errors["base"] = "cannot_connect"
        except FraenkError:
            errors["base"] = "unknown"
        else:
            return await self._finish(tokens, reauth=reauth)

        step_id = "reauth_confirm" if reauth else "user"
        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME, default=self._username): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )
        return self.async_show_form(step_id=step_id, data_schema=schema, errors=errors)

    async def _mfa(
        self, user_input: dict[str, Any], *, reauth: bool
    ) -> ConfigFlowResult:
        """Handle an mTAN."""
        errors: dict[str, str] = {}
        try:
            tokens = await self._api().async_login_mfa(
                self._username,
                self._password,
                user_input["mtan"].strip(),
                self._mfa_token,
            )
        except FraenkMfaError:
            errors["base"] = "invalid_mtan"
        except FraenkAuthenticationError:
            errors["base"] = "invalid_auth"
        except FraenkConnectionError:
            errors["base"] = "cannot_connect"
        except FraenkError:
            errors["base"] = "unknown"
        else:
            self._password = ""
            return await self._finish(tokens, reauth=reauth)
        return self.async_show_form(
            step_id="reauth_mfa" if reauth else "mfa",
            data_schema=STEP_MFA_SCHEMA,
            errors=errors,
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is not None:
            return await self._login(user_input, reauth=False)
        return self.async_show_form(step_id="user", data_schema=STEP_USER_SCHEMA)

    async def async_step_mfa(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle SMS MFA."""
        if user_input is not None:
            return await self._mfa(user_input, reauth=False)
        return self.async_show_form(step_id="mfa", data_schema=STEP_MFA_SCHEMA)

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Start reauthentication."""
        self._username = entry_data[CONF_USERNAME]
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm reauthentication credentials."""
        if user_input is not None:
            return await self._login(user_input, reauth=True)
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME, default=self._username): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
        )

    async def async_step_reauth_mfa(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Finish reauthentication with an mTAN."""
        if user_input is not None:
            return await self._mfa(user_input, reauth=True)
        return self.async_show_form(step_id="reauth_mfa", data_schema=STEP_MFA_SCHEMA)
