from uuid import UUID

import io
import json
import zipfile

from fastapi import APIRouter, Query, UploadFile
from fastapi.responses import JSONResponse, Response

from app.api.deps import CurrentUser, DbSession
from app.schemas.data import TrashResponse
from app.core.exceptions import AppError
from app.services.backup import BackupService
from app.services.trash import TrashService

router = APIRouter(tags=["data"])


@router.get("/trash", response_model=TrashResponse)
async def trash(
    db: DbSession,
    user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    items = await TrashService(db, user.id).list()
    start = (page - 1) * page_size
    return TrashResponse(items=items[start:start + page_size], page=page, page_size=page_size, total=len(items))


@router.post("/trash/{kind}/{resource_id}/restore", status_code=204)
async def restore(kind: str, resource_id: UUID, db: DbSession, user: CurrentUser):
    await TrashService(db, user.id).restore(kind, resource_id)


@router.delete("/trash/{kind}/{resource_id}", status_code=204)
async def permanently_delete(kind: str, resource_id: UUID, db: DbSession, user: CurrentUser):
    await TrashService(db, user.id).permanently_delete(kind, resource_id)


@router.get("/export/json")
async def export_json(db: DbSession, user: CurrentUser):
    content = await BackupService(db, user.id).export()
    return JSONResponse(
        content=content,
        headers={"Content-Disposition": "attachment; filename=auranoise-backup.json"},
    )


@router.get("/export/markdown")
async def export_markdown(db: DbSession, user: CurrentUser):
    service = BackupService(db, user.id)
    files = await service.markdown_files(await service.export())
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path, content in files.items():
            archive.writestr(path, content)
    return Response(
        content=buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=auranoise-markdown.zip"},
    )


@router.get("/export/zip")
async def export_zip(db: DbSession, user: CurrentUser):
    return Response(
        content=await BackupService(db, user.id).zip_bytes(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=auranoise-backup.zip"},
    )


@router.post("/import/json")
async def import_json(file: UploadFile, db: DbSession, user: CurrentUser, confirm: bool = False):
    content = await file.read(10 * 1024 * 1024 + 1)
    if len(content) > 10 * 1024 * 1024:
        raise AppError(413, "BACKUP_TOO_LARGE", "Backup files must be 10 MB or smaller")
    try:
        raw = json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise AppError(422, "INVALID_JSON", "The uploaded file is not valid JSON") from None
    service = BackupService(db, user.id)
    return await service.import_json(service.validate(raw), confirm)
