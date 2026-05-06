import os
import sqlite3
import aiosqlite


class DatabaseManager:
    def __init__(self, *, connection: aiosqlite.Connection) -> None:
        self.connection = connection

    ###=====  DB FUNCTIONS  =====###

    
    async def init_db(self) -> None:
        """Initialize the database's tables and schema from a SQL file.
        
        Assumes that schema.sql is present in the same directory, and is valid. 
        If called on an existing db file, tables must use 'IF NOT EXISTS' in schema.sql
        
        Raises:
            FileNotFoundError: If schema.sql cannot be found.
            aiosqlite.Error: If execution of the SQL script fails.
        """

        schema_path = os.path.join(
            os.path.dirname(__file__), "schema.sql"
        )

        if not os.path.exists(schema_path):
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        with open(schema_path, encoding="utf-8") as file:
            await self.connection.executescript(file.read())

        await self.connection.commit()



    ###=====  PLAYER FUNCTIONS  =====###

    async def add_player(self, name: str) -> int:
        """Insert a new player record into the database.

        Usage:
            add_player [NAME]

        Args:
            name (str): The name of the player to add. Should be UNIQUE

        Returns:
            int: the id of the new player, or None if the player already exists
        """

        try:
            cursor = await self.connection.execute(
                "INSERT INTO players(player_name) VALUES (?)",
                (name,)
            )
            await self.connection.commit()
            return cursor.lastrowid
        
        except sqlite3.IntegrityError:
            return None
        

    async def remove_player(self, player_name: str) -> int:
        """Remove a player by their name.
        
        Usage:
            remove_player [PLAYER_NAME]
            
        Args:
            player_name (str): The name of the player to remove.

        Returns:
            int: The number of removed rows (1 = success)
    
        """

        async with self.connection.execute(
            """
            DELETE FROM players 
            WHERE player_name = ?
            """,
            (player_name,)
        ) as cursor:
            await self.connection.commit()
            return cursor.rowcount
    

    async def get_players(self) -> list[tuple[int, str]]:
        """Return a list of all players, ordered by name.
        
        Returns:
            list[tuple[int, str]]: A list of (player_id, player_name) tuples,
            sorted alphabetically by player_name. Returns an empty list if
            no players exist.
        """

        cursor = await self.connection.execute(
            """
            SELECT player_id, player_name 
            FROM players 
            ORDER BY player_name
            """
        )
        return await cursor.fetchall()
    

    async def search_players(self, query: str) -> list[tuple[int, str]]:
        """Search for players whose names contain the given query string.

        Usage:
            player [NAME]

        Args:
            query (str): Partial or full name to search for.

        Returns:
            list[tuple[int, str]]: Up to 5 (player_id, player_name) tuples,
            sorted alphabetically by player_name. Returns an empty list if
            no matches are found.
        """
        if not isinstance(query, str):
            raise TypeError("query must be a string")

        query = query.strip()


        cursor = await self.connection.execute(
            """
            SELECT player_id, player_name 
            FROM players
            WHERE player_name LIKE ? COLLATE NOCASE 
            ORDER BY player_name
            LIMIT 5
            """,
            (f"%{query}%",)
        )
        return await cursor.fetchall()



    ###=====  DECK FUNCTIONS  =====###


    async def add_deck(self, commander_name:str, player_name:str) -> int:
        """Add a deck to a player's library.
        
        Usage:
            add_deck [COMMANDER_NAME] [PLAYER_NAME]
            
        Args:
            commander_name (str): Name of the deck's commander. Should be UNIQUE per player.
            player_name (str): The name of an existing player.
            
        Returns:
            int: the id of the newly created deck, or None if a deck with the same commander already 
                exists for this player.
            
        Raises:
            ValueError: If the target player cannot be found.
            aiosqlite.Error: If execution of the SQL script fails.
        """
        try:
            cursor = await self.connection.execute(
                "SELECT player_id FROM players WHERE player_name = ?",
                (player_name,)
            )
            row = await cursor.fetchone()

            if not row:
                raise ValueError(f"Player '{player_name}' not found")

            player_id = row[0]

            cursor = await self.connection.execute(
                "INSERT INTO decks(player_id, commander) VALUES (?, ?)",
                (player_id, commander_name)
            )
            await self.connection.commit()
            return cursor.lastrowid
        
        except sqlite3.IntegrityError:
            return None


    async def remove_deck(self, commander_name: str, player_name: str) -> int:
        """Delete a deck from a player's library.

        Usage:
            remove_deck [COMMANDER_NAME] [PLAYER_NAME]

        Args:
            commander_name (str): The name of the target deck's commander.
            player_name (str): The name of the player who owns the deck.

        Returns:
            int: Number of rows deleted. (1 for success)
        
        """

        cursor = await self.connection.execute(
            "SELECT player_id FROM players WHERE player_name = ?",
            (player_name,)
        )
        row = await cursor.fetchone()

        if not row:
            raise ValueError(f"Player '{player_name}' not found")

        player_id = row[0]


        async with self.connection.execute(
            """
            DELETE FROM decks 
            WHERE commander = ? AND player_id = ?
            """,
            (commander_name, player_id)
        ) as cursor:
            await self.connection.commit()
            return cursor.rowcount


    async def get_deck(self, commander_prefix: str, player_name: str)  -> list[tuple[int, str, str]]:
        """Get deck based on commander name and player name

        Usage:
            deck [COMMANDER_PREFIX] [PLAYER_NAME]

        Args:
            commander_prefix (str): Start of the target deck's commander's name
            player_name (str): Name of the player who owns the deck

        Returns:
            list[tuple[int, str, str]]: Up to 5 (deck_id, player_name, commander_name) tuples,
            sorted alphabetically by commander name.
        """

        cursor = await self.connection.execute(
            """
            SELECT d.deck_id, p.player_name, d.commander
            FROM decks d
            JOIN players p ON d.player_id = p.player_id
            WHERE d.commander LIKE ? || '%' COLLATE NOCASE
            AND p.player_name = ?
            ORDER BY d.commander
            LIMIT 5
            """,
            (commander_prefix, player_name)
        )
        return await cursor.fetchall()
        

    async def get_decks(self) -> list[tuple[int, str, str]]:
        """Return a list of all decks, ordered alphabetically by [player_name, commander_name]

        Usage:
            decks

        Returns:
            list[tuple[int,str,str]]: A list of (deck_id, player_name, commander_name) tuples,
                ordered alphabetically by player_name, then commander_name
        """

        async with self.connection.execute(
            """
            SELECT d.deck_id, p.player_name, d.commander
            FROM decks d 
            JOIN players p on p.player_id = d.player_id
            ORDER BY p.player_name, d.commander
            """
        ) as cursor:
            return await cursor.fetchall()

    ###=====  MATCH FUNCTIONS  =====###
    async def create_match(self) -> int:
        """Create a new match object.
        
        Usage:
            create_match
            
        Returns:
            int: the id of the newly created match
        """

        cursor = await self.connection.execute(
            "INSERT INTO matches DEFAULT VALUES",
            ()
        )
        await self.connection.commit()
        return cursor.lastrowid
    

    async def add_match_player(self, match_id:int, player_name:str, deck_id:int, placement:int) -> int:
        """Add a participant record to a match.
        
        Usage:
            add_match_player [MATCH_ID] [PLAYER_NAME] [DECK_ID] [PLACEMENT]
            
        Args:
            match_id (int): The uid of the target match. Match must exist.
            player_name (str): The exact name of the target player.
            deck_id (int): The uid of a target deck.
            placement (int): The player's placement in the match.
            
        Returns:
            int: the id of the newly created match
        """

        cursor = await self.connection.execute(
            "SELECT player_id FROM players WHERE player_name = ?",
            (player_name,)
        )
        row = await cursor.fetchone()

        if not row:
            raise ValueError(f"Player '{player_name}' not found")

        player_id = row[0]

        cursor = await self.connection.execute(
            "INSERT INTO match_participants(match_id, player_id, deck_id, placement) VALUES (?, ?, ?, ?)",
            (match_id, player_id, deck_id, placement)
        )
        await self.connection.commit()
        return cursor.lastrowid
    

    async def matches(self):

        cursor = await self.connection.execute(
            """
            SELECT 
                m.match_id,
                m.created_at,
                p.player_name,
                d.commander,
                mp.placement
            FROM matches m
            LEFT JOIN match_participants mp ON m.match_id = mp.match_id
            LEFT JOIN players p ON mp.player_id = p.player_id
            LEFT JOIN decks d ON mp.deck_id = d.deck_id
            ORDER BY m.match_id, mp.placement
            """
        )
        rows = await cursor.fetchall()


        matches = {}
    
        for match_id, created_at, player, commander, placement in rows:
            if match_id not in matches:
                matches[match_id] = {
                    "match_id": match_id,
                    "created_at": created_at,
                    "participants": []
                }

            if player is not None:
                matches[match_id]["participants"].append({
                    "player": player,
                    "commander": commander,
                    "placement": placement
                })

        return list(matches.values())
