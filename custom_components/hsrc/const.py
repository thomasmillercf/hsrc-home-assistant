from datetime import time, timedelta

DOMAIN = "hsrc"

BASE_URL = "https://hsrc.info/index.php"
LOGIN_URL = f"{BASE_URL}?main_page=login"
HOME_URL = f"{BASE_URL}?main_page=index"
ORDER_HISTORY_URL = f"{BASE_URL}?main_page=account_history"
ORDER_URL = f"{BASE_URL}?main_page=account_history_info&order_id={{order_id}}"
BASKET_URL = f"{BASE_URL}?main_page=shopping_cart"

MEMBERSHIP_STATUS = "Full"

# Zen Cart starts no session for user agents on its spider list, redirecting login to cookie_usage instead.
BROWSER_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"

SCAN_INTERVAL = timedelta(days=7)

# https://hsrc.info/index.php?main_page=page&id=21 – the U12 group trains 6.00pm to 7.25pm.
EARLY_START = time(18, 0)
EARLY_END = time(19, 25)
