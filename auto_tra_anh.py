import json
import os
from pathlib import Path
import discord
import aiohttp
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
async def xuly_tinnhan(message: discord.Message, content_raw: str, content_lower: str, db: dict) -> bool:
    if not content_raw or " " in content_raw or content_raw != content_lower:
        return False
    if len(message.attachments) != 1:
        return False
    attachment = message.attachments[0]
    if not is_image_attachment(attachment):
        return False
    db[content_lower] = attachment.url
    save_db(db)
    print(f"[LEARN] da luu ky tu trigger '{content_lower}' -> {attachment.url}")
    return True
async def xuly_trigger(message: discord.Message, content_lower: str, db: dict) -> None:
    if content_lower not in db:
        return
    tg = db[content_lower]
    print(f"[TRIGGER] {content_lower} -> sending {tg}")
    if tg.startswith(("http://", "https://")):
        is_valid = await url_is_valid(tg)
        if not is_valid:
            if content_lower in db:
                del db[content_lower]
            print(f"[CLEANUP] Tu '{content_lower}' bi xoa vi link hong")
            save_db(db)
            try:
                await message.channel.send("Ảnh đã bị xóa rồi, thêm lại đi con vợ")
            except Exception:
                pass
            return
    try:
        if tg.startswith(("http://", "https://")):
            await message.channel.send(tg)
        else:
            await message.channel.send(file=discord.File(tg))
    except (discord.Forbidden, discord.HTTPException, discord.NotFound, Exception):
        if content_lower in db:
            del db[content_lower]
        print(f"[CLEANUP] Tu '{content_lower}' bi xoa vi link hong")
        save_db(db)
        try:
            await message.channel.send("Ảnh đã bị xóa rồi, thêm lại đi con vợ")
        except Exception:
            pass
triggers_db = load_db()
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
@bot.event
async def on_ready():
    print("Online")
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    content_raw = message.content.strip()
    content_lower = content_raw.lower()
    if message.channel.id == LEARNING_CHANNEL_ID_INT:
        learned = await xuly_tinnhan(message, content_raw, content_lower, triggers_db)
        if learned:
            return
        await bot.process_commands(message)
        return
    await xuly_trigger(message, content_lower, triggers_db)
    await bot.process_commands(message)
bot.run(TOKEN)