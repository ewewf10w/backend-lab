import uvicorn
from fastapi import FastAPI
from app.config import settings
from contextlib import asynccontextmanager

from app.models import db_helper, Base
from app.api import router as api_router
from fastapi.staticfiles import StaticFiles

from fastapi_pagination import add_pagination
from app.task_queue import broker

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    if not broker.is_worker_process:
        await broker.startup()

    async with db_helper.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield
    # shutdown
    await db_helper.dispose()


main_app = FastAPI(
    lifespan=lifespan,
)
main_app.include_router(
    api_router,
)

add_pagination(main_app)

main_app.mount("/static", StaticFiles(directory="app/static"), name="static")

if __name__ == "__main__":
    uvicorn.run(
        "app.main:main_app",
        host=settings.run.host,
        port=settings.run.port,
        reload=settings.run.reload,
    )
