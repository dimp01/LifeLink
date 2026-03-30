"""
Adds donor matching related columns used by recipient-driven hospital matching.
Safe to run multiple times.
"""

import asyncio
from sqlalchemy import text
from database import engine


DDL_STATEMENTS = [
    "ALTER TABLE donors ADD COLUMN IF NOT EXISTS city VARCHAR",
    "ALTER TABLE donors ADD COLUMN IF NOT EXISTS state VARCHAR",
    "ALTER TABLE donors ADD COLUMN IF NOT EXISTS hospital_id UUID",
    "ALTER TABLE donors ADD COLUMN IF NOT EXISTS donation_mode VARCHAR DEFAULT 'general'",
    "ALTER TABLE donors ADD COLUMN IF NOT EXISTS relative_recipient_id UUID",
    "ALTER TABLE donors ADD COLUMN IF NOT EXISTS is_deceased BOOLEAN DEFAULT false",
    "ALTER TABLE donors ADD COLUMN IF NOT EXISTS deceased_at TIMESTAMP",
    "ALTER TABLE donors ADD CONSTRAINT donors_hospital_id_fkey FOREIGN KEY (hospital_id) REFERENCES hospitals(id)",
    "ALTER TABLE donors ADD CONSTRAINT donors_relative_recipient_id_fkey FOREIGN KEY (relative_recipient_id) REFERENCES recipients(id)",
]


async def migrate() -> None:
    async with engine.begin() as conn:
        for ddl in DDL_STATEMENTS:
            try:
                await conn.execute(text(ddl))
                print(f"OK: {ddl}")
            except Exception as exc:
                print(f"SKIP/FAIL: {ddl} -> {exc}")


if __name__ == "__main__":
    asyncio.run(migrate())
    print("Donor matching schema migration complete.")
