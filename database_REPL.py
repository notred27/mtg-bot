import asyncio
import inspect
import shlex
import aiosqlite

from database import DatabaseManager


class CLI:
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    CYAN   = "\033[96m"
    RESET  = "\033[0m"
    BOLD   = "\033[1m"

    indent_level = 1

    @classmethod
    def _indent(cls):
        return " " * cls.indent_level

    @classmethod
    def print(cls, msg):
        print(cls._indent() + cls.GREEN + msg + cls.RESET)

    @classmethod
    def error(cls, msg):
        print(cls._indent() + cls.YELLOW + "Error: " + msg + cls.RESET)

    @classmethod
    def header(cls, msg):
        print(cls._indent() + cls.CYAN + cls.BOLD + msg + cls.RESET)

    # ── Table printers ──────────────────────────────────────────────────────────

    @classmethod
    def print_players(cls, players):
        cls.header(f"{'id':<4}| {'name':<20}")
        cls.header("─" * 28)
        for pid, name in players:
            cls.print(f"{pid:<4}| {name:<20}")

    @classmethod
    def print_player_stats(cls, stats):
        cls.header(f"{'id':<4}| {'name':<16}| {'games':<6}| {'decks':<6}| {'avg place':<10}| rank")
        cls.header("─" * 60)
        for pid, name, games, decks, avg, rank in stats:
            rank_str = str(rank) if rank is not None else "—"
            avg_str  = f"{avg:.2f}" if avg is not None else "—"
            cls.print(f"{pid:<4}| {name:<16}| {games:<6}| {decks:<6}| {avg_str:<10}| {rank_str}")

    @classmethod
    def print_decks(cls, decks):
        # Accepts (deck_id, player_name, commander) or (deck_id, player_id, commander)
        cls.header(f"{'id':<4}| {'player':<16}| {'commander':<30}")
        cls.header("─" * 56)
        for deck_id, player, commander in decks:
            cls.print(f"{deck_id:<4}| {str(player):<16}| {commander:<30}")

    @classmethod
    def print_decks_with_stats(cls, decks):
        # (deck_id, commander, games_played, avg_placement)
        cls.header(f"{'id':<4}| {'commander':<30}| {'games':<6}| avg place")
        cls.header("─" * 56)
        for deck_id, commander, games, avg in decks:
            avg_str = f"{avg:.2f}" if avg else "—"
            cls.print(f"{deck_id:<4}| {commander:<30}| {games:<6}| {avg_str}")

    @classmethod
    def print_matches(cls, matches):
        for match in matches:
            cls.header(f"\nMatch {match['match_id']}  ({match['created_at']})")
            for p in match["participants"]:
                commander = p["commander"] or "unknown deck"
                placement = p["placement"] if p["placement"] is not None else "?"
                cls.print(f"  #{placement}  {p['player']:<16}  ({commander})")


def confirm(prompt: str) -> bool:
    return input(prompt + " (y/n): ").strip().lower() in ("y", "yes")


