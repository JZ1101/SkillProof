import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from .config import settings

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".webm", ".jpg", ".jpeg", ".png"}


async def save_upload(file: UploadFile) -> dict:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File type {ext} not allowed. Accepted: {ALLOWED_EXTENSIONS}")

    file_id = uuid.uuid4().hex
    filename = f"{file_id}{ext}"
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    filepath = upload_dir / filename

    async with aiofiles.open(filepath, "wb") as out:
        content = await file.read()
        await out.write(content)

    return {
        "file_id": file_id,
        "filename": filename,
        "path": str(filepath),
        "size_bytes": len(content),
    }
