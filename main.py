from fastapi import FastAPI
from routers.authetification import router as authentification_router
from routers.userdata import router as user_router
from routers.userskills import router as user_skill_router
from routers.results import router as results_router
from middleware import log_requests

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Hirely API")
app.include_router(authentification_router, prefix="/auth")

app.middleware("https")(log_requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello Guys. Ini API Hirely"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "query": q}

app.include_router(authentification_router, prefix="/auth", tags=["Authentication"])
app.include_router(user_router, prefix="/user", tags=["User"])
app.include_router(user_skill_router, prefix="/skill", tags=["Skill"])
app.include_router(results_router, prefix="/result", tags=["Results"])