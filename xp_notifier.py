import requests
import json
import os
from datetime import datetime

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
CHARACTERS = [
    "Ilumine",
    "Kamikedzei",
    "Hex good",
    "Jay the pally",
    "Zanron the monk"
]

CACHE_FILE = "xp_cache.json"

def fetch_current_xp(name):
    url = f"https://api.tibiadata.com/v3/character/{name.replace(' ', '%20')}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        char_data = data.get("characters", {}).get("data", {}).get("character", {})
        xp = char_data.get("experience")
        if xp is None:
            return None, "No XP data available"
        return xp, None
    except Exception as e:
        return None, str(e)

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

def build_report():
    cache = load_cache()
    results = []
    for char in CHARACTERS:
        current_xp, error = fetch_current_xp(char)
        if error:
            results.append({"name": char, "xp_gained": None, "error": error})
            continue

        prev_xp = cache.get(char)
        if prev_xp is None:
            xp_gained = None  # no previous data
        else:
            xp_gained = current_xp - prev_xp if current_xp >= prev_xp else 0

        cache[char] = current_xp
        results.append({"name": char, "xp_gained": xp_gained})

    save_cache(cache)

    today = datetime.utcnow().date()
    report = f"📊 **Tibia XP Gains – {today}**\n"

    valid = [r for r in results if r["xp_gained"] is not None]
    invalid = [r for r in results if r["xp_gained"] is None]

    valid.sort(key=lambda x: x["xp_gained"], reverse=True)

    medals = ["🥇", "🥈", "🥉"]
    for i, r in enumerate(valid):
        medal = medals[i] if i < len(medals) else "🎖️"
        report += f"{medal} {r['name']}: {r['xp_gained']:,} XP\n"

    for r in invalid:
        report += f"⚠️ {r['name']}: No previous XP data to calculate gains.\n"

    return report.strip()

def send_to_discord(message):
    if not DISCORD_WEBHOOK_URL:
        print("❌ DISCORD_WEBHOOK_URL not set.")
        return
    resp = requests.post(DISCORD_WEBHOOK_URL, json={"content": message})
    if resp.status_code != 204:
        print(f"❌ Failed to send message: {resp.status_code} {resp.text}")
    else:
        print("✅ Message sent to Discord!")

if __name__ == "__main__":
    print("🔍 Fetching XP data from TibiaData API...")
    message = build_report()
    print("📤 Report:\n", message)
    send_to_discord(message)
