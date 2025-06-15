import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os

# Get the webhook URL from environment variable (GitHub Actions Secret)
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# List of Tibia characters to track
CHARACTERS = [
    "Ilumine",
    "Kamikedzei",
    "Hex good",
    "Jay the pally",
    "Zanron the monk"
]

def fetch_character_xp(name):
    url = f"https://www.guildstats.eu/character?name={name.replace(' ', '+')}"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        return f"- {name}: ❌ Failed to fetch data ({e})"

    soup = BeautifulSoup(response.text, "html.parser")
    rows = soup.find_all("tr")

    # Yesterday's date in YYYY-MM-DD format
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')

    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 3:
            date_text = cols[0].text.strip().split()[0]  # e.g., "2025-06-14"
            xp_gained = cols[2].text.strip()
            if date_text == yesterday:
                return f"- {name}: {xp_gained} XP"

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

    payload = {"content": message}
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if response.status_code != 204:
        print(f"❌ Failed to send message: {response.status_code} - {response.text}")
    else:
        print("✅ Message sent to Discord.")

if __name__ == "__main__":
    print("🔍 Fetching Tibia XP data...")
    message = build_report()
    print("📤 Message preview:\n", message)
    send_to_discord(message)
