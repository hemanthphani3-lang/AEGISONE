import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.db.converters import from_domain_policy, to_domain_policy
from app.db.models import Base
from app.db.seed import seed_initial_policies
from app.engine.enums import AuthProtocol, PolicyDecision, UserRole
from app.engine.models import Policy
from app.engine.postgres_repository import PostgresPolicyRepository


@pytest_asyncio.fixture
async def async_session():
    """Create an isolated in-memory SQLite database session for repository testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_repo_create_and_get_by_id(async_session: AsyncSession):
    """Test creating and retrieving a policy by ID."""
    repo = PostgresPolicyRepository(async_session)
    policy = Policy(
        id="test-p1",
        name="Test Policy 1",
        description="Description 1",
        enabled=True,
        target_roles=[UserRole.ADMIN],
        target_protocols=[AuthProtocol.MODERN],
        target_locations=["IN"],
        target_device_managed=True,
        target_device_compliant=True,
        action=PolicyDecision.MFA_REQUIRED,
        exclusions=[UserRole.BREAK_GLASS],
        excluded_users=["u100"],
    )

    created = await repo.create_async(policy)
    assert created.id == "test-p1"
    assert created.name == "Test Policy 1"
    assert created.action == PolicyDecision.MFA_REQUIRED
    assert created.target_roles == [UserRole.ADMIN]
    assert created.target_protocols == [AuthProtocol.MODERN]
    assert created.target_locations == ["IN"]
    assert created.target_device_managed is True
    assert created.target_device_compliant is True
    assert created.exclusions == [UserRole.BREAK_GLASS]
    assert created.excluded_users == ["u100"]

    retrieved = await repo.get_by_id_async("test-p1")
    assert retrieved is not None
    assert retrieved.id == "test-p1"
    assert retrieved.name == "Test Policy 1"


@pytest.mark.asyncio
async def test_repo_list_policies(async_session: AsyncSession):
    """Test listing persisted policies."""
    repo = PostgresPolicyRepository(async_session)
    p1 = Policy(
        id="p1",
        name="P1",
        description="Desc 1",
        action=PolicyDecision.ALLOW,
    )
    p2 = Policy(
        id="p2",
        name="P2",
        description="Desc 2",
        action=PolicyDecision.BLOCK,
    )
    await repo.create_async(p1)
    await repo.create_async(p2)

    all_policies = await repo.get_all_async()
    assert len(all_policies) == 2
    ids = {p.id for p in all_policies}
    assert ids == {"p1", "p2"}


@pytest.mark.asyncio
async def test_repo_update_policy(async_session: AsyncSession):
    """Test updating policy mutable fields."""
    repo = PostgresPolicyRepository(async_session)
    policy = Policy(
        id="update-me",
        name="Old Name",
        description="Old Description",
        enabled=True,
        action=PolicyDecision.MFA_REQUIRED,
    )
    await repo.create_async(policy)

    updated = await repo.update_async(
        "update-me",
        {
            "name": "New Name",
            "enabled": False,
            "action": PolicyDecision.BLOCK,
            "target_roles": [UserRole.STUDENT],
        },
    )

    assert updated is not None
    assert updated.name == "New Name"
    assert updated.enabled is False
    assert updated.action == PolicyDecision.BLOCK
    assert updated.target_roles == [UserRole.STUDENT]


@pytest.mark.asyncio
async def test_repo_delete_policy(async_session: AsyncSession):
    """Test deleting a policy."""
    repo = PostgresPolicyRepository(async_session)
    policy = Policy(
        id="delete-me",
        name="To Delete",
        description="To Delete",
        action=PolicyDecision.BLOCK,
    )
    await repo.create_async(policy)

    success = await repo.delete_async("delete-me")
    assert success is True

    not_found = await repo.get_by_id_async("delete-me")
    assert not_found is None


@pytest.mark.asyncio
async def test_repo_not_found_returns_none(async_session: AsyncSession):
    """Test retrieving non-existent policy returns None."""
    repo = PostgresPolicyRepository(async_session)
    retrieved = await repo.get_by_id_async("non-existent-id")
    assert retrieved is None


@pytest.mark.asyncio
async def test_repo_create_duplicate_raises_value_error(async_session: AsyncSession):
    """Test creating duplicate policy ID raises ValueError."""
    repo = PostgresPolicyRepository(async_session)
    policy = Policy(
        id="dup",
        name="Dup",
        description="Dup",
        action=PolicyDecision.ALLOW,
    )
    await repo.create_async(policy)

    with pytest.raises(ValueError, match="already exists"):
        await repo.create_async(policy)


@pytest.mark.asyncio
async def test_seed_initial_policies(async_session: AsyncSession):
    """Test seeding initial development policies."""
    seeded_count = await seed_initial_policies(async_session)
    assert seeded_count >= 2

    # Seeding again should be idempotent and return 0
    reseed_count = await seed_initial_policies(async_session)
    assert reseed_count == 0

    repo = PostgresPolicyRepository(async_session)
    policies = await repo.get_all_async()
    p_ids = {p.id for p in policies}
    assert "admin-mfa" in p_ids
    assert "block-legacy-auth" in p_ids
