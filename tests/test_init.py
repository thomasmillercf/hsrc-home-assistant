import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.hsrc.const import DOMAIN

from .fixture_loader import load_fixture

INDEX = "https://hsrc.info/index.php"


def mock_site(aioclient_mock: AiohttpClientMocker, login_response: str = "home.html") -> None:
    aioclient_mock.get(f"{INDEX}?main_page=login", text=load_fixture("login.html"))
    aioclient_mock.post(f"{INDEX}?main_page=login&action=process", text=load_fixture(login_response))
    aioclient_mock.get(f"{INDEX}?main_page=index&cPath=225", text=load_fixture("october.html"))
    aioclient_mock.get(f"{INDEX}?main_page=index&cPath=227", text=load_fixture("december.html"))
    aioclient_mock.get(f"{INDEX}?main_page=index", text=load_fixture("home.html"))
    for order_id in (46117, 45103):
        aioclient_mock.get(
            f"{INDEX}?main_page=account_history_info&order_id={order_id}",
            text=load_fixture(f"order_{order_id}.html"),
        )
    aioclient_mock.get(f"{INDEX}?main_page=account_history", text=load_fixture("order_history.html"))


async def set_up_entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, data={"email": "me@example.com", "password": "secret"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


class TestHsrcIntegration:
    @pytest.fixture(autouse=True)
    async def friday_before_training(self, hass, freezer):
        await hass.config.async_set_time_zone("Europe/London")
        freezer.move_to("2026-10-02T09:00:00+01:00")

    async def test_reports_the_next_session_as_booked(self, hass, aioclient_mock):
        mock_site(aioclient_mock)

        await set_up_entry(hass)

        state = hass.states.get("binary_sensor.hsrc_next_early_session_booked")
        assert state.state == "on"
        assert state.attributes["date"] == "2026-10-05"
        assert state.attributes["places_left"] == 18

    async def test_counts_listed_sessions_that_are_not_booked(self, hass, aioclient_mock):
        mock_site(aioclient_mock)

        await set_up_entry(hass)

        state = hass.states.get("sensor.hsrc_unbooked_early_sessions")
        assert state.state == "2"
        assert [session["date"] for session in state.attributes["sessions"]] == ["2026-10-12", "2026-12-28"]
        assert state.attributes["sessions"][0]["url"] == (
            "https://hsrc.info/index.php?main_page=product_info&cPath=225&products_id=1567"
        )

    async def test_reports_when_the_next_booked_session_starts(self, hass, aioclient_mock):
        mock_site(aioclient_mock)

        await set_up_entry(hass)

        assert hass.states.get("sensor.hsrc_next_booked_early_session").state == "2026-10-05T17:00:00+00:00"

    async def test_shows_booked_sessions_on_the_calendar(self, hass, aioclient_mock):
        mock_site(aioclient_mock)

        await set_up_entry(hass)

        state = hass.states.get("calendar.hsrc_early_training")
        assert state.attributes["start_time"] == "2026-10-05 18:00:00"
        assert state.attributes["end_time"] == "2026-10-05 19:25:00"

    async def test_asks_to_sign_in_again_when_the_password_is_rejected(self, hass, aioclient_mock):
        mock_site(aioclient_mock, login_response="login_failed.html")

        entry = await set_up_entry(hass)

        assert entry.state is ConfigEntryState.SETUP_ERROR
        assert [flow["context"]["source"] for flow in hass.config_entries.flow.async_progress()] == ["reauth"]
