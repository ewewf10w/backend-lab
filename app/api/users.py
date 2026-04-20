from fastapi import APIRouter

from app.authentication.fastapi_users import fastapi_users
from app.config import settings
from app.authentication.schemas.user import (
    UserRead,
    UserUpdate,
)

router = APIRouter(
    prefix=settings.url.users,
    tags=["Users"],
)

# /me
# /{id}
router.include_router(
    router=fastapi_users.get_users_router(
        UserRead,
        UserUpdate,
    ),
)
