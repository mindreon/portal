from pydantic import BaseModel, Field


class AuthConfigOut(BaseModel):
    feishu_enabled: bool
    dev_login_enabled: bool


class FeishuLoginOut(BaseModel):
    authorize_url: str


class DevLoginIn(BaseModel):
    name: str = Field(default="本地管理员", max_length=64)


class CurrentUserOut(BaseModel):
    id: int
    name: str
    email: str | None
    avatar_url: str | None
    role: str

    model_config = {"from_attributes": True}
