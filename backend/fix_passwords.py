#!/usr/bin/env python3
"""Update password hashes for existing users"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from config import settings
from models import User
from auth import hash_password

DATABASE_URL = settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://').split('?')[0]
engine = create_async_engine(DATABASE_URL, connect_args={'ssl': 'require'})
Session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def update_passwords():
    async with Session() as db:
        # Update admin password
        result = await db.execute(select(User).where(User.email == "admin@lifelink.ai"))
        admin = result.scalar_one_or_none()
        if admin:
            admin.hashed_password = hash_password("Admin@123")
            print(f"Updated admin password for {admin.email}")
        
        # Update hospital password
        result = await db.execute(select(User).where(User.email == "hospital@lifelink.ai"))
        hospital = result.scalar_one_or_none()
        if hospital:
            hospital.hashed_password = hash_password("Hospital@123")
            print(f"Updated hospital password for {hospital.email}")
        
        await db.commit()
        print("Password hashes updated!")

asyncio.run(update_passwords())
