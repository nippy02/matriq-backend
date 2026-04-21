from pydantic import BaseModel, EmailStr


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    role: str
    name: str
    email: EmailStr
    user_id: int
    branch_id: int | None = None
