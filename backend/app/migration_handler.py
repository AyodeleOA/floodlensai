
import logging
import os
from pathlib import Path

from alembic import command
from alembic.config import Config

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """Run database migrations once when explicitly invoked."""

    backend_dir = Path(__file__).resolve().parent.parent
    alembic_ini = backend_dir / "alembic.ini"

    if not alembic_ini.exists():
        raise FileNotFoundError(f"Alembic config not found: {alembic_ini}")

    if not os.environ.get("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL environment variable is missing")

    config = Config(str(alembic_ini))

    # Use the secure runtime environment variable, not the INI credential.
    config.set_main_option(
        "sqlalchemy.url",
        os.environ["DATABASE_URL"].replace("%", "%%"),
    )

    logger.info("Starting FloodLens database migration")

    command.upgrade(config, "head")

    logger.info("FloodLens database migration completed successfully")

    return {
        "statusCode": 200,
        "body": "Database migration completed successfully",
    }
