import discord
from discord.ext import commands
from discord.ext.commands import Context


class PlayerSelect(discord.ui.Select):
    def __init__(self, players, selected_player_id = None):

        options = [
            discord.SelectOption(
                label=name,
                value=str(pid),
                default=(pid == selected_player_id)
            )
            for pid, name in players[:25]
        ]

        super().__init__(
            placeholder="Select a player...",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        view: MatchView = self.view

        player_id = int(self.values[0])

        view.current_player_id = player_id

        for pid, pname in view.players:
            if pid == player_id:
                view.current_player_name = pname
                break

        decks = view.decks_by_player.get(player_id, [])

        view.deck_select.set_decks(decks)
        view.refresh_components()

        await interaction.response.edit_message(
            embed=view.build_embed(),
            view=view
        )





class DeckSelect(discord.ui.Select):
    def __init__(self, selected_deck_id=None):
        self.selected_deck_id = selected_deck_id

        super().__init__(
            placeholder="Select a deck...",
            options=[
                discord.SelectOption(
                    label="Select a player first",
                    value="0"
                )
            ],
            disabled=True,
            min_values=1,
            max_values=1
        )


    def set_decks(self, decks):
        options = [
            discord.SelectOption(
                label="No Deck / Unknown",
                value="none",
                default=(self.selected_deck_id is -1)
            )
        ]

        options.extend([
            discord.SelectOption(
                label=commander,
                value=str(deck_id),
                default=(deck_id == self.selected_deck_id)
            )
            for deck_id, commander in decks[:24]
        ])

        self.options = options
        self.disabled = False


    async def callback(self, interaction: discord.Interaction):
        view: MatchView = self.view

        value = self.values[0]

        if value == "none":
            view.current_deck_id = -1
            view.current_deck_name = "No Deck"

        else:
            deck_id = int(value)

            for d_id, commander in view.decks_by_player.get(
                view.current_player_id,
                []
            ):
                if d_id == deck_id:
                    view.current_deck_id = d_id
                    view.current_deck_name = commander
                    break

        view.placement_select.disabled = False
        view.refresh_components()

        await interaction.response.edit_message(
            embed=view.build_embed(),
            view=view
        )





class PlacementSelect(discord.ui.Select):
    def __init__(self, selected_placement = None):
        options = [
            discord.SelectOption(
                label=f"{i} Place",
                value=str(i),
                default = (i == selected_placement)
            )
            for i in range(1, 9)
        ]

        super().__init__(
            placeholder="Select placement...",
            options=options,
            disabled=True,
            min_values=1,
            max_values=1
        )


    async def callback(self, interaction: discord.Interaction):
        view: MatchView = self.view

        view.current_placement = int(self.values[0])
        view.refresh_components()

        await interaction.response.edit_message(
            embed=view.build_embed(),
            view=view
        )





class MatchView(discord.ui.View):
    def __init__(self, bot, players, decks_by_player):
        super().__init__(timeout=300)

        self.bot = bot

        self.players = players
        self.decks_by_player = decks_by_player

        # Final entries
        self.entries = []

        # Current selections
        self.current_player_id = None
        self.current_player_name = None

        self.current_deck_id = None
        self.current_deck_name = None
        self.current_placement = None

        # Components
        self.player_select = PlayerSelect(players)
        self.deck_select = DeckSelect()
        self.placement_select = PlacementSelect()

        self.add_item(self.player_select)
        self.add_item(self.deck_select)
        self.add_item(self.placement_select)


    def refresh_components(self):
        self.remove_item(self.player_select)
        self.remove_item(self.deck_select)
        self.remove_item(self.placement_select)

        self.player_select = PlayerSelect(
            self.players,
            selected_player_id=self.current_player_id
        )

        self.deck_select = DeckSelect(
            selected_deck_id=self.current_deck_id
        )

        if self.current_player_id:
            decks = self.decks_by_player.get(
                self.current_player_id,
                []
            )

            self.deck_select.set_decks(decks)

        self.placement_select = PlacementSelect(
            selected_placement=self.current_placement
        )

        if self.current_deck_id is None:
            self.placement_select.disabled = True
        else:
            self.placement_select.disabled = False

        self.add_item(self.player_select)
        self.add_item(self.deck_select)
        self.add_item(self.placement_select)


    def build_embed(self):
        embed = discord.Embed(
            title="MTG Match Builder",
            color=0xBEBEFE
        )

        if not self.entries:
            embed.description = "No players added yet."

        else:
            sorted_entries = sorted(
                self.entries,
                key=lambda x: x["placement"]
            )

            lines = []

            for entry in sorted_entries:

                lines.append(
                    f"**{entry['placement']}**: "
                    f"**{entry['player_name']}** "
                    f"- {entry['deck_name']}"
                )

            embed.description = "\n".join(lines)

        current = []

        if self.current_player_name:
            current.append(f"Player: {self.current_player_name}")

        if self.current_deck_name:
            current.append(f"Deck: {self.current_deck_name}")

        if self.current_placement:
            current.append(f"Placement: {self.current_placement}")

        if current:
            embed.add_field(
                name="*Current Selection*",
                value="\n".join(current),
                inline=False
            )

        return embed


    def reset_current_selection(self):
        self.current_player_id = None
        self.current_player_name = None
        self.current_deck_id = None
        self.current_deck_name = None
        self.current_placement = None

        # Remove ONLY selects
        self.remove_item(self.player_select)
        self.remove_item(self.deck_select)
        self.remove_item(self.placement_select)

        # Recreate selects
        self.player_select = PlayerSelect(self.players)
        self.deck_select = DeckSelect()
        self.placement_select = PlacementSelect()

        # Add them back
        self.add_item(self.player_select)
        self.add_item(self.deck_select)
        self.add_item(self.placement_select)


    @discord.ui.button(label="Add Player", style=discord.ButtonStyle.primary, row=4)
    async def add_player_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Validate selection
        if (
            self.current_player_id is None
            or self.current_placement is None
        ):

            await interaction.response.send_message(
                "Complete all fields first.",
                ephemeral=True
            )
            return

        # Prevent duplicate players
        if any(
            e["player_id"] == self.current_player_id
            for e in self.entries
        ):

            await interaction.response.send_message(
                "That player is already in the match.",
                ephemeral=True
            )
            return

        # Save entry
        self.entries.append({
            "player_id": self.current_player_id,
            "player_name": self.current_player_name,
            "deck_id": self.current_deck_id,
            "deck_name": self.current_deck_name,
            "placement": self.current_placement
        })

        # Reset current inputs
        self.reset_current_selection()

        await interaction.response.edit_message(
            embed=self.build_embed(),
            view=self
        )


    @discord.ui.button(label="Finish Match", style=discord.ButtonStyle.green, row=4)
    async def finish_match_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Require at least 2 players
        if len(self.entries) < 2:
            await interaction.response.send_message(
                "You need at least 2 players.",
                ephemeral=True
            )
            return

        # Create match record in db
        match_id = await self.bot.database.create_match()

        # Save player info
        for player in self.entries:
            deck_id = (
                None
                if player["deck_id"] == -1
                else player["deck_id"]
            )

            await self.bot.database.add_match_player(
                match_id,
                player["player_id"],
                deck_id,
                player["placement"]
            )

        embed = self.build_embed()
        embed.title = "Match Saved"

        await interaction.response.edit_message(
            embed=embed,
            view=None
        )


    @discord.ui.button(label="Cancel Match", style=discord.ButtonStyle.danger, row=4)
    async def cancel_match_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Match Cancelled",
            description="The match was discarded.",
            color=discord.Color.red()
        )

        await interaction.response.edit_message(
            embed=embed,
            view=None
        )

        self.stop()


    async def on_timeout(self):

        for item in self.children:
            item.disabled = True





class Match(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="match", description="Log a new MTG match.")
    async def match(self, context: Context):
        players = await self.bot.database.get_players()

        if not players:

            await context.send(
                embed=discord.Embed(
                    description="No players found.",
                    color=0xBEBEFE
                )
            )
            return

        # Get decks
        decks = await self.bot.database.get_decks()

        decks_by_player = {}
        for deck_id, player_id, commander in decks:
            player_id = int(player_id)
            decks_by_player.setdefault(
                player_id,
                []
            ).append(
                (deck_id, commander)
            )

        view = MatchView(
            self.bot,
            players,
            decks_by_player
        )

        await context.send(
            embed=view.build_embed(),
            view=view
        )




async def setup(bot):
    await bot.add_cog(Match(bot))