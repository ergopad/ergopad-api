import pytest

from api.v1.routes.asset import get_asset_current_price
from cache.cache import RedisCache


def mock_get(self, key):
    return None


def mock_set(self, key, value, timeout=-1):
    return


class MockSqlAlchemyResponse:
    def fetchone(self):
        return None


class MockHttpResponse:
    def __init__(self, status):
        self.status = status

    def json(self):
        return {"status": self.status}


def init_mocks_success(mocker):
    mocker.patch.object(
        RedisCache,
        "get",
        mock_get,
    )
    mocker.patch.object(
        RedisCache,
        "set",
        mock_set,
    )
    mocker.patch(
        "api.v1.routes.asset.getErgodexTokenPrice",
        return_value={
            "status": "success",
            "price": 1,
        },
    )


def init_mocks_failure(mocker):
    mocker.patch.object(
        RedisCache,
        "get",
        mock_get,
    )
    mocker.patch.object(
        RedisCache,
        "set",
        mock_set,
    )
    mocker.patch(
        "api.v1.routes.asset.getErgodexTokenPrice",
        return_value={
            "status": "error",
        },
    )
    mocker.patch(
        "requests.get",
        return_value=MockHttpResponse("error"),
    )
    mocker.patch(
        "api.v1.routes.asset.con.execute",
        MockSqlAlchemyResponse(),
    )


@pytest.mark.asyncio
async def test_get_asset_current_price_for_ergopad(mocker):
    # setup
    init_mocks_success(mocker)

    # act
    ret = await get_asset_current_price("ergopad")

    # assert
    assert ret["status"] == "ok" and ret["price"] == 1


@pytest.mark.asyncio
async def test_get_asset_current_price_for_ergoxyz(mocker):
    # setup
    init_mocks_failure(mocker)

    # act
    ret = await get_asset_current_price("ergoxyz")

    # assert
    assert ret["status"] == "unavailable" and ret["price"] == None
