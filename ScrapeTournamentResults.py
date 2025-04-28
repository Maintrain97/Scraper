from playwright.sync_api import sync_playwright
import re
from collections import defaultdict

base_url = "https://app.utrsports.net"
EMAIL = "ianders@lisd.org"
password = input("Enter ianders UTR password: ")
tournament_input = input("Which tournament: ")
tournament = tournament_input.lower()

# Ask user to specify the tournament type
tournament_type = input("Tournament type (VARSITY, JV, or BOTH): ").upper()
while tournament_type not in ["VARSITY", "JV", "BOTH"]:
    print("Invalid tournament type. Please enter VARSITY, JV, or BOTH.")
    tournament_type = input("Tournament type (VARSITY, JV, or BOTH): ").upper()

# Player lists
VARSITY = [
    "Sydney", "Jasmine", "Anna", "Sophie", "Lucy", "Olivia",
    "Madalynn", "Leah", "Erika", "Audry", "Cole", "Aarush", "Nathaniel",
    "Jaden", "Kaden", "Sebastián", "Jessetyler", "Cohen", "Joe", "Ryan"
]

JV = [
    "Aaira", "Aidan", "Erika", "Ethan", "Gunnar", "Ishan", "Joe",
    "Juan", "Kingston", "Moses", "Reya", "Ryan", "Sana", "Sarah",
    "Sasha", "Audry", "Adan",
]

# Identify dual-team players
DUAL_TEAM_PLAYERS = set(VARSITY) & set(JV)
print(f"Dual-team players: {', '.join(sorted(DUAL_TEAM_PLAYERS))}")

# Determine which players to check based on tournament type
players_to_check = set()
if tournament_type == "VARSITY":
    players_to_check = set(VARSITY)
elif tournament_type == "JV":
    players_to_check = set(JV)
else:  # BOTH
    players_to_check = set(VARSITY) | set(JV)

# Cache for tournament results to avoid duplicates
tournament_results = set()

# Load player URLs from file and filter
def load_player_urls():
    with open("player_links.txt", "r") as f:
        profile_data = [line.strip().split() for line in f.readlines()]
    
    # Filter for selected players and exclude pre-freshmen
    return [
        data[-1] for data in profile_data
        if data[-2].lower() != "pre-freshman" and data[0] in players_to_check
    ]

def extract_set_scores(score_items):
    """Process and format set scores more efficiently"""
    num_sets = len(score_items) // 4
    quarters = len(score_items) // 4
    
    formatted_scores = []
    for i in range(num_sets):
        # Extract scores and tiebreaks
        team1_score = score_items[i]
        team2_score = score_items[i + quarters]
        
        # Process tiebreaks
        tiebreaks = []
        if len(team1_score) > 1:
            tiebreaks.append(int(team1_score[1:]))
        if len(team2_score) > 1:
            tiebreaks.append(int(team2_score[1:]))
        
        # Format the score
        score = f"{team1_score[0]}-{team2_score[0]}"
        if tiebreaks:
            score += f"({min(tiebreaks)})"
        
        formatted_scores.append(score)
    
    return " ".join(formatted_scores)

def scrape_matches(event_block, profile_url, tournament_name):
    """Extracts match results only from the correct tournament."""
    global tournament_results
    
    match_cards = event_block.locator(".utr-card.score-card.false").all()
    for match in match_cards:
        try:
            # Get player names more efficiently
            teams = []
            for team_idx in range(2):
                players = match.locator(".d-none.d-md-block .team") \
                               .nth(team_idx) \
                               .locator(".player-details a.flex-column.player-name") \
                               .all()
                
                team_names = "/".join([player.inner_text().strip() for player in players])
                teams.append(team_names)
            
            # Extract scores
            score_items = [item.inner_text().strip() for item in match.locator(".score-item").all()]
            set_scores = extract_set_scores(score_items)
            
            # Create result string
            result_line = f". {teams[0]} vs {teams[1]} {set_scores}"
            tournament_results.add(result_line)
            
        except Exception as match_error:
            print(f"Error processing match for {profile_url} in {tournament_name}: {match_error}")

def switch_event_type(page, event_type):
    """Switch between singles and doubles views efficiently"""
    current_selection = page.locator("div.popovermenu-anchor.resultsTab__anchorClass__PGL2O.pl8 h6") \
                           .first.inner_text().strip().lower()
    
    if event_type.lower() not in current_selection:
        page.locator("div.popovermenu-anchor.resultsTab__anchorClass__PGL2O.pl8").first.click()
        page.locator(f"div#item{event_type.lower()}.menu-item").click()
        page.wait_for_timeout(2000)  
        return True
    return False

def process_profile(page, profile_url):
    """Process a single player profile for tournament results"""
    page.goto(profile_url)
    page.wait_for_timeout(1000)
    
    # Check singles first
    switch_event_type(page, "singles")
    found_results = process_events(page, profile_url)
    
    # If no singles results, check doubles
    if not found_results:
        switch_event_type(page, "doubles")
        process_events(page, profile_url)

def process_events(page, profile_url):
    """Process all events on the current page"""
    found_results = False
    event_blocks = page.locator("div.eventItem__eventItem__2Xpsd").all()
    
    for event in event_blocks:
        try:
            tournament_name = event.locator(".eventItem__eventName__6hntZ span:not(.eventItem__middleDot__1ttwt)") \
                                .inner_text().strip()
            
            if tournament.lower() in tournament_name.lower():
                scrape_matches(event, profile_url, tournament_name)
                found_results = True
        except Exception as e:
            print(f"Error processing event for {profile_url}: {e}")
    
    return found_results

def main():
    # Get player URLs based on tournament type
    profile_urls = load_player_urls()
    player_count = len(profile_urls)
    print(f"Checking {player_count} player profiles for {tournament_type} tournament...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        # Login
        page.goto("https://app.utrsports.net/login")
        page.fill("#emailInput", EMAIL)
        page.fill("#passwordInput", password)
        page.click("button.btn.btn-primary.btn-xl.btn-block")
        page.wait_for_url("https://app.utrsports.net/home")
        
        # Process each player profile
        for i, profile_url in enumerate(profile_urls, 1):
            print(f"Processing profile {i}/{player_count}: {profile_url}")
            process_profile(page, profile_url)
        
        browser.close()
    
    # Write results to file
    with open("tournament_results.txt", "w") as f:
        team = "JV" if tournament_type == "JV" else "Varsity"
        f.write("INSERT_DATE_HERE "+ team + " @ " + tournament_input + " L0-0\n\nBoys Doubles\n\nGirls Doubles\n\nMixed Doubles\n\nBoys Singles\n\nGirls Singles\n")
        for result in sorted(tournament_results):
            f.write(result + "\n")
    
    print(f"Extracted {len(tournament_results)} tournament results.")

if __name__ == "__main__":
    main()