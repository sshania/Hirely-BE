from fastapi import Depends, HTTPException, UploadFile
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
import cloudinary.uploader
import base64, uuid, io, re, traceback
from passlib.context import CryptContext
from email.mime.text import MIMEText
import os, smtplib


from models import User, Major, User_Skills
from database import get_db

SECRET_KEY = "fw67adas6123fda5d5asdca67lwuq10dica"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

cloudinary.config(
    cloud_name="dkrmoogyp",
    api_key="474674148359112",
    api_secret="CkaDWGcbzw0Cpop69-7gbA4f9yY",
    secure=True
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(user_id: int, expires_delta: timedelta = None):
    to_encode = {"user_id": user_id}
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
    
def create_reset_token(user_id: int, expires_delta: timedelta = timedelta(minutes=30)):
    to_encode = {
        "user_id": user_id,
        "scope": "password_reset",
        "exp": datetime.utcnow() + expires_delta
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_reset_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("scope") != "password_reset":
            return None
        return payload
    except JWTError:
        return None

def send_reset_email(to_email: str, token: str):
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.example.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER", "your-email@example.com")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "your-password")

    reset_link = f"https://your-app.com/reset-password?token={token}"
    subject = "Password Reset Request"
    body = f"""
You requested to reset your password.
Click the link below to reset it:

{reset_link}

If you didn't request this, please ignore this email.
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(msg["From"], [msg["To"]], msg.as_string())

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=402, detail="Token is invalid or has expired")

    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=403, detail="Invalid token payload: missing 'user_id'")

    user = db.query(User).filter(User.User_id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user

def apply_major_update(user: User, major_id: int, confirm_clear: bool, db: Session):
    new_major = db.query(Major).filter(Major.Major_Id == major_id).first()
    if not new_major:
        raise HTTPException(
            status_code=404,
            detail={"message": "Major not found", "code": "major_not_found"}
        )

    warning = None

    if user.User_Major != new_major.Major_Id:
        if not confirm_clear:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Changing your major will delete all your existing skills. Do you want to proceed?",
                    "code": "confirm_clear_required"
                }
            )
        
        # Delete skills only if they exist
        skill_count = db.query(User_Skills).filter(User_Skills.User_id == user.User_id).count()
        if skill_count > 0:
            db.query(User_Skills).filter(User_Skills.User_id == user.User_id).delete()
            warning = "All existing skills have been removed because you changed your major."

    user.User_Major = new_major.Major_Id
    return warning

def upload_image_to_cloudinary(file: UploadFile) -> str:
    try:
        print(f"Uploading file: {file.filename}")
        result = cloudinary.uploader.upload(file.file, public_id=f"images/{uuid.uuid4()}")
        print("Upload successful:", result['secure_url'])
        return result['secure_url']
    except Exception as e:
        traceback.print_exc()  # <== This prints the full traceback in your server terminal
        raise HTTPException(status_code=500, detail=f"Image upload failed: {repr(e)}")