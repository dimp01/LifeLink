"""
Seed script: Creates default admin user and awareness content.
Run once: python seed.py
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

# Must be run from backend/ directory
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from config import settings
from models import Base, User, UserRole, AwarenessContent, ContentType
from auth import hash_password

DATABASE_URL = settings.DATABASE_URL.replace(
    "postgresql://", "postgresql+asyncpg://"
).split("?")[0]

engine = create_async_engine(DATABASE_URL, connect_args={"ssl": "require"})
Session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


AWARENESS_SEEDS = [
    {"title": "Myth: Organ donation disfigures the body", "content": "FACT: Organ donation is performed with the utmost care and respect. The body is treated respectfully and can still have an open-casket funeral if desired.", "type": ContentType.myth},
    {"title": "Myth: Rich patients get organs faster", "content": "FACT: Organ allocation is based on medical urgency, compatibility, and waiting time — not on wealth or social status.", "type": ContentType.myth},
    {"title": "Myth: Doctors won't try to save me if I'm a donor", "content": "FACT: Medical teams work tirelessly to save every patient. Organ donation is only considered after all lifesaving efforts have failed.", "type": ContentType.myth},
    {"title": "What is organ donation?", "content": "Organ donation is the process of surgically removing an organ or tissue from one person (the donor) and placing it into another person (the recipient). Transplantation is often the only treatment for end-stage organ failure.", "type": ContentType.faq},
    {"title": "Who can donate organs?", "content": "Almost anyone can be an organ donor, regardless of age or medical history. The medical team will determine at the time of death which organs and tissues are suitable for transplantation.", "type": ContentType.faq},
    {"title": "How to register as an organ donor?", "content": "You can register on the National Organ and Tissue Transplant Organisation (NOTTO) website at notto.mohfw.gov.in. Inform your family of your decision as well.", "type": ContentType.faq},
    {"title": "Transplantation of Human Organs Act (THOA)", "content": "The Transplantation of Human Organs Act, 1994 (amended 2011) regulates the removal, storage and transplantation of human organs for therapeutic purposes and for prevention of commercial dealings in human organs in India.", "type": ContentType.legal},
    {"title": "Brain Death and Legal Framework", "content": "Under THOA, brain death is legally recognized as death in India. A certified brain-dead patient can donate organs after consent from the next of kin. Brain death must be certified by a panel of doctors.", "type": ContentType.legal},
    {"title": "The Gift of Life – A Personal Story", "content": "Every year, thousands of lives are saved through organ donation. One donor can save up to 8 lives and improve the lives of up to 75 people through tissue donation. Your decision to donate is a profound act of generosity.", "type": ContentType.blog},
    {"title": "Religious Views on Organ Donation", "content": "Most major religions including Hinduism, Islam, Christianity, Sikhism, Buddhist and Jainism support organ donation as an act of compassion and generosity. Always consult with your religious leader if you have concerns.", "type": ContentType.blog},
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with Session() as db:
        # Create admin
        result = await db.execute(select(User).where(User.email == "admin@lifelink.ai"))
        if not result.scalar_one_or_none():
            admin = User(
                email="admin@lifelink.ai",
                hashed_password=hash_password("Admin@123"),
                full_name="Super Admin",
                role=UserRole.admin,
            )
            db.add(admin)
            print("Created admin: admin@lifelink.ai / Admin@123")
        else:
            print("Admin already exists")

        # Create hospital user
        result = await db.execute(select(User).where(User.email == "hospital@lifelink.ai"))
        if not result.scalar_one_or_none():
            hosp = User(
                email="hospital@lifelink.ai",
                hashed_password=hash_password("Hospital@123"),
                full_name="Demo Hospital",
                role=UserRole.hospital,
            )
            db.add(hosp)
            print("Created hospital: hospital@lifelink.ai / Hospital@123")

        # Seed awareness content
        result = await db.execute(select(AwarenessContent))
        existing = result.scalars().all()
        if not existing:
            for seed_item in AWARENESS_SEEDS:
                db.add(AwarenessContent(**seed_item))
            print(f"Seeded {len(AWARENESS_SEEDS)} awareness content items")
        else:
            print("Awareness content already exists")

        await db.commit()
    print("Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed())
