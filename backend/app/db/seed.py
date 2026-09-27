from sqlalchemy.ext.asyncio import AsyncSession
from app.db.converters import from_domain_policy
from app.db.models import DBPolicy
from app.engine.repository import DEFAULT_POLICIES


async def seed_initial_policies(session: AsyncSession) -> int:
    """Seed initial development policies if they do not exist.

    Returns number of newly seeded policies.
    """
    count = 0
    for domain_policy in DEFAULT_POLICIES:
        existing = await session.get(DBPolicy, domain_policy.id)
        if not existing:
            db_policy = from_domain_policy(domain_policy)
            session.add(db_policy)
            count += 1

    if count > 0:
        await session.commit()
    return count
