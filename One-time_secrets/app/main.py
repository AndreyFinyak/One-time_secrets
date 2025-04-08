from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.database import SessionLocal, engine
from fastapi.responses import JSONResponse
import os

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/secret", response_model=dict)
def create_secret(secret: schemas.SecretCreate, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host
    return crud.create_secret(db=db, secret=secret, ip=ip)

@app.get("/secret/{secret_key}", response_model=dict)
def read_secret(secret_key: str, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host
    secret = crud.get_secret(db=db, secret_key=secret_key, ip=ip)
    if secret is None:
        raise HTTPException(status_code=404, detail="Secret not found")
    return secret

@app.delete("/secret/{secret_key}", response_model=dict)
def delete_secret(secret_key: str, request: Request, passphrase: str = None, db: Session = Depends(get_db)):
    ip = request.client.host
    result = crud.delete_secret(db=db, secret_key=secret_key, passphrase=passphrase, ip=ip)
    if result is None:
        raise HTTPException(status_code=404, detail="Secret not found or incorrect passphrase")
    return result

@app.middleware("http")
async def add_cache_control_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response
