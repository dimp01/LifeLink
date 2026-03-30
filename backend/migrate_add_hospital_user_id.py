"""
Migration script to add user_id column to hospitals table.
This preserves existing data while updating the schema.
"""

import asyncio
from sqlalchemy import text
from database import engine


async def migrate_add_user_id() -> None:
    """Add user_id column to hospitals table if it doesn't exist"""
    async with engine.begin() as conn:
        # Check if column exists
        result = await conn.execute(
            text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='hospitals' AND column_name='user_id'
            )
            """)
        )
        column_exists = result.first()[0]
        
        if column_exists:
            print("✓ Column 'user_id' already exists in hospitals table")
        else:
            print("☐ Adding 'user_id' column to hospitals table...")
            # Add the column as nullable first
            await conn.execute(
                text("""
                ALTER TABLE hospitals 
                ADD COLUMN user_id UUID REFERENCES users(id)
                """)
            )
            print("✓ Column 'user_id' added successfully")


if __name__ == "__main__":
    asyncio.run(migrate_add_user_id())
    print("Migration complete.")
