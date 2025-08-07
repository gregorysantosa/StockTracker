import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

# Load environment variables from .env
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Setup intents
intents = discord.Intents.default()
intents.message_content = True  # Required for receiving message content

# Create bot with intents
bot = commands.Bot(command_prefix="!", intents=intents)

# List of Tickers we are tracking
ticker_list = []

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def hello(ctx):
    await ctx.send("Hello! I am your bot 🤖")

@bot.command()
async def addTicker(ctx, *, item: str):
    """Adds a ticker string to the list of tickers being watched by the bot"""
    ticker_list.append(item)
    await ctx.send(f"✅ Added: `{item}`\nCurrent list of tickers: {ticker_list}")

@bot.command()
async def removeTicker(ctx, *, item: str):
    """Remove a ticker from the ticker_list if it exists. Returns whether removal was successful or not."""
    try:
        ticker_list.remove(item)
        await ctx.send(f"❌ Removed: `{item}`\nCurrent list of tickers: {ticker_list}")
    except ValueError:
        await ctx.send(f"⚠️ Item `{item}` not found in the list.\nCurrent list of tickers: {ticker_list}")

@bot.command()
async def listTickers(ctx):
    """Lists all added Tickers"""
    if not ticker_list:
        await ctx.send("The list of tickers is currently empty.")
    else:
        await ctx.send("📃 Current list of tickers:\n" + "\n".join(f"- {s}" for s in ticker_list))

bot.run(TOKEN)
