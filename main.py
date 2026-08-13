import asyncio
from PIL import Image, ImageDraw, ImageFont
import io
import discord
from discord import app_commands
from curl_cffi import requests  # Use curl_cffi instead of standard requests
import os
from dotenv import load_dotenv
import random
import sqlite3
import time
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
        intents.members = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"✅ Slash commands synced for {self.user}")


bot = RLBot()


async def on_tree_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        msg = f"⏳ Slow down! Try that again in {error.retry_after:.1f}s."
    else:
        print(f"DEBUG: Unhandled command tree error: {error}")
        msg = "❌ Something went wrong running that command."

    if interaction.response.is_done():
        await interaction.followup.send(msg, ephemeral=True)
    else:
        await interaction.response.send_message(msg, ephemeral=True)


bot.tree.on_error = on_tree_error

# List of possible messages
random_messages = [
    "Chat… we pulled the ranks. It’s not looking good for bro.",
    "We got the ranks and I’m crying.",
    "These the ranks… imma let y’all process that.",
    "Ranked? Yeah. Respected? Debatable.",
    "We found the ranks and chat went silent.",
    "{user} This the rank? Oh nah 💀",
    "{user} We did the scan and I’m wheezing.",
    "{user} This what you wanted us to check? Crazy.",
    "Ranks obtained. Therapist contacted.",
    "I’d keep this private if I were you {user}.",
    "These the ranks. I need a moment {user}.",
    "{user} These the ranks… imma hold your hand when I say this…",
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def create_rank_card(username, platform_name, display_name, segments, mode_type="standard"):
    if mode_type == "extras":
        desired_modes = ['Rumble', 'Dropshot', 'Hoops', 'Heatseeker']
    else:
        desired_modes = ['Ranked Duel 1v1', 'Ranked Doubles 2v2', 'Ranked Standard 3v3', 'Tournament Matches']

    base = Image.new("RGBA", (900, 600), (29, 33, 42))
    draw = ImageDraw.Draw(base)

    rank_colors = {
        "bronze": (205, 127, 50), "silver": (192, 192, 192), "gold": (255, 215, 0),
        "platinum": (0, 255, 255), "diamond": (0, 191, 255), "champion": (160, 32, 240), "grand": (255, 50, 50),
        "grand_champion": (255, 50, 50), "supersonic_legend": (255, 255, 255), "unranked": (150, 150, 150)
    }

    reward_level = "Unranked"
    for s in segments:
        if s['type'] == 'overview':
            reward_level = s['stats'].get('seasonRewardLevel', {}).get('metadata', {}).get('rankName', 'Unranked')
            break

    font_path_med = os.path.join(BASE_DIR, "Bourgeois-Medium.ttf")
    font_path_bold = os.path.join(BASE_DIR, "Bourgeois-Bold.ttf")
    try:
        font_header = ImageFont.truetype(font_path_bold, 29)
        font_mode_title = ImageFont.truetype(font_path_med, 26)
        font_mode_reward = ImageFont.truetype(font_path_bold, 27)
        font_rank_name = ImageFont.truetype(font_path_bold, 33)
        font_stats = ImageFont.truetype(font_path_med, 23)
        font_mmr = ImageFont.truetype(font_path_med, 24)
    except Exception:
        font_header = font_mode_title = font_rank_name = font_stats = font_mmr = font_mode_reward = ImageFont.load_default()

    tile_color = (27, 31, 39)
    draw.rounded_rectangle([25, 20, 875, 85], radius=12, fill=tile_color)

    grad_start = (85, 200, 255, 100)
    grad_end = (170, 100, 255, 100)
    poly_coords = [(25, 20), (450, 20), (420, 85), (25, 85)]
    draw_slanted_gradient(draw, base, grad_start, grad_end, poly_coords)
    draw.pieslice([25, 20, 50, 85], 90, 270, fill=grad_start)

    for i in range(3):
        x_off = 480 + (i * 25)
        draw.line([x_off, 20, x_off - 30, 85], fill=tile_color, width=12)

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

    positions = [(25, 110), (465, 110), (25, 345), (465, 345)]
    segment_map = {s['metadata']['name']: s for s in segments if s['type'] == 'playlist'}

    for count, mode_key in enumerate(desired_modes):
        x, y = positions[count]
        draw.rounded_rectangle([x, y, x + 410, y + 215], radius=12, fill=tile_color)

        if mode_key in segment_map:
            s = segment_map[mode_key]
            stats = s['stats']

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
            draw.text((x + 20, y + 119), f"{stats['rating']['value']} MMR", font=font_mmr, fill=(160, 160, 160))
            draw.text((x + 20, y + 164), f"{stats.get('matchesPlayed', {}).get('value', 0)} Matches", font=font_stats, fill=(140, 140, 140))

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
    min_x = min(p[0] for p in polygon_coords)
    max_x = max(p[0] for p in polygon_coords)

    mask = Image.new('L', base_img.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.polygon(polygon_coords, fill=255)

    gradient = Image.new('RGBA', base_img.size)
    for x in range(min_x, max_x + 1):
        mix = (x - min_x) / (max_x - min_x)
        r = int(start_color[0] + (end_color[0] - start_color[0]) * mix)
        g = int(start_color[1] + (end_color[1] - start_color[1]) * mix)
        b = int(start_color[2] + (end_color[2] - start_color[2]) * mix)
        a = start_color[3] if len(start_color) > 3 else 255
        draw_grad = ImageDraw.Draw(gradient)
        draw_grad.line([(x, 0), (x, base_img.height)], fill=(r, g, b, a))

    base_img.paste(gradient, (0, 0), mask=mask)


# 1. INITIAL SETUP & KEY VERIFICATION
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


# --- FETCH LOGIC (shared by /rank and /rankme) -----------------------------
# NOTE: Tracker.gg does not publish an official Rocket League API (their own
# docs only cover CS2/Valorant/Fortnite/etc). This means /rank and /rankme are
# calling an internal endpoint that's only meant for tracker.gg's own website,
# and it sits behind Cloudflare bot detection. That detection can and does
# change over time, so 403s here can never be fully "solved" - only made more
# resilient. Treat everything below as damage control, not a permanent fix.

# Each impersonation profile MUST be paired with a matching User-Agent.
# The previous code randomized the TLS fingerprint (impersonate=chrome110/116/120)
# but always sent a Chrome/120 User-Agent header. A JA3/TLS fingerprint that
# doesn't match the declared browser version is one of the easiest bot signals
# to detect - this mismatch was very likely a big source of your 403s.
IMPERSONATION_PROFILES = {
    "chrome110": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "chrome116": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "chrome120": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

# Very small in-memory cache so a burst of /rank or /rankme calls for the
# same player within a short window doesn't hammer tracker.gg repeatedly -
# fewer requests per minute means less chance of tripping rate-based blocks.
_rank_cache = {}
CACHE_TTL_SECONDS = 60


class TrackerBlocked(Exception):
    """Raised when every retry attempt still comes back 403."""
    pass


class TrackerNotFound(Exception):
    pass


async def fetch_player_segments(platform_value: str, username: str, max_attempts: int = 3, force_refresh: bool = False):
    """
    Fetch segments for a player, with retry + backoff across a few
    fingerprint/UA pairs. Returns the segments list on success, or raises
    TrackerBlocked / TrackerNotFound / Exception on failure.

    force_refresh=True skips the cache lookup (but still writes the fresh
    result back into the cache) - use this for explicit "Update" clicks so
    the button doesn't just hand back the same cached data.
    """
    cache_key = f"{platform_value}:{username.lower()}"
    if not force_refresh:
        cached = _rank_cache.get(cache_key)
        if cached and (time.time() - cached[0]) < CACHE_TTL_SECONDS:
            return cached[1]

    url = f"https://api.tracker.gg/api/v2/rocket-league/standard/profile/{platform_value}/{username}"
    print(f"DEBUG: Fetching {url}")

    profiles = list(IMPERSONATION_PROFILES.items())
    random.shuffle(profiles)

    last_status = None
    last_body_snippet = ""

    for attempt in range(max_attempts):
        impersonate_profile, matching_ua = profiles[attempt % len(profiles)]

        session = requests.Session()
        headers = {
            'Accept': 'application/json, text/plain, */*',
            "User-Agent": matching_ua,
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://rocketleague.tracker.network/',
            "Origin": "https://rocketleague.tracker.network",
            "DNT": "1",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        }

        # small human-ish delay, growing a bit each retry
        await asyncio.sleep(random.uniform(0.5, 1.5) + attempt * 1.0)

        try:
            response = session.get(url, headers=headers, impersonate=impersonate_profile, timeout=10)
        except Exception as e:
            print(f"DEBUG: request error on attempt {attempt + 1} ({impersonate_profile}): {e}")
            last_status = "exception"
            continue

        print(f"DEBUG: attempt {attempt + 1}/{max_attempts} profile={impersonate_profile} -> status {response.status_code} "
              f"cf-ray={response.headers.get('cf-ray')} server={response.headers.get('server')}")

        if response.status_code == 200:
            data = response.json()
            segments = data['data']['segments']
            _rank_cache[cache_key] = (time.time(), segments)
            return segments

        if response.status_code == 404:
            raise TrackerNotFound()

        last_status = response.status_code
        last_body_snippet = response.text[:200]

        if response.status_code == 403:
            # log a snippet so you can tell an IP/rate block apart from a JS
            # challenge page apart from a straight-up ban, next time this happens
            print(f"DEBUG: 403 body snippet: {last_body_snippet!r}")
            continue  # try again with a different profile
        else:
            # non-403 non-200/404 error - no point burning retries on it
            break

    if last_status == 403:
        raise TrackerBlocked()
    raise Exception(f"Unhandled status: {last_status} | {last_body_snippet}")


# 2. BOT CLASS DEFINITION (kept as in original - RLBot already defined above,
# this second definition in the original file was dead code and has been removed)

class RankView(discord.ui.View):
    BUTTON_COOLDOWN_SECONDS = 20.0

    def __init__(self, username, platform_value, display_name, segments):
        super().__init__(timeout=None)
        self.username = username
        # raw platform code (epic/steam/psn/xbl) - needed both to re-fetch
        # from tracker.gg AND to pick the right platform icon in the card
        self.platform_value = platform_value
        self.display_name = display_name
        self.segments = segments
        self.current_mode = "standard"
        self._last_click = 0.0

    async def _cooldown_ok(self, interaction: discord.Interaction) -> bool:
        """Shared cooldown for both buttons - checked before either one
        mutates state, so a blocked click can't leave the button label out
        of sync with what's actually on the card."""
        now = time.time()
        remaining = self.BUTTON_COOLDOWN_SECONDS - (now - self._last_click)
        if remaining > 0:
            await interaction.response.send_message(
                f"⏳ Slow down! Try again in {remaining:.1f}s.", ephemeral=True
            )
            return False
        self._last_click = now
        return True

    async def send_new_card(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # Always pull fresh data on click - both the mode-switch button and
        # the Update button used to just redraw whatever self.segments was
        # from the very first fetch, so ranks looked "frozen." force_refresh
        # bypasses the short-lived cache so this isn't just re-serving the
        # same cached response either.
        try:
            self.segments = await fetch_player_segments(self.platform_value, self.username, force_refresh=True)
        except TrackerNotFound:
            await interaction.followup.send("❌ Could not find that profile anymore.", ephemeral=True)
            return
        except TrackerBlocked:
            await interaction.followup.send(
                "⚠️ Tracker.gg is blocking requests right now - showing the last ranks I was able to fetch.",
                ephemeral=True
            )
            # fall through and render with the last good self.segments
        except Exception as e:
            print(f"DEBUG Error refreshing: {e}")
            await interaction.followup.send(
                "⚠️ Couldn't refresh ranks right now - showing the last ranks I was able to fetch.",
                ephemeral=True
            )

        file = create_rank_card(
            self.username,
            self.platform_value,
            self.display_name,
            self.segments,
            mode_type=self.current_mode
        )
        selected_text = random.choice(random_messages).format(user=interaction.user.mention)
        await interaction.followup.send(
            content=selected_text,
            file=file,
            view=self
        )

    @discord.ui.button(label="Extras", style=discord.ButtonStyle.gray, emoji="🏀")
    async def extras_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._cooldown_ok(interaction):
            return

        if self.current_mode == "standard":
            self.current_mode = "extras"
            button.label = "Standard"
            button.emoji = "⚽"
        else:
            self.current_mode = "standard"
            button.label = "Extras"
            button.emoji = "🏀"
        await self.send_new_card(interaction)

    @discord.ui.button(label="Update", style=discord.ButtonStyle.gray, emoji="🔄")
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._cooldown_ok(interaction):
            return
        await self.send_new_card(interaction)


# 3. THE RANK COMMAND
@bot.tree.command(name="rank", description="Get Rocket League ranks by searching Username")
@app_commands.checks.cooldown(1, 15.0, key=lambda i: i.user.id)
@app_commands.describe(platform="Platform (epic, steam, psn, xbl)", username="Player ID")
@app_commands.choices(platform=[
    app_commands.Choice(name="Epic Games", value="epic"),
    app_commands.Choice(name="Steam", value="steam"),
    app_commands.Choice(name="PlayStation", value="psn"),
    app_commands.Choice(name="Xbox", value="xbl")
])
async def rank(interaction: discord.Interaction, platform: app_commands.Choice[str], username: str):
    await interaction.response.defer()

    display_name = username

    try:
        segments = await fetch_player_segments(platform.value, username)
    except TrackerNotFound:
        return await interaction.followup.send(f"❌ 404: Player `{username}` not found. Check platform and ID.")
    except TrackerBlocked:
        return await interaction.followup.send(
            "❌ 403: Tracker.gg is blocking requests right now (this happens with unofficial/undocumented "
            "APIs - there's no official public Rocket League API from tracker.gg). Try again in a bit."
        )
    except Exception as e:
        print(f"DEBUG Error: {e}")
        return await interaction.followup.send("❌ An unexpected error occurred. Check terminal for logs.")

    view = RankView(username, platform.value, display_name, segments)
    file = create_rank_card(username, platform.value, display_name, segments, mode_type="standard")
    selected_text = random.choice(random_messages).format(user=interaction.user.mention)
    await interaction.followup.send(
        content=selected_text,
        file=file,
        view=view
    )


@bot.tree.command(name="ranklink", description="Link your Rocket League account to your Discord ID")
@app_commands.checks.cooldown(1, 15.0, key=lambda i: i.user.id)
@app_commands.describe(platform="Select your platform", username="Your Rocket League Username/ID")
@app_commands.choices(platform=[
    app_commands.Choice(name="Epic Games", value="epic"),
    app_commands.Choice(name="Steam", value="steam"),
    app_commands.Choice(name="PlayStation", value="psn"),
    app_commands.Choice(name="Xbox", value="xbl")
])
async def ranklink(interaction: discord.Interaction, platform: app_commands.Choice[str], username: str):
    await interaction.response.defer(ephemeral=True)
    db_path = get_db_path()

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO users (discord_id, rl_username, rl_platform) VALUES (?, ?, ?)",
            (interaction.user.id, username, platform.value)
        )
        conn.commit()
        conn.close()
        await interaction.followup.send(f"✅ Successfully linked **{username}** ({platform.name})!")
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            init_db()
            await interaction.followup.send("⚠️ Database structure was missing but has been repaired. Please try the command again.")
        else:
            await interaction.followup.send(f"❌ Database Error: {e}")


@bot.tree.command(name="rankunlink", description="Unlink your Rocket League account from your Discord ID")
@app_commands.checks.cooldown(1, 15.0, key=lambda i: i.user.id)
async def rankunlink(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    db_path = get_db_path()

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT rl_username FROM users WHERE discord_id = ?", (interaction.user.id,))
        result = cursor.fetchone()

        if not result:
            conn.close()
            return await interaction.followup.send("❌ You don't have a linked account to unlink.", ephemeral=True)

        cursor.execute("DELETE FROM users WHERE discord_id = ?", (interaction.user.id,))
        conn.commit()
        conn.close()
        await interaction.followup.send(f"✅ Unlinked **{result[0]}** from your Discord account.", ephemeral=True)
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            init_db()
            await interaction.followup.send("⚠️ Database structure was missing but has been repaired. Please try again.", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Database Error: {e}", ephemeral=True)


@bot.tree.command(name="rankme", description="Show your own Rocket League ranks")
@app_commands.checks.cooldown(1, 15.0, key=lambda i: i.user.id)
async def rankme(interaction: discord.Interaction):
    await interaction.response.defer()
    db_path = get_db_path()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT rl_username, rl_platform FROM users WHERE discord_id = ?", (interaction.user.id,))
    result = cursor.fetchone()
    conn.close()

    if not result:
        return await interaction.followup.send("❌ You haven't linked your account! Use `/ranklink` first.")

    saved_username, saved_platform = result

    try:
        segments = await fetch_player_segments(saved_platform, saved_username)
    except TrackerNotFound:
        return await interaction.followup.send("❌ Could not find that linked profile anymore. Try `/ranklink` again.")
    except TrackerBlocked:
        return await interaction.followup.send(
            "❌ 403: Tracker.gg is blocking requests right now. Try again in a bit."
        )
    except Exception as e:
        print(f"DEBUG Error: {e}")
        return await interaction.followup.send("❌ An error occurred while fetching your ranks.")

    view = RankView(saved_username, saved_platform, saved_username, segments)
    file = create_rank_card(saved_username, saved_platform, saved_username, segments)
    selected_text = random.choice(random_messages).format(user=interaction.user.mention)
    await interaction.followup.send(content=selected_text, file=file, view=view)


# 4. RUN THE BOT
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Cannot start bot: DISCORD_TOKEN missing.")