from datetime import datetime

from pydantic import BaseModel, Field


class ObjectOut(BaseModel):
    id: str
    bucket_id: str
    object_key: str
    original_filename: str
    content_type: str | None
    etag: str
    size_bytes: int
    metadata_json: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class BulkDeleteRequest(BaseModel):
    object_ids: list[str] = Field(
        min_length=1,
        description="List of object IDs to delete.",
        examples=[["3f9a...", "7c21..."]],
    )


class BulkDeleteResult(BaseModel):
    deleted: list[str]
    failed: list[dict[str, str]]
