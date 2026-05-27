import asyncpg
import config


class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        try:
            # since we have no Authentication, we can just use the URL
            self.pool = await asyncpg.create_pool(
                config.DATABASE_URL,
                ssl=True,
                min_size=1,
                max_size=15,
            )

            # gets the database connection from pool
            async with self.pool.acquire() as conn:
                # setting the correct schema
                await conn.execute("CREATE SCHEMA IF NOT EXISTS public")
                await conn.execute("SET search_path TO public")

            print("✅Connected to the database.")

            await self.create_tables()
        except Exception as error:
            print(f"❌Failed to connect to the database: {error}")

    async def create_tables(self):
        try:
            # gets the database connection from pool
            async with self.pool.acquire() as conn:
                # creating a SQl table for master variables
                await conn.execute(
                    """
                    -- creating a table if not exists
                    CREATE TABLE IF NOT EXISTS MASTER_DATA (
                        NAME VARCHAR(100),
                        VALUE TEXT,
                        created_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'Asia/Dhaka'),
                        updated_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'Asia/Dhaka'),
                        -- ensures that the variable names are unique
                        PRIMARY KEY (NAME)
                    );           
                """
                )

                # creating a SQL table for dynamic variables
                await conn.execute(
                    """
                    -- creating a table if not exists
                    CREATE TABLE IF NOT EXISTS SERVER_DATA (
                        ID BIGINT,
                        NAME VARCHAR(100),
                        VALUE TEXT,
                        created_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'Asia/Dhaka'),
                        updated_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'Asia/Dhaka'),
                        -- ensures that the combination of server id and variable name is unique
                        PRIMARY KEY (ID, NAME)
                    );
                """
                )
                print("✅ Variables table ready!")
        except Exception as error:
            print(f"❌ Error creating tables: {error}")

    async def set_variable(
        self, server_id: int, variable_name: str, variable_value: str
    ):
        try:
            # gets the database connection from pool
            async with self.pool.acquire() as conn:
                # inserting/updating the variable
                await conn.execute(
                    """
                    -- inserts a new variable in the table
                    INSERT INTO SERVER_DATA (ID, NAME, VALUE)
                    -- $1, $2 and $3 are asyncpg placeholders
                    VALUES ($1, $2, $3)
                    -- conflict occurs when the variable name already exists
                    -- if the variable name already exists, it updates the variable_value
                    ON CONFLICT (ID, NAME) DO UPDATE
                    SET VALUE = $3,
                    updated_at = TIMEZONE('Asia/Dhaka', NOW())
                    """,
                    server_id,
                    variable_name,
                    variable_value,
                )
                print(f"✅ {variable_name} set to {variable_value} successfully!")
        except Exception as error:
            print(f"❌ Error setting variables: {error}")

    async def get_variable(self, variable_name: str):
        try:
            # gets the database connection from pool
            async with self.pool.acquire() as conn:
                # inserting/updating the variable
                value = await conn.fetchrow(
                    """
                    SELECT VALUE FROM MASTER_DATA
                    WHERE NAME = $1
                    """,
                    variable_name,
                )
                return value["value"]
        except Exception as error:
            print(f"❌ Error fetching variables: {error}")

    async def load_all_variables(self, variable_name: str):
        try:
            dictionary = {}

            # gets the database connection from pool
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    -- gets all the prefixes
                    SELECT ID, VALUE
                    FROM SERVER_DATA
                    WHERE NAME = $1
                    """,
                    variable_name,
                );
                # parsing the data into a dictionary
                for row in rows:
                    dictionary.update({row["id"]: row["value"]})

                return dictionary
        except Exception as error:
            print(f"Error at loading prefixes: {error}")
            return None

    async def delete_all_variables(self, server_id: int):
        try:
            # gets the database connection from pool
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    -- deletes all the variables with the given server id
                    DELETE FROM SERVER_DATA
                    WHERE ID = $1
                    """,
                    server_id,
                )
        except Exception as error:
            print(f"Error at deleting variables: {error}")

db = Database()
