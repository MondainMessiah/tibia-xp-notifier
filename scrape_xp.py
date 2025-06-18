import requests
import json
import os
import time
from bs4 import BeautifulSoup
from datetime import datetime

CHAR_FILE = "characters.txt"
HISTORY_PATH = "xp_history.json"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

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

def load_history():
    if os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH, "r") as f:
            return json.load(f)
    return {}

def save_history(history):
    with open(HISTORY_PATH, "w") as f:
        json.dump(history, f, indent=2)

def post_to_discord(message):
    if not DISCORD_WEBHOOK_URL:
        print("DISCORD_WEBHOOK_URL environment variable not set. Skipping Discord notification.")
        return
    payload = {"content": message}
    try:
        resp = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if resp.status_code in (200, 204):
            print("Posted to Discord successfully.")
        else:
            print(f"Failed to post to Discord: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"Exception posting to Discord: {e}")

if __name__ == "__main__":
    characters = load_characters()
    today = datetime.utcnow().strftime("%Y-%m-%d")

    xp_today = {}
    for name in characters:
        print(f"Scraping {name}...")
        xp_data = scrape_xp(name)
        time.sleep(1.5)
        if not xp_data:
            continue
        # Grab the latest XP entry
        latest_date = max(xp_data.keys(), default=None)
        if latest_date:
            xp_str = xp_data[latest_date].replace(",", "").replace("+", "").strip()
            try:
                xp_today[name] = int(xp_str)
            except ValueError:
                print(f"Invalid XP value for {name}: {xp_data[latest_date]}")

    if not xp_today:
        print("No XP data scraped.")
        exit()

    # Load and update history
    history = load_history()
    if today in history and history[today] == xp_today:
        print("No changes in XP data. Not updating.")
        exit()

    history[today] = xp_today
    save_history(history)

    # Compare with yesterday's data
    sorted_dates = sorted(history.keys())
    if len(sorted_dates) < 2:
        print("Not enough data for XP comparison.")
        exit()

    yesterday = sorted_dates[-2]
    xp_yesterday = history[yesterday]

    xp_diff = {}
    for name in characters:
        today_xp = xp_today.get(name, 0)
        yest_xp = xp_yesterday.get(name, 0)
        gain = today_xp - yest_xp
        xp_diff[name] = gain

    # Sort and format message
    ranked = sorted(xp_diff.items(), key=lambda x: x[1], reverse=True)
    medals = ["🥇", "🥈", "🥉"]
    message_lines = []

    print(f"\n🏆 XP Gains from {yesterday} to {today}:")
    for idx, (name, gain) in enumerate(ranked):
        medal = medals[idx] if idx < 3 else ""
        line = f"{medal} {name}: {gain:,} XP" if medal else f"{name}: {gain:,} XP"
        print(line)
        message_lines.append(line)

    # Post to Discord
    message = f"🏆 XP Gains from {yesterday} to {today}:\n" + "\n".join(message_lines)
    post_to_discord(message)

    # Commit to Git
    os.system("git config user.name github-actions")
    os.system("git config user.email github-actions@github.com")
    os.system("git add xp_history.json")
    commit_msg = f"XP update {today}\n" + "\n".join(message_lines)
    commit_result = os.system(f'git commit -m "{commit_msg}"')
    if commit_result == 0:
        os.system("git push")
    else:
        print("No changes to commit.")
