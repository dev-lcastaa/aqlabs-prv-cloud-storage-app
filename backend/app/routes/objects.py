import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models.bucket import Bucket
from ..models.object_entry import ObjectEntry
from ..schemas.object_entry import BulkDeleteRequest, BulkDeleteResult, ObjectOut
from ..storage.file_store import (
    delete_file_if_exists,
    resolve_storage_path,
    write_upload_file,
    select_and_resolve_path,
    path_from_stored_relative,
)

router = APIRouter(prefix="/buckets/{bucket_id}/objects", tags=["objects"])
settings = get_settings()
storage_roots = settings.storage_roots_list


def _get_bucket_or_404(bucket_id: str, db: Session) -> Bucket:
    bucket = db.get(Bucket, bucket_id)
    if not bucket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bucket not found")
    return bucket


def _parse_metadata(metadata: str | None) -> dict | None:
    if not metadata:
        return None
    try:
        parsed = json.loads(metadata)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="metadata must be valid JSON") from exc
    if not isinstance(parsed, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="metadata must be a JSON object")
    return parsed


@router.post(
    "/folders",
    status_code=status.HTTP_201_CREATED,
    summary="Create a folder",
    description="Create an empty folder (prefix) inside a bucket.",
    responses={404: {"description": "Bucket not found"}},
)
def create_folder(
    bucket_id: str,
    path: str = Form(...),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    _get_bucket_or_404(bucket_id, db)
    # Reuse object-key path validation by resolving a temp marker file path.
    # create marker in the first configured storage root
    first_root = Path(storage_roots[0]).resolve()
    marker_path = resolve_storage_path(first_root, bucket_id, f"{path.strip('/')}/.folder")
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    return {"folder_path": str(marker_path.parent.relative_to(first_root))}


@router.get(
    "",
    response_model=list[ObjectOut],
    summary="List objects",
    description="List all objects in a bucket, newest first.",
    responses={404: {"description": "Bucket not found"}},
)
def list_objects(bucket_id: str, db: Session = Depends(get_db)) -> list[ObjectEntry]:
    _get_bucket_or_404(bucket_id, db)
    stmt = select(ObjectEntry).where(ObjectEntry.bucket_id == bucket_id).order_by(ObjectEntry.created_at.desc())
    return list(db.scalars(stmt).all())


@router.post(
    "",
    response_model=ObjectOut,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an object",
    description=(
        "Upload a file to a bucket under the given key. "
        "Optionally attach JSON metadata. The object key must be unique within the bucket. "
        "Files are distributed across storage volumes via round-robin allocation."
    ),
    responses={
        404: {"description": "Bucket not found"},
        409: {"description": "Object key already exists in bucket"},
    },
)
async def upload_object(
    bucket_id: str,
    file: UploadFile = File(...),
    key: str = Form(...),
    metadata: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> ObjectEntry:
    _get_bucket_or_404(bucket_id, db)

    metadata_json = _parse_metadata(metadata)
    # Select storage root via DB-backed round-robin and resolve target path
    target_path, stored_relative = select_and_resolve_path(db, storage_roots, bucket_id, key)
    size_bytes, etag = await write_upload_file(target_path, file)

    entry = ObjectEntry(
        bucket_id=bucket_id,
        object_key=key,
        original_filename=file.filename or "unknown",
        stored_relative_path=stored_relative,
        content_type=file.content_type,
        etag=etag,
        size_bytes=size_bytes,
        metadata_json=metadata_json,
    )

    db.add(entry)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        delete_file_if_exists(target_path)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Object key already exists in bucket") from exc

    db.refresh(entry)
    return entry


@router.delete(
    "/{object_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an object",
    description="Delete a single object (file and metadata) from a bucket.",
    responses={404: {"description": "Bucket or object not found"}},
)
def delete_object(bucket_id: str, object_id: str, db: Session = Depends(get_db)) -> None:
    _get_bucket_or_404(bucket_id, db)
    entry = db.scalar(select(ObjectEntry).where(ObjectEntry.id == object_id, ObjectEntry.bucket_id == bucket_id))
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Object not found")

    file_path = path_from_stored_relative(storage_roots, entry.stored_relative_path)
    delete_file_if_exists(file_path)

    db.delete(entry)
    db.commit()


@router.post(
    "/delete-bulk",
    response_model=BulkDeleteResult,
    summary="Bulk delete objects",
    description="Delete multiple objects by ID. Returns per-item success and failure results.",
    responses={404: {"description": "Bucket not found"}},
)
def delete_objects_bulk(
    bucket_id: str,
    payload: BulkDeleteRequest,
    db: Session = Depends(get_db),
) -> BulkDeleteResult:
    _get_bucket_or_404(bucket_id, db)
    deleted: list[str] = []
    failed: list[dict[str, str]] = []

    for object_id in payload.object_ids:
        entry = db.scalar(select(ObjectEntry).where(ObjectEntry.id == object_id, ObjectEntry.bucket_id == bucket_id))
        if not entry:
            failed.append({"object_id": object_id, "reason": "not_found"})
            continue

        file_path = path_from_stored_relative(storage_roots, entry.stored_relative_path)
        try:
            delete_file_if_exists(file_path)
            db.delete(entry)
            deleted.append(object_id)
        except OSError:
            failed.append({"object_id": object_id, "reason": "filesystem_error"})

    db.commit()
    return BulkDeleteResult(deleted=deleted, failed=failed)
