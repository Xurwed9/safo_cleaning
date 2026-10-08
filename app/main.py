from fastapi import Depends, FastAPI
import asyncio

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.limiter import limiter
from app.db.session import get_db
from app.services.notification_worker import notification_worker

from app.api.v1.auth import router as auth_router
from app.api.v1.leads import router as leads_router
from app.api.v1.pricing import router as pricing_router
from app.api.v1.extra_service import router as extra_services_router
from app.api.v1.contacts import router as contacts_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.before_after import router as before_after_router
from app.api.v1.events import router as events_router
from app.api.v1.statistics import router as statistics_router
from app.api.v1.users import router as users_router

from fastapi.staticfiles import StaticFiles


app = FastAPI(
    title="Safo Cleaning API",
    version="1.0.0",
)

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)

worker_task = None


@app.on_event("startup")
async def startup_event():
    global worker_task

    worker_task = asyncio.create_task(
        notification_worker()
    )


@app.on_event("shutdown")
async def shutdown_event():
    global worker_task

    if worker_task is not None:
        worker_task.cancel()

        try:
            await worker_task
        except asyncio.CancelledError:
            pass


app.include_router(
    auth_router,
    prefix="/api/v1",
)

app.include_router(users_router, prefix="/api/v1")

app.include_router(
    leads_router,
    prefix="/api/v1",
)

app.include_router(
    pricing_router,
    prefix="/api/v1",
)

app.include_router(
    extra_services_router,
    prefix="/api/v1",
)

app.include_router(
    contacts_router,
    prefix="/api/v1",
)

app.include_router(
    reviews_router,
    prefix="/api/v1",
)

app.mount(
    "/storage",
    StaticFiles(directory="storage"),
    name="storage",
)

app.include_router(
    before_after_router,
    prefix="/api/v1",
)

app.include_router(
    events_router,
    prefix="/api/v1",
)

app.include_router(
    statistics_router,
    prefix="/api/v1",
)

@app.get("/")
async def root():
    return {
        "message": "Safo Cleaning Backend is running"
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/health/db")
async def health_db(
    db: AsyncSession = Depends(get_db),
):
    await db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}