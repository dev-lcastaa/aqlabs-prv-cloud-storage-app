import hashlib
import os
import tempfile
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.storage_alloc import StorageAlloc


def _safe_segments(object_key: str) -> list[str]:
    segments = [segment for segment in object_key.strip("/").split("/") if segment]
    if not segments:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Object key cannot be empty")
    if any(segment in {".", ".."} for segment in segments):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid object key path")
    return segments


def build_relative_path(object_key: str) -> Path:
    return Path(*_safe_segments(object_key))


def resolve_storage_path(storage_root: Path, bucket_id: str, object_key: str) -> Path:
    bucket_path = (storage_root / bucket_id).resolve()
    bucket_path.mkdir(parents=True, exist_ok=True)

    target_path = (bucket_path / build_relative_path(object_key)).resolve()
    if bucket_path not in target_path.parents and target_path != bucket_path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsafe object key path")

    target_path.parent.mkdir(parents=True, exist_ok=True)
    return target_path


def _select_storage_root_index(db: Session, num_roots: int) -> int:
    # Ensure a single-row counter exists and atomically increment it (DB-backed)
    stmt = select(StorageAlloc).where(StorageAlloc.id == 1).with_for_update()
    alloc = db.execute(stmt).scalar_one_or_none()
    if alloc is None:
        alloc = StorageAlloc(id=1, last_index=0)
        db.add(alloc)
        db.commit()
        return 0

    alloc.last_index = (alloc.last_index + 1) % num_roots
    db.commit()
    return int(alloc.last_index)


def select_and_resolve_path(db: Session, storage_roots: list[str], bucket_id: str, object_key: str) -> tuple[Path, str]:
    """Select a storage root index using DB counter and resolve a target path.

    Returns (target_path, stored_relative) where stored_relative is "{idx}:{relative_path}".
    """
    if not storage_roots:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No storage roots configured")
    idx = _select_storage_root_index(db, len(storage_roots))
    root = Path(storage_roots[idx])
    target_path = resolve_storage_path(root, bucket_id, object_key)
    rel = str(target_path.relative_to(root))
    stored_relative = f"{idx}:{rel}"
    return target_path, stored_relative


def path_from_stored_relative(storage_roots: list[str], stored_relative: str) -> Path:
    try:
        idx_str, rel = stored_relative.split(":", 1)
        idx = int(idx_str)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Invalid stored path format")
    roots = storage_roots
    if idx < 0 or idx >= len(roots):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Stored path references unknown storage root")
    return (Path(roots[idx]) / rel).resolve()


async def write_upload_file(target_path: Path, upload_file: UploadFile) -> tuple[int, str]:
    md5 = hashlib.md5()
    size_bytes = 0
    # Write to a temp file in the same directory then atomically replace
    temp_fd, temp_path = tempfile.mkstemp(dir=str(target_path.parent))
    os.close(temp_fd)
    try:
        with open(temp_path, "wb") as out_file:
            while True:
                chunk = await upload_file.read(1024 * 1024)
                if not chunk:
                    break
                size_bytes += len(chunk)
                md5.update(chunk)
                out_file.write(chunk)
        # Atomic replace
        os.replace(temp_path, str(target_path))
    finally:
        try:
            await upload_file.close()
        except Exception:
            pass
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

    return size_bytes, md5.hexdigest()


def delete_file_if_exists(path: Path) -> None:
    if path.exists():
        path.unlink()
