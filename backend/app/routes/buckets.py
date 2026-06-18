from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.bucket import Bucket
from ..models.object_entry import ObjectEntry
from ..config import get_settings
from ..storage.file_store import delete_file_if_exists, path_from_stored_relative
from ..schemas.bucket import BucketCreate, BucketOut


settings = get_settings()
storage_roots = settings.storage_roots_list

router = APIRouter(prefix="/buckets", tags=["buckets"])


@router.get("", response_model=list[BucketOut])
def list_buckets(db: Session = Depends(get_db)) -> list[Bucket]:
    return list(db.scalars(select(Bucket).order_by(Bucket.created_at.desc())).all())


@router.post("", response_model=BucketOut, status_code=status.HTTP_201_CREATED)
def create_bucket(payload: BucketCreate, db: Session = Depends(get_db)) -> Bucket:
    exists = db.scalar(select(Bucket).where(Bucket.name == payload.name))
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bucket name already exists")

    bucket = Bucket(name=payload.name)
    db.add(bucket)
    db.commit()
    db.refresh(bucket)
    return bucket


@router.delete("/{bucket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bucket(bucket_id: str, db: Session = Depends(get_db)) -> None:
    bucket = db.get(Bucket, bucket_id)
    if not bucket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bucket not found")

    db.delete(bucket)
    db.commit()


@router.delete("/{bucket_id}/objects", status_code=status.HTTP_204_NO_CONTENT)
def purge_bucket_objects(bucket_id: str, db: Session = Depends(get_db)) -> None:
    bucket = db.get(Bucket, bucket_id)
    if not bucket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bucket not found")

    stmt = select(ObjectEntry).where(ObjectEntry.bucket_id == bucket_id)
    entries = list(db.scalars(stmt).all())
    for entry in entries:
        try:
            file_path = path_from_stored_relative(storage_roots, entry.stored_relative_path)
            delete_file_if_exists(file_path)
        except HTTPException:
            # ignore and still delete metadata
            pass
        db.delete(entry)

    db.commit()


@router.patch("/{bucket_id}", response_model=BucketOut)
def rename_bucket(bucket_id: str, payload: BucketCreate, db: Session = Depends(get_db)) -> Bucket:
    bucket = db.get(Bucket, bucket_id)
    if not bucket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bucket not found")

    # ensure unique name
    exists = db.scalar(select(Bucket).where(Bucket.name == payload.name, Bucket.id != bucket_id))
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bucket name already exists")

    bucket.name = payload.name
    db.add(bucket)
    db.commit()
    db.refresh(bucket)
    return bucket
