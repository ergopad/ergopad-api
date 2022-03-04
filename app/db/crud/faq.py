from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import typing as t

from db.models import faq as models
from db.schemas import faq as schemas


#########################################
### CRUD OPERATIONS FOR FAQ SECTION ###
#########################################

def get_faq(db: Session, id: int):
    faq = db.query(models.Faq).filter(models.Faq.id == id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    return faq


def get_faqs(
    db: Session, tag: str, skip: int = 0, limit: int = 100
) -> t.List[schemas.Faq]:
    if tag == 'all':
        return db.query(models.Faq).offset(skip).limit(limit).all()
    else:
        return db.query(models.Faq).filter(models.Faq.tag == tag).offset(skip).limit(limit).all()


def create_faq(db: Session, faq: schemas.CreateAndUpdateFaq):
    db_faq = models.Faq(
        question=faq.question,
        solution=faq.solution,
        tag=faq.tag,
    )
    db.add(db_faq)
    db.commit()
    db.refresh(db_faq)
    return db_faq


def delete_faq(db: Session, id: int):
    faq = get_faq(db, id)
    if not faq:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            detail="FAQ not found")
    db.delete(faq)
    db.commit()
    return faq


def edit_faq(
    db: Session, id: int, faq: schemas.CreateAndUpdateFaq
) -> schemas.Faq:
    db_faq = get_faq(db, id)
    if not db_faq:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            detail="FAQ not found")

    update_data = faq.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_faq, key, value)

    db.add(db_faq)
    db.commit()
    db.refresh(db_faq)
    return db_faq
