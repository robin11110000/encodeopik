import os
import json
from uuid import uuid4
from pathlib import Path
from fastapi import APIRouter, File, Form, HTTPException, UploadFile


async def persist_file_in_local(metadata, file_to_persist, file_type):

    case_id = None
    if metadata:
        try:
            meta = json.loads(metadata)
            case_id = meta.get("caseId") or meta.get("userId")
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=400, detail=f"Invalid metadata payload: {exc}"
            ) from exc

    if not case_id:
        case_id = str(uuid4())

    base_dir = Path(os.getcwd()) / "resources" / case_id
    base_dir.mkdir(parents=True, exist_ok=True)

    folder_name = file_type.replace("_", "-")
    category_dir = base_dir / folder_name
    filename = sanitize_filename(file_to_persist.filename)
    destination = category_dir / filename
    await save_upload_file(file_to_persist, destination)

    return case_id, folder_name


async def save_upload_file(upload_file: UploadFile, destination: Path) -> None:
    """Persist an UploadFile to disk in chunks to avoid high memory usage."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        await upload_file.seek(0)
        with destination.open("wb") as buffer:
            while True:
                chunk = await upload_file.read(1024 * 1024)
                if not chunk:
                    break
                buffer.write(chunk)
    finally:
        await upload_file.close()


def sanitize_filename(filename: str) -> str:
    return Path(filename).name
