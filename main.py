from PIL import Image, ImageDraw, ImageFont
import io
import discord
from discord import app_commands
from curl_cffi import requests  # Use curl_cffi instead of standard requests
import os
from dotenv import load_dotenv

# Custom mapping for Rank Icons (Example URLs - Replace with your preferred hosting or CDN)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def create_rank_card(username, platform_name, segments, ):
    # 1. Canvas Setup
    base = Image.new("RGBA", (850, 550), (24, 28, 35))
    draw = ImageDraw.Draw(base)
    
    # Color mapping for rank accent colors
    rank_colors = {
        "bronze": (205, 127, 50), "silver": (192, 192, 192), "gold": (255, 215, 0),
        "platinum": (0, 255, 255), "diamond": (0, 191, 255), "champion": (160, 32, 240),
        "grand_champion": (255, 0, 0), "supersonic_legend": (255, 255, 255), "unranked": (150, 150, 150)
    }

    # 2. Extract Reward Level Dynamically
    reward_level = "Unranked"
    for s in segments:
        if s['type'] == 'overview': # TRN often places rewards in the overview segment
            reward_level = s['stats'].get('seasonRewardLevel', {}).get('metadata', {}).get('rankName', 'Unranked')
            break

    # 2. Fonts
    try:
        font_main = ImageFont.truetype(os.path.join(BASE_DIR, "TitilliumWeb-Bold.ttf"), 32)
        font_sub = ImageFont.truetype(os.path.join(BASE_DIR, "TitilliumWeb-Bold.ttf"), 18)
        font_small = ImageFont.truetype(os.path.join(BASE_DIR, "TitilliumWeb-Bold.ttf"), 14)
    except:
        font_main = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_small = ImageFont.load_default()

    platform_map = {
        "epic": "epic.png",
        "steam": "steam.png",
        "xbl": "xbl.png",
        "psn": "psn.png",
        "xbox": "xbl.png",
        "playstation": "psn.png"
    }

    # Get filename from mapping or default to epic
    input_plat = platform_name.lower().split()[0]
    filename = platform_map.get(input_plat, "epic.png")
    plat_icon_path = os.path.join(BASE_DIR, "icons", filename)

    # --- 3. TOP NAVBAR WITH PLATFORM ICON ---
    # Draw header tile
    draw.rounded_rectangle([25, 20, 825, 80], radius=10, fill=(30, 34, 43))
    
    
    if os.path.exists(plat_icon_path):
        p_img = Image.open(plat_icon_path).convert("RGBA")
        
        # PROPORTIONAL RESIZE: Prevent squeezing
        max_size = 40
        ratio = min(max_size / p_img.width, max_size / p_img.height)
        new_size = (int(p_img.width * ratio), int(p_img.height * ratio))
        plat_icon = p_img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Center the icon vertically in the 60px bar
        # Header is y=20 to y=80 (height 60). Middle is y=50.
        icon_y = 50 - (new_size[1] // 2)
        base.paste(plat_icon, (45, icon_y), mask=plat_icon)
    else:
        print(f"⚠️ Platform icon NOT FOUND: {plat_icon_path}")

    # FIXED: Decreased y from 35 to 28 to move the username slightly UP
    draw.text((100, 26), f"{username.upper()}", font=font_main, fill=(255, 255, 255))
    
    # Reward Level (Champion text on the right)
    draw.text((720, 40), reward_level, font=font_sub, fill=(219, 90, 115))

    # --- 4. RANK TILES ---
    # --- 4. RANK TILES (Final Layout with Tournament Fix) ---
    positions = [(25, 100), (435, 100), (25, 320), (435, 320)]
    
    # Priority list to ensure we get 1v1, 2v2, 3v3, and Tournament specifically
    # Note: TRN API uses "Tournament Match" for the metadata name
    desired_modes = ['Ranked Duel 1v1', 'Ranked Doubles 2v2', 'Ranked Standard 3v3', 'Tournament Matches']
    
    # Create a dictionary of segments keyed by their metadata name
    segment_map = {s['metadata']['name']: s for s in segments if s['type'] == 'playlist'}
    
    for count, mode_key in enumerate(desired_modes):
        x, y = positions[count]
        draw.rounded_rectangle([x, y, x + 390, y + 200], radius=10, fill=(30, 34, 43))
        
        if mode_key in segment_map:
            s = segment_map[mode_key]
            stats = s['stats']
            
            # # Use normal tier or fetch Highest Finish for Tournaments
            # if mode_key == 'Tournament Matches':
            #     display_mode_name = "Highest Season Finish"
            #     tier = stats.get('seasonHighest', {}).get('metadata', {}).get('name', stats['tier']['metadata']['name'])
            # else:
            display_mode_name = mode_key
            tier = stats['tier']['metadata']['name']
            
            # Rank Color and Logic
            rank_base = tier.split()[0].lower()
            text_color = rank_colors.get(rank_base, (255, 255, 255))
            file_rank = tier.lower().replace(" ", "_").replace("_iii", "_3").replace("_ii", "_2").replace("_i", "_1")

            # Column 1: Stats
            draw.text((x + 20, y + 20), display_mode_name, font=font_sub, fill=(100, 200, 255))
            draw.text((x + 20, y + 50), tier, font=font_main, fill=text_color)
            draw.text((x + 20, y + 90), stats.get('division', {}).get('metadata', {}).get('name', ''), font=font_small, fill=(150, 150, 150))
            draw.text((x + 20, y + 110), f"{stats['rating']['value']} MMR", font=font_small, fill=(100, 100, 100))
            draw.text((x + 20, y + 150), f"{stats.get('matchesPlayed', {}).get('value', 0)} Matches", font=font_small, fill=(150, 150, 150))

            # Column 2: Icon and Streak Alignment
            icon_path = os.path.join(BASE_DIR, "icons", f"{file_rank}.png")
            if os.path.exists(icon_path):
                icon = Image.open(icon_path).convert("RGBA").resize((100, 100))
                base.paste(icon, (x + 250, y + 30), mask=icon)

            # --- STREAK LOGIC (BASED ON YOUR JSON) ---
            streak_data = stats.get('winStreak', {})
            val = streak_data.get('value', 0)
            stype = streak_data.get('metadata', {}).get('type', 'win') # From your screenshot
            
            if stype == 'loss':
                streak_text = f"{val} {'Loss' if val == 1 else 'Losses'}"
                streak_color = (255, 60, 60) # Red
            else:
                streak_text = f"{val} {'Win' if val == 1 else 'Wins'}"
                streak_color = (0, 255, 100) # Green

            draw.text((x + 275, y + 150), streak_text, font=font_sub, fill=streak_color)
       
        else:
            # Fallback for unplayed modes
            draw.text((x + 20, y + 20), mode_key, font=font_sub, fill=(100, 200, 255))
            draw.text((x + 20, y + 50), "Unranked", font=font_main, fill=(150, 150, 150))

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