from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_at: datetime
    refresh_token: Optional[str] = None

class TokenData(BaseModel):
    user_id: str
    email: EmailStr
    role: str
    exp: datetime

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False

class RefreshTokenRequest(BaseModel):
    refresh_token: str 