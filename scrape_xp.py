import requests
import json
import os
from bs4 import BeautifulSoup

CHAR_FILE = "characters.txt"
JSON_PATH = "xp_log.json"

def scrape_xp(char_name):
    url = f"https://guildstats.eu/character?name={char_name.replace(' ', '+')}"
    soup = BeautifulSoup(requests.get(url).text, "html.parser")
    table = soup.find("table", class_="chart_table")
    if not table:
        print(f"No XP data found for {char_name}.")
        return {}
    return {
        row.find_all("td")[0].text.strip(): row.find_all("td")[1].text.strip()
        for row in table.find_all("tr")[1:]
    }

def load_characters():
    with open(CHAR_FILE, "r") as f:
        return [line.strip() for line in f if line.strip()]

def load_existing():
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r") as f:
            return json.load(f)
    return {}

def save_if_changed(data):
    old = load_existing()
    if data == old:
        print("No XP changes.")
        return False
    with open(JSON_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print("XP data updated.")
    return True

if __name__ == "__main__":
    characters = load_characters()
    all_xp = {}

    for name in characters:
        print(f"Scraping {name}...")
        all_xp[name] = scrape_xp(name)

    if not all_xp:
        print("No data scraped for any characters.")
        exit()

    if save_if_changed(all_xp):
        # Determine latest date with XP data across all characters
        latest_dates = [max(xp.keys()) for xp in all_xp.values() if xp]
        if not latest_dates:
            print("No XP dates found.")
            exit()
        latest_date = max(latest_dates)

        # Prepare list of (name, xp_value) for the latest date
        daily_xp_ranking = []
        for name, xp_dict in all_xp.items():
            xp_str = xp_dict.get(latest_date, "+0").replace(",", "").replace("+", "").strip()
            try:
                xp_val = int(xp_str)
            except ValueError:
                xp_val = 0
            daily_xp_ranking.append((name, xp_val))

        # Sort descending by XP
        daily_xp_ranking.sort(key=lambda x: x[1], reverse=True)

        # Assign medals for top 3
        medals = ["🥇", "🥈", "🥉"]
        medaled_output = []
        print(f"\n🏆 Daily XP Gains for {latest_date}:")
        for idx, (name, xp_val) in enumerate(daily_xp_ranking):
            medal = medals[idx] if idx < 3 else ""
            line = f"{medal} {name}: {xp_val:,} XP" if medal else f"{name}: {xp_val:,} XP"
            print(line)
            medaled_output.append(line)

        # Commit & push changes to GitHub
        os.system("git config user.name github-actions")
        os.system("git config user.email github-actions@github.com")
        os.system("git add xp_log.json")
        commit_message = f"Daily XP update {latest_date}\n" + "\n".join(medaled_output)
        os.system(f'git commit -m "{commit_message}"')
        os.system("git push")
