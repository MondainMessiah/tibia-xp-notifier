import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os

# List of your characters
characters = [
    "Illumine", "Kamikedzei", "Hex good", "Jay the pally", "Zanron the monk"
]

# Replace with your guildstats URL
GUILD_URL = "https://www.guildstats.eu/stats/view/guild/YOUR_GUILD_NAME"
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def fetch_xp_gains():
    yesterday = datetime.utcnow().date() - timedelta(days=1)
    response = requests.get(GUILD_URL)
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table", class_="statistics")  # Adjust class name if needed
    if not table:
        return "⚠️ Could not find XP table."

    rows = table.find_all("tr")[1:]  # Skip header
    xp_report = f"📊 **Tibia XP Gains - {yesterday}**\n"

    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 4:
            name = cols[0].text.strip()
            xp_gained = cols[3].text.strip()
            if name in characters:
                xp_report += f"- {name}: {xp_gained} XP\n"

    return xp_report.strip()

def send_to_discord(message):
    payload = {"content": message}
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if response.status_code != 204:
        print(f"Failed to send message: {response.text}")

if __name__ == "__main__":
    message = fetch_xp_gains()
    send_to_discord(message)
