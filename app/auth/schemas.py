from pydantic import BaseModel, ConfigDict, Field

class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str
    password: str = Field(min_length=8)
    role: str = Field(pattern="^(admin|interviewer)$")


class InterviewerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str
    password: str = Field(min_length=8)

class UserLogin(BaseModel):
    email: str
    password: str

class SessionUser(BaseModel):
    id: str
    name: str
    email: str
    role: str


class SessionResponse(BaseModel):
    user: SessionUser

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str
    role: str
