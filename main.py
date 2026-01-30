from PIL import Image, ImageDraw, ImageFont
import io
import discord
from discord import app_commands
from curl_cffi import requests  # Use curl_cffi instead of standard requests
import os
from dotenv import load_dotenv
import random # Add this at the top of your script
import sqlite3


def get_db_connection():
    # If /data exists (on Railway), use it. Otherwise, use local (for your PC).
    db_path = "/data/bot_data.db" if os.path.exists("/data") else "bot_data.db"
    return sqlite3.connect(db_path)

# Initialize the database and table
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            discord_id INTEGER PRIMARY KEY,
            rl_username TEXT,
            rl_platform TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# List of possible messages
random_messages = [
    "Chat… we pulled the ranks. It’s not looking good for bro.",
    "We got the ranks and I’m crying.",
    "These the ranks… imma let y’all process that.",
    "Ranked? Yeah. Respected? Debatable.",
    "We found the ranks and chat went silent.",
    "{user}  This the rank? Oh nah 💀",
    "{user}  We did the scan and I’m wheezing.",
    "{user}  This what you wanted us to check? Crazy.",
    "Ranks obtained. Therapist contacted.",
    "I’d keep this private if I were you {user}.",
    "These the ranks. I need a moment {user}.",
    "{user}  These the ranks… imma hold your hand when I say this…",
    "This ain’t even mid, this is tragic-core.",
    "We pulled your ranks. You’re not him.",
    "This ain’t leaderboard behavior.",
    "Telemetry confirms… skill deficiency.",
    "Packet analysis done. You not built for this..",
    "We checked the system and the system judged you back.",
    "These ranks just humbled the whole server.",
    "{user} I looked it up so you didn’t have to.",
    "System report generated. Proceed with caution.",
    "{user} I wasn’t ready for this information.",
]

