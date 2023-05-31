from pydantic import BaseModel
import typing as t


class CreateOrUpdateCardanoMetadataWhitelistExt(BaseModel):
    adaAddresses: t.List[str]
    kycApproval: bool


class CardanoMetadataWhitelistExt(CreateOrUpdateCardanoMetadataWhitelistExt):
    id: int

    class Config:
        orm_mode = True
