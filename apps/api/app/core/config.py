"""
从环境变量读取配置。

pydantic-settings 会自动读取进程环境，以及当前工作目录下的 .env。
改配置时只改 .env，不用改代码。
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Portal"
    secret_key: str = "change-me-to-a-long-random-string"
    cookie_name: str = "portal_session"
    cookie_secure: bool = False
    session_hours: int = 24 * 7

    # 浏览器访问的对外地址，飞书回调完成后要跳回这里
    public_url: str = "http://localhost"

    database_url: str = "sqlite:///./portal.db"

    # 没配飞书 App ID 时，前端只显示开发登录
    auth_allow_dev_login: bool = True
    feishu_app_id: str = ""
    feishu_app_secret: str = ""
    feishu_redirect_uri: str = "http://localhost/api/v1/auth/feishu/callback"
    feishu_scopes: str = "auth:user.id:read"
    feishu_authorize_url: str = "https://accounts.feishu.cn/open-apis/authen/v1/authorize"
    feishu_token_url: str = "https://open.feishu.cn/open-apis/authen/v2/oauth/token"
    feishu_user_info_url: str = "https://open.feishu.cn/open-apis/authen/v1/user_info"
    upload_dir: str = "./data/uploads"

    # 扫描件 OCR：只在电子 PDF 抽不出字、草稿要素也不齐时按页调用。
    # 默认用文档 OCR 模型；通用多模态更贵，可用 QWEN_OCR_MODEL 覆盖。
    qwen_api_key: str = ""
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_ocr_model: str = "qwen3.5-ocr"

    @property
    def feishu_enabled(self) -> bool:
        return bool(self.feishu_app_id and self.feishu_app_secret)

    @property
    def qwen_ocr_enabled(self) -> bool:
        return bool(self.qwen_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    """进程内只解析一次配置，避免每次请求都读环境变量。"""
    return Settings()
