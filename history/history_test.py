from playwright.sync_api import sync_playwright

URL = "https://www.set.or.th/en/market/index/set/overview"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)

    page = browser.new_page()

    page.goto(URL, wait_until="networkidle")

    print("Title:", page.title())

    print("\n========== BODY ==========")

    print(page.locator("body").inner_text())

    print("==========================")

    input("Press Enter...")

    browser.close()