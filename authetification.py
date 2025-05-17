from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field, validator
from passlib.context import CryptContext
from typing import Optional, Literal
from jose import JWTError, jwt
from datetime import datetime, timedelta

from models import User, AcademicLevel
from database import get_db

router = APIRouter()

SECRET_KEY = "fw67adas6123fda5d5asdca67lwuq10dica"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

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

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_id = payload.get("sub")
    return db.query(User).filter(User.User_id == int(user_id)).first()

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
    if not user or not pwd_context.verify(user_credentials.User_Password, user.User_Password):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    token = create_access_token(data={"sub": str(user.User_id)})
    return {"access_token": token, "token_type": "bearer"}
