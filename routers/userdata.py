from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from typing_extensions import Literal
import cloudinary
import cloudinary.uploader

from models import User, AcademicLevel, Major, User_Skills
from database import get_db
from utils import get_current_user, apply_major_update, upload_image_to_cloudinary

router = APIRouter()

cloudinary.config(
    cloud_name="dkrmoogyp",
    api_key="474674148359112",
    api_secret="CkaDWGcbzw0Cpop69-7gbA4f9yY",
    secure=True
)

# --------- Schemas ---------
class MajorResponse(BaseModel):
    Major_Id: int
    Major_Name: str

    class Config:
        from_attributes = True

class MajorUpdateRequest(BaseModel):
    User_Major: int
    confirm_clear: Optional[bool] = False

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
    confirm_clear: Optional[bool] = False

# --------- Routes ---------
@router.get("/all-majors", response_model=List[MajorResponse])
def get_all_majors(db: Session = Depends(get_db)):
    return db.query(Major).order_by(Major.Major_Name).all()

@router.get("/user-major", response_model=MajorResponse)
def get_current_user_major(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.User_id == current_user.User_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user.major

@router.put("/update-user-major", response_model=dict)
def update_current_user_major(
    major_update: MajorUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.User_id == current_user.User_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    warning = apply_major_update(user, major_update.User_Major, major_update.confirm_clear, db)

    try:
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    return {
        "message": "Major updated successfully.",
        "major": {
            "Major_Id": user.User_Major,
            "Major_Name": db.query(Major).get(user.User_Major).Major_Name
        },
        "warning": warning
    }

@router.get("/all-data", response_model=UserResponse)
def get_user(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/update-all-data", response_model=UserResponse)
async def update_user_details(
    update_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Fetch user from DB
    user = db.query(User).filter(User.User_id == current_user.User_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_dict = update_data.dict(exclude_unset=True)

    # Handle major update separately
    if "User_Major" in update_dict:
        major_id = update_dict.pop("User_Major")
        confirm_clear = update_dict.pop("confirm_clear", False)  # get confirm_clear if present
        if major_id is not None:
            warning = apply_major_update(user, major_id, confirm_clear=confirm_clear, db=db)
            if warning:
                print("Warning:", warning)
        else:
            user.User_Major = None

    # Handle file upload if provided
    # if file is not None:
    #     update_dict["User_Picture"] = upload_image_to_cloudinary(file)

    # Apply other updates to user model
    for key, value in update_dict.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)

    return user