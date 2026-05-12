import urllib.parse
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

from utils.autocomplete import player_autocomplete, valid_player_fallback


class MatchHistoryView(discord.ui.View):
    def __init__(self, matches, per_page=4):
        super().__init__(timeout=180)

        self.matches = matches
        self.per_page = per_page
        self.page = 0


    def build_embed(self):
        start = self.page * self.per_page
        end = start + self.per_page

        chunk = self.matches[start:end]

        embed = discord.Embed(
            title="Match History",
            color=0xBEBEFE
        )

        if not chunk:
            embed.description = "No matches found."
            return embed

        for match in chunk:
            lines = []

            for e in match["participants"]:
                print(e)
                commander = e["commander"] or "N/A"
                encoded = urllib.parse.quote(commander)

                lines.append(
                    f"**{e['placement']}** - {e['player']} ([{commander}](https://scryfall.com/search?q={encoded}))"
                )

            embed.add_field(
                name=f"`Match #{match['match_id']}` - ({match["created_at"]})",
                value="\n".join(lines),
                inline=False
            )

        total_pages = (len(self.matches) - 1) // self.per_page + 1
        embed.set_footer(text=f"Page {self.page + 1}/{total_pages}")
        return embed


    @discord.ui.button(label="Prev", style=discord.ButtonStyle.secondary)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1

        await interaction.response.edit_message(
            embed=self.build_embed(),
            view=self
        )


    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        max_page = (len(self.matches) - 1)

        if self.page < max_page:
            self.page += 1

        await interaction.response.edit_message(
            embed=self.build_embed(),
            view=self
        )


    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="Closed",
                description="Match history closed.",
                color=discord.Color.red()
            ),
            view=None
        )
        self.stop()






class PlayerStatsView(discord.ui.View):
    def __init__(self, general_stats, decks):
        super().__init__(timeout=180)
        self.general_stats = general_stats[0]
        self.decks = decks


    def build_embed(self):
        embed = discord.Embed(
            title=f"{self.general_stats[1]}'s Stats",
            color=0xBEBEFE
        )

        embed.add_field(
            name="`General:`",
            value="\n".join([f"- **Games played:** {self.general_stats[2]}", 
                                f"- **Avg placement:** {(self.general_stats[3] if self.general_stats[3] is not None else 'N/A')}", 
                                f"- **Ranking:** {(self.general_stats[4] if self.general_stats[4] is not None else 'N/A')}"]),
            inline=False
        )

        lines = []
        lines.append(f"{'Deck':<22} Games Avg")
        lines.append("-" * 33)

        for deck in self.decks:
            lines.append(f"{deck[1][:20]:<22} {deck[2]:<5} {deck[3]:<3.1f}")

        embed.add_field(
            name="`Deck Stats`",
            value = "```txt\n" + "\n".join(lines) + "\n```",
            inline=False
        )
        return embed

        # Old formatting
        # for deck in self.decks:
        #     commander = deck[1]

        #     embed.add_field(
        #         name=f"`{commander}`",
        #         value = f" **{deck[2]}** games - **{deck[3]}** avg.",
        #         inline=False
        #     )

        


class History(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.hybrid_command(
        name="history",
        description="View previous matches"
    )
    async def matches(self, ctx: Context):
        matches = await self.bot.database.matches()
        
        if not matches:
            await ctx.send(
                "No matches found."
            )
            return

        # Order so most recent comes first
        matches.reverse()
        view = MatchHistoryView(matches)

        await ctx.send(
            embed=view.build_embed(),
            view=view
        )


    @commands.hybrid_command(
        name="stats",
        description="View stats about a player"
    )
    @app_commands.autocomplete(player=player_autocomplete)
    async def stats(self, ctx: Context, player:int):
        # Fallback if no username was selected in the dropdown
        try:
            player_id = int(player)
        except ValueError:
            player_id = await valid_player_fallback(
                self.bot,
                None,
                player
            )

        general_stats = await self.bot.database.get_player_by_id(player_id)
        decks = await self.bot.database.get_decks_by_player_id(player_id)
        view = PlayerStatsView(general_stats, decks)

        await ctx.send(
            embed=view.build_embed(),
            view=view
        )


# Load cog
async def setup(bot):
    await bot.add_cog(History(bot))