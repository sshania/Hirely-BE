from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from typing_extensions import Literal

from models import User, AcademicLevel, Major
from database import get_db
from utils import get_current_user

router = APIRouter()


# --------- Schemas ---------
class MajorResponse(BaseModel):
    Major_Id: int
    Major_Name: str

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    User_id: int
    User_Name: str
    User_Email: str
    User_Phone_Number: str
    User_Gender: Optional[str] = None
    User_Description: Optional[str] = None
    User_Work_Experience: Optional[int] = None
    User_Final_Academic: Optional[AcademicLevel] = None
    User_Picture: Optional[str] = None

    User_Major: Optional[MajorResponse] = Field(default=None, alias="major")

    class Config:
        from_attributes = True
        populate_by_name = True

class UserUpdate(BaseModel):
    User_Name: Optional[str]
    User_Email: Optional[EmailStr]
    User_Phone_Number: Optional[str]
    User_Gender: Optional[Literal["Male", "Female", "Other"]]
    User_Description: Optional[str]
    User_Work_Experience: Optional[int]
    User_Final_Academic: Optional[AcademicLevel] = None
    User_Picture: Optional[str]
    User_Major: Optional[int] = None


# --------- Routes ---------
@router.get("/majors", response_model=List[MajorResponse])
def get_all_majors(db: Session = Depends(get_db)):
    return db.query(Major).order_by(Major.Major_Name).all()

@router.get("/data", response_model=UserResponse)
def get_user(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/update", response_model=UserResponse)
def update_user_details(
    update_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.User_id == current_user.User_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_dict = update_data.dict(exclude_unset=True)

    if "User_Major" in update_dict:
        major_id = update_dict["User_Major"]
        if major_id is not None:
            major = db.query(Major).filter(Major.Major_Id == major_id).first()
            if not major:
                raise HTTPException(status_code=404, detail="Major not found")
            update_dict["User_Major"] = major.Major_Id
        else:
            update_dict["User_Major"] = None

    for key, value in update_dict.items():
        setattr(user, key, value)


    db.commit()
    db.refresh(user)

    return user