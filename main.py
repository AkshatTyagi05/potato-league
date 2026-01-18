from PIL import Image, ImageDraw, ImageFont
import io
import discord
from discord import app_commands
from curl_cffi import requests  # Use curl_cffi instead of standard requests
import os
from dotenv import load_dotenv

# Custom mapping for Rank Icons (Example URLs - Replace with your preferred hosting or CDN)

def create_rank_card(username, platform_name, segments):
    # 1. Load Background
    base = Image.open("background.png").convert("RGBA")
    base = base.resize((850, 480), Image.Resampling.LANCZOS) # Forces correct size
    draw = ImageDraw.Draw(base)
    
    # 2. Load Fonts
    font_large = ImageFont.truetype("TitilliumWeb-Bold.ttf", 36)
    font_small = ImageFont.truetype("TitilliumWeb-Regular.ttf", 20)
    
    # 3. Draw Header (Username and Platform)
    draw.text((40, 30), f"SHERRY {username}", font=font_large, fill=(255, 255, 255))
    draw.text((700, 35), "Champion", font=font_small, fill=(219, 90, 115))

    # 4. Draw Stats (Looping through playlists)
    # Positions based on a 2x2 grid layout
    positions = [(40, 120), (420, 120), (40, 280), (420, 280)]
    
    playlist_count = 0
    for s in segments:
        if s['type'] == 'playlist' and playlist_count < 4:
            x, y = positions[playlist_count]
            
            mode_name = s['metadata']['name']
            tier = s['stats']['tier']['metadata']['name']
            mmr = s['stats']['rating']['value']
            
            # Draw Mode and Rank Text
            draw.text((x, y), mode_name, font=font_small, fill=(100, 200, 255))
            draw.text((x, y + 30), tier, font=font_large, fill=(255, 255, 255))
            draw.text((x, y + 70), f"{mmr} MMR", font=font_small, fill=(150, 150, 150))
            
            # Paste Rank Icon
            icon_path = f"icons/{tier.split()[0].lower()}.png"
            try:
                icon = Image.open(icon_path).resize((80, 80)).convert("RGBA")
                base.paste(icon, (0, 0), mask=icon)
            except:
                pass # Skip if icon file is missing
                
            playlist_count += 1

    # 5. Convert to Discord File
    buffer = io.BytesIO()
    base.save(buffer, format="PNG")
    buffer.seek(0)
    return discord.File(fp=buffer, filename="rank_card.png")

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
async def rank(interaction: discord.Interaction, platform: app_commands.Choice[str], username: str):
    
    url = f"https://api.tracker.gg/api/v2/rocket-league/standard/profile/{platform.value}/{username}"
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

            # Generate the custom image
            rank_card_file = create_rank_card(username, platform.name, segments)
            await interaction.followup.send(file=rank_card_file)
            
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