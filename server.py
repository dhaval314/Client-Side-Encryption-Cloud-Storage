import sqlite3
import os
import uuid
from datetime import datetime, timedelta, timezone
import aiofiles
import aiofiles.os
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt, JWTError
from dotenv import load_dotenv

load_dotenv()

DATABASE_PATH = "./app.db"
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY not set")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
security = HTTPBearer()

storage_path = "/home/ubuntu/secure-file-server/storage"

app = FastAPI()

# Database
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            is_disabled INTEGER NOT NULL
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS files (
            file_id TEXT PRIMARY KEY,
            owner_user_id TEXT NOT NULL,
            storage_path TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(owner_user_id) REFERENCES users(user_id)
        )
    """)
    db.commit()
    db.close()

init_db()

# Models

class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


# Helper Functions

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    db = get_db()
    row = db.execute(
        "SELECT * FROM users WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    db.close()

    if not row or row["is_disabled"]:
        raise HTTPException(status_code=401, detail="User disabled")

    return row

# Routes

@app.get("/")
def root():
    return {"hello":"welcome"}


@app.post("/auth/register")
def register(req: RegisterRequest):
    db = get_db()
    try:
        db.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?, ?)",
            (
                str(uuid.uuid4()),
                req.username,
                hash_password(req.password),
                datetime.utcnow().isoformat(),
                0
            )
        )
        db.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        db.close()

    return {"status": "ok"}

@app.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest):
    db = get_db()
    row = db.execute(
        "SELECT * FROM users WHERE username = ?",
        (req.username,)
    ).fetchone()
    db.close()

    if not row or not verify_password(req.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    token = create_access_token(row["user_id"])
    return TokenResponse(
        access_token=token,
        token_type="Bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@app.post("/upload")
async def upload( encrypted_file_key: str = Form(...), file: UploadFile = File(...), current_user = Depends(get_current_user)):
    user_id = current_user["user_id"]
    file_uuid = uuid.uuid4()

    os.makedirs(f"{storage_path}/{user_id}/{file_uuid}", exist_ok=True)

    file_name = file.filename

    async with aiofiles.open(f"{storage_path}/{user_id}/{file_uuid}/{file_name}", mode= "wb") as f:
        while content := await file.read(1024):
            await f.write(content)
    
    with open(f"{storage_path}/{user_id}/{file_uuid}/key.txt", "w") as key_file:
        key_file.write(encrypted_file_key)
    
    return file_uuid




@app.get("/download_file/{file_id}")
async def download_file(file_id,current_user = Depends(get_current_user)):
    user_id = current_user["user_id"]
    
    p = Path(f"{storage_path}/{user_id}/{file_id}")
    file_name = None
    for item in p.iterdir():
        if item.name != "key.txt":
            file_name = item.name
    def file_iterator():
        with open(f"{storage_path}/{user_id}/{file_id}/{file_name}", "rb") as file:
            while chunk := file.read(1024):
                yield chunk
    
    return StreamingResponse(
        file_iterator()
    )
        
@app.get("/download_key/{file_id}")
async def download_key(file_id, current_user = Depends(get_current_user)):
    user_id = current_user["user_id"]
    with open(f"{storage_path}/{user_id}/{file_id}/key.txt") as f:
        key_text = f.read()
    return key_text