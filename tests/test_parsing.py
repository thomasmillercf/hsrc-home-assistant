from datetime import date

import pytest

from custom_components.hsrc.parsing import (
    HsrcParseError,
    ListingRow,
    LoginForm,
    OrderItem,
    OrderSummary,
    TrainingCategory,
    is_logged_in,
    parse_listing,
    parse_login_error,
    parse_login_form,
    parse_order_history,
    parse_order_items,
    parse_training_categories,
)

from .fixture_loader import load_fixture


class TestParsing:
    def test_reads_the_login_form_rather_than_the_sign_up_form(self):
        assert parse_login_form(load_fixture("login.html")) == LoginForm(
            action="https://hsrc.info/index.php?main_page=login&action=process",
            fields={"securityToken": "the-token", "email_address": "", "password": ""},
        )

    def test_rejects_a_page_without_a_login_form(self):
        with pytest.raises(HsrcParseError):
            parse_login_form("<html></html>")

    def test_treats_a_log_out_link_as_signed_in(self):
        assert is_logged_in(load_fixture("home.html"))
        assert not is_logged_in(load_fixture("login_failed.html"))

    def test_reads_the_login_error(self):
        assert parse_login_error(load_fixture("login_failed.html")) == (
            "Error: Sorry, there is no match for that email address and/or password."
        )

    def test_finds_each_training_category_once_over_https(self):
        assert parse_training_categories(load_fixture("home.html")) == [
            TrainingCategory("OCTOBER TRAINING 2026", 2026, "https://hsrc.info/index.php?main_page=index&cPath=225"),
            TrainingCategory("DECEMBER TRAINING 2026", 2026, "https://hsrc.info/index.php?main_page=index&cPath=227"),
        ]

    def test_reads_every_listed_product_with_its_places_left(self):
        assert parse_listing(load_fixture("october.html")) == [
            ListingRow(
                "Mem27_FULL",
                "HSRC MEMBERSHIP - 2026/2027",
                0,
                "https://hsrc.info/index.php?main_page=product_info&cPath=225&products_id=1555",
            ),
            ListingRow(
                "OCT05E",
                "EARLY - Training - Monday 05 OCTOBER",
                18,
                "https://hsrc.info/index.php?main_page=product_info&cPath=225&products_id=1565",
            ),
            ListingRow(
                "OCT05L",
                "LATE - Training - Monday 05 OCTOBER",
                4,
                "https://hsrc.info/index.php?main_page=product_info&cPath=225&products_id=1566",
            ),
            ListingRow(
                "OCT12E",
                "EARLY - Training - Monday 12 OCTOBER",
                0,
                "https://hsrc.info/index.php?main_page=product_info&cPath=225&products_id=1567",
            ),
        ]

    def test_reads_each_order_with_its_status_and_date(self):
        assert parse_order_history(load_fixture("order_history.html")) == [
            OrderSummary(46117, date(2026, 9, 7), "Paid"),
            OrderSummary(45103, date(2026, 4, 27), "Refunded"),
        ]

    def test_reads_order_items_without_their_attributes(self):
        assert parse_order_items(load_fixture("order_46117.html")) == [
            OrderItem(1, "EARLY - Training - Monday 05 OCTOBER"),
            OrderItem(1, "DRY Slope Training - Friday 21 AUGUST - WELWYN"),
        ]
