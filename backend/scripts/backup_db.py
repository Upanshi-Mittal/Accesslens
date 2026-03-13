



import argparse
import subprocess
from datetime import datetime
from pathlib import Path
import os

def main():
    parser = argparse.ArgumentParser(description="Backup AccessLens database")
    parser.add_argument("--host", default="localhost", help="Database host")
    parser.add_argument("--port", type=int, default=5432, help="Database port")
    parser.add_argument("--database", default="accesslens", help="Database name")
    parser.add_argument("--user", default="accesslens", help="Database user")
    parser.add_argument("--password", default="accesslens", help="Database password")
    parser.add_argument("--output", help="Output directory for backup")

    args = parser.parse_args()


    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"accesslens_backup_{timestamp}.sql"


    output_dir = args.output or "./backups"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    backup_path = Path(output_dir) / backup_file


    env = os.environ.copy()
    env["PGPASSWORD"] = args.password


    cmd = [
        "pg_dump",
        "-h", args.host,
        "-p", str(args.port),
        "-U", args.user,
        "-d", args.database,
        "-f", str(backup_path),
        "--clean",
        "--if-exists"
    ]

    print(f"Creating backup: {backup_path}")
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)

    if result.returncode == 0:
        print(f" Backup created successfully: {backup_path}")
        print(f"Size: {backup_path.stat().st_size / 1024 / 1024:.2f} MB")
    else:
        print(f" Backup failed: {result.stderr}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())