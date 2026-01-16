import discord
from discord import app_commands
import requests
import os
from dotenv import load_dotenv

# 1. INITIAL SETUP & KEY VERIFICATION
# Tell load_dotenv to look specifically for your custom filename
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
        # Default intents are enough for Slash Commands
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # This registers your /rank command with Discord
        await self.tree.sync()
        print(f"Synced slash commands for {self.user}")

bot = RLBot()

# 3. THE RANK COMMAND
@bot.tree.command(name="rank", description="Check Rocket League ranks for a player")
@app_commands.describe(platform="Platform (epic, steam, psn, xbl)", username="Player ID")
async def rank(interaction: discord.Interaction, platform: str, username: str):
    # Standardize platform input to lowercase
    platform = platform.lower()
    # Try this version if the headers still don't work
    # url = f"https://public-api.tracker.gg/v2/rocket-league/standard/profile/{platform}/{username}?api_key={TRACKER_KEY}"

    headers = {
        # 'TRN-Api-Key': str(TRACKER_KEY).strip(),
        'User-Agent': 'Thunder Client (https://www.thunderclient.com)' # Helps prevent blocks from the API server
    }
    url = f"https://api.tracker.gg/api/v2/rocket-league/standard/profile/{platform}/{username}?"

    response = requests.get(url, headers=headers)

    print(f"DEBUG: Requesting URL: {url}")
    print(f"DEBUG: TRACKER_KEY is: {TRACKER_KEY}")
    
    # Headers must match Tracker Network requirements exactly
    # response = requests.get(url, headers=headers)
    print(f"DEBUG: Sent Headers: {response.request.headers}") # Verify what was actually sent

    # Defer gives the API up to 15 minutes to respond
    await interaction.response.defer()
    print(response.text)

    try:
        print(headers)
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            segments = data['data']['segments']
            
            embed = discord.Embed(
                title=f"Rocket League Stats: {username}", 
                color=discord.Color.blue(),
                url=f"https://rocketleague.tracker.network/rocket-league/profile/{platform}/{username}"
            )
            
            # Loop through game modes (2v2, 3v3, etc.)
            for s in segments:
                if s['type'] == 'playlist':
                    mode_name = s['metadata']['name']
                    rank_name = s['stats']['tier']['metadata']['name']
                    division = s['stats']['division']['metadata']['name']
                    mmr = s['stats']['rating']['value']
                    
                    embed.add_field(
                        name=mode_name, 
                        value=f"**{rank_name}**\n{division} ({mmr} MMR)", 
                        inline=True
                    )

            await interaction.followup.send(embed=embed)
            
        elif response.status_code == 403:
            await interaction.followup.send("❌ API Key Error: Your key may not be authorized for RL data.")
        elif response.status_code == 404:
            await interaction.followup.send(f"❌ Player `{username}` not found on `{platform}`. Try searching them on tracker.gg first.")
        else:
            await interaction.followup.send(f"❌ API Error: Received status code {response.status_code}")
            
    except Exception as e:
        print(f"Code Error: {e}")
        await interaction.followup.send("❌ An unexpected error occurred while fetching data.")

# 4. RUN THE BOT
if TOKEN:
    bot.run(TOKEN)