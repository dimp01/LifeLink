"""
Allow partial recipient/hospital profiles by making key columns nullable.
"""

import asyncio
from sqlalchemy import text
from database import engine


DDL_STATEMENTS = [
    # hospitals (actual DB column names)
    "ALTER TABLE hospitals ALTER COLUMN name DROP NOT NULL",
    "ALTER TABLE hospitals ALTER COLUMN city DROP NOT NULL",
    "ALTER TABLE hospitals ALTER COLUMN state DROP NOT NULL",

    # recipients
    "ALTER TABLE recipients ALTER COLUMN full_name DROP NOT NULL",
    "ALTER TABLE recipients ALTER COLUMN age DROP NOT NULL",
    "ALTER TABLE recipients ALTER COLUMN blood_group DROP NOT NULL",
    "ALTER TABLE recipients ALTER COLUMN medical_condition DROP NOT NULL",
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
    print("Nullable profile migration complete.")
