from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Health check",
    description="Return service status. Used by container orchestration health probes.",
)
def health() -> dict[str, str]:
    return {"status": "ok"}
