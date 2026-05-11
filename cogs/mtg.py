import aiohttp
from urllib.parse import quote
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

from utils.autocomplete import player_autocomplete, card_autocomplete, valid_player_fallback




async def _get_card(card_id: str):
    """Get Scryfall data about a card. 
    
    Args:
        card_id: valid Scryfall MTG card id
    """
    url = f"https://api.scryfall.com/cards/{card_id}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()
        



class Mtg(commands.Cog, name="mtg"):
    def __init__(self, bot) -> None:
        self.bot = bot


    @commands.hybrid_command(
        name="players",
        description="Return a table of all tracked players.",
    )
    async def players(self, context: Context):
        players = await self.bot.database.get_all_player_stats()

        if not players:
            await context.send(embed=discord.Embed(description=f"No players found.", color=0xBEBEFE))
            return
        
        # Format md for "table".
        rows = [
            f"{p[1]:<10} "
            f"{p[2]:<6} "
            f"{p[3]:<6} "
            f"{(p[5] if p[5] is not None else 'N/A'):<6}"
            f"{(f'{p[4]:.2f}' if p[4] is not None else 'N/A'):<10} "
            for p in players[:10]
        ]

        await context.send(
            "```\n"
                f"{'Name':<10} {'Games':<6} {'Decks':<6} {'Rank':<6} {'Avg.':<6}\n"
                + "----------+------+------+-----+------\n"
                + "\n".join(rows) +
            "\n```"
        )



    @commands.hybrid_command(
        name="addplayer",
        description="Start tracking a new player.",
    )
    @app_commands.describe(player="The name of the new player")
    async def add_player(self, context: Context, player:str) -> None:
        res = await self.bot.database.add_player(player)

        if res:
            return await context.send(embed=discord.Embed(description=f"{player} added!", color=0xBEBEFE))
   
        return await context.send(embed=discord.Embed(description=f"{player} already exists!", color=0xBEBEFE))


    @commands.hybrid_command(
        name="removeplayer",
        description="Remove a player's records.",
    )
    @app_commands.describe(player="The name of the player to remove")
    async def remove_player(self, context: Context, player:str) -> None:
        res = await self.bot.database.remove_player(player)

        if res:
            return await context.send(embed=discord.Embed(description=f"{player} removed!", color=0xBEBEFE))
   
        return await context.send(embed=discord.Embed(description=f"{player} could not be removed!", color=0xBEBEFE))


    @app_commands.command(name="deck", description="Add a new deck to a player's library.")
    @app_commands.autocomplete(player=player_autocomplete)
    @app_commands.autocomplete(card=card_autocomplete)
    async def add_deck(self, interaction: discord.Interaction, player:str, card: str):
        # Fallback for if player_name is not selected through the dropdown
        try:
            player_id = int(player)
        except ValueError:
            player_id = await valid_player_fallback(
                self.bot,
                interaction,
                player
            )

        data = await _get_card(card)

        embed = discord.Embed(
            title=f"**{data["name"]}** added to **{player_id}'s** decks.",
            # description=data.get("oracle_text", "No text available")
        )

        await self.bot.database.add_deck_by_id(data["name"], player_id)

        if "image_uris" in data:
            embed.set_image(url=data["image_uris"]["normal"])

        await interaction.response.send_message(embed=embed)



# Load cog
async def setup(bot) -> None:
    await bot.add_cog(Mtg(bot))
