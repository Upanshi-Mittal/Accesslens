


import asyncio
import asyncpg
import argparse
import logging
from pathlib import Path
import sys
from typing import Optional
import getpass


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseSetup:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "accesslens",
        user: str = "accesslens",
        password: Optional[str] = None,
        admin_user: str = "postgres",
        admin_password: Optional[str] = None
    ):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.admin_user = admin_user
        self.admin_password = admin_password

    async def create_database(self) -> bool:

        try:

            conn = await asyncpg.connect(
                host=self.host,
                port=self.port,
                user=self.admin_user,
                password=self.admin_password,
                database='postgres'
            )


            user_exists = await conn.fetchval(
                "SELECT 1 FROM pg_roles WHERE rolname = $1",
                self.user
            )

            if not user_exists:
                logger.info(f"Creating user: {self.user}")
                await conn.execute(f"CREATE USER {self.user} WITH PASSWORD $1", self.password)
            else:
                logger.info(f"User {self.user} already exists")


            db_exists = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1",
                self.database
            )

            if not db_exists:
                logger.info(f"Creating database: {self.database}")
                await conn.execute(f"CREATE DATABASE {self.database} OWNER {self.user}")
            else:
                logger.info(f"Database {self.database} already exists")


            await conn.execute(f"GRANT ALL PRIVILEGES ON DATABASE {self.database} TO {self.user}")

            await conn.close()
            return True

        except Exception as e:
            logger.error(f"Failed to create database: {e}")
            return False

    async def create_tables(self) -> bool:

        try:

            conn = await asyncpg.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )


            migration_path = Path(__file__).parent.parent / "migrations" / "001_init.sql"

            if not migration_path.exists():
                logger.error(f"Migration file not found: {migration_path}")
                return False

            with open(migration_path, 'r') as f:
                sql = f.read()


            logger.info("Creating database tables...")
            await conn.execute(sql)


            tables = await conn.fetch()

            logger.info(f"Created {len(tables)} tables:")
            for table in tables:

                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table['table_name']}")
                logger.info(f"  - {table['table_name']}: {count} rows")

            await conn.close()
            return True

        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            return False

    async def test_connection(self) -> bool:

        try:
            conn = await asyncpg.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )


            result = await conn.fetchval("SELECT 1")
            await conn.close()

            return result == 1

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    async def setup(self) -> bool:

        logger.info(" Starting database setup...")
        logger.info(f"Host: {self.host}:{self.port}")
        logger.info(f"Database: {self.database}")
        logger.info(f"User: {self.user}")


        if not await self.create_database():
            logger.error("Failed to create database")
            return False


        if not await self.create_tables():
            logger.error("Failed to create tables")
            return False


        if not await self.test_connection():
            logger.error("Connection test failed")
            return False

        logger.info(" Database setup completed successfully!")
        return True

    async def reset(self) -> bool:

        logger.warning("  This will DELETE ALL DATA in the database!")
        response = input("Are you absolutely sure? Type 'YES' to confirm: ")

        if response != "YES":
            logger.info("Reset cancelled")
            return False

        try:
            conn = await asyncpg.connect(
                host=self.host,
                port=self.port,
                user=self.admin_user,
                password=self.admin_password,
                database='postgres'
            )


            # Terminate other connections to the database to allow dropping it
            await conn.execute(f"""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = '{self.database}'
                  AND pid <> pg_backend_pid()
            """)


            await conn.execute(f"DROP DATABASE IF EXISTS {self.database}")
            await conn.execute(f"CREATE DATABASE {self.database} OWNER {self.user}")

            await conn.close()


            return await self.create_tables()

        except Exception as e:
            logger.error(f"Reset failed: {e}")
            return False

async def main_async():
    parser = argparse.ArgumentParser(description="Setup AccessLens database")
    parser.add_argument("--host", default="localhost", help="Database host")
    parser.add_argument("--port", type=int, default=5432, help="Database port")
    parser.add_argument("--database", default="accesslens", help="Database name")
    parser.add_argument("--user", default="accesslens", help="Database user")
    parser.add_argument("--password", help="Database password (will prompt if not provided)")
    parser.add_argument("--admin-user", default="postgres", help="Admin user for creating database")
    parser.add_argument("--admin-password", help="Admin password (will prompt if not provided)")
    parser.add_argument("--reset", action="store_true", help="Reset database (delete all data)")
    parser.add_argument("--test-only", action="store_true", help="Only test connection")

    args = parser.parse_args()


    if not args.password:
        args.password = getpass.getpass(f"Password for {args.user}: ")

    if not args.admin_password:
        args.admin_password = getpass.getpass(f"Password for admin user {args.admin_user}: ")

    setup = DatabaseSetup(
        host=args.host,
        port=args.port,
        database=args.database,
        user=args.user,
        password=args.password,
        admin_user=args.admin_user,
        admin_password=args.admin_password
    )

    if args.test_only:
        if await setup.test_connection():
            logger.info(" Connection successful!")
            return 0
        else:
            logger.error(" Connection failed!")
            return 1

    if args.reset:
        if await setup.reset():
            logger.info(" Database reset successfully!")
            return 0
        else:
            logger.error(" Database reset failed!")
            return 1

    if await setup.setup():
        return 0
    else:
        return 1

def main():

    try:
        return asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("\nSetup cancelled")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())