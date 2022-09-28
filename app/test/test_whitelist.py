import pytest
from api.v1.routes.whitelist import Whitelist, checkEventConstraints
from db.schemas import whitelistEvents as schema


def getEvent(additionalDetails):
    return schema.WhitelistEvent(
        id=1,
        eventName="test",
        description="test",
        total_sigusd=0,
        buffer_sigusd=0,
        individualCap=0,
        start_dtz=0,
        end_dtz=0,
        projectName="test",
        roundName="test",
        eventId=1,
        title="test",
        subtitle="test",
        details="test",
        checkBoxes={"checkBoxText": []},
        additionalDetails=additionalDetails
    )


@pytest.mark.asyncio
def test_checkEventConstraints_for_default_events(mocker):
    # setup
    mocker.patch('api.v1.routes.whitelist.staked', return_value={
        "totalStaked": 0,
        "addresses": []
    })
    mocker.patch('api.v1.routes.whitelist.get_whitelist_event_by_event_id',
                 return_value=getEvent({}))

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
    ret = checkEventConstraints(1, whitelist, None)

    # assert
    assert ret[0] == True and ret[1] == 'ok'


@pytest.mark.asyncio
def test_checkEventConstraints_for_paideia_staker_success(mocker):
    # setup
    mocker.patch('api.v1.routes.whitelist.staked', return_value={
        "totalStaked": 1000,
        "addresses": []
    })
    mocker.patch('api.v1.routes.whitelist.get_whitelist_event_by_event_id',
                 return_value=getEvent({"min_stake": 550}))

    # act
    whitelist = Whitelist(
        event="staker-seed-paideia-202203wl",
        ergoAddress="test",
        email="test@test.com",
        name="test",
        sigValue=0,
        socialHandle="test",
        socialPlatform="test",
        chatHandle="test",
        chatPlatform="test",
    )
    ret = checkEventConstraints(1, whitelist, None)

    # assert
    assert ret[0] == True and ret[1] == 'ok'


@pytest.mark.asyncio
def test_checkEventConstraints_for_paideia_staker_not_enough_staked(mocker):
    # setup
    mocker.patch('api.v1.routes.whitelist.staked', return_value={
        "totalStaked": 500,
        "addresses": []
    })
    mocker.patch('api.v1.routes.whitelist.get_whitelist_event_by_event_id',
                 return_value=getEvent({"min_stake": 1000}))

    # act
    whitelist = Whitelist(
        event="staker-seed-paideia-202203wl",
        ergoAddress="test",
        email="test@test.com",
        name="test",
        sigValue=0,
        socialHandle="test",
        socialPlatform="test",
        chatHandle="test",
        chatPlatform="test",
    )
    ret = checkEventConstraints(1, whitelist, None)

    # assert
    assert ret[0] == False and ret[1] == 'Not enough ergopad staked for this address. Min stake required is 1000.'
