from datetime import datetime

from pydantic import BaseModel, Field


class BucketCreate(BaseModel):
    name: str = Field(min_length=3, max_length=120)


class BucketOut(BaseModel):
    id: str
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}
