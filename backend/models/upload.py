from pydantic import BaseModel


class UploadResponse(BaseModel):
    success: bool
    uid: str
    name: str
    email: str
    role: str