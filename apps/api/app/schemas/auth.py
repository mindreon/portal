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
    # 当前能进哪些业务模块，前端用它画菜单。后端仍会再拦一次。
    modules: list[str]

    model_config = {"from_attributes": True}
