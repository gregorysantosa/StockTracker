from datetime import datetime
import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord.ext import tasks
import requests

# Load environment variables from .env
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
GUILD_ID = 1402852211083448380  # Replace with your actual server ID
CHANNEL_ID = 1402885504742985760  # Replace with your target channel ID

# Setup intents
intents = discord.Intents.default()
intents.message_content = True  # Required for receiving message content

# Create bot with intents
bot = commands.Bot(command_prefix="!", intents=intents)

# List of Tickers we are tracking
ticker_list = []

# ---- READY COMMAND ----
@bot.event
async def on_ready():
    # Uncomment this block ONLY when you want to clear commands,
    # then comment it out after cleanup is done!

    # Example: Delete all guild commands
    guild = discord.Object(id=GUILD_ID)
    commands = await bot.tree.fetch_commands(guild=guild)
    for cmd in commands:
        await cmd.delete()
    print("Deleted all guild commands")

    # Example: Delete all global commands
    commands = await bot.tree.fetch_commands()
    for cmd in commands:
        await cmd.delete()
    print("Deleted all global commands")

    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"✅ Synced {len(synced)} command(s) to guild {GUILD_ID}:")
        for command in synced:
            print(f" • /{command.name} — {command.description}")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")


# ---- TICKER COMMANDS ----
@bot.tree.command(name="addticker", description="Add a ticker to the list", guild=discord.Object(id=GUILD_ID))
async def addticker(interaction: discord.Interaction, item: str):
    item = item.upper()
    if item in ticker_list:
        embed = discord.Embed(
            title="⚠️ Ticker Already Exists",
            description=f"`{item}` is already in the list.",
            color=discord.Color.orange()
        )
    else:
        ticker_list.append(item)
        embed = discord.Embed(
            title="✅ Ticker Added",
            description=f"`{item}` has been added to the list of tickers.",
            color=discord.Color.green()
        )

    # Format and show the updated ticker list
    if ticker_list:
        formatted_list = "\n".join(f"• `{t}`" for t in ticker_list)
        embed.add_field(name="📃 Current Ticker List", value=formatted_list, inline=False)
    else:
        embed.add_field(name="📃 Current Ticker List", value="*(List is empty)*", inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="listtickers", description="Show all tickers in the list", guild=discord.Object(id=GUILD_ID))
async def listtickers(interaction: discord.Interaction):
    if not ticker_list:
        embed = discord.Embed(
            title="📃 List",
            description="The ticker list is currently empty.",
            color=discord.Color.orange()
        )
    else:
        description = "\n".join(f"**{i+1}.** {s}" for i, s in enumerate(ticker_list))
        embed = discord.Embed(
            title="📃 List of tickers",
            description=description,
            color=discord.Color.blurple()
        )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="removeticker", description="Remove a ticker from the list", guild=discord.Object(id=GUILD_ID))
async def removeticker(interaction: discord.Interaction, item: str):
    item = item.upper()
    if item in ticker_list:
        ticker_list.remove(item)
        embed = discord.Embed(
            title="❌ Ticker Removed",
            description=f"`{item}` has been removed from the list of tickers.",
            color=discord.Color.red()
        )
    else:
        embed = discord.Embed(
            title="⚠️ Not Found",
            description=f"`{item}` was not found in the list of tickers.",
            color=discord.Color.dark_gold()
        )

    # Format and show the updated ticker list
    if ticker_list:
        formatted_list = "\n".join(f"• `{t}`" for t in ticker_list)
        embed.add_field(name="📃 Current Ticker List", value=formatted_list, inline=False)
    else:
        embed.add_field(name="📃 Current Ticker List", value="*(List is empty)*", inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ---- BROADCAST COMMANDS AND EVENT ----
@tasks.loop(minutes=30)
async def broadcast_tickers():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ Channel not found.")
        return

    if not ticker_list:
        await channel.send("⚠️ No tickers are currently being tracked.")
        return

    price_lines = []
    for ticker in ticker_list:
        price = get_stock_price(ticker)
        if price is not None:
            price_lines.append(f"• `{ticker.upper()}` → **${price:.2f}**")
        else:
            price_lines.append(f"• `{ticker.upper()}` → ❌ Failed to fetch")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"Broadcast happening at: {now}")
    embed = discord.Embed(
        title=f"📡 Ticker Broadcast Update ({now})",
        description="\n".join(price_lines),
        color=discord.Color.blue()
    )

    await channel.send(embed=embed)

@bot.tree.command(name="startbroadcast", description="Start periodic stock price updates", guild=discord.Object(id=GUILD_ID))
async def startbroadcast(interaction: discord.Interaction):
    if not broadcast_tickers.is_running():
        broadcast_tickers.start()
        await interaction.response.send_message("🟢 Broadcast loop started.", ephemeral=True)
    else:
        await interaction.response.send_message("⚠️ Broadcast loop is already running.", ephemeral=True)

@bot.tree.command(name="stopbroadcast", description="Stop periodic stock price updates", guild=discord.Object(id=GUILD_ID))
async def stopbroadcast(interaction: discord.Interaction):
    if broadcast_tickers.is_running():
        broadcast_tickers.stop()
        await interaction.response.send_message("🔴 Broadcast loop stopped.", ephemeral=True)
    else:
        await interaction.response.send_message("⚠️ Broadcast loop is not running.", ephemeral=True)

@bot.tree.command(name="gettickerprice", description="Get the latest price for a stock", guild=discord.Object(id=GUILD_ID))
async def gettickerprice(interaction: discord.Interaction, ticker: str):
    await interaction.response.defer(thinking=True)

    price = get_stock_price(ticker)
    if price is None:
        await interaction.followup.send(f"❌ Could not fetch price for `{ticker}`.")
    else:
        embed = discord.Embed(
            title=f"📈 {ticker.upper()} Price",
            description=f"Latest price: **${price:.2f}**",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="help", description="Show a summary of available commands", guild=discord.Object(id=GUILD_ID))
async def help(interaction: discord.Interaction):
    commands = await bot.tree.fetch_commands(guild=discord.Object(id=GUILD_ID))
    
    embed = discord.Embed(
        title="🤖 Bot Command Help",
        description="Here are the commands you can use:",
        color=discord.Color.blue()
    )
    
    for command in commands:
        embed.add_field(name=f"/{command.name}", value=command.description or "No description", inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ---- ALPHA VANTAGE API CALLS ----

def get_stock_price(ticker):
    url = (
        "https://www.alphavantage.co/query"
        f"?function=GLOBAL_QUOTE&symbol={ticker.upper()}&apikey={ALPHA_VANTAGE_API_KEY}"
    )
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error fetching price for {ticker}: {response.status_code} {response.text}")
        return None

    data = response.json()
    try:
        price_str = data["Global Quote"]["05. price"]
        return float(price_str)
    except (KeyError, ValueError):
        print(f"Price data not found or invalid for {ticker}")
        return None

# ---- MAIN ----
bot.run(TOKEN)
