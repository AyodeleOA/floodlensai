from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ingestion.seed import seed_demo_data

logger = logging.getLogger(__name__)


async def run_seed(db: AsyncSession) -> dict[str, int]:
    """Seed the database with synthetic demo data for Lagos, Nigeria.

    All data is clearly labelled is_synthetic=True / is_illustrative=True.
    Never label seeded data as live data.
    """
    result = await seed_demo_data(db)
    logger.info(f"Seeded demo data: {result}")
    return result
