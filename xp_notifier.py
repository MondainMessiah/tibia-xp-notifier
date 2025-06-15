import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os

# ✅ Add your actual guildstats URL here
GUILD_URL = "https://www.guildstats.eu/stats/view/guild/YOUR-GUILD-NAME"

# ✅ Characters to track
CHARACTERS = ["Illumine", "Kamikedzei", "Hex good", "Jay the pally", "Zanron the monk"]

# ✅ Webhook from GitHub Secrets or .env
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def fetch_xp_gains():
    try:
        response = requests.get(GUILD_URL)
        response.raise_for_status()
    except requests.RequestException as e:
        return f"❌ Failed to fetch guild page: {e}"

    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table", class_="statistics")
    if not table:
        return "❌ Could not find XP table on guildstats.eu."

    rows = table.find_all("tr")[1:]  # skip header
    yesterday = datetime.utcnow().date() - timedelta(days=1)
    report = f"📊 **Tibia XP Gains – {yesterday}**\n"

    found = False
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 4:
            continue

        name = cols[0].text.strip()
        xp_gained = cols[3].text.strip()

        for tracked_name in CHARACTERS:
            if name.lower() == tracked_name.lower():
                report += f"- {name}: {xp_gained} XP\n"
                found = True

    if not found:
        report += "No XP data found for specified characters."

    return report

def send_to_discord(message):
    if not DISCORD_WEBHOOK_URL:
        print("❌ DISCORD_WEBHOOK_URL not set.")
        return

    payload = {"content": message}
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if response.status_code != 204:
        print(f"❌ Failed to send message: {response.status_code} - {response.text}")
    else:
        print("✅ Message sent to Discord!")

if __name__ == "__main__":
    message = fetch_xp_gains()
    print("Debug Output:\n", message)  # 👀 for GitHub Actions log
    send_to_discord(message)
