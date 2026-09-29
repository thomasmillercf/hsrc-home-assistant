from __future__ import annotations

import aiohttp

from .const import BASKET_URL, BROWSER_USER_AGENT, HOME_URL, LOGIN_URL, MEMBERSHIP_STATUS, ORDER_HISTORY_URL, ORDER_URL
from .parsing import (
    HsrcParseError,
    OrderItem,
    OrderSummary,
    is_logged_in,
    parse_add_to_basket_form,
    parse_basket_product_ids,
    parse_listing,
    parse_login_error,
    parse_login_form,
    parse_order_history,
    parse_order_items,
    parse_training_categories,
)
from .training import ListedSession, build_listed_sessions

HEADERS = {"User-Agent": BROWSER_USER_AGENT}


class HsrcApiError(Exception):
    pass


class HsrcAuthError(HsrcApiError):
    pass


class HsrcClient:
    def __init__(self, session: aiohttp.ClientSession, email: str, password: str) -> None:
        self._session = session
        self._email = email
        self._password = password

    async def _async_fetch(self, url: str) -> str:
        async with self._session.get(url, headers=HEADERS) as response:
            if response.status >= 400:
                raise HsrcApiError(f"GET {url} returned {response.status}")
            return await response.text()

    async def async_login(self) -> None:
        try:
            form = parse_login_form(await self._async_fetch(LOGIN_URL))
        except HsrcParseError as error:
            raise HsrcApiError(str(error)) from error
        fields = {**form.fields, "email_address": self._email, "password": self._password}
        async with self._session.post(form.action, data=fields, headers=HEADERS) as response:
            html = await response.text()
        if not is_logged_in(html):
            raise HsrcAuthError(parse_login_error(html) or "hsrc.info did not accept the login")

    async def _async_fetch_signed_in(self, url: str) -> str:
        html = await self._async_fetch(url)
        if is_logged_in(html):
            return html
        await self.async_login()
        html = await self._async_fetch(url)
        if not is_logged_in(html):
            raise HsrcAuthError("hsrc.info signed us out straight after logging in")
        return html

    async def async_get_listed_sessions(self) -> list[ListedSession]:
        sessions: list[ListedSession] = []
        for category in parse_training_categories(await self._async_fetch(HOME_URL)):
            rows = parse_listing(await self._async_fetch(category.url))
            sessions.extend(build_listed_sessions(rows, category.year))
        return sessions

    async def async_get_orders(self) -> list[OrderSummary]:
        return parse_order_history(await self._async_fetch_signed_in(ORDER_HISTORY_URL))

    async def async_get_order_items(self, order_id: int) -> list[OrderItem]:
        return parse_order_items(await self._async_fetch_signed_in(ORDER_URL.format(order_id=order_id)))

    async def async_get_basket_product_ids(self) -> set[int]:
        return parse_basket_product_ids(await self._async_fetch_signed_in(BASKET_URL))

    async def async_add_to_basket(self, product_url: str) -> None:
        try:
            form = parse_add_to_basket_form(await self._async_fetch_signed_in(product_url), MEMBERSHIP_STATUS)
        except HsrcParseError as error:
            raise HsrcApiError(str(error)) from error
        async with self._session.post(form.action, data=form.fields, headers=HEADERS) as response:
            if response.status >= 400:
                raise HsrcApiError(f"Adding {product_url} to the basket returned {response.status}")
