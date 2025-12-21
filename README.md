# Discord Trigger Bot

## Overview
This bot learns keyword triggers from a learning channel and responds with the original media (image/video/audio) or text. Triggers are case-insensitive and isolated per guild.

## Features
- Learn triggers from messages in a configured learning channel.
- Respond to triggers by fetching the original message and sending its attachment (avoids CDN expiry issues).
- Support image, video, and audio attachments.
- Support text triggers via `!text keyword-reply`.
- Per-guild learning channels via `!setlearning`.
- Scan learning history with `!scan`.
- List triggers with `!list`.
- Help text stored in `help.txt` and shown by `!h`.

## Requirements
```
pip install -r requirements.txt
```

## .env
Create a `.env` file:
```
DISCORD_BOT_TOKEN="your_bot_token_here"
```
`LEARNING_CHANNEL_ID` is optional. If set, it is used as a fallback learning channel for guilds that have not run `!setlearning`.

## Permissions
Recommended permissions:
- View Channels
- Send Messages (learning channel)
- Embed Links
- Attach Files
- Add Reactions
- Use External Emoji
- Use External Stickers
- Read Message History

## Commands
- `!setlearning <channel_id>`: set the learning channel for the current guild (requires Manage Guild or Administrator).
- `!scan`: scan the learning channel history and add missing triggers.
- `!text keyword-reply`: add a text trigger (example: `!text abc-xyz`).
- `!list`: list saved keywords for the current guild.
- `!h`: show help text from `help.txt`.

## Learning Rules
In the learning channel:
- Message must be a single word (no spaces). Case does not matter.
- Message must have exactly one attachment (image/video/audio).
- If the keyword already exists, the bot reacts with ❌.
- If new, the bot saves it and reacts with ✅.

## Trigger Behavior
- Triggers are matched case-insensitively.
- Text triggers reply with the configured text.
- Media triggers fetch the original message by channel_id and message_id, then send the attachment URL.
- If the source message is missing or cannot be fetched, the trigger is removed.

## Database Format
`triggers.json` structure (per guild):
```
{
  "<guild_id>": {
    "_LEARNING_CHANNEL_ID": 1234567890,
    "_TEXT_TRIGGERS": {
      "hello": "hi"
    },
    "<media_keyword>": {
      "channel_id": 123,
      "message_id": 456
    }
  }
}
```

## Notes
- Enable Message Content Intent in the Discord developer portal and bot settings.
- The bot is designed to run 24/7 and handle multiple servers.
