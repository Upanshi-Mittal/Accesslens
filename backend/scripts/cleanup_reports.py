



import asyncio
import asyncpg
import argparse
from datetime import datetime, timedelta

async def cleanup_reports(days: int, host: str, port: int, database: str, user: str, password: str):


    conn = await asyncpg.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database
    )

    cutoff_date = datetime.now() - timedelta(days=days)


    count = await conn.fetchval(
        "SELECT COUNT(*) FROM reports WHERE timestamp < $1",
        cutoff_date
    )

    if count == 0:
        print(f"No reports older than {days} days found")
        return

    print(f"Found {count} reports older than {days} days")


    result = await conn.execute(
        "DELETE FROM reports WHERE timestamp < $1",
        cutoff_date
    )

    deleted = result.split()[-1]
    print(f"Deleted {deleted} reports")

    await conn.close()

def main():
    parser = argparse.ArgumentParser(description="Clean up old reports")
    parser.add_argument("--days", type=int, default=30, help="Delete reports older than DAYS")
    parser.add_argument("--host", default="localhost", help="Database host")
    parser.add_argument("--port", type=int, default=5432, help="Database port")
    parser.add_argument("--database", default="accesslens", help="Database name")
    parser.add_argument("--user", default="accesslens", help="Database user")
    parser.add_argument("--password", default="accesslens", help="Database password")

    args = parser.parse_args()

    asyncio.run(cleanup_reports(
        days=args.days,
        host=args.host,
        port=args.port,
        database=args.database,
        user=args.user,
        password=args.password
    ))

if __name__ == "__main__":
    main()