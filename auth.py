from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client
from typing import Optional
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

router = APIRouter(prefix="/auth", tags=["authentication"])

# Supabase configuration
SUPABASE_URL = "https://zvmseqpsgsgnzwxvvkak.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp2bXNlcXBzZ3Nnbnp3eHZ2a2FrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzU4NTI3MzgsImV4cCI6MjA1MTQyODczOH0.pBP5G8Igj4MtItR8Zz7EobAL_2rCSYzTGcSvek7yvIs"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp2bXNlcXBzZ3Nnbnp3eHZ2a2FrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTg1MjczOCwiZXhwIjoyMDUxNDI4NzM4fQ.Wd0JQvOXJKMHW4d_yYqGbcr5l9rCBPPZkCZQpn2_HBE"

# Initialize two Supabase clients
admin_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)  # For admin operations
auth_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)      # For auth operations

# Initialize OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    
class UserLogin(BaseModel):
    email: EmailStr
    password: str

@router.post("/signup")
async def signup(user: UserCreate):
    try:
        # Use admin client for signup
        response = admin_client.auth.admin.create_user({
            "email": user.email,
            "password": user.password,
            "email_confirm": True
        })
        return {
            "message": "User created successfully",
            "user_id": response.user.id,
            "email": response.user.email
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(user: UserLogin):
    try:
        # Use auth client for login
        response = auth_client.auth.sign_in_with_password({
            "email": user.email,
            "password": user.password
        })
        return {
            "access_token": response.session.access_token,
            "user_id": response.user.id,
            "email": response.user.email
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    print(f"Verifying token in get_current_user: {token[:20]}...")  # Debug log
    try:
        user = auth_client.auth.get_user(token)
        print(f"User verified: {user.user.id}")  # Debug log
        return user.user.id
    except Exception as e:
        print(f"Token verification failed: {str(e)}")  # Debug log
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        ) 