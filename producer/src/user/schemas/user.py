from pydantic import BaseModel, Field
from typing import Optional

class RegisterModel(BaseModel):
    username: str = Field(..., example="ivanov")
    password: str = Field(..., min_length=4, example="1234")
    role: str = ""

class LoginModel(BaseModel):
    username: str = Field(..., example="ivanov")
    password: str = Field(..., min_length=4, example="1234")

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
