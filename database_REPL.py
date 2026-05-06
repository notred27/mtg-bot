import asyncio
import inspect
import shlex
import aiosqlite

from database import DatabaseManager
    

class CLI:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"

    indent_level = 1

    @classmethod
    def _indent(cls):
        return "    " * cls.indent_level
    
    @classmethod
    def print(cls, msg):
        print(cls._indent() + cls.GREEN + msg + cls.RESET)

    @classmethod
    def error(cls, msg):
        print(cls._indent() + CLI.YELLOW + msg + CLI.RESET)

    @classmethod
    def print_players(cls, players):
        CLI.print(f"{"id":<2}| {"name":<16}| ")
        CLI.print("-------------------------------------------------------------------")
        for pid, name in players:
            CLI.print(f"{pid:<2}| {name:<16}| ")


    @classmethod
    def print_decks(cls, decks):
        CLI.print(f"{"id":<2}| {"player_name":<16}| {"commander_name":<30}|")
        CLI.print("-------------------------------------------------------------------")
        for pid, player_name, commander in decks:
            CLI.print(f"{pid:<2}| {player_name:<16}| {commander:<30} ")


async def REPL():
    async with aiosqlite.connect("database/database.db") as connection:

        # Setup DB and ensure schema is loaded
        await connection.execute("PRAGMA foreign_keys = ON")
        db = DatabaseManager(connection=connection)
        await db.init_db()

        COMMANDS = {
            "players": db.get_players,
            "player": db.search_players,
            "add_player": db.add_player,
            "remove_player": db.remove_player,

            "decks": db.get_decks,
            "deck": db.get_deck,
            "add_deck": db.add_deck,
            "remove_deck": db.remove_deck,

            "matches": db.matches,
            "create_match": db.create_match,
            "add_match_player": db.add_match_player
        }


        CLI.print("\n- MTG Match Tracker REPL - MyCoelacanth -\nEnter 'h' for help, 'q' to quit.")
        # print("---------------")

        # Main REPL Loop
        while True:
            try:
                i = input(">>> " )
                args = shlex.split(i)

                
                match args[0].lower(): # Command switch
                
                # Player Commands
                    case "players":
                        players = await db.get_players()
                        CLI.print_players(players)


                    case "player":
                        players = await db.search_players(args[1])

                        if not players:
                            CLI.error("No users found!")
                            continue

                        for pid, name in players:
                            CLI.print(f"{name} [id: {pid}]")


                    case "add_player" | "ap":
                        id = await db.add_player(args[1])

                        if id is None:
                            CLI.error(f"User '{args[1]}' already exists!")
                            continue

                        CLI.print(f"New user '{args[1]}' added successfully with id '{id}'")
                        

                    case "remove_player" | "rp":
                        player = await db.search_players(str(args[1]))
                        if len(player) < 1:
                            CLI.error("No matching player found")
                            continue

                        confirm =  input(f"Are you sure you want to delete '{player[0]}'? (y/n)\n").strip().lower()
                        
                        if confirm not in ("y", "yes"):
                            CLI.print("Deletion cancelled")
                            continue
                        
                        rows_deleted = await db.remove_player(str(args[1]))
                        print(rows_deleted)
                        if rows_deleted:
                            CLI.print("Deleted successfully")
                        else:
                            CLI.error("No matching player found")
                        


                # Deck Commands
                    case "decks":
                        decks = await db.get_decks()
                        CLI.print_decks(decks)
                        # for deck_id, player_name, commander in decks:
                        #     CLI.print(f"[{deck_id}] {commander} (Player: {player_name})")


                    case "deck":
                        decks = await db.get_deck(args[1], args[2])
                        CLI.print_decks(decks)



                    case "add_deck" | "ad":
                        id = await db.add_deck(args[1], args[2])
                        if id is None:
                            CLI.error(f"Deck '{args[1]}' already exists for '{args[2]}'!")
                            continue

                        CLI.print(f"New deck '{args[1]}' added successfully to player '{args[2]}' with id '{id}'")


                    case "remove_deck" | "rd":
                        try:

                            commander = await db.get_deck(args[1], args[2])
                            confirm =  input(f"Are you sure you want to delete '{commander}' from '{args[2]}'s decks? (y/n)\n").strip().lower()
                            if confirm not in ("y", "yes"):
                                CLI.print("Deletion cancelled")
                                continue
                            
                            rows_deleted = await db.remove_deck(args[1], args[2])
                            if rows_deleted:
                                CLI.print("Deleted successfully")
                            else:
                                CLI.error("No matching deck found")
                        except Exception as e:
                            CLI.error(f"Error: {e}")



                    # Match commands
                    case "matches":
                        rows = await db.matches()

                        for match in rows:
                            CLI.print(f"\nMatch {match['match_id']} ({match['created_at']})")

                            for p in match["participants"]:
                                print(f"  - {p['player']:<16} | {p['commander']:<30} | {p['placement']}")
                    

                    case "create_match" | "add_match" | "am":
                        id = await db.create_match()
                        CLI.print(f"New match created with id:{id}")


                    case "add_match_player" | "amp":
                        id = await db.add_match_player(args[1], args[2], args[3], args[4])



                    # CLI Commands
                    case "h" | "help":

                        if len(args) > 1:
                            cmd = args[1]
                            if cmd in COMMANDS:
                                doc = inspect.getdoc(COMMANDS[cmd])
                                CLI.print(f"\nHelp for '{cmd}':\n")
                                CLI.print(doc or "No documentation available.")
                            else:
                                CLI.error(f"Unknown command: {cmd}")

                        else:

                            for name, func in COMMANDS.items():
                                doc = inspect.getdoc(func) or "No description available."
                                first_line = doc.split("\n")[0]
                                CLI.print(f"{name}: {first_line}")
                            CLI.print("q: Quit out of the REPL.\n")
                            CLI.print("For more detailed info on a specific command, enter 'h [COMMAND_NAME]'")

                    case "q" | "quit" | "exit":
                        CLI.print("Bye bye!")
                        break

                    case _:
                        CLI.error("Unknown Command")

        

                # print("---------------")

            except Exception as e:
                CLI.error(f"Error: {e}")
                    


if __name__ == "__main__":
    asyncio.run(REPL())