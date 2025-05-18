from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from typing_extensions import Literal

from models import User
from database import get_db
from utils import get_current_user, SECRET_KEY, ALGORITHM

router = APIRouter(
    prefix="/user",
    tags=["User"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

class UserUpdate(BaseModel):
    User_Name: Optional[str]
    User_Email: Optional[EmailStr]
    User_Phone_Number: Optional[str]
    User_Gender: Optional[Literal["Male", "Female", "Other"]]
    User_Description: Optional[str]
    User_Work_Experience: Optional[int]
    User_Final_Academic: Optional[str]
    User_Picture: Optional[str]
    User_Major: Optional[str]

@router.put("/update")
def update_user_details(update_data: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.User_id == current_user.User_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return {"message": "User details updated successfully", "user": update_data}