import discord
from discord import app_commands
from curl_cffi import requests  # Use curl_cffi instead of standard requests
import os
from dotenv import load_dotenv

# Custom mapping for Rank Icons (Example URLs - Replace with your preferred hosting or CDN)
RANK_ICONS = {
    "Bronze": "https://trackercdn.com/cdn/rocketleague/ranks/1.png",
    "Silver": "https://trackercdn.com/cdn/rocketleague/ranks/4.png",
    "Gold": "https://trackercdn.com/cdn/rocketleague/ranks/7.png",
    "Platinum": "https://trackercdn.com/cdn/rocketleague/ranks/10.png",
    "Diamond": "https://trackercdn.com/cdn/rocketleague/ranks/13.png",
    "Champion": "https://trackercdn.com/cdn/rocketleague/ranks/16.png",
    "Grand Champion": "https://trackercdn.com/cdn/rocketleague/ranks/19.png",
    "Supersonic Legend": "https://trackercdn.com/cdn/rocketleague/ranks/22.png"
}

# 1. INITIAL SETUP & KEY VERIFICATION
# Loads your custom apikey.env file
load_dotenv("apikey.env") 

TOKEN = os.getenv('DISCORD_TOKEN')
TRACKER_KEY = os.getenv('TRACKER_KEY')

print("--- STARTUP DEBUG CHECK ---")
if TOKEN:
    print(f"✅ Discord Token found: {TOKEN[:10]}...") 
else:
    print("❌ ERROR: 'DISCORD_TOKEN' not found in apikey.env")

if TRACKER_KEY:
    print(f"✅ Tracker API Key found: {TRACKER_KEY[:5]}...")
else:
    print("❌ ERROR: 'TRACKER_KEY' not found in apikey.env")
print("---------------------------")

# 2. BOT CLASS DEFINITION
class RLBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Syncs commands so they appear in Discord as /rank
        await self.tree.sync()
        print(f"✅ Commands Synced. Logged in as: {self.user}")

bot = RLBot()

# 3. THE RANK COMMAND
@bot.tree.command(name="rank", description="Get Rocket League ranks using browser impersonation")
@app_commands.describe(platform="Platform (epic, steam, psn, xbl)", username="Player ID")

@app_commands.choices(platform=[
    app_commands.Choice(name="Epic Games", value="epic"),
    app_commands.Choice(name="Steam", value="steam"),
    app_commands.Choice(name="PlayStation", value="psn"),
    app_commands.Choice(name="Xbox", value="xbl")
])
async def rank(interaction: discord.Interaction, platform: str, username: str):
    platform = platform.lower()
    url = f"https://api.tracker.gg/api/v2/rocket-league/standard/profile/{platform}/{username}"
    print(f"DEBUG: Testing this URL manually: {url}")
    
    # These headers match what a real browser sends
    headers = {
        # 'TRN-Api-Key': str(TRACKER_KEY).strip(),
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': 'Thunder Client (https://www.thunderclient.com)',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://rocketleague.tracker.network/',
    }

    print(f"DEBUG: Testing this URL manually: {url}")

    # Inform Discord that the bot is thinking (prevents "interaction failed" timeout)
    await interaction.response.defer()

    try:
        # We use impersonate="chrome" to mimic a real Chrome browser's TLS fingerprint
        response = requests.get(url, headers=headers, impersonate="chrome")
        
        if response.status_code == 200:
            data = response.json()
            segments = data['data']['segments']
            
            embed = discord.Embed(
                title=f"Rocket League Stats: {username}", 
                color=discord.Color.blue(),
                url=f"https://rocketleague.tracker.network/rocket-league/profile/{platform}/{username}"
            )
            
            # Loop through game modes to find ranks
            for s in segments:
                if s['type'] == 'playlist':
                    mode_name = s['metadata']['name']
                    stats = s['stats']
                    
                    # Extract rank and MMR safely
                    rank_name = stats.get('tier', {}).get('metadata', {}).get('name', 'Unranked')
                    division = stats.get('division', {}).get('metadata', {}).get('name', '')
                    mmr = stats.get('rating', {}).get('value', 'N/A')
                    
                    embed.add_field(
                        name=mode_name, 
                        value=f"**{rank_name}**\n{division} ({mmr} MMR)", 
                        inline=True
                    )

            await interaction.followup.send(embed=embed)
            
        elif response.status_code == 401:
            await interaction.followup.send("❌ 401: API Key rejected. Check TRN-Api-Key in apikey.env")
        elif response.status_code == 403:
            await interaction.followup.send("❌ 403: Access Forbidden. Tracker.gg is blocking the request.")
        elif response.status_code == 404:
            await interaction.followup.send(f"❌ 404: Player `{username}` not found. Check platform and ID.")
        else:
            await interaction.followup.send(f"❌ API Error: Status {response.status_code}")
            
    except Exception as e:
        print(f"DEBUG Error: {e}")
        await interaction.followup.send("❌ An unexpected error occurred. Check terminal for logs.")

# 4. RUN THE BOT
if TOKEN:
    bot.run(TOKEN)