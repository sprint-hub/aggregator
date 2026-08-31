import asyncio
import sys
from pathlib import Path


sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal
from app.services.user_service import user_service
from app.schemas.user import UserCreate
from app.models.user import UserRole, AgentTier


async def create_test_users():
    async with AsyncSessionLocal() as db:
        # Create an admin user
        admin_data = UserCreate(
            email="admin@finref.com",
            password="Admin123!",
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
            phone="+1234567890",
        )
        
        admin = await user_service.create(db, admin_data)
        admin.status = "active"
        await db.commit()
        print(f" Admin created: {admin.email}")

        
        agent_data = UserCreate(
            email="agent@finref.com",
            password="Agent123!",
            first_name="Alex",
            last_name="Henderson",
            role=UserRole.AGENT,
            agent_code="AGENT_PRO_42",
            agent_tier=AgentTier.SENIOR_PARTNER,
            region="North East",
            phone="+1234567891",
        )
        
        agent = await user_service.create(db, agent_data)
        agent.status = "active"
        agent.verification_status = True
        agent.efficiency_score = 94.0
        await db.commit()
        print(f" Agent created: {agent.email}")

        print("\n Test Credentials:")
        print("Admin: admin@finref.com / Admin123!")
        print("Agent: agent@finref.com / Agent123!")


if __name__ == "__main__":
    asyncio.run(create_test_users())