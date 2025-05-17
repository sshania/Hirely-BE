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
    User_Gender = Column(String(10))
    User_Description = Column(String(255))
    User_Work_Experience = Column(Integer)
    # User_Final_Academic  = Column(String(50)) # sd, smp, sma, d3, s1, s2, s3
    User_Final_Academic = Column(Enum(AcademicLevel), nullable=True)
    User_Picture = Column(String(255)) 
    User_Major = Column(String(255))

    skills = relationship("User_Skills", back_populates="user")
    job_history = relationship("Job_Matchmaking_History", back_populates="user")



class Company(Base):
    __tablename__ = "Company"

    Company_id = Column(Integer, primary_key=True, index=True)
    Company_Name = Column(String(100), unique=True, index=True)
    Company_Email = Column(String(50), nullable=False)
    Company_Phone_Number = Column(String(10), nullable=False)
    Company_Description = Column(String(255))
    Company_Location = Column(String(100))
    Company_Link = Column(String(100))

    job_history = relationship("Job_Matchmaking_History", back_populates="company")
    skill_requirements = relationship("Skill_Requirements", back_populates="company")

class User_Skills(Base):
    __tablename__ = "User_Skills"

    User_Skills_Id = Column(Integer, primary_key=True, index=True)
    User_id = Column(Integer, ForeignKey("User.User_id"))
    Skill_id = Column(Integer, ForeignKey("Skill.Skill_Id"))

    user = relationship("User", back_populates="skills")
    skill = relationship("Skill", back_populates="user_skills")

class Skill(Base):
    __tablename__ = "Skill"

    Skill_Id = Column(Integer, primary_key=True, index=True)  
    Skill_Name = Column(String(50), unique=True, index=True)
    Skill_Type = Column(String(50))

    Skill_Requirements = relationship("Skill_Requirements", back_populates="skills")
    user_skills = relationship("User_Skills", back_populates="skill")



class Skill_Requirements(Base):
    __tablename__ = "Skill_Requirements"

    Skill_Requirements_Id = Column(Integer, primary_key=True, index=True)
    Company_id = Column(Integer, ForeignKey("Company.Company_id"))
    Skill_id = Column(Integer, ForeignKey("Skill.Skill_Id"))

    company = relationship("Company", back_populates="skill_requirements")
    skill = relationship("Skill", back_populates="skill_requirements")


class Job_Matchmaking_History(Base):
    __tablename__ = "Job_Matchmaking_History"

    History_Id = Column(Integer, primary_key=True, index=True)
    User_id = Column(Integer, ForeignKey("User.User_id"), nullable=False)
    Company_id = Column(Integer, ForeignKey("Company.Company_id"), nullable=False)
    Score = Column(Float)

    user = relationship("User", back_populates="job_history")
    company = relationship("Company", back_populates="job_history")
