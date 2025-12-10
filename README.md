# Trigger Photo Discord Bot
Features
- Get new triggers directly from user messages in the channel.
- Stores keyword–image mappings in `triggers.json`.
- Includes a `!scan` command to rebuild the database from channel history if the JSON file is lost.
Installation
1. Install dependencies
```
pip install -r requirements.txt
```
2. Create a `.env` file
```
DISCORD_BOT_TOKEN="your_bot_token_here"
LEARNING_CHANNEL_ID=1234567890
```
Required Permissions
Make sure the bot has at least the following permissions in both the learning channel and any channel it needs to respond in:
- Read Messages
- Send Messages
- Read Message History
- Attach Files
How to Teach the Bot a New Trigger
1. Create the photo channel.
2. Send a message that contains only one lowercase keyword (no spaces) and image at the same time.
Example:
```
abc1
<image attachment>
```
The bot will store:
```
"abc1": "https://cdn.discordapp.com/..."
```
Restoring Lost Triggers (Scan History)

If `triggers.json` gets deleted or corrupted, you can rebuild the trigger list:
Inside Discord, type:
```
!scan
```
The bot will scan the entire message history of the learning channel and restore all valid keyword–image pairs.
Notes
This project is intended for personal use, automation, and experimentation with Discord triggers.  
Feel free to fork, modify, or extend the bot as you like.
