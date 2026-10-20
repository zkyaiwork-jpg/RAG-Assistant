from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.permission import require_permission
from app.database.database import get_db
from app.models.document import DocumentVisibility
from app.models.user import User
from app.services.document_mutation_service import (
    delete_owned_document,
    document_folder_snapshot,
    update_owned_document_metadata,
)
from app.services.audit_service import write_audit_log
from app.utils.datetime import serialize_utc_datetime


router = APIRouter()


class DocumentUpdateRequest(BaseModel):
    original_name: str | None = None
    visibility: DocumentVisibility | None = None
    team_id: int | None = None
    # 传 null 表示移回“未分配文件夹”，不传表示不修改所属文件夹。
    folder_id: int | None = None


@router.delete("/documents/{filename}")
def remove_document(
    filename: str,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("file_delete"))],
    database: Annotated[Session, Depends(get_db)],
):
    try:
        result = delete_owned_document(database, current_user, filename)
    except Exception as exc:
        write_audit_log(
            database,
            action="document_delete",
            resource_type="document",
            user_id=current_user.id,
            resource_name=filename,
            result="failed",
            detail=f"operation_failed:{type(exc).__name__}",
            ip_address=request.client.host if request.client else None,
        )
        raise
    write_audit_log(
        database,
        action="document_delete",
        resource_type="document",
        user_id=current_user.id,
        resource_id=result["document_id"],
        resource_name=result["filename"],
        result="success",
        detail=f"vectors_deleted={result['delete_vector']}",
        ip_address=request.client.host if request.client else None,
    )
    return {**result, "message": "删除成功"}


@router.patch("/documents/{document_id}")
def update_document(
    document_id: int,
    request: DocumentUpdateRequest,
    http_request: Request,
    current_user: Annotated[User, Depends(require_permission("file_edit"))],
    database: Annotated[Session, Depends(get_db)],
):
    old_visibility = None
    old_original_name = None
    old_folder = None
    folder_supplied = "folder_id" in request.model_fields_set
    try:
        from app.models.document import Document
        existing = database.get(Document, document_id)
        if existing is not None:
            old_visibility = existing.visibility.value
            old_original_name = existing.original_name
        if folder_supplied:
            old_folder = document_folder_snapshot(document_id)
        document = update_owned_document_metadata(
            database,
            current_user,
            document_id,
            original_name=request.original_name,
            visibility=request.visibility,
            team_id=request.team_id,
            team_id_supplied="team_id" in request.model_fields_set,
            folder_id=request.folder_id,
            folder_id_supplied=folder_supplied,
        )
    except Exception as exc:
        write_audit_log(
            database,
            action="document_update",
            resource_type="document",
            user_id=current_user.id,
            resource_id=document_id,
            result="failed",
            detail=f"operation_failed:{type(exc).__name__}",
            ip_address=http_request.client.host if http_request.client else None,
        )
        raise
    changes = []
    if request.visibility is not None:
        changes.append(f"visibility:{old_visibility}->{request.visibility.value}")
    if request.original_name is not None:
        changes.append(f"original_name_changed={old_original_name != request.original_name.strip()}")
    if folder_supplied:
        changes.append(f"folder:{(old_folder or {}).get('folder_id')}->{request.folder_id}")
    write_audit_log(
        database,
        action="document_update",
        resource_type="document",
        user_id=current_user.id,
        resource_id=document.id,
        resource_name=document.filename,
        result="success",
        detail=";".join(changes) or "no_fields_changed",
        ip_address=http_request.client.host if http_request.client else None,
    )
    try:
        folder_state = document_folder_snapshot(document.id)
    except Exception:
        # 修改已提交；这里读取失败只影响响应里的文件夹信息，不影响写入结果。
        folder_state = {"folder_id": None, "folder_name": None}
    return {
        "document_id": document.id,
        "filename": document.filename,
        "original_name": document.original_name,
        "visibility": document.visibility.value,
        "team_id": document.team_id,
        "folder_id": folder_state["folder_id"],
        "folder_name": folder_state["folder_name"],
        "updated_time": serialize_utc_datetime(document.updated_time),
    }
