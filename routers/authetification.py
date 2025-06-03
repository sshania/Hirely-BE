from fastapi import APIRouter, Depends, HTTPException,Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from passlib.context import CryptContext
from typing import Optional, Literal
import secrets
from datetime import datetime, timedelta
import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from models import User, AcademicLevel, Major, PasswordReset
from database import get_db
from utils import create_access_token

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

class ResetPasswordRequest(BaseModel):
    email: EmailStr
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




@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.User_Email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.User_Password = get_password_hash(request.new_password)
    db.commit()
    db.refresh(user)

    return {"message": "Password has been reset successfully."}

class ForgotPasswordRequest(BaseModel):
    email: str


@router.post('/forgot-password')
def forgot_password(request: Request, forgot_data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    # **TIDAK CEK DOMAIN EMAIL**
    user = db.query(User).filter(User.User_Email == forgot_data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email tidak ditemukan!")

    # Generate token angka 5 digit
    reset_token = ''.join([str(secrets.randbelow(10)) for _ in range(5)])

    # Insert ke table password_reset
    now = datetime.utcnow()
    expires_at = now + timedelta(minutes=15)
    reset = PasswordReset(
        email=forgot_data.email,
        token=reset_token,
        created_at=now,
        expires_at=expires_at
    )
    db.add(reset)
    db.commit()

    # Kirim email
    send_reset_email_hirely(forgot_data.email, reset_token)

    return {"message": "Cek email untuk reset password."}


def send_reset_email_hirely(email, token):
    sender_email = "admin@hirely.my.id"
    sender_password = "g+6L+I6hJg5N"
    smtp_server = "mail.hirely.my.id"  # Ganti dengan server SMTP Hirely kamu jika beda
    smtp_port = 465

    message = MIMEMultipart('alternative')
    message['Subject'] = "Reset Password - Hirely"
    message['From'] = sender_email
    message['To'] = email
    message['X-Priority'] = '1'

    html = f"""
    <html>
      <body>
        <h2>Hirely Password Reset</h2>
        <p>Anda melakukan permintaan reset password pada akun Hirely Anda.</p>
        <p>Kode reset password Anda adalah: <strong>{token}</strong></p>
        <p>Jangan berikan kode ini kepada siapa pun. Jika Anda tidak meminta reset password, abaikan email ini.</p>
        <br>
        <p>Salam,</p>
        <p>Tim Hirely</p>
      </body>
    </html>
    """

    part = MIMEText(html, 'html')
    message.attach(part)

    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.login(sender_email, sender_password)
            server.send_message(message)
            print(f"Reset password email sent successfully to {email}")

    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send reset email: {str(e)}"
        )

class VerifyTokenRequest(BaseModel):
    email: EmailStr
    token: str

@router.post('/verify-token')
def verify_token(request: Request, verify_data: VerifyTokenRequest, db: Session = Depends(get_db)):
    # Query token yang valid
    reset_data = db.query(PasswordReset).filter(
        PasswordReset.email == verify_data.email,
        PasswordReset.token == verify_data.token
    ).order_by(PasswordReset.created_at.desc()).first()

    if not reset_data:
        return {"message": "Token tidak valid atau email tidak cocok!", "status": False}

    if datetime.utcnow() > reset_data.expires_at:
        return {"message": "Token sudah kadaluarsa!", "status": False}

    return {"message": "Token valid, lanjutkan reset password.", "status": True}


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    token: str
    new_password: str
    confirm_password: str

@router.post('/reset-password')
def reset_password(request: Request, reset_data: ResetPasswordRequest, db: Session = Depends(get_db)):
    # 1. Validasi password match
    if reset_data.new_password != reset_data.confirm_password:
        raise HTTPException(status_code=400, detail="Password baru dan konfirmasi tidak cocok!")

    # 2. Validasi token (email + token) dan cek expired
    reset_record = db.query(PasswordReset).filter(
        PasswordReset.email == reset_data.email,
        PasswordReset.token == reset_data.token
    ).order_by(PasswordReset.created_at.desc()).first()

    if not reset_record:
        raise HTTPException(status_code=400, detail="Token reset tidak valid!")

    if datetime.utcnow() > reset_record.expires_at:
        raise HTTPException(status_code=400, detail="Token reset sudah kadaluarsa!")

    # 3. Validasi user
    user = db.query(User).filter(User.User_Email == reset_data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email tidak ditemukan di sistem!")

    # 4. Update password
    hashed_password = pwd_context.hash(reset_data.new_password).strip()
    user.User_Password = hashed_password
    db.commit()
    db.refresh(user)

    # 5. Hapus token setelah reset
    db.query(PasswordReset).filter(PasswordReset.email == reset_data.email).delete()
    db.commit()

    return {"message": "Password berhasil diperbarui!", "status": True}