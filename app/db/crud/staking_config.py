from fastapi import status
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from db.models import stakingConfig as model
from db.schemas import stakingConfig as schema

##########################################
### CRUD OPERATIONS FOR STAKING CONFIG ###
##########################################


def get_staking_config_by_name(db: Session, project: str):
    staking_config = (
        db.query(model.StakingConfig)
        .filter(model.StakingConfig.project == project)
        .first()
    )
    if not staking_config:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content=f"Config not found"
        )
    return staking_config


def get_staking_config(db: Session, id: int):
    staking_config = (
        db.query(model.StakingConfig).filter(model.StakingConfig.id == id).first()
    )
    if not staking_config:
        return None
    return staking_config


def get_all_staking_config(db: Session, skip: int = 0, limit: int = 100):
    return db.query(model.StakingConfig).offset(skip).limit(limit).all()


def create_staking_config(
    db: Session, staking_config: schema.CreateAndUpdateStakingConfig
):
    db_staking_config = model.StakingConfig(
        project=staking_config.project,
        title=staking_config.title,
        tokenId=staking_config.tokenId,
        tokenDecimals=staking_config.tokenDecimals,
        stakingInfo=staking_config.stakingInfo,
        terms=staking_config.terms,
        additionalDetails=staking_config.additionalDetails,
    )
    db.add(db_staking_config)
    db.commit()
    db.refresh(db_staking_config)
    # return
    return db_staking_config


def delete_staking_config(db: Session, id: int):
    ret = get_staking_config(db, id)
    if not ret:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content=f"Config not found"
        )
    db.delete(ret)
    db.commit()
    return ret


def edit_staking_config(
    db: Session, id: int, staking_config: schema.CreateAndUpdateStakingConfig
):
    db_staking_config = get_staking_config(db, id)
    if not db_staking_config:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content=f"Config not found"
        )

    update_data = staking_config.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_staking_config, key, value)

    db.add(db_staking_config)
    db.commit()
    db.refresh(db_staking_config)

    return db_staking_config
