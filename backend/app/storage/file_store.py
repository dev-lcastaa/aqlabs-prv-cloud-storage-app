import hashlib
from pathlib import Path

from fastapi import HTTPException, UploadFile, status


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


async def write_upload_file(target_path: Path, upload_file: UploadFile) -> tuple[int, str]:
    md5 = hashlib.md5()
    size_bytes = 0
    with target_path.open("wb") as out_file:
        while True:
            chunk = await upload_file.read(1024 * 1024)
            if not chunk:
                break
            size_bytes += len(chunk)
            md5.update(chunk)
            out_file.write(chunk)

    await upload_file.close()
    return size_bytes, md5.hexdigest()


def delete_file_if_exists(path: Path) -> None:
    if path.exists():
        path.unlink()
