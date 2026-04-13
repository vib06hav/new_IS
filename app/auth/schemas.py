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


class InterviewerUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str


class AdminPasswordChange(BaseModel):
    new_password: str = Field(min_length=8)


class SelfPasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)

class SelfProfileUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)

class UserLogin(BaseModel):
    email: str
    password: str

class SessionUser(BaseModel):
    id: str
    name: str
    email: str
    role: str
    profile_image_url: str | None = None


class SessionResponse(BaseModel):
    user: SessionUser

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str
    role: str
    profile_image_url: str | None = None
