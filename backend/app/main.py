from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import Base, engine
from .models import bucket, object_entry  # noqa: F401
from .routes.buckets import router as buckets_router
from .routes.health import router as health_router
from .routes.objects import router as objects_router

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Path(settings.storage_root).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)


app.include_router(health_router)
app.include_router(buckets_router, prefix=settings.api_prefix)
app.include_router(objects_router, prefix=settings.api_prefix)
