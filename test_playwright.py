from playwright.sync_api import sync_playwright

with sync_playwright() as p:

    browser = p.chromium.launch(headless=False)

    page = browser.new_page(viewport={"width": 1600, "height": 900})

    page.goto(
        "https://www.set.or.th/en/market/index/set/overview",
        wait_until="domcontentloaded"
    )

    # JavaScript Load ပြီးအောင် ၈ စက္ကန့်စောင့်
    page.wait_for_timeout(8000)

    # HTML သိမ်း
    with open("set_page.html", "w", encoding="utf-8") as f:
        f.write(page.content())

    # Screenshot သိမ်း
    page.screenshot(path="set_page.png", full_page=True)

    print("✅ HTML Saved -> set_page.html")
    print("✅ Screenshot Saved -> set_page.png")

    browser.close()