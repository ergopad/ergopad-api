# bootstrap
import pytest

# imports
from main import ping, DEBUG


def test_always_passes():
    return True


@pytest.mark.asyncio
async def test_ping():
    res = await ping()
    if DEBUG:
        assert res["hello,"] == "is it me you're looking for?"
    else: 
        assert res["status"] == "invalid"