from pydantic import BaseModel, ConfigDict, Field

class InterviewerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str
    

class LogoutResponse(BaseModel):
    logout_url: str | None = None

class SessionUser(BaseModel):
    id: str
    name: str
    email: str
    role: str
    access_status: str
    profile_image_url: str | None = None


class SessionResponse(BaseModel):
    user: SessionUser

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str
    role: str
    access_status: str
    profile_image_url: str | None = None
