import asyncio
from PIL import Image, ImageDraw, ImageFont
import io
import discord
from discord import app_commands
from curl_cffi import requests  # Use curl_cffi instead of standard requests
import os
from dotenv import load_dotenv
import random # Add this at the top of your script
import sqlite3
from discord.ext import commands
from discord import app_commands

def get_db_path():
    if os.path.exists("/data"):
        return "/data/bot_data.db"
    
    # This creates an absolute path to your current folder
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_data.db")

# Initialize the database and table
def init_db():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Create table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            discord_id INTEGER PRIMARY KEY,
            rl_username TEXT,
            rl_platform TEXT
        )
    """)
    conn.commit()
    conn.close()
    print(f"✅ Database initialized at: {db_path}")

# IMPORTANT: Call this immediately before the bot class starts
init_db()

# --- 2. BOT CLASS ---
class RLBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        # Ensure these intents are enabled
        intents.members = True 
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Syncing commands
        await self.tree.sync()
        print(f"✅ Slash commands synced for {self.user}")

bot = RLBot()


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

def create_rank_card(username, platform_name, display_name, segments, mode_type="standard"):
    if mode_type == "extras":
        desired_modes = ['Rumble', 'Dropshot', 'Hoops', 'Heatseeker']
    else:
        desired_modes = ['Ranked Duel 1v1', 'Ranked Doubles 2v2', 'Ranked Standard 3v3', 'Tournament Matches']

    # 1. Canvas Setup
    base = Image.new("RGBA", (900, 600), (29, 33, 42))
    draw = ImageDraw.Draw(base)

    # Colors boosted in saturation/brightness to stand out
    rank_colors = {
        "bronze": (205, 127, 50), "silver": (192, 192, 192), "gold": (255, 215, 0),
        "platinum": (0, 255, 255), "diamond": (0, 191, 255), "champion": (160, 32, 240),"grand": (255, 50, 50),
        "grand_champion": (255, 50, 50), "supersonic_legend": (255, 255, 255), "unranked": (150, 150, 150)
    }

    reward_level = "Unranked"
    for s in segments:
        if s['type'] == 'overview':
            reward_level = s['stats'].get('seasonRewardLevel', {}).get('metadata', {}).get('rankName', 'Unranked')
            break

    # 2. Updated Fonts (Moved from Light/Medium to Medium/Bold)
    # Ensure Bourgeois-Medium.ttf and Bourgeois-Bold.ttf are in your directory
    font_path_med = os.path.join(BASE_DIR, "Bourgeois-Medium.ttf")
    font_path_bold = os.path.join(BASE_DIR, "Bourgeois-Bold.ttf")
    
    try:
        font_header = ImageFont.truetype(font_path_bold, 29)    # Player Name
        font_mode_title = ImageFont.truetype(font_path_med, 26)  # Mode Titles
        font_mode_reward = ImageFont.truetype(font_path_bold, 27)  # Mode Titles
        font_rank_name = ImageFont.truetype(font_path_med, 34)  # Rank (Champion I, etc)
        font_stats = ImageFont.truetype(font_path_med, 24)      # Sub-stats
    except:
        font_header = font_mode_title = font_rank_name = font_stats = ImageFont.load_default()

    # --- 3. UPDATED HEADER (Clipped at Dividers) ---
    tile_color = (27, 31, 39)
    # First, draw the background bar for the whole header (Dark)
    draw.rounded_rectangle([25, 20, 875, 85], radius=12, fill=tile_color)
    
    # Second, draw the COLOR fill only till the first slanted divider (approx 450px)
    # We use a polygon to create the slanted edge at the end of the color bar

    grad_start = (85, 200, 255,100)  # Vibrant Blue (with your requested transparency)
    grad_end = (170, 100, 255,100)   # Vibrant Purple

    # Define the coordinates for the slanted color bar
    # Stopping at approximately 450px as before
    poly_coords = [(25, 20), (450, 20), (420, 85), (25, 85)]
    draw_slanted_gradient(draw, base, grad_start, grad_end, poly_coords)

    # Smooth the far-left rounded corner with the starting blue
    draw.pieslice([25, 20, 50, 85], 90, 270, fill=grad_start)

    # Third, draw the Slanted Divider Design Elements
    for i in range(3):
        x_off = 480 + (i * 25)
        draw.line([x_off, 20, x_off - 30, 85], fill=tile_color, width=12)

    # --- 4. ASSETS & TEXT ---
    platform_map = {"epic": "epic.png", "steam": "steam.png", "xbl": "xbl.png", "psn": "psn.png"}
    input_plat = platform_name.lower().split()[0]
    filename = platform_map.get(input_plat, "epic.png")
    plat_icon_path = os.path.join(BASE_DIR, "icons", filename)

    if os.path.exists(plat_icon_path):
        p_img = Image.open(plat_icon_path).convert("RGBA").resize((50, 38))
        base.paste(p_img, (36, 35), mask=p_img)

    draw.text((84, 34), f"{display_name.upper()}", font=font_header, fill=(255, 255, 255))
    
    reward_key = reward_level.split()[0].lower()
    reward_color = rank_colors.get(reward_key, (219, 90, 115))
    draw.text((640, 38), f"{reward_level}", font=font_mode_reward, fill=reward_color)

    # --- 5. RANK TILES ---
    positions = [(25, 110), (465, 110), (25, 345), (465, 345)]
    segment_map = {s['metadata']['name']: s for s in segments if s['type'] == 'playlist'}
    
    for count, mode_key in enumerate(desired_modes):
        x, y = positions[count]
        draw.rounded_rectangle([x, y, x + 410, y + 215], radius=12, fill=tile_color)
        
        if mode_key in segment_map:
            s = segment_map[mode_key]
            stats = s['stats']

            # NEW MAPPING: Shortens all main mode names for the UI
            short_names = {
                'Ranked Duel 1v1': 'Ranked 1v1',
                'Ranked Doubles 2v2': 'Ranked 2v2',
                'Ranked Standard 3v3': 'Ranked 3v3',
                'Tournament Matches': 'Tournament Rank'
            }
            display_mode_name = short_names.get(mode_key, mode_key)
            tier = stats['tier']['metadata']['name']
            rank_base = tier.split()[0].lower()
            text_color = rank_colors.get(rank_base, (255, 255, 255))
            file_rank = tier.lower().replace(" ", "_").replace("_iii", "_3").replace("_ii", "_2").replace("_i", "_1")

            draw.text((x + 20, y + 15), display_mode_name, font=font_mode_title, fill=(100, 200, 255))
            draw.text((x + 20, y + 53), tier, font=font_rank_name, fill=text_color)
            draw.text((x + 20, y + 89), stats.get('division', {}).get('metadata', {}).get('name', ''), font=font_mode_title, fill=(200, 200, 200))
            draw.text((x + 20, y + 115), f"{stats['rating']['value']} MMR", font=font_stats, fill=(160, 160, 160))
            draw.text((x + 20, y + 163), f"{stats.get('matchesPlayed', {}).get('value', 0)} Matches", font=font_stats, fill=(140, 140, 140))

            icon_path = os.path.join(BASE_DIR, "icons", f"{file_rank}.png")
            if os.path.exists(icon_path):
                icon = Image.open(icon_path).convert("RGBA").resize((105, 105))
                base.paste(icon, (x + 287, y + 24), mask=icon)

            streak_data = stats.get('winStreak', {})
            val = streak_data.get('value', 0)
            stype = streak_data.get('metadata', {}).get('type', 'win') 
            streak_text = f"{val} {'Loss' if stype == 'loss' else 'Win'}{'s' if val != 1 and stype == 'win' else '' if val != 1 else ''}"
            streak_color = (255, 60, 60) if stype == 'loss' else (0, 255, 100)
            draw.text((x + 314, y + 155), streak_text, font=font_stats, fill=streak_color)
        else:
            draw.text((x + 20, y + 20), mode_key, font=font_mode_title, fill=(100, 200, 255))
            draw.text((x + 20, y + 55), "Unranked", font=font_rank_name, fill=(150, 150, 150))
            # ADD THIS: Show unranked icon even if the mode isn't in segment_map
            unranked_icon_path = os.path.join(BASE_DIR, "icons", "unranked.png")
            if os.path.exists(unranked_icon_path):
                u_icon = Image.open(unranked_icon_path).convert("RGBA").resize((110, 110))
                base.paste(u_icon, (x + 286, y + 25), mask=u_icon)

    buffer = io.BytesIO()
    base.save(buffer, format="PNG")
    buffer.seek(0)
    return discord.File(fp=buffer, filename="rank_card.png")


def draw_slanted_gradient(draw, base_img, start_color, end_color, polygon_coords):
    """Draws a linear horizontal gradient within a slanted polygon."""
    # Find the bounds of the polygon
    min_x = min(p[0] for p in polygon_coords)
    max_x = max(p[0] for p in polygon_coords)
    
    # Create a mask for the slanted shape
    mask = Image.new('L', base_img.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.polygon(polygon_coords, fill=255)
    
    # Create the gradient overlay
    gradient = Image.new('RGBA', base_img.size)
    for x in range(min_x, max_x + 1):
        # Calculate the color at this X position
        mix = (x - min_x) / (max_x - min_x)
        r = int(start_color[0] + (end_color[0] - start_color[0]) * mix)
        g = int(start_color[1] + (end_color[1] - start_color[1]) * mix)
        b = int(start_color[2] + (end_color[2] - start_color[2]) * mix)
        a = start_color[3] if len(start_color) > 3 else 255
        
        # Draw a vertical line for this color step
        draw_grad = ImageDraw.Draw(gradient)
        draw_grad.line([(x, 0), (x, base_img.height)], fill=(r, g, b, a))
    
    # Paste the gradient onto the base image using the slanted mask
    base_img.paste(gradient, (0, 0), mask=mask)



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

    await interaction.response.defer()
    
    # Add a tiny "human" delay
    await asyncio.sleep(random.uniform(0.5, 1.5))
    
    url = f"https://api.tracker.gg/api/v2/rocket-league/standard/profile/{platform.value}/{username}"
    print(f"DEBUG: Testing this URL manually: {url}")
    if(username.lower()=="akshattyagi05"):
        display_name= "AkshatTyagi05"
        username="iiRw9"
        url = f"https://api.tracker.gg/api/v2/rocket-league/standard/profile/epic/iiRw9"
    else:
        display_name= username


    session = requests.Session()
    
    # These headers match what a real browser sends
    headers = {
        # 'TRN-Api-Key': str(TRACKER_KEY).strip(),
        'Accept': 'application/json, text/plain, */*',
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://rocketleague.tracker.network/',
        "Origin": "https://rocketleague.tracker.network",
        "DNT": "1",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
    }

    # Rotate between chrome versions to avoid fingerprint flagging
    impersonations = ["chrome110", "chrome116", "chrome120"]
    selected_profile = random.choice(impersonations)
    
    # Using a session to persist cookies and bypass basic Cloudflare checks
    

    print(f"DEBUG: Testing this URL manually: {url}")

    # Inform Discord that the bot is thinking (prevents "interaction failed" timeout)
    # await interaction.response.defer()

    try:
        # We use impersonate="chrome" to mimic a real Chrome browser's TLS fingerprint
        response = session.get(url, headers=headers, impersonate=selected_profile, timeout=10)
        
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

    # FIX: Define the path variable by calling your helper function
    db_path = get_db_path()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # INSERT OR REPLACE keeps the DB clean by updating existing users
        cursor.execute(
            "INSERT OR REPLACE INTO users (discord_id, rl_username, rl_platform) VALUES (?, ?, ?)",
            (interaction.user.id, username, platform.value)
        )
        conn.commit()
        conn.close()
        
        await interaction.followup.send(f"✅ Successfully linked **{username}** ({platform.name})!")
        
    except sqlite3.OperationalError as e:
        # If the table is missing for some reason, fix it on the fly
        if "no such table" in str(e):
            init_db()
            # Retry logic could go here, but a second click by the user is safer
            await interaction.followup.send("⚠️ Database structure was missing but has been repaired. Please try the command again.")
        else:
            await interaction.followup.send(f"❌ Database Error: {e}")



@bot.tree.command(name="rankme", description="Show your own Rocket League ranks")
async def rankme(interaction: discord.Interaction):
    await interaction.response.defer()

    db_path = get_db_path()
    
    # 1. Check Database for the user
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT rl_username, rl_platform FROM users WHERE discord_id = ?", (interaction.user.id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return await interaction.followup.send("❌ You haven't linked your account! Use `/ranklink` first.")
    
    saved_username, saved_platform = result
    
    # 2. Reuse your existing rank fetching logic here
    url = f"https://api.tracker.gg/api/v2/rocket-league/standard/profile/{saved_platform}/{saved_username}"


    session = requests.Session()
    
    # These headers match what a real browser sends
    headers = {
        # 'TRN-Api-Key': str(TRACKER_KEY).strip(),
        'Accept': 'application/json, text/plain, */*',
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://rocketleague.tracker.network/',
        "Origin": "https://rocketleague.tracker.network",
        "DNT": "1",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
    }

    # Rotate between chrome versions to avoid fingerprint flagging
    impersonations = ["chrome110", "chrome116", "chrome120"]
    selected_profile = random.choice(impersonations)

    print(f"DEBUG: Testing this URL manually: {url}")
    
    try:
        response = session.get(url, headers=headers, impersonate=selected_profile, timeout=10)
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
    # if(username.lower=="akshattyagi05"):
    #     display_name= "AkshatTyagi05"
    #     username="iiRw9"
    # else:
    #     display_name= username