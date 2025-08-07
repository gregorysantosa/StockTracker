# StockTracker

A Discord bot that tracks stock prices using their ticker symbols and periodically broadcasts ticker values in a server.

## Requirements
- Python 3.10+
- `Discord.py` v2.3+
- Discord Bot Token
- Alpha Vantage API Key

## Installation and Setup
1. Clone the repository
2. Install dependencies by running `pip install -r requirements.txt`
3. Follow instructions for Discord Bot setup at `https://discordpy.readthedocs.io/en/stable/discord.html`, make sure the bot has OAuth2 enabled and has permission to send embed links.
4. Get an API key from Alpha Vantage located at `https://www.alphavantage.co/`
5. Create a file named `.env` containing your DISCORD_BOT_TOKEN and ALPHA_VANTAGE_TOKEN.
6. Update `GUILD_ID` and `CHANNEL_ID` within `bot.py` with your server ID and channel ID, respectively.
7. Run `python discord.py`
