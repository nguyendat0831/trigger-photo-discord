import json
import os
from pathlib import Path
import discord
from discord.ext import commands
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
LEARNING_CHANNEL_ID = os.getenv("LEARNING_CHANNEL_ID")
LEARNING_CHANNEL_ID_INT = None
if not TOKEN:
    raise RuntimeError("chua nhet DISCORD_BOT_TOKEN vao .env")
if LEARNING_CHANNEL_ID:
    try:
        LEARNING_CHANNEL_ID_INT = int(LEARNING_CHANNEL_ID)
    except ValueError as exc:
        raise RuntimeError("bat quyen devs va lay ID kenh chua con vo?") from exc
LEARNING_CHANNEL_KEY = "_LEARNING_CHANNEL_ID"
TEXT_TRIGGERS_KEY = "_TEXT_TRIGGERS"
TRIGGERS_FILE = Path(__file__).resolve().parent / "triggers.json"
def load_db() -> dict:
    if not TRIGGERS_FILE.exists():
        TRIGGERS_FILE.write_text("{}", encoding="utf-8")
        data = {}
        print(f"[DB] Loaded {len(data)} triggers")
        return data
    try:
        data = json.loads(TRIGGERS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        data = {}
    if not isinstance(data, dict):
        data = {}
    cleaned = {}
    for guild_id, triggers in data.items():
        if not isinstance(triggers, dict):
            continue
        guild_triggers = {}
        for key, value in triggers.items():
            if not isinstance(key, str):
                continue
            if key == LEARNING_CHANNEL_KEY:
                if isinstance(value, int):
                    guild_triggers[key] = value
                continue
            if key == TEXT_TRIGGERS_KEY:
                if isinstance(value, dict):
                    text_triggers = {}
                    for text_key, text_value in value.items():
                        if isinstance(text_key, str) and isinstance(text_value, str):
                            text_triggers[text_key] = text_value
                    if text_triggers:
                        guild_triggers[key] = text_triggers
                continue
            if not isinstance(value, dict):
                continue
            channel_id = value.get("channel_id")
            message_id = value.get("message_id")
            if isinstance(channel_id, int) and isinstance(message_id, int):
                guild_triggers[key] = {
                    "channel_id": channel_id,
                    "message_id": message_id,
                }
        if guild_triggers:
            cleaned[str(guild_id)] = guild_triggers
    total = 0
    for triggers in cleaned.values():
        for key, value in triggers.items():
            if key == LEARNING_CHANNEL_KEY:
                continue
            if key == TEXT_TRIGGERS_KEY:
                if isinstance(value, dict):
                    total += len(value)
                continue
            total += 1
    print(f"[DB] Loaded {total} triggers")
    return cleaned
def save_db(db: dict) -> None:
    TRIGGERS_FILE.write_text(json.dumps(db, indent=2), encoding="utf-8")
def is_media_attachment(attachment: discord.Attachment) -> bool:
    content_type = attachment.content_type or ""
    if content_type.startswith(("image/", "video/", "audio/")):
        return True
    filename = (attachment.filename or "").lower()
    return filename.endswith((
        ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp",
        ".mp4", ".webm", ".mov", ".avi", ".mkv", ".m4v",
        ".mp3", ".wav", ".ogg", ".m4a", ".flac", ".aac", ".opus",
    ))
def remove_trigger(db: dict, guild_id: str, key: str) -> None:
    guild_triggers = db.get(guild_id)
    if not guild_triggers or key not in guild_triggers:
        return
    del guild_triggers[key]
    if not guild_triggers:
        del db[guild_id]
    save_db(db)
    print(f"[CLEANUP] Trigger '{key}' removed due to missing source message.")
async def handle_learning(message: discord.Message, content_raw: str, content_lower: str, db: dict) -> bool:
    if not content_raw or " " in content_raw:
        return False
    if len(message.attachments) != 1:
        return False
    attachment = message.attachments[0]
    if not is_media_attachment(attachment):
        return False
    if message.guild is None:
        return False
    guild_id = str(message.guild.id)
    guild_triggers = db.setdefault(guild_id, {})
    text_triggers = guild_triggers.get(TEXT_TRIGGERS_KEY)
    if not isinstance(text_triggers, dict):
        text_triggers = {}
    if content_lower in guild_triggers or content_lower in text_triggers:
        try:
            await message.add_reaction("❌")
        except Exception:
            pass
        return True
    guild_triggers[content_lower] = {
        "channel_id": message.channel.id,
        "message_id": message.id,
    }
    save_db(db)
    print(f"[LEARN] Saved keyword '{content_lower}' -> {message.channel.id}/{message.id}")
    try:
        await message.add_reaction("✅")
    except Exception:
        pass
    return True
async def respond_if_trigger(message: discord.Message, content_lower: str, db: dict) -> None:
    if message.guild is None:
        return
    guild_id = str(message.guild.id)
    guild_triggers = db.get(guild_id)
    if not guild_triggers:
        return
    text_triggers = guild_triggers.get(TEXT_TRIGGERS_KEY)
    if isinstance(text_triggers, dict) and content_lower in text_triggers:
        try:
            await message.channel.send(text_triggers[content_lower])
        except (discord.Forbidden, discord.HTTPException, discord.NotFound):
            pass
        return
    if content_lower not in guild_triggers:
        return
    entry = guild_triggers[content_lower]
    channel_id = entry.get("channel_id")
    message_id = entry.get("message_id")
    if not isinstance(channel_id, int) or not isinstance(message_id, int):
        remove_trigger(db, guild_id, content_lower)
        return
    print(f"[TRIGGER] {content_lower} -> fetch {channel_id}/{message_id}")
    try:
        channel = message.guild.get_channel(channel_id)
        if channel is None:
            channel = await message.guild.fetch_channel(channel_id)
    except (discord.Forbidden, discord.NotFound, discord.HTTPException):
        remove_trigger(db, guild_id, content_lower)
        try:
            await message.channel.send("ảnh đã bị xóa rồi")
        except Exception:
            pass
        return
    try:
        original_message = await channel.fetch_message(message_id)
    except (discord.Forbidden, discord.NotFound, discord.HTTPException):
        remove_trigger(db, guild_id, content_lower)
        try:
            await message.channel.send("ảnh đã bị xóa rồi")
        except Exception:
            pass
        return
    if len(original_message.attachments) != 1:
        remove_trigger(db, guild_id, content_lower)
        try:
            await message.channel.send("ảnh đã bị xóa rồi")
        except Exception:
            pass
        return
    attachment = original_message.attachments[0]
    try:
        await message.channel.send(attachment.url)
    except discord.Forbidden:
        return
    except (discord.HTTPException, discord.NotFound):
        remove_trigger(db, guild_id, content_lower)
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
@bot.command(name="setlearning")
async def set_learning_channel(ctx: commands.Context, channel_id: str = None):
    if ctx.guild is None:
        return
    perms = ctx.author.guild_permissions
    if not (perms.manage_guild or perms.administrator):
        return
    if channel_id is None:
        return
    try:
        channel_id_int = int(channel_id)
    except ValueError:
        return
    channel = ctx.guild.get_channel(channel_id_int)
    if channel is None:
        try:
            channel = await ctx.guild.fetch_channel(channel_id_int)
        except Exception:
            return
    guild_id = str(ctx.guild.id)
    guild_triggers = triggers_db.setdefault(guild_id, {})
    guild_triggers[LEARNING_CHANNEL_KEY] = channel.id
    save_db(triggers_db)
    try:
        await ctx.message.add_reaction("✅")
    except Exception:
        pass
@bot.command(name="text")
async def add_text_trigger(ctx: commands.Context, *, payload: str = None):
    if ctx.guild is None:
        return
    if not payload or "-" not in payload:
        return
    key, reply = payload.split("-", 1)
    key = key.strip().lower()
    reply = reply.strip()
    if not key or " " in key:
        return
    if not reply:
        return
    guild_id = str(ctx.guild.id)
    guild_triggers = triggers_db.setdefault(guild_id, {})
    text_triggers = guild_triggers.get(TEXT_TRIGGERS_KEY)
    if not isinstance(text_triggers, dict):
        text_triggers = {}
        guild_triggers[TEXT_TRIGGERS_KEY] = text_triggers
    if key in guild_triggers or key in text_triggers:
        try:
            await ctx.message.add_reaction("❌")
        except Exception:
            pass
        return
    text_triggers[key] = reply
    save_db(triggers_db)
    try:
        await ctx.message.add_reaction("✅")
    except Exception:
        pass
@bot.command(name="h")
async def show_help(ctx: commands.Context):
    try:
        help_path = Path(__file__).resolve().parent / "help.txt"
        content = help_path.read_text(encoding="utf-8").strip()
        if not content:
            return
        await ctx.send(content)
    except Exception:
        pass
@bot.command(name="list")
async def list_triggers(ctx: commands.Context):
    if ctx.guild is None:
        return
    guild_id = str(ctx.guild.id)
    guild_triggers = triggers_db.get(guild_id, {})
    text_triggers = guild_triggers.get(TEXT_TRIGGERS_KEY)
    if not isinstance(text_triggers, dict):
        text_triggers = {}
    media_keys = []
    for key in guild_triggers.keys():
        if key in (LEARNING_CHANNEL_KEY, TEXT_TRIGGERS_KEY):
            continue
        media_keys.append(key)
    media_keys.sort()
    text_keys = sorted(text_triggers.keys())
    if not media_keys and not text_keys:
        try:
            await ctx.send("Chua co keyword nao.")
        except Exception:
            pass
        return
    lines = ["Danh sach keyword:"]
    if media_keys:
        lines.append("Media: " + ", ".join(media_keys))
    if text_keys:
        lines.append("Text: " + ", ".join(text_keys))
    message = "\n".join(lines)
    try:
        await ctx.send(message)
    except Exception:
        pass
@bot.command(name="scan")
async def scan_learning_channel(ctx: commands.Context):
    if ctx.guild is None:
        return
    guild_id = str(ctx.guild.id)
    guild_triggers = triggers_db.setdefault(guild_id, {})
    text_triggers = guild_triggers.get(TEXT_TRIGGERS_KEY)
    if not isinstance(text_triggers, dict):
        text_triggers = {}
    learning_channel_id = guild_triggers.get(LEARNING_CHANNEL_KEY)
    if not isinstance(learning_channel_id, int):
        learning_channel_id = LEARNING_CHANNEL_ID_INT
    if not isinstance(learning_channel_id, int):
        print("[DB] Scan failed: learning channel not set")
        return
    channel = ctx.guild.get_channel(learning_channel_id)
    if channel is None:
        try:
            channel = await ctx.guild.fetch_channel(learning_channel_id)
        except Exception as exc:
            print(f"[DB] Scan failed: cannot fetch learning channel ({exc})")
            return
    added = 0
    async for msg in channel.history(limit=None, oldest_first=True):
        if msg.author.bot:
            continue
        content_raw = msg.content.strip()
        content_lower = content_raw.lower()
        if not content_raw or " " in content_raw:
            continue
        if len(msg.attachments) != 1:
            continue
        attachment = msg.attachments[0]
        if not is_media_attachment(attachment):
            continue
        if content_lower in guild_triggers or content_lower in text_triggers:
            continue
        guild_triggers[content_lower] = {
            "channel_id": channel.id,
            "message_id": msg.id,
        }
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
    learning_channel_id = None
    if message.guild is not None:
        guild_id = str(message.guild.id)
        guild_triggers = triggers_db.get(guild_id, {})
        stored_id = guild_triggers.get(LEARNING_CHANNEL_KEY)
        if isinstance(stored_id, int):
            learning_channel_id = stored_id
        else:
            learning_channel_id = LEARNING_CHANNEL_ID_INT
    if learning_channel_id is not None and message.channel.id == learning_channel_id:
        learned = await handle_learning(message, content_raw, content_lower, triggers_db)
        if learned:
            return
        await bot.process_commands(message)
        return
    await respond_if_trigger(message, content_lower, triggers_db)
    await bot.process_commands(message)
bot.run(TOKEN)
