"""Minimal client for sending SMS via the web interface of an AVM FRITZ!Box.

Based on pyfritzsms 0.1.4 by Marc Hörsken (https://github.com/mback2k/pyfritzsms,
Apache License 2.0), vendored into this integration and extended:

- login via PBKDF2 (challenge version 2) with MD5 fallback for old FRITZ!OS versions
- dedicated exception classes instead of bare RuntimeError/KeyError
- tolerant JSON parsing (FRITZ!OS does not always send application/json)
"""

from __future__ import annotations

import asyncio
import hashlib
from typing import Any
from xml.etree import ElementTree

from aiohttp import ClientError, ClientSession
import pyotp

DATA_URL = "http://{}/data.lua"
LOGIN_URL = "http://{}/login_sid.lua"
TWOFACTOR_URL = "http://{}/twofactor.lua"

INVALID_SID = "0000000000000000"


class FritzBoxError(Exception):
    """Base error of the FRITZ!Box SMS client."""


class FritzBoxConnectionError(FritzBoxError):
    """FRITZ!Box not reachable or unexpected HTTP response."""


class FritzBoxAuthError(FritzBoxError):
    """Login failed (username/password) or session expired."""


class FritzBoxTwoFactorError(FritzBoxError):
    """Second factor (TOTP) not configured, not valid or not accepted."""


class FritzBoxSmsError(FritzBoxError):
    """SMS could not be sent or deleted."""


def _pbkdf2_response(challenge: str, password: str) -> str:
    """Calculate the response for a version 2 (PBKDF2) challenge."""
    _, iter1, salt1, iter2, salt2 = challenge.split("$")
    hash1 = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt1), int(iter1)
    )
    hash2 = hashlib.pbkdf2_hmac("sha256", hash1, bytes.fromhex(salt2), int(iter2))
    return f"{salt2}${hash2.hex()}"


def _md5_response(challenge: str, password: str) -> str:
    """Calculate the response for a legacy (MD5) challenge."""
    md5hash = hashlib.md5(  # noqa: S324 - required by the legacy FRITZ!OS protocol
        (challenge + "-" + password).encode("utf-16le")
    ).hexdigest()
    return f"{challenge}-{md5hash}"