# Custom mapping for Rank Icons (Example URLs - Replace with your preferred hosting or CDN)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def create_rank_card(username, platform_name,display_name, segments,mode_type="standard"):
    
    
    if mode_type == "extras":
        desired_modes = ['Rumble', 'Dropshot', 'Hoops', 'Heatseeker']
    else:
        desired_modes = ['Ranked Duel 1v1', 'Ranked Doubles 2v2', 'Ranked Standard 3v3', 'Tournament Matches']
        
    print(mode_type)


    # 1. Canvas Setup
    base = Image.new("RGBA", (850, 550), (24, 28, 35))
    draw = ImageDraw.Draw(base)

    print(username)
    print(display_name)


    # if(username.lower=="akshattyagi05"):
    #     display_name= "AkshatTyagi05"
    #     username="iiRw9"
    # else:
    #     display_name= username
    
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
    font_path = os.path.join(BASE_DIR, "TitilliumWeb-Bold.ttf")
    try:
        font_main = ImageFont.truetype(font_path, 32)   
        font_main_small = ImageFont.truetype(font_path, 26) # Added for long rank names
        font_bigsub = ImageFont.truetype(font_path, 22)    
        font_sub = ImageFont.truetype(font_path, 20)    
        font_med = ImageFont.truetype(font_path, 18)    
        font_smallmed = ImageFont.truetype(font_path, 17)  
        font_small = ImageFont.truetype(font_path, 16)
    except:
        font_main = font_sub = font_med = font_small = ImageFont.load_default()
        font_main_small = ImageFont.load_default()



    # --- 4. TOP NAVBAR ---
    draw.rounded_rectangle([25, 20, 825, 80], radius=10, fill=(30, 34, 43))
    
    platform_map = {"epic": "epic.png", "steam": "steam.png", "xbl": "xbl.png", "psn": "psn.png", "xbox": "xbl.png", "playstation": "psn.png"}
    input_plat = platform_name.lower().split()[0]
    filename = platform_map.get(input_plat, "epic.png")
    plat_icon_path = os.path.join(BASE_DIR, "icons", filename)

    if os.path.exists(plat_icon_path):
        p_img = Image.open(plat_icon_path).convert("RGBA")
        ratio = min(40 / p_img.width, 40 / p_img.height)
        new_size = (int(p_img.width * ratio), int(p_img.height * ratio))
        plat_icon = p_img.resize(new_size, Image.Resampling.LANCZOS)
        base.paste(plat_icon, (45, 50 - (new_size[1] // 2)), mask=plat_icon)

    draw.text((100, 26), f"{display_name}", font=font_main, fill=(255, 255, 255))
    
    # Adjusted Reward Level position to avoid edge clipping
    reward_key = reward_level.split()[0].lower()
    reward_color = rank_colors.get(reward_key, (219, 90, 115))
    draw.text((640, 38), f"{reward_level}", font=font_sub, fill=reward_color)

    # --- 5. RANK TILES ---
    positions = [(25, 100), (435, 100), (25, 320), (435, 320)]
    segment_map = {s['metadata']['name']: s for s in segments if s['type'] == 'playlist'}
    
    for count, mode_key in enumerate(desired_modes):
        x, y = positions[count]
        draw.rounded_rectangle([x, y, x + 390, y + 200], radius=10, fill=(30, 34, 43))
        
        if mode_key in segment_map:
            s = segment_map[mode_key]
            stats = s['stats']
            
            display_mode_name = "Tournament Rank" if mode_key == 'Tournament Matches' else mode_key
            tier = stats['tier']['metadata']['name']
            
            # Logic for long rank names
            current_font = font_main_small if len(tier) > 15 else font_main
            rank_base = tier.split()[0].lower()
            text_color = rank_colors.get(rank_base, (255, 255, 255))
            file_rank = tier.lower().replace(" ", "_").replace("_iii", "_3").replace("_ii", "_2").replace("_i", "_1")

            # Column 1: Stats (Slightly moved left to give rank more room)
            draw.text((x + 20, y + 15), display_mode_name, font=font_bigsub, fill=(100, 200, 255))
            draw.text((x + 20, y + 53), tier, font=current_font, fill=text_color)
            draw.text((x + 20, y + 90), stats.get('division', {}).get('metadata', {}).get('name', ''), font=font_med, fill=(200, 200, 200))
            draw.text((x + 20, y + 121), f"{stats['rating']['value']} MMR", font=font_med, fill=(160, 160, 160))
            draw.text((x + 20, y + 160), f"{stats.get('matchesPlayed', {}).get('value', 0)} Matches", font=font_small, fill=(140, 140, 140))

            # Column 2: Icon (Shifted right from 250 to 265 to prevent overlap)
            icon_path = os.path.join(BASE_DIR, "icons", f"{file_rank}.png")
            if os.path.exists(icon_path):
                icon = Image.open(icon_path).convert("RGBA").resize((110, 110)) # Slightly bigger icon
                base.paste(icon, (x + 265, y + 23), mask=icon)

            streak_data = stats.get('winStreak', {})
            val = streak_data.get('value', 0)
            stype = streak_data.get('metadata', {}).get('type', 'win') 
            
            streak_text = f"{val} {'Loss' if stype == 'loss' and val == 1 else 'Loss' if stype == 'loss' else 'Win' if val == 1 else 'Wins'}"
            streak_color = (255, 60, 60) if stype == 'loss' else (0, 255, 100)
            # Centered under the new icon position
            draw.text((x + 295, y + 160), streak_text, font=font_smallmed, fill=streak_color)
        else:
            draw.text((x + 20, y + 20), mode_key, font=font_sub, fill=(100, 200, 255))
            draw.text((x + 20, y + 55), "Unranked", font=font_main, fill=(150, 150, 150))

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

class RankView(discord.ui.View):
    def __init__(self, username, platform_name, display_name, segments):
        super().__init__(timeout=None)
        self.username = username
        self.platform_name = platform_name
        self.display_name = display_name
        self.segments = segments
        self.current_mode = "standard" # Initial state

    async def send_new_card(self, interaction: discord.Interaction):
        # 1. Defer to give PIL time to generate the image
        await interaction.response.defer()
        
        # 2. Use the updated self.current_mode to generate the card
        file = create_rank_card(
            self.username, 
            self.platform_name, 
            self.display_name, 
            self.segments, 
            mode_type=self.current_mode # Pass the current mode here!
        )
        
        # 3. Send the brand new card as a follow-up
        selected_text = random.choice(random_messages).format(user=interaction.user.mention)

        await interaction.followup.send(
            content=selected_text,
            file=file,
            view=self
        )

    @discord.ui.button(label="Extras", style=discord.ButtonStyle.gray, emoji="🏀")
    async def extras_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Toggle logic: If standard, switch to extras and vice-versa
        if self.current_mode == "standard":
            self.current_mode = "extras"
            button.label = "Standard"
            button.emoji = "⚽"  # Switch to Football for Extra Modes
        else:
            self.current_mode = "standard"
            button.label = "Extras"
            button.emoji = "🏀"  # Switch back to Basketball for Standard
            
        await self.send_new_card(interaction)

    @discord.ui.button(label="Update", style=discord.ButtonStyle.gray, emoji="🔄")
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Refresh uses the same mode we are currently on
        await self.send_new_card(interaction)


# 3. THE RANK COMMAND
@bot.tree.command(name="rank", description="Get Rocket League ranks by searching Username")
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
    if(username.lower()=="akshattyagi05"):
        display_name= "AkshatTyagi05"
        username="iiRw9"
        url = f"https://api.tracker.gg/api/v2/rocket-league/standard/profile/epic/iiRw9"
    else:
        display_name= username
    
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


            view = RankView(username, platform.name, display_name, segments)
            
            # Generate the initial "standard" image
            file = create_rank_card(username, platform.name, display_name, segments, mode_type="standard")
            
            # Send the message with both the file and the buttons
            selected_text = random.choice(random_messages).format(user=interaction.user.mention)

            await interaction.followup.send(
                content=selected_text,
                file=file,
                view=view
            )
            
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

@bot.tree.command(name="ranklink", description="Link your Rocket League account to your Discord ID")
@app_commands.describe(platform="Select your platform", username="Your Rocket League Username/ID")
# Add the choices decorator here
@app_commands.choices(platform=[
    app_commands.Choice(name="Epic Games", value="epic"),
    app_commands.Choice(name="Steam", value="steam"),
    app_commands.Choice(name="PlayStation", value="psn"),
    app_commands.Choice(name="Xbox", value="xbl")
])
async def ranklink(interaction: discord.Interaction, platform: app_commands.Choice[str], username: str):
    await interaction.response.defer(ephemeral=True)
    
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    
    # Use platform.value to save the ID (e.g., 'epic') and platform.name for the display
    cursor.execute(
        "INSERT OR REPLACE INTO users (discord_id, rl_username, rl_platform) VALUES (?, ?, ?)",
        (interaction.user.id, username, platform.value)
    )
    
    conn.commit()
    conn.close()
    
    await interaction.followup.send(f"✅ Linked **{username}** ({platform.name}) to your account! You can now use `/rankme`.")



@bot.tree.command(name="rankme", description="Show your own Rocket League ranks")
async def rankme(interaction: discord.Interaction):
    await interaction.response.defer()
    
    # 1. Check Database for the user
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT rl_username, rl_platform FROM users WHERE discord_id = ?", (interaction.user.id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return await interaction.followup.send("❌ You haven't linked your account! Use `/ranklink` first.")
    
    saved_username, saved_platform = result
    
    # 2. Reuse your existing rank fetching logic here
    url = f"https://api.tracker.gg/api/v2/rocket-league/standard/profile/{saved_platform}/{saved_username}"
    headers = {
        # 'TRN-Api-Key': str(TRACKER_KEY).strip(),
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': 'Thunder Client (https://www.thunderclient.com)',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://rocketleague.tracker.network/',
    }

    print(f"DEBUG: Testing this URL manually: {url}")
    
    try:
        response = requests.get(url, headers=headers, impersonate="chrome")
        if response.status_code == 200:
            segments = response.json()['data']['segments']
            
            # Using your existing View and Card functions
            view = RankView(saved_username, saved_platform, saved_username, segments)
            file = create_rank_card(saved_username, saved_platform, saved_username, segments)
            
            selected_text = random.choice(random_messages).format(user=interaction.user.mention)
            await interaction.followup.send(content=selected_text, file=file, view=view)
        else:
            await interaction.followup.send("❌ Could not fetch stats. Your linked account might be private or invalid.")
    except Exception as e:
        print(f"DEBUG Error: {e}")
        await interaction.followup.send("❌ An error occurred while fetching your ranks.")

# 4. RUN THE BOT
if TOKEN:
    bot.run(TOKEN)