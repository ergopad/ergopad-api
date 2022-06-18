# bootstrap
import pytest

# imports
from main import ping


def test_always_passes():
    return True


# @pytest.mark.asyncio
def test_ping():
    res = ping()
    assert res["hello"] == "world"
