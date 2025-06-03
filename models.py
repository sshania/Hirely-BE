from sqlalchemy import (CheckConstraint, Column, Integer, String, Boolean, ForeignKey, Float, Text, Enum, Date, TIMESTAMP, DECIMAL, DateTime, BigInteger)
from sqlalchemy.orm import relationship, declarative_base

from database import Base
from enum import Enum as PyEnum


class AcademicLevel(PyEnum):
    SD = "sd"
    SMP = "smp"
    SMA = "sma"
    D3 = "d3"
    S1 = "s1"
    S2 = "s2"
    S3 = "s3"

class User(Base):
    __tablename__ = "User"

    User_id = Column(Integer, primary_key=True, index=True)
    User_Name = Column(String(100), unique=True, index=True)
    User_Password = Column(String(100), nullable=False)
    User_Email = Column(String(50), nullable=False)
    User_Phone_Number = Column(String(10), nullable=False)
    User_Gender = Column(String(10), nullable=True)
    User_Description = Column(String(255), nullable=True)
    User_Work_Experience = Column(Integer, nullable=True)
    # User_Final_Academic  = Column(String(50)) # sd, smp, sma, d3, s1, s2, s3
    User_Final_Academic = Column(Enum(AcademicLevel), nullable=True)
    User_Picture = Column(String(255), nullable=True) 
    User_Major = Column(Integer, ForeignKey("Major.Major_Id"), nullable=True)
    
    major = relationship("Major", back_populates="users")
    user_skills = relationship("User_Skills", back_populates="user")
    job_matches = relationship("JobMatchResult", back_populates="user", cascade="all, delete-orphan")

class Major(Base):
    __tablename__ = "Major"

    Major_Id = Column(Integer, primary_key=True, index=True)
    Major_Name = Column(String(255), unique=True, nullable=False)

    users = relationship("User", back_populates="major")

class Company(Base):
    __tablename__ = "Company"

    Company_id = Column(Integer, primary_key=True, index=True)
    Company_Name = Column(String(100), unique=True, index=True)
    Company_Email = Column(String(50), nullable=False)
    Company_Phone_Number = Column(String(10), nullable=False)
    Company_Description = Column(String(255))
    Company_Location = Column(String(100))
    Company_Link = Column(String(100))

    skill_requirements = relationship("Skill_Requirements", back_populates="company")

class User_Skills(Base):
    __tablename__ = "User_Skills"

    User_Skills_Id = Column(Integer, primary_key=True, index=True)
    User_id = Column(Integer, ForeignKey("User.User_id"))
    Skill_id = Column(Integer, ForeignKey("Skill.Skill_Id"))

    user = relationship("User", back_populates="user_skills")
    skill = relationship("Skill", back_populates="user_skills")

class Skill(Base):
    __tablename__ = "Skill"

    Skill_Id = Column(Integer, primary_key=True, index=True)
    Skill_Name = Column(String(50), unique=True, index=True)
    Skill_Type = Column(String(50))

    user_skills = relationship("User_Skills", back_populates="skill")
    skill_requirements = relationship("Skill_Requirements", back_populates="skill")



class Skill_Requirements(Base):
    __tablename__ = "Skill_Requirements"

    Skill_Requirements_Id = Column(Integer, primary_key=True, index=True)
    Company_id = Column(Integer, ForeignKey("Company.Company_id"))
    Skill_id = Column(Integer, ForeignKey("Skill.Skill_Id"))

    company = relationship("Company", back_populates="skill_requirements")
    skill = relationship("Skill", back_populates="skill_requirements")


class JobMatchResult(Base):
    __tablename__ = "job_match_results"

    result_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("User.User_id"), nullable=False)
    job_title = Column(String(50))
    company = Column(String(50))
    url = Column(String(255))

    user = relationship("User", back_populates="job_matches")

class PasswordReset(Base):
    __tablename__ = "password_reset"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), nullable=False)
    token = Column(String(5), nullable=False)
    created_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)