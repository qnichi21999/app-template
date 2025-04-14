from fastapi import FastAPI
from .db import init_db

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/")
async def root():
    return {"message": "Application is running"}
