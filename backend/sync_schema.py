"""
One-time schema sync utility.
Creates missing tables defined in SQLAlchemy models without dropping data.
"""

import asyncio

from database import engine, Base
import models  # noqa: F401 - ensure models are registered in Base metadata


async def sync_schema() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(sync_schema())
    print("Schema sync complete.")
