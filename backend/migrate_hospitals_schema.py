"""
Comprehensive migration script to sync hospitals table schema.
Checks all columns and adds any that are missing.
"""

import asyncio
from sqlalchemy import text
from database import engine


async def migrate_hospitals_schema() -> None:
    """Check and add all missing columns to hospitals table"""
    
    # Define expected columns with their SQL definitions
    columns_to_check = {
        "id": "UUID PRIMARY KEY DEFAULT gen_random_uuid()",
        "user_id": "UUID NOT NULL REFERENCES users(id)",
        "hospital_name": "TEXT NOT NULL",
        "registration_number": "TEXT NOT NULL UNIQUE",
        "city": "TEXT NOT NULL",
        "state": "TEXT NOT NULL",
        "phone": "TEXT NOT NULL",
        "email": "TEXT NOT NULL",
        "website": "TEXT",
        "bed_capacity": "INTEGER",
        "specializations": "JSONB DEFAULT '[]'::jsonb",
        "is_verified": "BOOLEAN DEFAULT false",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    }
    
    async with engine.begin() as conn:
        print("Checking hospitals table schema...")
        
        # Get all existing columns
        result = await conn.execute(
            text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name='hospitals'
            ORDER BY column_name
            """)
        )
        existing_columns = {row[0]: row[1] for row in result.fetchall()}
        
        print(f"\nExisting columns: {list(existing_columns.keys())}")
        print(f"Expected columns: {list(columns_to_check.keys())}")
        
        # Find missing columns
        missing_columns = set(columns_to_check.keys()) - set(existing_columns.keys())
        
        if missing_columns:
            print(f"\n⚠️  Missing columns: {missing_columns}")
            
            for col in missing_columns:
                try:
                    # Special handling for different column types
                    if col == "specializations":
                        sql = f"ALTER TABLE hospitals ADD COLUMN {col} JSONB DEFAULT '[]'::jsonb"
                    elif col in ["website", "bed_capacity"]:
                        # These are nullable columns
                        col_type = "TEXT" if col == "website" else "INTEGER"
                        sql = f"ALTER TABLE hospitals ADD COLUMN {col} {col_type}"
                    elif col in ["created_at", "updated_at"]:
                        sql = f"ALTER TABLE hospitals ADD COLUMN {col} TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                    elif col == "is_verified":
                        sql = f"ALTER TABLE hospitals ADD COLUMN {col} BOOLEAN DEFAULT false"
                    else:
                        col_type = "TEXT" if col != "user_id" else "UUID"
                        nullable = "" if col != "user_id" else " NOT NULL"
                        sql = f"ALTER TABLE hospitals ADD COLUMN {col} {col_type}{nullable}"
                    
                    await conn.execute(text(sql))
                    print(f"  ✓ Added column: {col}")
                except Exception as e:
                    print(f"  ✗ Error adding column {col}: {e}")
        else:
            print("\n✓ All expected columns exist!")
        
        # Show final schema
        result = await conn.execute(
            text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name='hospitals'
            ORDER BY ordinal_position
            """)
        )
        
        print("\n" + "="*60)
        print("Final hospitals table schema:")
        print("="*60)
        for row in result.fetchall():
            nullable = "NULL" if row[2] == "YES" else "NOT NULL"
            print(f"  {row[0]:20} {row[1]:15} {nullable}")
        print("="*60)


if __name__ == "__main__":
    asyncio.run(migrate_hospitals_schema())
    print("\nMigration check complete.")
