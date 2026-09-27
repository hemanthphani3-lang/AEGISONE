import pytest
import asyncio
from app.db.session import engine

@pytest.fixture(scope="session", autouse=True)
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def cleanup_engine():
    yield
    await engine.dispose()
