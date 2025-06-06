from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional, Literal

from models import User, AcademicLevel, Major
from database import get_db
from utils import create_access_token, create_reset_token, verify_reset_token, send_reset_email, verify_password, get_password_hash

router = APIRouter()

# --------- Schemas ---------
class UserRegister(BaseModel):
    User_Name: str
    User_Password: str
    confirm_password: str
    User_Email: EmailStr
    User_Phone_Number: str
    User_Gender: Optional[Literal["Male", "Female", "Other"]] = None
    User_Description: Optional[str] = None
    User_Work_Experience: Optional[int] = 0
    User_Final_Academic: Optional[AcademicLevel] = None
    User_Picture: Optional[str] = None
    Major_id: Optional[int] = None
    terms_accepted: bool

    @field_validator("User_Password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return v

    @field_validator("terms_accepted")
    @classmethod
    def must_accept_terms(cls, v):
        if not v:
            raise ValueError("You must accept the terms and services.")
        return v
    
    @model_validator(mode="after")
    def passwords_match(self):
        if self.User_Password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self

class UserLogin(BaseModel):
    email: EmailStr
    User_Password: str

class ResetPasswordConfirmRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return v

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


# --------- Routes ---------
@router.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(
    (User.User_Email == user.User_Email) |
    (User.User_Name == user.User_Name)
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email or username already registered")

    if user.Major_id:
        major = db.query(Major).filter(Major.Major_Id == user.Major_id).first()
        if not major:
            raise HTTPException(status_code=404, detail="Major not found")

    hashed_password = get_password_hash(user.User_Password)

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
        User_Major=user.Major_id
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "Registration successful",
        "user_id": new_user.User_id
    }

@router.post("/login")
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.User_Email == user_credentials.email).first()
    if not user or not verify_password(user_credentials.User_Password, user.User_Password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user_id=user.User_id)
    return {
        "access_token": token,
        "token_type": "bearer"
    }

@router.post("/request-password-reset")
def request_password_reset(
    email: EmailStr,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.User_Email == email).first()
    if not user:
        return {"message": "If the email is registered, a reset link will be sent."}

    reset_token = create_reset_token(user.User_id)
    background_tasks.add_task(send_reset_email, user.User_Email, reset_token)

    return {"message": "If the email is registered, a reset link will be sent."}

@router.post("/reset-password")
def reset_password_confirm(
    request: ResetPasswordConfirmRequest,
    db: Session = Depends(get_db)
):
    payload = verify_reset_token(request.token)
    if not payload:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=400, detail="Invalid token payload")

    user = db.query(User).filter(User.User_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.User_Password = get_password_hash(request.new_password)
    db.commit()
    db.refresh(user)

    return {"message": "Password has been reset successfully."}