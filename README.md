# Gemini Telegram Bot
A telegram bot that interacts with Google's Gemini API and can be hosted on serverless functions.

# Demo
A working demo can be found at [@NotAIChatBot](https://telegram.dog/NotAIChatBot).

# Requirements

#### Telegram API ID and Hash
Get your API ID and Hash from [my.telegram.org](https://my.telegram.org).
#### Telegram Bot API Token
Create a bot and get the bot token from [@BotFather](https://telegram.dog/BotFather).
#### Python 3.8+
Install Python 3.8 or higher from [here](https://www.python.org/downloads/)
#### Gemini API Key
Get your Gemini API key from [here](https://makersuite.google.com/)
#### PostgreSQL Database (optional)
Install PostgreSQL from [here](https://www.postgresql.org/download/) or use a managed database service like [ElephantSQL](https://www.elephantsql.com/)

# Environment Variables

- `API_ID` - Your [API ID](#telegram-api-id-and-hash)
- `API_HASH` - Your [API Hash](#telegram-api-id-and-hash)
- `BOT_TOKEN` - Your [bot token](#telegram-bot-api-token)
- `GEMINI_API_KEY` - Your [Gemini API key](#gemini-api-key)
- `DATABASE_URI` - Your PostgreSQL database URI (optional)

> **NOTE:** By default, the bot uses a SQLite database.

# Hosting
# Self Hosting

```bash
git clone https://github.com/EverythingSuckz/GeminiTelegramBot
cd GeminiTelegramBot
python3 -m venv venv
source venv/bin/activate # Linux
.\venv\Scripts\activate # For windows
pip install -r requirements.txt
python -m bot
```

# To Do
- [ ] Reactions
- [ ] Give the bot context of chat stickers
- [ ] Add more features
- [ ] Optimize code

_Based on [pyrogram](https://github.com/pyrogram/pyrogram)._

**Give a ⭐ if you like this project!**