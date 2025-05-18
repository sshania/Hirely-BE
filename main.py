from fastapi import FastAPI
from authetification import router as authentification_router
from updateuserdata import router as user_router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Hirely API")
app.include_router(authentification_router, prefix="/auth")

@app.get("/")
def read_root():
    return {"message": "Hello Guys. Ini API Hirely"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "query": q}

app.include_router(authentification_router, prefix="/auth", tags=["Authentication"])
app.include_router(user_router, prefix="/user", tags=["User"])