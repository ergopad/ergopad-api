import json
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import typing as t

from db.models import projects as models
from db.schemas import projects as schemas

####################################
### CRUD OPERATIONS FOR PROJECTS ###
####################################


def get_projects(
    db: Session, include_drafts: bool, skip: int = 0, limit: int = 100
) -> t.List[schemas.Project]:
    if include_drafts:
        return db.query(models.Project).offset(skip).limit(limit).all()
    return db.query(models.Project).filter(
        models.Project.isDraft == False
    ).offset(skip).limit(limit).all()


def generate_project_slug(title: str) -> str:
    # Project Title -> (projecttitle, project_title)
    title = ''.join(
        list(filter(lambda c: c.isalnum() or c == ' ', list(title.lower()))))
    return (''.join(title.split()), '_'.join(title.split()))


def get_project(db: Session, id: str):
    project = None
    id = str(id)
    if (id.isdecimal()):
        # get project by project id
        project = db.query(models.Project).filter(
            models.Project.id == int(id)).first()
    else:
        # get project by project slug
        projects = list(filter(lambda project: id in generate_project_slug(project.name),
                        db.query(models.Project).all()))
        if len(projects):
            project = projects[0]
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="project not found")
    return project


def create_project(db: Session, project: schemas.CreateAndUpdateProject):
    db_project = models.Project(
        name=project.name,
        shortDescription=project.shortDescription,
        description=project.description,
        fundsRaised=project.fundsRaised,
        bannerImgUrl=project.bannerImgUrl,
        isLaunched=project.isLaunched,
        socials=project.socials.dict(),
        roadmap=project.roadmap.dict(),
        team=project.team.dict(),
        tokenomics=project.tokenomics.dict(),
        isDraft=project.isDraft
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def delete_project(db: Session, id: int):
    project = get_project(db, id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            detail="project not found")
    db.delete(project)
    db.commit()
    return project


def edit_project(
    db: Session, id: int, project: schemas.CreateAndUpdateProject
):
    db_project = get_project(db, id)
    if not db_project:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            detail="project not found")

    update_data = project.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_project, key, value)

    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    return db_project