async def REPL():
    async with aiosqlite.connect("database/database.db") as connection:
        await connection.execute("PRAGMA foreign_keys = ON")
        db = DatabaseManager(connection=connection)
        await db.init_db()

        COMMANDS = {
            # players
            "players":            ("List all players",                          "players"),
            "stats":              ("Show all player stats with rankings",        "stats"),
            "player":             ("Search players by name",                    "player [NAME]"),
            "player_id":          ("Get a single player's stats by id",         "player_id [ID]"),
            "add_player":         ("Add a new player",                          "add_player [NAME]"),
            "remove_player":      ("Remove a player by name",                   "remove_player [NAME]"),
            "remove_player_id":   ("Remove a player by id",                     "remove_player_id [ID]"),
            # decks
            "decks":              ("List all decks",                            "decks"),
            "deck":               ("Search decks by commander prefix + player", "deck [COMMANDER_PREFIX] [PLAYER_NAME]"),
            "player_decks":       ("List all decks for a player id",            "player_decks [PLAYER_ID]"),
            "add_deck":           ("Add a deck to a player",                    "add_deck [COMMANDER] [PLAYER_NAME]"),
            "add_deck_id":        ("Add a deck to a player by player id",       "add_deck_id [COMMANDER] [PLAYER_ID]"),
            "remove_deck":        ("Remove a deck by commander + player name",  "remove_deck [COMMANDER] [PLAYER_NAME]"),
            "remove_deck_id":     ("Remove a deck by deck id",                  "remove_deck_id [DECK_ID]"),
            # matches
            "matches":            ("List all matches",                          "matches"),
            "create_match":       ("Create a new match",                        "create_match"),
            "add_match_player":   ("Add a player to a match",                   "add_match_player [MATCH_ID] [PLAYER_ID] [DECK_ID] [PLACEMENT]"),
        }

        CLI.header("\n── MTG Match Tracker REPL ──")
        CLI.print("Enter 'h' for help, 'q' to quit.\n")

        while True:
            try:
                raw = input(">>> ").strip()
                if not raw:
                    continue

                args = shlex.split(raw)
                cmd  = args[0].lower()

                # ── Player commands ────────────────────────────────────────────

                if cmd == "players":
                    players = await db.get_players()
                    if not players:
                        CLI.error("No players found.")
                    else:
                        CLI.print_players(players)

                elif cmd == "stats":
                    stats = await db.get_all_player_stats()
                    if not stats:
                        CLI.error("No player stats found.")
                    else:
                        CLI.print_player_stats(stats)

                elif cmd == "player":
                    if len(args) < 2:
                        CLI.error("Usage: player [NAME]")
                        continue
                    players = await db.search_players(args[1])
                    if not players:
                        CLI.error("No players found.")
                    else:
                        CLI.print_players(players)

                elif cmd == "player_id":
                    if len(args) < 2:
                        CLI.error("Usage: player_id [ID]")
                        continue
                    rows = await db.get_player_by_id(int(args[1]))
                    if not rows:
                        CLI.error(f"No player found with id {args[1]}.")
                    else:
                        pid, name, games, avg, rank = rows[0]
                        rank_str = str(rank) if rank is not None else "—"
                        avg_str  = f"{avg:.2f}" if avg is not None else "—"
                        CLI.header(f"\n{name}  (id: {pid})")
                        CLI.print(f"Games played : {games}")
                        CLI.print(f"Avg placement: {avg_str}")
                        CLI.print(f"Ranking      : {rank_str}")

                elif cmd in ("add_player", "ap"):
                    if len(args) < 2:
                        CLI.error("Usage: add_player [NAME]")
                        continue
                    new_id = await db.add_player(args[1])
                    if new_id is None:
                        CLI.error(f"Player '{args[1]}' already exists.")
                    else:
                        CLI.print(f"Player '{args[1]}' added with id {new_id}.")

                elif cmd in ("remove_player", "rp"):
                    if len(args) < 2:
                        CLI.error("Usage: remove_player [NAME]")
                        continue
                    matches_found = await db.search_players(args[1])
                    if not matches_found:
                        CLI.error(f"No player matching '{args[1]}' found.")
                        continue
                    CLI.print_players(matches_found)
                    if not confirm(f"Delete player '{args[1]}'?"):
                        CLI.print("Cancelled.")
                        continue
                    deleted = await db.remove_player(args[1])
                    CLI.print("Deleted successfully.") if deleted else CLI.error("No matching player found.")

                elif cmd in ("remove_player_id", "rpi"):
                    if len(args) < 2:
                        CLI.error("Usage: remove_player_id [ID]")
                        continue
                    if not confirm(f"Delete player with id {args[1]}?"):
                        CLI.print("Cancelled.")
                        continue
                    deleted = await db.remove_player_by_id(int(args[1]))
                    CLI.print("Deleted successfully.") if deleted else CLI.error("No player with that id.")

                # ── Deck commands ──────────────────────────────────────────────

                elif cmd == "decks":
                    decks = await db.get_decks()
                    if not decks:
                        CLI.error("No decks found.")
                    else:
                        CLI.print_decks(decks)

                elif cmd == "deck":
                    if len(args) < 3:
                        CLI.error("Usage: deck [COMMANDER_PREFIX] [PLAYER_NAME]")
                        continue
                    decks = await db.get_deck(args[1], args[2])
                    if not decks:
                        CLI.error("No matching decks found.")
                    else:
                        CLI.print_decks(decks)

                elif cmd == "player_decks":
                    if len(args) < 2:
                        CLI.error("Usage: player_decks [PLAYER_ID]")
                        continue
                    decks = await db.get_decks_by_player_id(int(args[1]))
                    if not decks:
                        CLI.error("No decks found for that player.")
                    else:
                        CLI.print_decks_with_stats(decks)

                elif cmd in ("add_deck", "ad"):
                    if len(args) < 3:
                        CLI.error("Usage: add_deck [COMMANDER] [PLAYER_NAME]")
                        continue
                    new_id = await db.add_deck(args[1], args[2])
                    if new_id is None:
                        CLI.error(f"Deck '{args[1]}' already exists for '{args[2]}'.")
                    else:
                        CLI.print(f"Deck '{args[1]}' added to '{args[2]}' with id {new_id}.")

                elif cmd == "add_deck_id":
                    if len(args) < 3:
                        CLI.error("Usage: add_deck_id [COMMANDER] [PLAYER_ID]")
                        continue
                    new_id = await db.add_deck_by_id(args[1], int(args[2]))
                    if new_id is None:
                        CLI.error(f"Deck '{args[1]}' already exists for player id {args[2]}.")
                    else:
                        CLI.print(f"Deck '{args[1]}' added with id {new_id}.")

                elif cmd in ("remove_deck", "rd"):
                    if len(args) < 3:
                        CLI.error("Usage: remove_deck [COMMANDER] [PLAYER_NAME]")
                        continue
                    if not confirm(f"Delete '{args[1]}' from '{args[2]}'?"):
                        CLI.print("Cancelled.")
                        continue
                    deleted = await db.remove_deck(args[1], args[2])
                    CLI.print("Deleted successfully.") if deleted else CLI.error("No matching deck found.")

                elif cmd in ("remove_deck_id", "rdi"):
                    if len(args) < 2:
                        CLI.error("Usage: remove_deck_id [DECK_ID]")
                        continue
                    if not confirm(f"Delete deck with id {args[1]}?"):
                        CLI.print("Cancelled.")
                        continue
                    deleted = await db.remove_deck_by_id(int(args[1]))
                    CLI.print("Deleted successfully.") if deleted else CLI.error("No deck with that id.")

                # ── Match commands ─────────────────────────────────────────────

                elif cmd == "matches":
                    all_matches = await db.matches()
                    if not all_matches:
                        CLI.error("No matches found.")
                    else:
                        CLI.print_matches(all_matches)

                elif cmd in ("create_match", "cm"):
                    new_id = await db.create_match()
                    CLI.print(f"New match created with id {new_id}.")

                elif cmd in ("add_match_player", "amp"):
                    if len(args) < 5:
                        CLI.error("Usage: add_match_player [MATCH_ID] [PLAYER_ID] [DECK_ID] [PLACEMENT]")
                        continue
                    await db.add_match_player(int(args[1]), int(args[2]), int(args[3]), int(args[4]))
                    CLI.print(f"Player {args[2]} added to match {args[1]} (placement: {args[4]}).")

                # ── Meta commands ──────────────────────────────────────────────

                elif cmd in ("h", "help"):
                    if len(args) > 1:
                        key = args[1]
                        if key in COMMANDS:
                            _, usage = COMMANDS[key]
                            CLI.header(f"\n{key}")
                            CLI.print(f"Usage: {usage}")
                        else:
                            CLI.error(f"Unknown command: {key}")
                    else:
                        CLI.header(f"\n{'command':<22}| description")
                        CLI.header("─" * 60)
                        for name, (desc, usage) in COMMANDS.items():
                            CLI.print(f"{name:<22}| {desc}")
                        CLI.print("\nFor usage details: h [COMMAND]")

                elif cmd in ("q", "quit", "exit"):
                    CLI.print("Bye!")
                    break

                else:
                    CLI.error(f"Unknown command '{cmd}'. Enter 'h' for help.")

            except (IndexError, ValueError) as e:
                CLI.error(f"Bad arguments — {e}")
            except Exception as e:
                CLI.error(str(e))


if __name__ == "__main__":
    asyncio.run(REPL())