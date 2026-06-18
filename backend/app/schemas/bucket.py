from datetime import datetime

from pydantic import BaseModel, Field


class BucketCreate(BaseModel):
    name: str = Field(
        min_length=3,
        max_length=120,
        description="Unique bucket name (3-120 characters).",
        examples=["my-app-assets"],
    )


class BucketOut(BaseModel):
    id: str
    name: str
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "00c69b16-39e0-462d-afb5-ace042afe5e2",
                    "name": "my-app-assets",
                    "created_at": "2026-06-18T11:22:04Z",
                }
            ]
        },
    }
