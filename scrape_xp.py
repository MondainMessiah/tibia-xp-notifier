import requests
import json
import os
import time
from datetime import datetime

CHAR_FILE = "characters.txt"
HISTORY_PATH = "xp_history.json"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")


def fetch_character_data(name):
    url = f"https://api.tibiadata.com/v3/character/{name.replace(' ', '%20')}"
    try:
        resp = requests.get(url)
        data = resp.json()
        character = data.get("characters", {}).get("character", {})
        if not character:
            print(f"❌ No data for {name}")
            return None
        return {
            "level": character.get("level"),
            "experience": character.get("experience")
        }
    except Exception as e:
        print(f"⚠️ Error fetching {name}: {e}")
        return None


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
        print("🚫 DISCORD_WEBHOOK_URL not set.")
        return
    payload = {"content": message}
    try:
        resp = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if resp.status_code in (200, 204):
            print("✅ Posted to Discord.")
        else:
            print(f"❌ Discord error: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"❌ Exception posting to Discord: {e}")


if __name__ == "__main__":
    today = datetime.utcnow().strftime("%Y-%m-%d")
    characters = load_characters()
    history = load_history()
    xp_today = {}

    for name in characters:
        print(f"📦 Fetching {name}...")
        data = fetch_character_data(name)
        time.sleep(1)
        if data:
            xp_today[name] = data["experience"]

    if not xp_today:
        print("❌ No XP data collected.")
        exit()

    if history.get(today) == xp_today:
        print("🔁 No changes since last run.")
        exit()

    history[today] = xp_today
    save_history(history)

    sorted_dates = sorted(history.keys())
    if len(sorted_dates) < 2:
        print("ℹ️ Not enough data to compare.")
        exit()

    yesterday = sorted_dates[-2]
    xp_yesterday = history[yesterday]

    xp_diff = {
        name: xp_today.get(name, 0) - xp_yesterday.get(name, 0)
        for name in characters
    }

    ranked = sorted(xp_diff.items(), key=lambda x: x[1], reverse=True)

    medals = ["🥇", "🥈", "🥉"]
    lines = []

    print(f"\n🏆 XP Gains from {yesterday} to {today}:")
    for i, (name, gain) in enumerate(ranked):
        medal = medals[i] if i < 3 else ""
        line = f"{medal} {name}: {gain:,} XP" if medal else f"{name}: {gain:,} XP"
        print(line)
        lines.append(line)

    msg = f"🏆 XP Gains from {yesterday} to {today}:\n" + "\n".join(lines)
    post_to_discord(msg)

    # Git commit
    os.system("git config user.name github-actions")
    os.system("git config user.email github-actions@github.com")
    os.system("git add xp_history.json")
    commit_msg = f"XP update {today}\n" + "\n".join(lines)
    commit_result = os.system(f'git commit -m "{commit_msg}"')
    if commit_result == 0:
        os.system("git push")
    else:
        print("✅ No changes to commit.")
