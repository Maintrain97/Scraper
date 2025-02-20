from playwright.sync_api import sync_playwright

# URL to scrape
URL = 'https://app.utrsports.net/schools/785?t=2'
BASE_URL = 'https://app.utrsports.net'
EMAIL = "ianders@lisd.org"
password = input("Enter your UTR password: ")

player_info = {}  # Use a dictionary to ensure unique URLs

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # Navigate to login page
    page.goto('https://app.utrsports.net/login')

    # Fill in login credentials
    page.fill('#emailInput', EMAIL)
    page.fill('#passwordInput', password)

    # Click login button
    page.click('#myutr-app-body > div > div > div > div > div > div:nth-child(3) > form > div:nth-child(3) > button')

    # Wait for navigation to complete
    page.wait_for_url('https://app.utrsports.net/home')

    # Navigate to the roster page
    page.goto(URL)

    # Scroll to the bottom to ensure dynamic content loads
    previous_height = None
    while True:
        current_height = page.evaluate("document.body.scrollHeight")
        if previous_height == current_height:
            break
        previous_height = current_height
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)

    # Extract player profile links and names
    elements = page.locator("a[href*='/profiles/']").all()
    for element in elements:
        href = element.get_attribute('href')
        if href:
            full_url = BASE_URL + href
            name = element.inner_text().strip()
            name_parts = name.split()
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = " ".join(name_parts[1:])
                player_info[full_url] = f"{first_name} {last_name} {full_url}"

    browser.close()

# Write extracted player information to a file
with open('player_links.txt', 'w') as f:
    for info in sorted(player_info.values()):
        f.write(info + '\n')

print(f"Extracted {len(player_info)} unique players with names and links.")
