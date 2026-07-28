"""Async client for the private fraenk app API."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any
from urllib.parse import quote
from uuid import uuid4

from aiohttp import ClientError, ClientResponse, ClientSession

from .const import (
    API_BASE_URL,
    API_SCOPE,
    APP_DEVICE,
    APP_DEVICE_VENDOR,
    APP_OS_VERSION,
    APP_VERSION,
)

CORRELATION_SALT = b"pm9xVE8R22x9YqZbYrodrzYyJaUsUImGsM7h7n4e"


class FraenkError(Exception):
    """Base fraenk API exception."""


class FraenkConnectionError(FraenkError):
    """The fraenk API could not be reached."""


class FraenkAuthenticationError(FraenkError):
    """Authentication failed or expired."""


class FraenkMfaRequired(FraenkAuthenticationError):
    """The login requires an SMS mTAN."""

    def __init__(self, mfa_token: str) -> None:
        """Initialize the MFA challenge."""
        super().__init__("mfa_required")
        self.mfa_token = mfa_token


class FraenkMfaError(FraenkAuthenticationError):
    """The supplied mTAN was rejected."""


@dataclass(slots=True)
class FraenkTokens:
    """Tokens returned by the fraenk API."""

    access_token: str
    refresh_token: str
    customer_id: str


def _okhttp_quote(value: str) -> str:
    """Encode a form component like OkHttp FormBody."""
    # OkHttp leaves alphanumerics and -._* unchanged, uses + for a space and
    # percent-encodes the remaining UTF-8 bytes (including ~).
    return quote(value, safe="-._*").replace("%20", "+").replace("~", "%7E")


def build_form(fields: list[tuple[str, str]]) -> str:
    """Build an ordered OkHttp-compatible form body."""
    return "&".join(f"{_okhttp_quote(key)}={_okhttp_quote(value)}" for key, value in fields)


def build_correlation_id(body: str | None) -> str:
    """Build the X-App-Correlation-Id used by the Android app."""
    if not body:
        return str(uuid4())

    body_bytes = body.encode()
    if len(body_bytes) <= 64:
        okio_text = f"[text={body}]"
    else:
        prefix = body_bytes[:64].decode()
        okio_text = f"[size={len(body_bytes)} text={prefix}\u2026]"
    return hashlib.sha256(CORRELATION_SALT + okio_text.encode()).hexdigest()


class FraenkApi:
    """Client for the fraenk Android app backend."""

    def __init__(
        self,
        session: ClientSession,
        *,
        refresh_token: str | None = None,
        customer_id: str | None = None,
    ) -> None:
        """Initialize the client."""
        self._session = session
        self.refresh_token = refresh_token
        self.customer_id = customer_id
        self.access_token: str | None = None

    @staticmethod
    def _headers(body: str | None = None) -> dict[str, str]:
        """Return the Android app request headers."""
        return {
            "X-Tenant": "fraenk",
            "X-App-OS": "Android",
            "X-App-Device": APP_DEVICE,
            "X-App-Device-Vendor": APP_DEVICE_VENDOR,
            "X-App-OS-Version": APP_OS_VERSION,
            "X-App-Version": APP_VERSION,
            "X-App-Correlation-Id": build_correlation_id(body),
            "User-Agent": "okhttp/5.3.2",
        }

    async def _response_json(self, response: ClientResponse) -> dict[str, Any] | list[Any]:
        """Decode a response while retaining useful API errors."""
        text = await response.text()
        data: dict[str, Any] | list[Any] = {}
        if text:
            try:
                data = json.loads(text)
            except json.JSONDecodeError as err:
                raise FraenkError(f"Invalid API response (HTTP {response.status})") from err

        if response.status in (401, 403):
            raise FraenkAuthenticationError("Authentication expired")
        if response.status >= 400:
            error = data.get("error") if isinstance(data, dict) else None
            description = data.get("error_description") if isinstance(data, dict) else None
            if error == "mfa_required":
                token = data.get("mfa_token")
                if token:
                    raise FraenkMfaRequired(str(token))
            if error in {"wrong_mtan", "mfa_invalid_request", "mfa_already_requested"}:
                raise FraenkMfaError(str(description or error))
            if error in {"invalid_grant", "unauthorized", "invalid_token"}:
                raise FraenkAuthenticationError(str(description or error))
            raise FraenkError(str(description or error or f"HTTP {response.status}"))
        return data

    async def _post_form(
        self, path: str, fields: list[tuple[str, str]]
    ) -> dict[str, Any]:
        """POST an ordered form body."""
        body = build_form(fields)
        headers = self._headers(body)
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        try:
            async with self._session.post(
                API_BASE_URL + path,
                data=body,
                headers=headers,
            ) as response:
                data = await self._response_json(response)
        except FraenkError:
            raise
        except (ClientError, TimeoutError) as err:
            raise FraenkConnectionError from err
        if not isinstance(data, dict):
            raise FraenkError("Unexpected API response")
        return data

    def _apply_tokens(self, data: dict[str, Any]) -> FraenkTokens:
        """Apply an authentication response."""
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token") or self.refresh_token
        customer_id = data.get("customerId") or data.get("customer_id") or self.customer_id
        if not access_token or not refresh_token or not customer_id:
            raise FraenkAuthenticationError("Authentication response is incomplete")
        self.access_token = str(access_token)
        self.refresh_token = str(refresh_token)
        self.customer_id = str(customer_id)
        return FraenkTokens(self.access_token, self.refresh_token, self.customer_id)

    async def async_login(self, username: str, password: str) -> FraenkTokens:
        """Log in with username and password."""
        data = await self._post_form(
            "v13/login",
            [
                ("grant_type", "password"),
                ("username", username),
                ("password", password),
                ("scope", API_SCOPE),
            ],
        )
        return self._apply_tokens(data)

    async def async_login_mfa(
        self, username: str, password: str, mtan: str, mfa_token: str
    ) -> FraenkTokens:
        """Finish a login using the SMS mTAN."""
        data = await self._post_form(
            "v13/login-with-mfa",
            [
                ("username", username),
                ("password", password),
                ("mtan", mtan),
                ("mfa_token", mfa_token),
            ],
        )
        return self._apply_tokens(data)

    async def async_refresh_access_token(self) -> FraenkTokens:
        """Refresh the access token."""
        if not self.refresh_token:
            raise FraenkAuthenticationError("No refresh token")
        data = await self._post_form(
            "v13/refresh",
            [("refresh_token", self.refresh_token), ("scope", API_SCOPE)],
        )
        return self._apply_tokens(data)

    async def _get(self, path: str) -> dict[str, Any] | list[Any]:
        """GET an authenticated API resource."""
        if not self.access_token:
            await self.async_refresh_access_token()
        headers = self._headers()
        headers["Authorization"] = f"Bearer {self.access_token}"
        try:
            async with self._session.get(
                API_BASE_URL + path,
                headers=headers,
            ) as response:
                if response.status in (401, 403):
                    await response.read()
                    await self.async_refresh_access_token()
                    headers = self._headers()
                    headers["Authorization"] = f"Bearer {self.access_token}"
                    async with self._session.get(
                        API_BASE_URL + path, headers=headers
                    ) as retry:
                        return await self._response_json(retry)
                return await self._response_json(response)
        except FraenkError:
            raise
        except (ClientError, TimeoutError) as err:
            raise FraenkConnectionError from err

    async def async_get_consumption(self) -> list[dict[str, Any]]:
        """Return consumption passes for all contracts."""
        if not self.customer_id:
            raise FraenkAuthenticationError("No customer ID")
        contracts_data = await self._get(
            f"v13/customers/{quote(self.customer_id, safe='')}/contracts"
        )
        contracts = contracts_data if isinstance(contracts_data, list) else []
        result: list[dict[str, Any]] = []
        for contract_index, contract in enumerate(contracts):
            if not isinstance(contract, dict):
                continue
            contract_id = contract.get("id") or contract.get("contractId")
            if not contract_id:
                continue
            consumption = await self._get(
                "v13/customers/"
                f"{quote(self.customer_id, safe='')}/contracts/"
                f"{quote(str(contract_id), safe='')}/dataconsumption"
            )
            if not isinstance(consumption, dict):
                continue
            passes = consumption.get("passes")
            if not isinstance(passes, list):
                passes = [consumption]
            for pass_index, data_pass in enumerate(passes):
                if not isinstance(data_pass, dict):
                    continue
                result.append(
                    {
                        **data_pass,
                        "_contract_id": str(contract_id),
                        "_contract_index": contract_index,
                        "_pass_index": pass_index,
                    }
                )
        return result

