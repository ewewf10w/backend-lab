from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)
from typing import Literal


class RunConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = True


class DatabaseConfig(BaseModel):
    url: str 
    echo: bool = True
    echo_pool: bool = False
    pool_size: int = 50
    max_overflow: int = 10
    future: bool = True

class UrlPrefix(BaseModel):
    prefix: str = "/api"
    test: str = "/test"
    posts: str = "/posts"
    examples: str = "/examples"
    recipes: str = "/recipes"
    auth: str = "/auth"  
    users: str = "/users"

    @property
    def bearer_token_url(self) -> str:
        # api/auth/login
        parts = (self.prefix, self.auth, "/login")
        path = "".join(parts)
        return path.removeprefix("/")

class AuthConfig(BaseModel):
    cookie_max_age: int = 3600
    cookie_secure: bool = False
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"

class AccessToken(BaseModel):
    lifetime_seconds: int = 3600
    reset_password_token_secret: str = ""
    verification_token_secret: str = ""

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.template", ".env"),
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
    )
    run: RunConfig = RunConfig()
    url: UrlPrefix = UrlPrefix()
    auth: AuthConfig = AuthConfig()
    db: DatabaseConfig = DatabaseConfig(url="sqlite+aiosqlite:///./recipes_v2.sqlite")
    access_token: AccessToken = AccessToken()


settings = Settings()
