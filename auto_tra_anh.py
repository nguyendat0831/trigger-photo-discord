import os
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_BOT_TOKEN is missing. Create a .env file with DISCORD_BOT_TOKEN=<your_token>")

TRIGGERS = ["niggapb", "dmpb", "36", ]
PHOEBE_IMAGES = [
    r"D:\code\Python\My_project\image_raw\20250514212808.png",
    r"D:\code\Python\My_project\image_raw\20251114011137.png",
    r"D:\code\Python\My_project\image_raw\20251016130259.png",
]
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
@bot.event
async def on_ready():
    print("Online")
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    content = message.content.strip().lower()
    if content in TRIGGERS:
        image = random.choice(PHOEBE_IMAGES)
        if image.startswith(("http://", "https://")):
            await message.channel.send(image)
        else:
            await message.channel.send(file=discord.File(image))
        return
    await bot.process_commands(message)
bot.run(TOKEN)
