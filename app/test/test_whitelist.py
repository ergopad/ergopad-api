import pytest
from api.v1.routes.whitelist import Whitelist, checkEventConstraints


@pytest.mark.asyncio
async def test_checkEventConstraints_for_default_events(mocker):
    # setup
    mocker.patch('api.v1.routes.staking.staked', return_value={
        "totalStaked": 0,
        "addresses": []
    })

    # act
    whitelist = Whitelist(
        event="test",
        ergoAddress="test",
        email="test@test.com",
        name="test",
        sigValue=0,
        socialHandle="test",
        socialPlatform="test",
        chatHandle="test",
        chatPlatform="test",
    )
    ret = await checkEventConstraints(whitelist)

    # assert
    assert ret[0] == True and ret[1] == 'ok'

@pytest.mark.asyncio
async def test_checkEventConstraints_for_paideia_staker_success(mocker):
    # setup
    mocker.patch('api.v1.routes.whitelist.staked', return_value={
        "totalStaked": 1000,
        "addresses": []
    })

    # act
    whitelist = Whitelist(
        event="paideia-presale-staker-202203wl",
        ergoAddress="test",
        email="test@test.com",
        name="test",
        sigValue=0,
        socialHandle="test",
        socialPlatform="test",
        chatHandle="test",
        chatPlatform="test",
    )
    ret = await checkEventConstraints(whitelist)

    # assert
    assert ret[0] == True and ret[1] == 'ok'

@pytest.mark.asyncio
async def test_checkEventConstraints_for_paideia_staker_not_enough_staked(mocker):
    # setup
    mocker.patch('api.v1.routes.whitelist.staked', return_value={
        "totalStaked": 500,
        "addresses": []
    })

    # act
    whitelist = Whitelist(
        event="paideia-presale-staker-202203wl",
        ergoAddress="test",
        email="test@test.com",
        name="test",
        sigValue=0,
        socialHandle="test",
        socialPlatform="test",
        chatHandle="test",
        chatPlatform="test",
    )
    ret = await checkEventConstraints(whitelist)

    # assert
    assert ret[0] == False and ret[1] == 'Not enough ergopad staked for this address. Min stake required is 1000.'