class FritzBox:
    """Session against the FRITZ!Box web interface."""

    def __init__(self, host: str, session: ClientSession) -> None:
        self._host = host
        self._session = session
        self._sid = ""
        self._otp: pyotp.TOTP | None = None
        # one session per box: serialise parallel sends (several notify targets)
        self.lock = asyncio.Lock()

    @property
    def logged_in(self) -> bool:
        """Return True if a session is open."""
        return bool(self._sid)

    def set_otp(self, otp_secret: str) -> None:
        """Set the TOTP secret (plaintext, base32)."""
        self._otp = pyotp.TOTP(otp_secret)

    def get_otp(self) -> str:
        """Return the current TOTP code."""
        if not self._otp:
            raise FritzBoxTwoFactorError("TOTP secret is not set")
        return self._otp.now()

    async def _request(
        self, method: str, url: str, *, xml: bool = False, **kwargs: Any
    ) -> Any:
        """Execute a request and return parsed XML or JSON."""
        try:
            async with self._session.request(
                method, url.format(self._host), **kwargs
            ) as response:
                if response.status != 200:
                    raise FritzBoxConnectionError(
                        f"Unexpected response from FRITZ!Box: HTTP {response.status}"
                    )
                if xml:
                    return ElementTree.fromstring(await response.text())
                data = await response.json(content_type=None)
        except (ClientError, TimeoutError) as err:
            raise FritzBoxConnectionError(f"FRITZ!Box not reachable: {err}") from err
        except (ValueError, ElementTree.ParseError) as err:
            # HTML login page instead of JSON -> session invalid
            raise FritzBoxAuthError("Invalid response, session expired?") from err
        if isinstance(data, dict) and "sid" in data:
            self._sid = data["sid"]
        return data

    async def _data(self, url: str, **fields: Any) -> dict[str, Any]:
        """POST to a FRITZ!Box page with the current session."""
        return await self._request("POST", url, data={"sid": self._sid, **fields})

    async def login(self, username: str, password: str) -> str:
        """Open a session (PBKDF2, MD5 fallback)."""
        tree = await self._request(
            "GET", LOGIN_URL, xml=True, params={"version": "2"}
        )
        challenge = tree.findtext("Challenge") or ""
        if challenge.startswith("2$"):
            # 2 x PBKDF2 with up to several 10k iterations -> do not block the event loop
            response = await asyncio.get_running_loop().run_in_executor(
                None, _pbkdf2_response, challenge, password
            )
        else:
            response = _md5_response(challenge, password)

        tree = await self._request(
            "POST",
            LOGIN_URL,
            xml=True,
            data={"username": username, "response": response},
            params={"version": "2"},
        )
        sid = tree.findtext("SID") or INVALID_SID
        if sid == INVALID_SID:
            block = tree.findtext("BlockTime") or "0"
            raise FritzBoxAuthError(
                f"Login failed (wrong username or password, block time {block} s)"
            )
        self._sid = sid
        return sid

    async def logout(self) -> None:
        """Close the session; errors are ignored."""
        if not self._sid:
            return
        try:
            await self._request(
                "GET",
                LOGIN_URL,
                xml=True,
                params={"sid": self._sid, "logout": "1"},
            )
        except FritzBoxError:
            pass
        finally:
            self._sid = ""

    async def _twofactor(self, **fields: Any) -> dict[str, Any]:
        return await self._data(TWOFACTOR_URL, no_sidrenew="", **fields)

    async def is_otp_configured(self) -> bool:
        """Return True if app-based 2FA (TOTP) is configured for the user."""
        data = await self._twofactor(tfa_googleauth_info="")
        try:
            return bool(data["googleauth"]["isConfigured"])
        except (KeyError, TypeError) as err:
            raise FritzBoxAuthError("Unexpected 2FA info response") from err

    async def list_sms(self) -> list[dict[str, Any]]:
        """Return the SMS list."""
        data = await self._data(DATA_URL, page="smsList")
        try:
            return data["data"]["smsListData"]["messages"]
        except (KeyError, TypeError) as err:
            raise FritzBoxSmsError("Unexpected SMS list response") from err

    async def delete_sms(self, sms_id: int | str) -> None:
        """Delete an SMS from the list (e.g. the sent message)."""
        data = await self._data(DATA_URL, page="smsList", messageId=sms_id, delete="")
        if (data.get("data") or {}).get("delete") != "ok":
            raise FritzBoxSmsError("SMS could not be deleted")

    async def send_sms(self, number: str, message: str) -> str | bool:
        """Send an SMS; return the uid of the sent message (or True)."""
        base = {"page": "smsSendMsg", "recipient": number, "newMessage": message}

        # initial request to send SMS
        data = await self._data(DATA_URL, **base, apply="true")
        result = data.get("data") or {}
        if "new_uid" not in result:
            return True

        # second factor required via TOTP
        new_uid = result["new_uid"]
        data = await self._data(DATA_URL, **base, new_uid=new_uid, second_apply="")
        if (data.get("data") or {}).get("second_apply") != "twofactor":
            raise FritzBoxTwoFactorError("FRITZ!Box did not ask for the second factor")

        # check if TOTP is configured and available
        data = await self._twofactor(tfa_googleauth_info="")
        auth = data.get("googleauth") or {}
        if not auth.get("isConfigured"):
            raise FritzBoxTwoFactorError("TOTP is not configured for this user")
        if not auth.get("isAvailable"):
            raise FritzBoxTwoFactorError("TOTP is not available")

        # send TOTP
        data = await self._twofactor(tfa_googleauth=self.get_otp())
        if data.get("err") != 0:
            raise FritzBoxTwoFactorError("TOTP code was not accepted")

        # check if TOTP is active and done
        data = await self._twofactor(tfa_active="")
        if not data.get("active") or not data.get("done"):
            raise FritzBoxTwoFactorError("Second factor was not completed")

        # finally send SMS again
        data = await self._data(
            DATA_URL,
            **base,
            new_uid=new_uid,
            second_apply="",
            confirmed="",
            twofactor="",
        )
        if (data.get("data") or {}).get("second_apply") != "ok":
            raise FritzBoxSmsError("SMS was not confirmed by the FRITZ!Box")
        return new_uid
