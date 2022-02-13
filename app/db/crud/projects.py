import json
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import typing as t

from db.models import projects as models
from db.schemas import projects as schemas

####################################
### CRUD OPERATIONS FOR PROJECTS ###
####################################


def social_compatible_project(project):
    try:
        project.socials = schemas.Socials.parse_obj(
            json.loads(project.socials))
    except:
        # make backward compatible with older data
        project.socials = schemas.Socials(telegram=project.socials)
    return project


def get_projects(
    db: Session, skip: int = 0, limit: int = 100
) -> t.List[schemas.Project]:
    data = db.query(models.Project).offset(skip).limit(limit).all()
    return [social_compatible_project(project) for project in data]


def get_project(db: Session, id: int, model="out"):
    project = db.query(models.Project).filter(models.Project.id == id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="project not found")
    if model == "db":
        return project
    else:
        return social_compatible_project(project)


def get_project_team(db: Session, projectId: int, skip: int = 0, limit: int = 100) -> t.List[schemas.ProjectTeamMember]:
    return db.query(models.ProjectTeam).filter(models.ProjectTeam.projectId == projectId).all()


def create_project(db: Session, project: schemas.CreateAndUpdateProjectWithTeam):
    db_project = models.Project(
        name=project.name,
        shortDescription=project.shortDescription,
        description=project.description,
        fundsRaised=project.fundsRaised,
        socials=str(project.socials.json()),
        bannerImgUrl=project.bannerImgUrl,
        isLaunched=project.isLaunched,
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    if (project.team):
        set_project_team(db, db_project.id, project.team)
    return schemas.ProjectWithTeam(
        id=db_project.id,
        name=db_project.name,
        shortDescription=db_project.shortDescription,
        description=db_project.description,
        fundsRaised=db_project.fundsRaised,
        socials=schemas.Socials.parse_obj(json.loads(db_project.socials)),
        bannerImgUrl=db_project.bannerImgUrl,
        isLaunched=db_project.isLaunched,
        team=get_project_team(db, db_project.id)
    )


def set_project_team(db: Session, projectId: int, teamMembers: t.List[schemas.CreateAndUpdateProjectTeamMember]):
    db_teamMembers = list(map(lambda teamMember: models.ProjectTeam(
        name=teamMember.name, description=teamMember.description, profileImgUrl=teamMember.profileImgUrl, projectId=projectId), teamMembers))
    delete_project_team(db, projectId)
    db.add_all([member for member in db_teamMembers])
    db.commit()
    return get_project_team(db, projectId)


def delete_project(db: Session, id: int):
    project = get_project(db, id, model="db")
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            detail="project not found")
    delete_project_team(db, id)
    db.delete(project)
    db.commit()
    return social_compatible_project(project)


def delete_project_team(db: Session, projectId: int):
    ret = get_project_team(db, projectId)
    db.query(models.ProjectTeam).filter(models.ProjectTeam.projectId ==
                                        projectId).delete(synchronize_session=False)
    db.commit()
    return ret


def edit_project(
    db: Session, id: int, project: schemas.CreateAndUpdateProjectWithTeam
):
    db_project = get_project(db, id, model="db")
    if not db_project:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            detail="project not found")

    update_data = project.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key == "socials":
            setattr(db_project, key, str(project.socials.json()))
        else:
            setattr(db_project, key, value)

    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    if (project.team != None):
        set_project_team(db, db_project.id, project.team)

    return schemas.ProjectWithTeam(
        id=db_project.id,
        name=db_project.name,
        shortDescription=db_project.shortDescription,
        description=db_project.description,
        fundsRaised=db_project.fundsRaised,
        socials=schemas.Socials.parse_obj(json.loads(db_project.socials)),
        bannerImgUrl=db_project.bannerImgUrl,
        isLaunched=db_project.isLaunched,
        team=get_project_team(db, db_project.id)
    )
