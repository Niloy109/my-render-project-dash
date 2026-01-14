# bot/bot.py
import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN", "")

bot = commands.Bot(command_prefix="!")

@bot.event
async def on_ready():
    print(f"Bot online as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓")

if TOKEN:
    bot.run(TOKEN)
else:
    print("⚠️ No Discord token set!")
