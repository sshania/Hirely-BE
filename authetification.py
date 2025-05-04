from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field, validator
from passlib.context import CryptContext
from typing import Optional, Literal

from models import User, AcademicLevel
from database import get_db  # This should be your database session dependency

router = APIRouter()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# --------- Schemas ---------
class UserRegister(BaseModel):
    User_Name: str
    User_Password: str
    User_Email: EmailStr
    User_Phone_Number: str
    User_Gender: Literal["Male", "Female", "Other"] = Field(...)
    User_Description: str = None
    User_Work_Experience: int = 0
    User_Final_Academic: str
    User_Picture: str = None
    User_Major: str = None
    terms_accepted: bool

    @validator("terms_accepted")
    def must_accept_terms(cls, v):
        if not v:
            raise ValueError("You must accept the terms and services.")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    User_Password: str

# --------- Routes ---------
@router.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.User_Email == user.User_Email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = pwd_context.hash(user.User_Password)
    new_user = User(
        User_Name=user.User_Name,
        User_Password=hashed_password,
        User_Email=user.User_Email,
        User_Phone_Number=user.User_Phone_Number,
        User_Gender=user.User_Gender,
        User_Description=user.User_Description,
        User_Work_Experience=user.User_Work_Experience,
        User_Final_Academic=user.User_Final_Academic,
        User_Picture=user.User_Picture,
        User_Major=user.User_Major
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Registration successful", "user_id": new_user.User_id}


@router.post("/login")
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.User_Email == user_credentials.email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    if not pwd_context.verify(user_credentials.password, user.User_Password):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    return {"message": "Login successful", "user_id": user.User_id}
