#!/bin/bash
set -e

# Create necessary directories if they don't exist
mkdir -p /app/data /app/models /app/logs

# Execute the given command (usually uvicorn)
echo "Starting AccessLens API..."
exec "$@"
