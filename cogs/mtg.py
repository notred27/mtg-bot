import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context


import aiohttp

async def search_cards(query: str):
    url = f"https://api.scryfall.com/cards/search?q={query}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()

            return data.get("data", [])[:25]



from discord import app_commands

async def card_autocomplete(interaction: discord.Interaction, current: str):
    if not current:
        return []

    cards = await search_cards(current)

    return [
        app_commands.Choice(
            name=card["name"][:100],  # Discord name limit
            value=card["id"]          # Use Scryfall ID
        )
        for card in cards
    ]


async def player_autocomplete(interaction: discord.Interaction, current: str):
    db = interaction.client.database  # same as self.bot.database

    # Fetch matching players (you’ll implement this)
    players = await db.search_players(current)

    return [
        app_commands.Choice(
            name=name,        # what user sees
            value=str(pid)    # what your command receives
        )
        for pid, name in players[:25]
    ]





async def get_card(card_id: str):
    url = f"https://api.scryfall.com/cards/{card_id}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()
        




class PlayerSelect(discord.ui.Select):
    def __init__(self, players):
        options = [
            discord.SelectOption(label=name, value=str(pid))
            for pid, name in players
        ]

        super().__init__(
            placeholder="Select a player...",
            options=options[:25]
        )

        self.players = {str(pid): name for pid, name in players}

    async def callback(self, interaction: discord.Interaction):
        player_id = self.values[0]
        player_name = self.players[player_id]

        # Open modal after selecting player
        await interaction.response.send_modal(
            PlayerInputModal(int(player_id), player_name)
        )

class PlayerView(discord.ui.View):
    def __init__(self, players):
        super().__init__()
        self.add_item(PlayerSelect(players))





class PlayerInputModal(discord.ui.Modal, title="Enter details"):
    def __init__(self, player_id: int, player_name: str):
        super().__init__()
        self.player_id = player_id
        self.player_name = player_name

        self.input = discord.ui.TextInput(
            label="Deck Name",
            placeholder="Type something...",
            required=True,
            max_length=200
        )
        self.add_item(self.input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"Added {self.input.value} to {self.player_name}'s decks!",
            ephemeral=True
        )



# Here we name the cog and create a new class for the cog.
class Mtg(commands.Cog, name="mtg"):
    def __init__(self, bot) -> None:
        self.bot = bot

    # Here you can just add your own commands, you'll always need to provide "self" as first parameter.

    @commands.hybrid_command(
        name="addplayer",
        description="Start tracking a new player.",
    )
    @app_commands.describe(player="The name of the new player")
    async def add_player(self, context: Context, player:str) -> None:
        """
        This is a testing command that does nothing.

        :param context: The application command context.
        """
        # Do your stuff here

        # Don't forget to remove "pass", I added this just because there's no content in the method.

        total = await self.bot.database.add_user(
                    player
                )


        embed = discord.Embed(description=f"{player} added!", color=0xBEBEFE)
        await context.send(embed=embed)



    @commands.hybrid_command(
        name="adddeck",
        description="Select a player and enter text"
    )
    async def player_input(self, context: Context):
        players = await self.bot.database.get_players()

        if not players:
            await context.send("No players found.")
            return

        await context.send(
            "Choose a player:",
            view=PlayerView(players)
    )
        


    @app_commands.command(name="deck", description="Add a new deck to a player's library.")
    @app_commands.autocomplete(player=player_autocomplete)
    @app_commands.autocomplete(card=card_autocomplete)
    async def card(self, interaction: discord.Interaction, player:str, card: str):
        data = await get_card(card)

        embed = discord.Embed(
            title=data["name"],
            description=data.get("oracle_text", "No text available")
        )


        await self.bot.database.add_deck(
                            player,
                            data
                        )


        if "image_uris" in data:
            embed.set_image(url=data["image_uris"]["normal"])

        await interaction.response.send_message(embed=embed)

# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
async def setup(bot) -> None:
    await bot.add_cog(Mtg(bot))
