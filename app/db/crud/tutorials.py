from fastapi import status
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session
import typing as t

from db.models import tutorials as models
from db.schemas import tutorials as schemas


#############################################
### CRUD OPERATIONS FOR TUTORIALS SECTION ###
#############################################

def get_tutorial(db: Session, id: int):
    return db.query(models.Tutorial).filter(
        models.Tutorial.id == id).first()


def get_tutorials(
    db: Session, category: str, skip: int = 0, limit: int = 100
) -> t.List[schemas.Tutorial]:
    if category == 'all':
        return db.query(models.Tutorial).order_by(models.Tutorial.id).offset(skip).limit(limit).all()
    else:
        return db.query(models.Tutorial).filter(
            models.Tutorial.category == category).order_by(models.Tutorial.id).offset(skip).limit(limit).all()


def get_unique_categories(db: Session, skip: int = 0, limit: int = 100) -> t.List[str]:
    tutorials = get_tutorials(db, 'all', skip, limit)
    categories = list(set(map(lambda tutorial: tutorial.category, tutorials)))
    return categories


def create_tutorial(db: Session, tutorial: schemas.CreateAndUpdateTutorial):
    db_tutorial = models.Tutorial(
        title=tutorial.title,
        shortDescription=tutorial.shortDescription,
        description=tutorial.description,
        link=tutorial.link,
        linkType=tutorial.linkType,
        bannerImgUrl=tutorial.bannerImgUrl,
        category=tutorial.category,
        config=tutorial.config
    )
    db.add(db_tutorial)
    db.commit()
    db.refresh(db_tutorial)
    return db_tutorial


def delete_tutorial(db: Session, id: int):
    tutorial = get_tutorial(db, id)
    if not tutorial:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="tutorial not found.")
    db.delete(tutorial)
    db.commit()
    return tutorial


def edit_tutorial(
    db: Session, id: int, tutorial: schemas.CreateAndUpdateTutorial
) -> schemas.Tutorial:
    db_tutorial = get_tutorial(db, id)
    if not db_tutorial:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="tutorial not found.")

    update_data = tutorial.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_tutorial, key, value)

    db.add(db_tutorial)
    db.commit()
    db.refresh(db_tutorial)
    return db_tutorial
