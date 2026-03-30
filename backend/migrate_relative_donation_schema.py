#!/usr/bin/env python3
"""
Migration script to update donor schema for email-based relative donations
and create match_requests table for match request tracking.

Changes:
1. Drop old foreign key constraint on relative_recipient_id
2. Drop relative_recipient_id column
3. Add relative_recipient_email column
4. Create match_requests table
"""

import asyncio
from database import engine
from sqlalchemy import text


async def run_migration():
    async with engine.begin() as conn:
        # Migration steps
        DDL_STATEMENTS = [
            # Step 1: Drop old FK constraint if it exists
            """ALTER TABLE donors DROP CONSTRAINT IF EXISTS donors_relative_recipient_id_fkey;""",
            
            # Step 2: Drop old column if it exists
            """ALTER TABLE donors DROP COLUMN IF EXISTS relative_recipient_id;""",
            
            # Step 3: Add email column for relative recipient
            """ALTER TABLE donors ADD COLUMN IF NOT EXISTS relative_recipient_email VARCHAR;""",
            
            # Step 4: Create match_requests table
            """CREATE TABLE IF NOT EXISTS match_requests (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                donor_id UUID NOT NULL REFERENCES donors(id),
                recipient_id UUID NOT NULL REFERENCES recipients(id),
                status VARCHAR DEFAULT 'pending',
                message TEXT,
                requested_at TIMESTAMP DEFAULT NOW(),
                responded_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );""",
            
            # Step 5: Create index for faster lookups
            """CREATE INDEX IF NOT EXISTS idx_match_requests_donor_id ON match_requests(donor_id);""",
            """CREATE INDEX IF NOT EXISTS idx_match_requests_recipient_id ON match_requests(recipient_id);""",
            """CREATE INDEX IF NOT EXISTS idx_match_requests_status ON match_requests(status);""",
        ]
        
        for sql in DDL_STATEMENTS:
            try:
                await conn.execute(text(sql))
                print(f"✓ OK: {sql.strip()[:60]}...")
            except Exception as e:
                print(f"✗ Error: {sql.strip()[:60]}...")
                print(f"  Details: {str(e)}")
                raise
        
        print("\nRelative donation schema migration complete.")


if __name__ == "__main__":
    asyncio.run(run_migration())
