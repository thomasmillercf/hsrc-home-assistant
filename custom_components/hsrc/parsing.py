from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from urllib.parse import parse_qs, urlsplit

from bs4 import BeautifulSoup, Tag

TRAINING_CATEGORY = re.compile(r"^[A-Z]+ TRAINING (?P<year>\d{4})$")
STOCK = re.compile(r"In Stock:\s*(?P<places>-?\d+)")
ORDER_NUMBER = re.compile(r"Order Number:\s*(?P<order_id>\d+)")
ORDER_STATUS = re.compile(r"Order Status:\s*(?P<status>[A-Za-z ]+?)\s*$", re.MULTILINE)
ORDER_DATE = re.compile(r"Order Date:\s*(?P<placed_on>\w+ \d{1,2} \w+, \d{4})")
QUANTITY = re.compile(r"(?P<quantity>\d+)\s*x")


class HsrcParseError(Exception):
    pass


@dataclass(frozen=True)
class LoginForm:
    action: str
    fields: dict[str, str]


@dataclass(frozen=True)
class AddToBasketForm:
    action: str
    fields: dict[str, str]


@dataclass(frozen=True)
class TrainingCategory:
    title: str
    year: int
    url: str


@dataclass(frozen=True)
class ListingRow:
    code: str
    name: str
    places_left: int
    url: str


@dataclass(frozen=True)
class OrderSummary:
    order_id: int
    placed_on: date
    status: str


@dataclass(frozen=True)
class OrderItem:
    quantity: int
    name: str


def to_https(url: str) -> str:
    return url.replace("http://", "https://", 1)


def read_product_id(url: str) -> int | None:
    product_ids = parse_qs(urlsplit(url).query).get("products_id")
    return int(product_ids[0].split(":")[0]) if product_ids else None


def read_option_label(page: BeautifulSoup, option: Tag) -> str:
    label = page.find("label", attrs={"for": option.get("id")}) if option.get("id") else None
    return label.get_text(strip=True).split("(")[0].strip() if label else ""


def parse_login_form(html: str) -> LoginForm:
    form = BeautifulSoup(html, "html.parser").select_one("form[name=loginForm]")
    if form is None:
        raise HsrcParseError("No login form on the login page")
    fields = {field["name"]: field.get("value", "") for field in form.find_all("input") if field.get("name")}
    return LoginForm(action=to_https(form["action"]), fields=fields)


def is_logged_in(html: str) -> bool:
    return "main_page=logoff" in html


def parse_login_error(html: str) -> str | None:
    error = BeautifulSoup(html, "html.parser").select_one(".messageStackError")
    return error.get_text(" ", strip=True) if error else None


def parse_training_categories(html: str) -> list[TrainingCategory]:
    categories: dict[str, TrainingCategory] = {}
    for link in BeautifulSoup(html, "html.parser").select("a[href*=cPath]"):
        title = link.get_text(strip=True)
        if match := TRAINING_CATEGORY.match(title):
            categories[title] = TrainingCategory(title=title, year=int(match["year"]), url=to_https(link["href"]))
    return list(categories.values())


def parse_listing(html: str) -> list[ListingRow]:
    rows: list[ListingRow] = []
    for row in BeautifulSoup(html, "html.parser").select("tr.productListing-odd, tr.productListing-even"):
        cells = row.find_all("td")
        title = row.select_one(".itemTitle a")
        stock = STOCK.search(cells[1].get_text(" ", strip=True)) if len(cells) > 1 else None
        if title is None or stock is None:
            continue
        rows.append(
            ListingRow(
                code=cells[0].get_text(strip=True),
                name=title.get_text(strip=True),
                places_left=int(stock["places"]),
                url=to_https(title["href"]),
            )
        )
    return rows


def parse_order_history(html: str) -> list[OrderSummary]:
    orders: list[OrderSummary] = []
    for card in BeautifulSoup(html, "html.parser").select("div.card[id^=order][id$=-card]"):
        text = card.get_text("\n", strip=True)
        order_number = ORDER_NUMBER.search(text)
        status = ORDER_STATUS.search(text)
        placed_on = ORDER_DATE.search(" ".join(text.split()))
        if not (order_number and status and placed_on):
            continue
        orders.append(
            OrderSummary(
                order_id=int(order_number["order_id"]),
                placed_on=datetime.strptime(placed_on["placed_on"], "%A %d %B, %Y").date(),
                status=status["status"],
            )
        )
    return orders


def read_product_name(cell: Tag) -> str:
    return " ".join(text.strip() for text in cell.find_all(string=True, recursive=False) if text.strip())


def parse_order_items(html: str) -> list[OrderItem]:
    items: list[OrderItem] = []
    for row in BeautifulSoup(html, "html.parser").select("#orderHistory-orderTableDisplay tr"):
        quantity_cell = row.select_one("td.qtyCell")
        product_cell = row.select_one("td.productCell")
        if quantity_cell is None or product_cell is None:
            continue
        quantity = QUANTITY.search(quantity_cell.get_text(strip=True))
        if quantity is None:
            continue
        items.append(OrderItem(quantity=int(quantity["quantity"]), name=read_product_name(product_cell)))
    return items


def parse_add_to_basket_form(html: str, membership_status: str) -> AddToBasketForm:
    page = BeautifulSoup(html, "html.parser")
    form = page.select_one("form[name=cart_quantity]")
    if form is None:
        raise HsrcParseError("No add-to-basket form on the product page")
    fields = {field["name"]: field.get("value", "") for field in form.select("input[type=hidden]") if field.get("name")}
    for option in form.select("input[type=radio]"):
        if read_option_label(page, option).casefold() == membership_status.casefold():
            fields[option["name"]] = option["value"]
            break
    else:
        raise HsrcParseError(f"No {membership_status} membership option on the product page")
    return AddToBasketForm(action=to_https(form["action"]), fields=fields)


def parse_basket_product_ids(html: str) -> set[int]:
    return {
        int(field["value"].split(":")[0])
        for field in BeautifulSoup(html, "html.parser").select('input[name="products_id[]"]')
        if field.get("value")
    }
