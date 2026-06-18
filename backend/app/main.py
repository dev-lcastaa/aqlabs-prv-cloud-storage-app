from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import Base, engine
from .models import bucket, object_entry, storage_alloc  # noqa: F401
from .routes.buckets import router as buckets_router
from .routes.health import router as health_router
from .routes.objects import router as objects_router

settings = get_settings()

tags_metadata = [
    {
        "name": "health",
        "description": "Service liveness checks for orchestration and uptime probes.",
    },
    {
        "name": "buckets",
        "description": "Create, list, rename, purge, and delete storage buckets.",
    },
    {
        "name": "objects",
        "description": "Upload, list, and delete objects within a bucket. "
        "Objects are distributed across storage volumes using round-robin allocation.",
    },
]

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    summary="Private S3-compatible object storage backed by host-mounted volumes.",
    description=(
        "Aqlabs Object Store is a lightweight, self-hosted object storage service.\n\n"
        "**Features**\n"
        "- Create and manage buckets\n"
        "- Upload keyed objects with optional JSON metadata\n"
        "- Round-robin storage distribution across multiple mounted drives\n"
        "- Metadata persisted in PostgreSQL; file bytes stored on disk\n"
        "- Single and bulk delete, plus full bucket purge\n"
    ),
    openapi_tags=tags_metadata,
    contact={"name": "Aqlabs"},
    license_info={"name": "Proprietary"},
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    # Create all configured storage roots
    for root in settings.storage_roots_list:
        Path(root).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)


app.include_router(health_router)
app.include_router(buckets_router, prefix=settings.api_prefix)
app.include_router(objects_router, prefix=settings.api_prefix)
