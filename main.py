import json
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

import models, schemas, database
from database import engine, get_db
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Security Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "DOCTOR_PORTAL_DEVELOPMENT_KEY_DO_NOT_USE_IN_PROD")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 480))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Initialize DB
models.Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_initial_doctor()
    yield

app = FastAPI(
    title="HealthTrack MD", 
    description="Secure Clinical Portal for Doctors",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Static Files & Frontend ---
@app.get("/")
async def read_index():
    return FileResponse("index.html")

@app.get("/login")
async def read_login():
    return FileResponse("login.html")

@app.get("/register")
async def read_register():
    return FileResponse("register.html")

# --- Auth Utilities ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

# --- Startup & Migration ---
def seed_initial_doctor():
    db = database.SessionLocal()
    try:
        if db.query(models.User).count() == 0:
            print("Creating default doctor account: doctor / password123")
            hashed_pwd = get_password_hash("password123")
            db_user = models.User(username="doctor", hashed_password=hashed_pwd)
            db.add(db_user)
            db.commit()
    finally:
        db.close()

# --- Auth Endpoints ---

@app.post("/token", response_model=schemas.Token, tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/register", response_model=schemas.UserResponse, tags=["Authentication"])
async def register_doctor(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user_in.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_pwd = get_password_hash(user_in.password)
    new_user = models.User(username=user_in.username, hashed_password=hashed_pwd)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# --- Patient Endpoints (Protected) ---

@app.get("/patients", response_model=List[schemas.PatientResponse], tags=["Patients"])
def read_patients(
    skip: int = 0, 
    limit: int = 100, 
    sort_by: str = Query(None, pattern="^(height|weight|bmi|age)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Patient).filter(models.Patient.doctor_id == current_user.id)
    if sort_by:
        column = getattr(models.Patient, sort_by)
        query = query.order_by(column.desc() if order == "desc" else column.asc())
    return query.offset(skip).limit(limit).all()

@app.get("/patients/{patient_id}", response_model=schemas.PatientResponse, tags=["Patients"])
def read_patient(patient_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id, 
        models.Patient.doctor_id == current_user.id
    ).first()
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return db_patient

@app.post("/patients", response_model=schemas.PatientResponse, status_code=status.HTTP_201_CREATED, tags=["Patients"])
def create_patient(patient: schemas.PatientCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_patient = db.query(models.Patient).filter(models.Patient.id == patient.id).first()
    if db_patient:
        raise HTTPException(status_code=400, detail="Patient ID already registered")
    
    bmi = schemas.PatientResponse.calculate_bmi(patient.weight, patient.height)
    verdict = schemas.PatientResponse.get_verdict(bmi)
    
    new_patient = models.Patient(
        **patient.model_dump(),
        doctor_id=current_user.id,
        bmi=bmi,
        verdict=verdict
    )
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    return new_patient

@app.patch("/patients/{patient_id}", response_model=schemas.PatientResponse, tags=["Patients"])
def update_patient(
    patient_id: str, 
    patient_update: schemas.PatientUpdate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    db_patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.doctor_id == current_user.id
    ).first()
    if not db_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    update_data = patient_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_patient, key, value)
    
    if "weight" in update_data or "height" in update_data:
        db_patient.bmi = schemas.PatientResponse.calculate_bmi(db_patient.weight, db_patient.height)
        db_patient.verdict = schemas.PatientResponse.get_verdict(db_patient.bmi)
        
    db.commit()
    db.refresh(db_patient)
    return db_patient

@app.delete("/patients/{patient_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Patients"])
def delete_patient(patient_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.doctor_id == current_user.id
    ).first()
    if not db_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    db.delete(db_patient)
    db.commit()
    return None

# Mount current directory to serve app.js, style.css, etc. 
# This must be at the end to avoid shadowing API routes.
app.mount("/", StaticFiles(directory=".", html=True), name="static")
