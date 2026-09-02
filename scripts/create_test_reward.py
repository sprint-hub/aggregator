import asyncio
import uuid
from app.core.database import AsyncSessionLocal
from app.models.transaction import Transaction, TransactionStatus, TransactionType
from app.models.user import User
from app.models.referral import Customer, ReferralCode  # noqa: F401 - needed to register relationships
from app.models.payment import Payment  # noqa: F401 - needed to register relationships
from sqlalchemy import select


async def main():
    async with AsyncSessionLocal() as db:
        agent = (await db.execute(
            select(User).where(User.email == "agent@finref.com")
        )).scalar_one()

        txn = Transaction(
            transaction_id=f"RW-{uuid.uuid4().hex[:6].upper()}",
            agent_id=agent.id,
            type=TransactionType.CREDIT,
            amount=250.0,
            status=TransactionStatus.PENDING,
            description="Test reward for admin approval testing",
        )
        db.add(txn)
        await db.commit()
        await db.refresh(txn)

        print(f"Created test reward:")
        print(f"  id (use this as reward_id in the URL): {txn.id}")
        print(f"  transaction_id: {txn.transaction_id}")
        print(f"  status: {txn.status.value}")


if __name__ == "__main__":
    asyncio.run(main())
