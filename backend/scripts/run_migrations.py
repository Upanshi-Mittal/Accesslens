



import asyncio
import asyncpg
import argparse
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_migrations(host: str, port: int, database: str, user: str, password: str):


    conn = await asyncpg.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database
    )


    await conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


    current = await conn.fetchval("SELECT MAX(version) FROM schema_migrations")
    current = current or 0


    migrations_dir = Path(__file__).parent / "../migrations"
    migration_files = sorted(migrations_dir.glob("*.sql"))

    for migration_file in migration_files:

        version = int(migration_file.stem.split('_')[0])

        if version > current:
            logger.info(f"Applying migration {migration_file.name}...")


            with open(migration_file, 'r') as f:
                sql = f.read()

            async with conn.transaction():
                await conn.execute(sql)
                await conn.execute(
                    "INSERT INTO schema_migrations (version, name) VALUES ($1, $2)",
                    version, migration_file.name
                )

            logger.info(f"Migration {migration_file.name} applied successfully")

    await conn.close()
    logger.info("All migrations completed")

def main():
    parser = argparse.ArgumentParser(description="Run database migrations")
    parser.add_argument("--host", default="localhost", help="Database host")
    parser.add_argument("--port", type=int, default=5432, help="Database port")
    parser.add_argument("--database", default="accesslens", help="Database name")
    parser.add_argument("--user", default="accesslens", help="Database user")
    parser.add_argument("--password", default="accesslens", help="Database password")

    args = parser.parse_args()

    asyncio.run(run_migrations(
        host=args.host,
        port=args.port,
        database=args.database,
        user=args.user,
        password=args.password
    ))

if __name__ == "__main__":
    main()