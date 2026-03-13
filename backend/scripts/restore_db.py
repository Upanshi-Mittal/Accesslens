



import argparse
import subprocess
from pathlib import Path
import os

def main():
    parser = argparse.ArgumentParser(description="Restore AccessLens database")
    parser.add_argument("--host", default="localhost", help="Database host")
    parser.add_argument("--port", type=int, default=5432, help="Database port")
    parser.add_argument("--database", default="accesslens", help="Database name")
    parser.add_argument("--user", default="accesslens", help="Database user")
    parser.add_argument("--password", default="accesslens", help="Database password")
    parser.add_argument("backup_file", help="Backup file to restore")

    args = parser.parse_args()


    backup_path = Path(args.backup_file)
    if not backup_path.exists():
        print(f" Backup file not found: {backup_path}")
        return 1


    print(f"  WARNING: This will overwrite the database '{args.database}'")
    response = input("Are you sure you want to continue? [y/N]: ")

    if response.lower() != 'y':
        print("Restore cancelled")
        return 0


    env = os.environ.copy()
    env["PGPASSWORD"] = args.password


    drop_cmd = [
        "psql",
        "-h", args.host,
        "-p", str(args.port),
        "-U", args.user,
        "-d", "postgres",
        "-c", f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{args.database}';"
    ]

    subprocess.run(drop_cmd, env=env, capture_output=True)


    drop_db_cmd = [
        "psql",
        "-h", args.host,
        "-p", str(args.port),
        "-U", args.user,
        "-d", "postgres",
        "-c", f"DROP DATABASE IF EXISTS {args.database};"
    ]

    subprocess.run(drop_db_cmd, env=env, capture_output=True)

    create_db_cmd = [
        "psql",
        "-h", args.host,
        "-p", str(args.port),
        "-U", args.user,
        "-d", "postgres",
        "-c", f"CREATE DATABASE {args.database};"
    ]

    subprocess.run(create_db_cmd, env=env, capture_output=True)


    restore_cmd = [
        "psql",
        "-h", args.host,
        "-p", str(args.port),
        "-U", args.user,
        "-d", args.database,
        "-f", str(backup_path)
    ]

    print(f"Restoring from: {backup_path}")
    result = subprocess.run(restore_cmd, env=env, capture_output=True, text=True)

    if result.returncode == 0:
        print(f" Database restored successfully")
    else:
        print(f" Restore failed: {result.stderr}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())