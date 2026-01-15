import discord
from discord.ext import commands
import json, os
from dotenv import load_dotenv

load_dotenv()  # loads .env

TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = "!"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Discord config file
DISCORD_JSON = "backend/data/discord.json"
if not os.path.exists(DISCORD_JSON):
    with open(DISCORD_JSON,"w") as f:
        json.dump({"enabled":True,"token":TOKEN,"commands":{}},f, indent=2)

def save_discord(data):
    json.dump(data, open(DISCORD_JSON,"w"), indent=2)

def load_discord():
    return json.load(open(DISCORD_JSON))

# ================== Command Toggle Logic ==================
@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")
    config = load_discord()
    if not config.get("enabled", True):
        print("Bot is disabled in config!")

# Example Admin-only command
@bot.command()
async def admincmd(ctx):
    config = load_discord()
    cmd_cfg = config.get("commands", {}).get("admincmd", {})
    if cmd_cfg.get("admin_only", True):
        # Only allow users with role "Admin" (or admin in dashboard)
        allowed_roles = cmd_cfg.get("role_ids", [])
        if not any(role.id in allowed_roles for role in ctx.author.roles):
            await ctx.send("You do not have permission to run this command.")
            return
    await ctx.send(f"Admin command executed by {ctx.author}!")

# Example normal command
@bot.command()
async def hello(ctx):
    config = load_discord()
    cmd_cfg = config.get("commands", {}).get("hello", {"admin_only": False})
    await ctx.send(f"Hello {ctx.author}!")

# ================== Toggle Commands from Dashboard ==================
def toggle_command(cmd_name, enable=True):
    config = load_discord()
    if "commands" not in config:
        config["commands"] = {}
    if cmd_name not in config["commands"]:
        config["commands"][cmd_name] = {"enabled": enable, "admin_only": True, "role_ids": [], "user_ids": []}
    else:
        config["commands"][cmd_name]["enabled"] = enable
    save_discord(config)

# ================== Run Bot ==================
bot.run(TOKEN)
