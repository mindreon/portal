from pydantic import BaseModel, Field


class UserOut(BaseModel):
    id: int
    name: str
    email: str | None
    role: str
    modules: list[str]


class UserPatchIn(BaseModel):
    role: str | None = Field(default=None)
    modules: list[str] | None = Field(default=None)
