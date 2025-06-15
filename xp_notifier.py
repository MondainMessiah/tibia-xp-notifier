import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
CHARACTERS = ["Illumine", "Kamikedzei", "Hex good", "Jay the pally", "Zanron the monk"]

def fetch_character_xp(name):
    url = f"https://www.guildstats.eu/character?name={name.replace(' ', '+')}"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        return f"- {name}: ❌ Failed to fetch: {e}"

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", class_="table table-striped")
    if not table:
        return f"- {name}: ❌ No experience table found."

    rows = table.find_all("tr")[1:]  # skip header
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%d.%m.%Y')

    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 3:
            date = cols[0].text.strip()
            xp_gain = cols[2].text.strip()
            if date == yesterday:
                return f"- {name}: {xp_gain} XP"

    return f"- {name}: ⚠️ No XP data for {yesterday}"

def build_report():
    yesterday = datetime.utcnow().date() - timedelta(days=1)
    report = f"📊 **Tibia XP Gains – {yesterday}**\n"
    for char in CHARACTERS:
        report += fetch_character_xp(char) + "\n"
    return report.strip()

def send_to_discord(message):
    if not DISCORD_WEBHOOK_URL:
        print("❌ DISCORD_WEBHOOK_URL not set.")
        return

    response = requests.post(DISCORD_WEBHOOK_URL, json={"content": message})
    if response.status_code != 204:
        print(f"❌ Discord error: {response.status_code} - {response.text}")
    else:
        print("✅ Message sent to Discord.")

if __name__ == "__main__":
    print("🔍 Fetching XP data for characters...")
    message = build_report()
    print("📤 Message:\n", message)
    send_to_discord(message)
