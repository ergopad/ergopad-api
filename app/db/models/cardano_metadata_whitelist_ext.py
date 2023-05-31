from sqlalchemy import Column, Integer, Boolean, JSON

from db.session import Base

class CardanoMetadataWhitelistExt(Base):
    __tablename__ = "cardano_metadata_whitelist_ext"

    id = Column(Integer, primary_key=True)
    kyc_approval = Column(Boolean)
    ada_address_list = Column(JSON)
