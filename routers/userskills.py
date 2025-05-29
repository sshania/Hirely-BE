from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from models import User_Skills, Skill, User
from database import get_db
from utils import get_current_user

router = APIRouter()


# --------- Schemas ---------
class SkillResponse(BaseModel):
    Skill_Id: int
    Skill_Name: str
    Skill_Type: str

    class Config:
        from_attributes = True

class AddUserSkills(BaseModel):
    Skill_ids: List[int]

    class Config:
        from_attributes = True


# --------- Routes ---------
@router.get("/list", response_model=List[SkillResponse])
def get_all_skills(search: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Skill)
    if search:
        query = query.filter(Skill.Skill_Name.ilike(f"%{search}%"))
    return query.order_by(Skill.Skill_Name).all()

@router.post("/add-user")
def add_user_skills(skill_data: AddUserSkills, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    added_skills = []
    already_have = []
    not_found = []

    for skill_id in skill_data.Skill_ids:
        skill = db.query(Skill).filter(Skill.Skill_Id == skill_id).first()
        if not skill:
            not_found.append({"Skill_Id": skill_id, "reason": "Skill not found"})
            continue

        existing = db.query(User_Skills).filter_by(User_id=current_user.User_id, Skill_id=skill_id).first()
        if existing:
            already_have.append({"Skill_Id": skill_id, "reason": "Skill already added"})
            continue

        user_skill = User_Skills(User_id=current_user.User_id, Skill_id=skill_id)
        db.add(user_skill)
        added_skills.append(skill_id)

    db.commit()

    return {
        "message": "Skill processing completed",
        "added_skills": added_skills,
        "already_have": already_have,
        "not_found": not_found
    }