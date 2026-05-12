import asyncio
import time

import aiohttp
import discord
from discord import app_commands
from urllib.parse import quote

_last_scryfall_call = {} # Dict of players and their last query timestamp
DEBOUNCE_DELAY = 0.4


async def search_cards(query: str):
    q = f'{query} t:"legendary creature"'
    url = f"https://api.scryfall.com/cards/search?q={quote(q)}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()

            return data.get("data", [])[:25]


async def card_autocomplete(interaction: discord.Interaction, current: str):
    if not current or len(current) < 4:
        return []

    # Debounce handling to prevent spamming scryfall
    user_id = interaction.user.id
    now = time.monotonic()

    _last_scryfall_call[user_id] = now

    await asyncio.sleep(DEBOUNCE_DELAY)

    if _last_scryfall_call.get(user_id) != now:
        return []

    cards = await search_cards(current)

    return [
        app_commands.Choice(
            name=card["name"][:100],
            value=card["id"]
        )
        for card in cards
    ]


async def player_autocomplete(interaction: discord.Interaction, current: str):
    if not current:
        return []
    
    db = interaction.client.database

    players = await db.search_players(current)

    return [
        app_commands.Choice(
            name=name,
            value=str(pid)
        )
        for pid, name in players[:25]
    ]


async def valid_player_fallback(bot, interaction, player_name:str):
    id = await bot.database.search_players(player_name)
                
    if not id and interaction:
        await interaction.response.send_message(
            "Please select a valid player.",
            ephemeral=True
        )
        return
    
    return id[0][0]