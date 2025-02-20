from playwright.sync_api import sync_playwright

base_url = "https://app.utrsports.net"
EMAIL = "ianders@lisd.org"
password = input("Enter ianders UTR password: ")
tournament = input("Which tournament: ")

# VARSITY = ['Aarush', 'Nathaniel', 'Cole']
VARSITY = [
    "Sydney",
    "Jasmine",
    "Anna",
    "Sophie",
    "Lucy",
    "Olivia",
    "Olivia",
    "Madalynn",
    "Leah",
    "Erika",
    "Audry",
    "Cole",
    "Aarush",
    "Nathaniel",
    "Jaden",
    "Kaden",
    "Sebasti�n",
    "Jessetyler",
    "Cohen",
    "Joe",
]
JV = [
    "Aaira",
    "Aidan",
    "Erika",
    "Ethan",
    "Gunnar",
    "Ishan",
    "Joe",
    "Juan",
    "Kingston",
    "Moses",
    "Reya",
    "Ryan",
    "Sana",
    "Sarah",
    "Sasha",
    "Audry",
    "Adan",
]
tournament_results = []

# Read player URLs from file
with open("player_links.txt", "r") as f:
    profile_data = [line.strip().split() for line in f.readlines()]

# Filter out Pre-Freshmen and get profile URLs
profile_urls = [
    data[-1]
    for data in profile_data
    if data[-2].lower() != "pre-freshman" and data[0] in JV
]


def scrape_matches(event_block, profile_url, tournament_name):
    """Extracts match results only from the correct tournament."""
    match_cards = event_block.locator(".utr-card.score-card").all()
    for match in match_cards:
        try:
            # Get all player names from the desktop view for each team
            team1_players = (
                match.locator(".d-none.d-md-block .team")
                .nth(0)
                .locator(".player-details a.flex-column.player-name")
                .all()
            )
            team2_players = (
                match.locator(".d-none.d-md-block .team")
                .nth(1)
                .locator(".player-details a.flex-column.player-name")
                .all()
            )

            # Join the names for each team
            team_1_names = "/".join(
                [player.inner_text().strip() for player in team1_players]
            )
            team_2_names = "/".join(
                [player.inner_text().strip() for player in team2_players]
            )

            score_items = match.locator(".score-item").all()
            for i in range(len(score_items)):
                score_items[i] = score_items[i].inner_text().strip()

            # Format the match scores
            # Divison by 4 needed to exclude desktop copy of scores
            set_scores = ""
            for i in range(len(score_items) // 4):
                tb = []
                if len(score_items[i]) > 1:
                    tb.append(int(score_items[i][1:]))
                set_scores += score_items[i][0]
                set_scores += "-"
                if len(score_items[int(i + len(score_items) * (1 / 4))]) > 1:
                    tb.append(int(score_items[int(i + len(score_items) * (1 / 4))][1:]))
                set_scores += score_items[int(i + len(score_items) * (1 / 4))][0]

                if len(tb) > 0:
                    set_scores += f"({str(min(tb))})"

                set_scores += " "
            result_line = f". {team_1_names} vs {team_2_names} {set_scores}"

            if result_line not in tournament_results:
                tournament_results.append(result_line)

        except Exception as match_error:
            print(
                f"Error processing match for {profile_url} in {tournament_name}: {match_error}"
            )


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    # Navigate to login page
    page.goto("https://app.utrsports.net/login")
    page.fill("#emailInput", EMAIL)
    page.fill("#passwordInput", password)
    page.click(
        "#myutr-app-body > div > div > div > div > div > div:nth-child(3) > form > div:nth-child(3) > button"
    )
    page.wait_for_url("https://app.utrsports.net/home")

    # Visit each player's profile and extract tournament results
    for profile_url in profile_urls:
        page.goto(profile_url)
        page.wait_for_timeout(2000)

        # Ensure we are starting on Singles
        current_selection = (
            page.locator("div.popovermenu-anchor.resultsTab__anchorClass__PGL2O.pl8 h6")
            .first.inner_text()
            .strip()
            .lower()
        )
        if "singles" not in current_selection:
            dropdown_anchor = page.locator(
                "div.popovermenu-anchor.resultsTab__anchorClass__PGL2O.pl8"
            ).first
            dropdown_anchor.click()
            page.locator("div#itemsingles.menu-item").click()
            page.wait_for_timeout(2000)

        found_results = False

        # In your main loop where you're processing events
        event_blocks = page.locator("div.eventItem__eventItem__2Xpsd").all()
        for event in event_blocks:
            try:
                tournament_name = (
                    event.locator(
                        ".eventItem__eventName__6hntZ span:not(.eventItem__middleDot__1ttwt)"
                    )
                    .inner_text()
                    .strip()
                )
                if tournament.lower() in tournament_name.lower():
                    # Pass the event block instead of the page
                    scrape_matches(event, profile_url, tournament_name)
                    found_results = True
            except Exception as e:
                print(f"Error processing event for {profile_url}: {e}")

        # If no SINGLES results, check DOUBLES
        if not found_results:
            try:
                current_selection = (
                    page.locator(
                        "div.popovermenu-anchor.resultsTab__anchorClass__PGL2O.pl8 h6"
                    )
                    .first.inner_text()
                    .strip()
                    .lower()
                )
                if "doubles" not in current_selection:
                    dropdown_anchor = page.locator(
                        "div.popovermenu-anchor.resultsTab__anchorClass__PGL2O.pl8"
                    ).first
                    dropdown_anchor.click()
                    page.locator("div#itemdoubles.menu-item").click()
                    page.wait_for_timeout(2000)

                    # In your main loop where you're processing events
                    event_blocks = page.locator("div.eventItem__eventItem__2Xpsd").all()
                    for event in event_blocks:
                        try:
                            tournament_name = (
                                event.locator(
                                    ".eventItem__eventName__6hntZ span:not(.eventItem__middleDot__1ttwt)"
                                )
                                .inner_text()
                                .strip()
                            )
                            if tournament.lower() in tournament_name.lower():
                                # Pass the event block instead of the page
                                scrape_matches(event, profile_url, tournament_name)
                        except Exception as e:
                            print(f"Error processing event for {profile_url}: {e}")

            except Exception as e:
                print(f"Error switching to doubles for {profile_url}: {e}")

    browser.close()


# Write tournament results to a file
with open("tournament_results.txt", "w") as f:
    f.write(tournament + "\n")
    for result in tournament_results:
        f.write(result + "\n")

print(f"Extracted {len(tournament_results)} tournament results.")
