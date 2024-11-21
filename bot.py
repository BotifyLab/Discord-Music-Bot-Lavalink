# bot.py
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix="?", intents=intents, help_command=None)

@client.event
async def on_ready():
    # Set the bot's playing status
    await client.change_presence(activity=discord.Game("MYBOT"))
    print(f'Logged in as {client.user.name} (ID: {client.user.id})')

async def main():
    # Load the play command cog
    await client.load_extension("commands.play")
    await client.start(TOKEN)

# Run the bot
asyncio.run(main())
