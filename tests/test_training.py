from datetime import date, datetime

from custom_components.hsrc.parsing import ListingRow, OrderItem, OrderSummary
from custom_components.hsrc.training import (
    BookedSession,
    ListedSession,
    build_booked_sessions,
    build_listed_sessions,
    find_next_session_day,
    find_sessions_to_add_to_basket,
    find_unbooked,
    read_early_session_day,
)


def build_listed(day: date, places_left: int = 10) -> ListedSession:
    return ListedSession(
        day,
        f"EARLY - Training - {day:%A %d %B}",
        f"E{day:%m%d}",
        places_left,
        f"https://hsrc.info/index.php?main_page=product_info&products_id={day:%m%d}",
    )


def build_booked(day: date) -> BookedSession:
    return BookedSession(day, f"EARLY - Training - {day:%A %d %B}", 1, 1)


class TestTraining:
    class TestReadEarlySessionDay:
        def test_reads_the_date_from_the_name(self):
            assert read_early_session_day("EARLY - Training - Monday 05 OCTOBER", date(2026, 9, 1)) == date(2026, 10, 5)

        def test_rolls_into_next_year_when_the_date_has_passed(self):
            day = read_early_session_day("EARLY - Training - Monday 04 JANUARY", date(2026, 12, 20))

            assert day == date(2027, 1, 4)

        def test_ignores_a_date_that_falls_on_another_weekday(self):
            assert read_early_session_day("EARLY - Training - Monday 06 OCTOBER", date(2026, 9, 1)) is None

        def test_ignores_late_and_dry_slope_sessions(self):
            assert read_early_session_day("LATE - Training - Monday 05 OCTOBER", date(2026, 9, 1)) is None
            assert read_early_session_day("DRY Slope Training - Friday 21 AUGUST - WELWYN", date(2026, 8, 1)) is None

    class TestBuildListedSessions:
        def test_keeps_only_early_sessions(self):
            rows = [
                ListingRow("OCT05E", "EARLY - Training - Monday 05 OCTOBER", 18, "https://example/5e"),
                ListingRow("OCT05L", "LATE - Training - Monday 05 OCTOBER", 4, "https://example/5l"),
            ]

            assert build_listed_sessions(rows, 2026) == [
                ListedSession(
                    date(2026, 10, 5), "EARLY - Training - Monday 05 OCTOBER", "OCT05E", 18, "https://example/5e"
                )
            ]

    class TestBuildBookedSessions:
        def test_dates_each_early_session_after_the_order(self):
            order = OrderSummary(46117, date(2026, 9, 7), "Paid")
            items = [
                OrderItem(1, "EARLY - Training - Monday 14 SEPTEMBER"),
                OrderItem(1, "DRY Slope Training - Friday 21 AUGUST - WELWYN"),
            ]

            assert build_booked_sessions(order, items) == [
                BookedSession(date(2026, 9, 14), "EARLY - Training - Monday 14 SEPTEMBER", 46117, 1)
            ]

        def test_skips_a_refunded_order(self):
            order = OrderSummary(45103, date(2026, 4, 27), "Refunded")

            assert build_booked_sessions(order, [OrderItem(1, "EARLY - Training - Monday 04 MAY")]) == []

    class TestFindUnbooked:
        def test_lists_upcoming_sessions_without_a_booking(self):
            listed = [build_listed(date(2026, 10, 5)), build_listed(date(2026, 10, 12))]

            unbooked = find_unbooked(listed, [build_booked(date(2026, 10, 5))], datetime(2026, 10, 2, 9))

            assert [session.day for session in unbooked] == [date(2026, 10, 12)]

        def test_keeps_tonights_session_until_it_ends(self):
            listed = [build_listed(date(2026, 10, 5))]

            assert find_unbooked(listed, [], datetime(2026, 10, 5, 19, 0)) == listed
            assert find_unbooked(listed, [], datetime(2026, 10, 5, 19, 30)) == []

    class TestFindNextSessionDay:
        def test_picks_the_earliest_upcoming_session_listed_or_booked(self):
            listed = [build_listed(date(2026, 10, 12))]
            booked = [build_booked(date(2026, 9, 28)), build_booked(date(2026, 10, 5))]

            assert find_next_session_day(listed, booked, datetime(2026, 10, 2, 9)) == date(2026, 10, 5)

        def test_is_none_when_nothing_is_upcoming(self):
            assert find_next_session_day([], [build_booked(date(2026, 9, 28))], datetime(2026, 10, 2, 9)) is None

    class TestFindSessionsToAddToBasket:
        def test_skips_booked_full_and_already_added_sessions(self):
            listed = [
                build_listed(date(2026, 10, 5)),
                build_listed(date(2026, 10, 12), places_left=0),
                build_listed(date(2026, 10, 19)),
                build_listed(date(2026, 10, 26)),
            ]

            sessions = find_sessions_to_add_to_basket(
                listed, [build_booked(date(2026, 10, 5))], {1019}, datetime(2026, 10, 2, 9)
            )

            assert [session.day for session in sessions] == [date(2026, 10, 26)]
