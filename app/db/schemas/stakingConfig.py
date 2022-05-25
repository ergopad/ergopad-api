from pydantic import BaseModel
import typing as t


class CreateAndUpdateStakingConfig(BaseModel):
    project: str
    title: str
    tokenId: str
    tokenDecimals: int
    stakingInfo: t.Optional[str]
    terms: t.Optional[str]
    # others
    additionalDetails: dict


class StakingConfig(CreateAndUpdateStakingConfig):
    id: int

    class Config:
        orm_mode = True
