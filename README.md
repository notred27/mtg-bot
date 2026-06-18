# Magic The Gathering Ranking Bot

A Discord bot for Magic: The Gathering, built with [discord.py](https://discordpy.readthedocs.io/en/stable/) and Python 3.12. Supports slash commands, a persistent SQLite database, and Docker deployment.

> Built on top of [kkrypt0nn/Python-Discord-Bot-Template](https://github.com/kkrypt0nn/Python-Discord-Bot-Template).

---

## Features

- MTG-focused Discord commands via a modular cogs system
- Persistent data storage with SQLite (`aiosqlite`)
- Colored console logging + file logging to `discord.log`
- Docker and Docker Compose support for easy deployment
- Configurable via environment variables

---

## Project Structure

```
mtg-bot/
├── bot.py              # Main bot entry point
├── database_REPL.py    # Interactive database CLI
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── cogs/               # Command modules (auto-loaded)
├── database/           # SQLite schema and DatabaseManager
└── utils/              # Shared utilities
```

---

## Prerequisites

- Python 3.12+
- A Discord bot token ([create one here](https://discord.com/developers/applications))

---

## Setup

**1. Clone the repository**

```bash
git clone https://github.com/notred27/mtg-bot.git
cd mtg-bot
```

**2. Configure environment variables**

Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

```env
TOKEN=your_discord_bot_token
PREFIX=!
INVITE_LINK=https://discord.com/oauth2/authorize?...
```

**3. Install dependencies**

```bash
python -m pip install -r requirements.txt
```

**4. Run the bot**

```bash
python bot.py
```

> **Note:** Depending on your system, you may need to use `py`, `python3`, or `python3.12` instead of `python`.

---

## Running with Docker

Make sure [Docker](https://www.docker.com/) is installed, then:

```bash
docker compose up -d --build
```

The `-d` flag runs the container in detached (background) mode.

---

## Slash Command Note

Slash commands can take time to register globally. For instant registration during development, use the `@app_commands.guilds()` decorator with your guild ID:

```python
@commands.hybrid_command(name="command", description="...")
@app_commands.guilds(discord.Object(id=YOUR_GUILD_ID))
async def my_command(self, context):
    ...
```

---

## Adding New Commands

Add a new `.py` file to the `cogs/` directory. The bot auto-loads all cogs on startup. Each cog should be a standard discord.py `Cog` class.

---

## Database

The bot uses SQLite via `aiosqlite`. The schema is defined in `database/schema.sql` and is applied automatically on first run. Use `database_REPL.py` for interactive inspection or manual queries.

---

## License

Licensed under the [Apache License 2.0](LICENSE.md).

---

## Credits

Bot template by [kkrypt0nn](https://github.com/kkrypt0nn/Python-Discord-Bot-Template).  
Per the template license, credits and a link to the original repository must be kept in all files containing the original code.
