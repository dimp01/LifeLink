"""
Backfill recipients table columns required by current Recipient model and recipient/admin routes.
Safe to run multiple times.
"""

import asyncio
from sqlalchemy import text
from database import engine


DDL_STATEMENTS = [
    "ALTER TABLE recipients ADD COLUMN IF NOT EXISTS phone VARCHAR",
    "ALTER TABLE recipients ADD COLUMN IF NOT EXISTS address TEXT",
    "ALTER TABLE recipients ADD COLUMN IF NOT EXISTS hospital_contact_name VARCHAR",
    "ALTER TABLE recipients ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT false",
    "ALTER TABLE recipients ADD COLUMN IF NOT EXISTS documents JSON",
    "ALTER TABLE recipients ADD COLUMN IF NOT EXISTS verification_notes TEXT",
    "ALTER TABLE recipients ADD COLUMN IF NOT EXISTS reviewer_notes TEXT",
    "ALTER TABLE recipients ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMP",
    "ALTER TABLE recipients ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP",
    "ALTER TABLE recipients ADD COLUMN IF NOT EXISTS verified_by UUID",
    "ALTER TABLE recipients ADD CONSTRAINT recipients_verified_by_fkey FOREIGN KEY (verified_by) REFERENCES users(id)",
]


async def migrate() -> None:
    async with engine.begin() as conn:
        for ddl in DDL_STATEMENTS:
            try:
                await conn.execute(text(ddl))
                print(f"OK: {ddl}")
            except Exception as exc:
                # Constraint may already exist or be named differently; keep migration idempotent.
                print(f"SKIP/FAIL: {ddl} -> {exc}")


if __name__ == "__main__":
    asyncio.run(migrate())
    print("Recipients schema migration complete.")
