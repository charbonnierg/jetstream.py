import pytest

from jsm import JS, connect


@pytest.fixture
async def js() -> JS:
    js = await connect()
    try:
        yield js
    finally:
        await js.close()
