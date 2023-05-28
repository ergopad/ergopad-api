from sqlalchemy.orm import Session

from db.models import cardano_metadata_whitelist_ext as models
from db.schemas import cardano_metadata_whitelist_ext as schemas


def get_metadata(db: Session, id: int):
    db_metadata = db.query(models.CardanoMetadataWhitelistExt).filter(models.CardanoMetadataWhitelistExt.id == id).first()
    if not db_metadata:
        return None
    return schemas.CardanoMetadataWhitelistExt(
        id=db_metadata.id,
        kycApproval=db_metadata.kyc_approval,
        adaAddresses=db_metadata.ada_address_list
    )


def create_metadata(db: Session, metadata: schemas.CardanoMetadataWhitelistExt):
    db_metadata = models.CardanoMetadataWhitelistExt(
        ada_address_list=metadata.adaAddresses,
        kyc_approval=metadata.kycApproval
    )
    db.add(db_metadata)
    db.commit()
    db.refresh(db_metadata)
    return db_metadata


def edit_mt(
    db: Session, id: int, mt: schemas.CreateOrUpdateCardanoMetadataWhitelistExt
) -> schemas.CardanoMetadataWhitelistExt:
    db_metadata = db.query(models.CardanoMetadataWhitelistExt).filter(models.CardanoMetadataWhitelistExt.id == id).first()
    if not db_metadata:
        return None

    update_data = mt.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_metadata, key, value)

    db.add(db_metadata)
    db.commit()
    db.refresh(db_metadata)
    return get_metadata(id)
