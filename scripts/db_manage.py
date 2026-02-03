#!/usr/bin/env python3
"""
Database management script for Resume Optimizer Arab.

This script provides idempotent database operations:
- nuke: Drop all tables, enums, and alembic version
- reset: Nuke + create all tables fresh (no migrations)
- migrate: Run alembic migrations
- fresh: Nuke + generate new migration + apply it

Usage:
    python scripts/db_manage.py nuke      # Drop everything
    python scripts/db_manage.py reset     # Drop and recreate tables
    python scripts/db_manage.py migrate   # Run pending migrations
    python scripts/db_manage.py fresh     # Full reset with new migration
    python scripts/db_manage.py status    # Show current migration status
"""

import argparse
import asyncio
import os
import subprocess
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables from .env.dev or .env.prod
from dotenv import load_dotenv

env_file = PROJECT_ROOT / ".env.dev"
if not env_file.exists():
    env_file = PROJECT_ROOT / ".env.prod"
if env_file.exists():
    load_dotenv(env_file)
    print(f"📁 Loaded environment from: {env_file.name}")

from libs.common.config import get_settings
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# All enum types used in the models
ENUM_TYPES = [
    "resume_source_enum",
    "embedding_status_enum",
    "job_status_enum",
    "task_type_enum",
    "task_status_enum",
]

# All tables in dependency order (children first for clean drops)
TABLES = [
    "optimizations",
    "task_queue",
    "resume_versions",
    "jobs",
    "resumes",
    "workflow_tokens",
    "alembic_version",
    "alembic_version_academy",
]


async def get_engine():
    """Create async engine for database operations."""
    settings = get_settings()
    return create_async_engine(
        settings.DATABASE_URL,
        echo=True,
        pool_pre_ping=True,
    )


async def nuke_database():
    """Drop all tables and enum types."""
    print("\n🔥 NUKING DATABASE...")
    print("=" * 50)

    engine = await get_engine()

    async with engine.begin() as conn:
        # Drop all tables
        for table in TABLES:
            print(f"  Dropping table: {table}")
            await conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))

        # Drop all enum types
        for enum_type in ENUM_TYPES:
            print(f"  Dropping enum: {enum_type}")
            await conn.execute(text(f"DROP TYPE IF EXISTS {enum_type} CASCADE"))

    await engine.dispose()
    print("\n✅ Database nuked successfully!")


async def create_tables():
    """Create all tables using SQLAlchemy models."""
    print("\n🔨 CREATING TABLES...")
    print("=" * 50)

    # Import models to register them with Base.metadata
    from libs.db.base import Base
    from services.orchestrator_service.app.db.models import (
        Job,
        Optimization,
        Resume,
        ResumeVersion,
        TaskQueue,
        WorkflowToken,
    )

    engine = await get_engine()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()
    print("\n✅ Tables created successfully!")


async def reset_database():
    """Nuke and recreate all tables."""
    await nuke_database()
    await create_tables()
    print("\n🎉 Database reset complete!")


def run_alembic_command(args: list[str], cwd: Path = PROJECT_ROOT):
    """Run an alembic command."""
    cmd = ["alembic", "-c", "services/orchestrator_service/alembic.ini"] + args
    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    return result.returncode == 0


def generate_migration(message: str = "auto_migration"):
    """Generate a new alembic migration."""
    print("\n📝 GENERATING MIGRATION...")
    print("=" * 50)

    success = run_alembic_command(["revision", "--autogenerate", "-m", message])

    if success:
        print("\n✅ Migration generated successfully!")
    else:
        print("\n❌ Failed to generate migration!")
        sys.exit(1)


def run_migrations():
    """Apply all pending alembic migrations."""
    print("\n🚀 RUNNING MIGRATIONS...")
    print("=" * 50)

    success = run_alembic_command(["upgrade", "head"])

    if success:
        print("\n✅ Migrations applied successfully!")
    else:
        print("\n❌ Failed to apply migrations!")
        sys.exit(1)


def show_status():
    """Show current migration status."""
    print("\n📊 MIGRATION STATUS...")
    print("=" * 50)

    run_alembic_command(["current"])
    print("\n📋 Migration History:")
    run_alembic_command(["history", "--verbose"])


async def fresh_database(message: str = "initial_schema"):
    """Nuke, generate new migration, and apply it."""
    await nuke_database()

    # Remove existing migration files
    versions_dir = (
        PROJECT_ROOT / "services" / "orchestrator_service" / "alembic" / "versions"
    )
    print("\n🗑️  CLEANING OLD MIGRATIONS...")
    for f in versions_dir.glob("*.py"):
        print(f"  Removing: {f.name}")
        f.unlink()

    generate_migration(message)
    run_migrations()
    print("\n🎉 Fresh database setup complete!")


def main():
    parser = argparse.ArgumentParser(
        description="Database management for Resume Optimizer Arab",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # nuke command
    subparsers.add_parser("nuke", help="Drop all tables and enums")

    # reset command
    subparsers.add_parser("reset", help="Nuke and recreate tables (no migrations)")

    # migrate command
    subparsers.add_parser("migrate", help="Run pending alembic migrations")

    # fresh command
    fresh_parser = subparsers.add_parser(
        "fresh", help="Nuke, generate migration, and apply"
    )
    fresh_parser.add_argument(
        "-m",
        "--message",
        default="initial_schema",
        help="Migration message (default: initial_schema)",
    )

    # status command
    subparsers.add_parser("status", help="Show migration status")

    # generate command
    gen_parser = subparsers.add_parser("generate", help="Generate new migration")
    gen_parser.add_argument(
        "-m",
        "--message",
        default="auto_migration",
        help="Migration message",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "nuke":
        asyncio.run(nuke_database())
    elif args.command == "reset":
        asyncio.run(reset_database())
    elif args.command == "migrate":
        run_migrations()
    elif args.command == "fresh":
        asyncio.run(fresh_database(args.message))
    elif args.command == "status":
        show_status()
    elif args.command == "generate":
        generate_migration(args.message)


if __name__ == "__main__":
    main()
