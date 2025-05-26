from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import User_Skills, Skill, User
from database import get_db
from utils import get_current_user
from pydantic import BaseModel

router = APIRouter()

class AddUserSkill(BaseModel):
    User_id: int
    Skill_id: int

    class Config:
        from_attributes = True

@router.post("/skill")
def add_user_skill(skill_data: AddUserSkill, db: Session = Depends(get_db)):
    skill = db.query(Skill).filter(Skill.Skill_Id == skill_data.Skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    user = db.query(User).filter(User.User_id == skill_data.User_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = db.query(User_Skills).filter_by(User_id=skill_data.User_id, Skill_id=skill_data.Skill_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already has this skill")

    user_skill = User_Skills(User_id=skill_data.User_id, Skill_id=skill_data.Skill_id)
    db.add(user_skill)
    db.commit()
    db.refresh(user_skill)
    return {"message": "Skill added successfully"}