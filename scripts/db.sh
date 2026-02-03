#!/bin/bash
#
# Database management wrapper script
#
# Usage:
#   ./scripts/db.sh nuke      # Drop all tables and enums
#   ./scripts/db.sh reset     # Drop and recreate tables
#   ./scripts/db.sh migrate   # Run pending migrations
#   ./scripts/db.sh fresh     # Nuke + new migration + apply
#   ./scripts/db.sh status    # Show migration status
#   ./scripts/db.sh generate  # Generate new migration
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Load environment variables
if [ -f ".env.dev" ]; then
    export $(grep -v '^#' .env.dev | xargs)
fi

# Run the Python script
python scripts/db_manage.py "$@"
