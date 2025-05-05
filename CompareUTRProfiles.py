# Quick and dirty code to get some info for regional tournament.
# Not all logic is working or optimized,
# but it gets the job I needed done

from playwright.sync_api import sync_playwright
import time

UTR_LOGIN_URL = "https://app.utrsports.net/login"
PLAYER_URLS = [
    "https://app.utrsports.net/profiles/1552490?t=2",
    "https://app.utrsports.net/profiles/1307252",
    # Add more player URLs here if needed
]

EMAIL = input("Enter UTR Email: ")
PASSWORD = input("Enter UTR Password: ")


def get_opponents_from_profile(page, profile_url, game_type="singles"):
    page.goto(profile_url, wait_until="domcontentloaded")
    page.wait_for_selector("text=Results")
    opponents = set()

    # Toggle game type (singles or doubles)
    switch_event_type(page, game_type)

    # Scroll to load more results if needed
    for _ in range(5):
        page.mouse.wheel(0, 500)
        time.sleep(1)

    matches = page.query_selector_all("a[href*='/profiles/']")  # opponent links
    for match in matches:
        name = match.inner_text().strip()
        if name:
            opponents.add(name)

    return opponents


def switch_event_type(page, event_type: str) -> bool:
    """Switch between singles and doubles views efficiently."""
    event_type = event_type.lower()
    
    # Get current selection
    current_selection = page.locator("div.popovermenu-anchor.resultsTab__anchorClass__PGL2O.pl8 h6").first.inner_text().strip().lower()
    
    if event_type not in current_selection:
        # Click to open the dropdown
        page.locator("div.popovermenu-anchor.resultsTab__anchorClass__PGL2O.pl8").first.click()

        # Wait for the dropdown options to be rendered
        page.wait_for_selector(f"#item{event_type}.menu-item")

        # Click the correct menu item (e.g., #itemdoubles)
        page.locator(f"#item{event_type}.menu-item").click()

        # Wait for the results section to update — adjust this to something on the page that changes
        page.wait_for_timeout(1000)  # Or better: wait for a selector that updates
        return True
    
    return False


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        # Login
        page.goto(UTR_LOGIN_URL, wait_until="domcontentloaded")  # or "networkidle"
        page.wait_for_selector("#emailInput")  # ensures form is ready
        print("Filling login form...")
        page.fill("#emailInput", EMAIL)
        page.fill("#passwordInput", PASSWORD)
        page.click("button.btn.btn-primary.btn-xl.btn-block")
        page.wait_for_selector("text=My Ratings")  # or whatever element appears after login
        print("Login successful!")

        # Dictionary to store opponents for each player
        players_opponents = {}

        for url in PLAYER_URLS:
            player_name = url.split("/")[-1].split("?")[0]  # Assuming the last part of the URL is the player identifier
            print(f"Getting opponents for {player_name}...")
            opponents = get_opponents_from_profile(page, url, game_type="doubles")  # Use "doubles" here if needed
            players_opponents[player_name] = opponents

        # Check if the two players have played each other
        player_1, player_2 = list(players_opponents.keys())

        player_1_opponents = players_opponents.get(player_1, set())
        player_2_opponents = players_opponents.get(player_2, set())

        if player_2 in player_1_opponents and player_1 in player_2_opponents:
            print(f"\n🎾 {player_1} and {player_2} have played each other!")
        else:
            print(f"\n🎾 {player_1} and {player_2} have not played each other.")

        # Find common opponents among all players
        common_opponents = set.intersection(*players_opponents.values())

        print("\n🎾 Common Opponents across all players:")
        if common_opponents:
            for name in common_opponents:
                print(f"- {name}")
        else:
            print("No common opponents found.")

        browser.close()


if __name__ == "__main__":
    main()
