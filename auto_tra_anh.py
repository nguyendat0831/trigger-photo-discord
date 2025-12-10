import json
import os
from pathlib import Path
import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
LEARNING_CHANNEL_ID = os.getenv("LEARNING_CHANNEL_ID")
if not TOKEN:
    raise RuntimeError("chua nhét DISCORD_BOT_TOKEN vào .env")
if not LEARNING_CHANNEL_ID:
    raise RuntimeError("chua nhét LEARNING_CHANNEL_ID vào .env")
try:
    LEARNING_CHANNEL_ID_INT = int(LEARNING_CHANNEL_ID)
except ValueError as exc:
    raise RuntimeError("Bật quyền devs và lấy ID kênh chưa con vợ?") from exc
TRIGGERS_FILE = Path(__file__).resolve().parent / "triggers.json"
def load_db() -> dict:
    if not TRIGGERS_FILE.exists():
        TRIGGERS_FILE.write_text("{}", encoding="utf-8")
        data = {}
        print(f"[DB] Loaded {len(data)} triggers")
        return data
    try:
        data = json.loads(TRIGGERS_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            print(f"[DB] Loaded {len(data)} triggers")
            return data
    except json.JSONDecodeError:
        pass
    data = {}
    TRIGGERS_FILE.write_text("{}", encoding="utf-8")
    print(f"[DB] Loaded {len(data)} triggers")
    return data
def save_db(db: dict) -> None:
    TRIGGERS_FILE.write_text(json.dumps(db, indent=2), encoding="utf-8")
def is_image_attachment(attachment: discord.Attachment) -> bool:
    content_type = attachment.content_type or ""
    if content_type.startswith("image/"):
        return True
    filename = (attachment.filename or "").lower()
    return filename.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"))
async def url_is_valid(url: str) -> bool:
    timeout = aiohttp.ClientTimeout(total=5)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status >= 400:
                    return False
                return True
    except Exception:
        return False
async def handle_learning(message: discord.Message, content_raw: str, content_lower: str, db: dict) -> bool:
    if not content_raw or " " in content_raw or content_raw != content_lower:
        return False
    if len(message.attachments) != 1:
        return False
    attachment = message.attachments[0]
    if not is_image_attachment(attachment):
        return False
    db[content_lower] = attachment.url
    save_db(db)
    print(f"[LEARN] da luu keyword '{content_lower}' -> {attachment.url}")
    return True
async def respond_if_trigger(message: discord.Message, content_lower: str, db: dict) -> None:
    if content_lower not in db:
        return
    target = db[content_lower]
    print(f"Tu khoa {content_lower} -> sending {target}")
    if target.startswith(("http://", "https://")):
        is_valid = await url_is_valid(target)
        if not is_valid:
            if content_lower in db:
                del db[content_lower]
            print(f"[CLEANUP] Tu khoa '{content_lower}' bi xoa vi anh bi xoa trong kenh lay anh")
            save_db(db)
            try:
                await message.channel.send("ảnh đã bị xóa rồi")
            except Exception:
                pass
            return
    try:
        if target.startswith(("http://", "https://")):
            await message.channel.send(target)
        else:
            await message.channel.send(file=discord.File(target))
    except (discord.Forbidden, discord.HTTPException, discord.NotFound, Exception):
        if content_lower in db:
            del db[content_lower]
        print(f"[CLEANUP] Trigger '{content_lower}' removed due to broken URL.")
        save_db(db)
        try:
            await message.channel.send("ảnh đã bị xóa rồi")
        except Exception:
            pass
triggers_db = load_db()
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
@bot.event
async def on_ready():
    print("Online")
@bot.command(name="scan")
async def scan_learning_channel(ctx: commands.Context):
    channel = bot.get_channel(LEARNING_CHANNEL_ID_INT)
    if channel is None:
        try:
            channel = await bot.fetch_channel(LEARNING_CHANNEL_ID_INT)
        except Exception as exc:
            print(f"[DB] Scan bi loi trong kenh lay anh ({exc})")
            return
    added = 0
    async for msg in channel.history(limit=None, oldest_first=True):
        if msg.author.bot:
            continue
        content_raw = msg.content.strip()
        content_lower = content_raw.lower()
        if not content_raw or " " in content_raw or content_raw != content_lower:
            continue
        if len(msg.attachments) != 1:
            continue
        attachment = msg.attachments[0]
        if not is_image_attachment(attachment):
            continue
        if content_lower in triggers_db:
            continue
        url = attachment.url
        if url.startswith(("http://", "https://")):
            valid = await url_is_valid(url)
            if not valid:
                continue
        triggers_db[content_lower] = url
        added += 1
    if added > 0:
        save_db(triggers_db)
    print(f"[DB] Scan added {added} triggers")
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    content_raw = message.content.strip()
    content_lower = content_raw.lower()
    if message.channel.id == LEARNING_CHANNEL_ID_INT:
        learned = await handle_learning(message, content_raw, content_lower, triggers_db)
        if learned:
            return
        await bot.process_commands(message)
        return
    await respond_if_trigger(message, content_lower, triggers_db)
    await bot.process_commands(message)
bot.run(TOKEN)