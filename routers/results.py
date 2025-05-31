import socket
import gradio_client
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from gradio_client import Client

from models import User, User_Skills, Skill, Major
from database import get_db
from utils import get_current_user

router = APIRouter()
url = "https://hf.space/embed/ShaniaS/HirelyJobMatchmaking/api/predict/"
socket.setdefaulttimeout(600000)

class JobMatch(BaseModel):
    Job_Title: str
    Company: str
    Category: Optional[str] = None
    Snippet: Optional[str] = None
    Apply_Now: Optional[HttpUrl] = None


@router.post("/match-result", response_model=List[JobMatch])
def get_match_result(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    major = db.query(Major).filter(Major.Major_Id == current_user.User_Major).first()
    if not major:
        raise HTTPException(status_code=404, detail="Major not found")

    user_skills = (
        db.query(Skill.Skill_Name)
        .join(User_Skills, Skill.Skill_Id == User_Skills.Skill_id)
        .filter(User_Skills.User_id == current_user.User_id)
        .all()
    )
    skill_names = [skill.Skill_Name for skill in user_skills]

    try:
        client = Client("ShaniaS/HirelyJobMatchmaking")
        result = client.predict(
            major=major.Major_Name,
            skills=" ".join(skill_names),
            api_name="/predict"
        )

        if not result or 'results' not in result:
            raise HTTPException(status_code=500, detail="Invalid response from AI model")

        job_matches = [
            JobMatch(
                Job_Title=job['title'],
                Company=job['company'],
                Category=job['category'],
                Snippet=job['snippet'],
                Apply_Now=job['url']
            )
            for job in result['results']
        ]
        return job_matches

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with AI model: {str(e)}")