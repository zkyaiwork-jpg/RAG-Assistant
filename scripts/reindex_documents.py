"""Rebuild the vector index with the current text splitter, keeping document ids.

Run this with the API stopped: it writes to the same Chroma directory the server
opens. Existing metadata (folder, visibility, uploader, timestamps) is carried over
from the document's current chunks, so re-indexing does not change permissions or
folder assignment.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import select

from app.database.database import SessionLocal
from app.models.document import Document
from app.services.document_service import UPLOAD_DIR
from app.services.parsers.parser_factory import get_parser
from app.services.text_splitter import split_text
from app.services.vector_store import collection

CHUNK_SPECIFIC_KEYS = ("chunk_id", "chunk_index", "chunk_count")


def existing_metadata(document_id: int) -> dict | None:
    result = collection.get(where={"document_id": document_id}, include=["metadatas"])
    for metadata in result.get("metadatas") or []:
        if isinstance(metadata, dict):
            return {key: value for key, value in metadata.items() if key not in CHUNK_SPECIFIC_KEYS}
    return None


def reindex(dry_run: bool) -> int:
    with SessionLocal() as database:
        documents = database.scalars(select(Document).order_by(Document.id)).all()

    print(f"{'文档':<34}{'旧块数':>7}{'新块数':>7}  平均长度")
    print("-" * 66)
    total_old = total_new = 0
    failures: list[str] = []

    for document in documents:
        path = UPLOAD_DIR / document.filename
        if not path.is_file():
            failures.append(f"{document.filename}: 源文件缺失")
            continue
        try:
            text = get_parser(path).parse(path)
            chunks = split_text(text)
        except Exception as exc:  # noqa: BLE001 - reported below
            failures.append(f"{document.filename}: 解析失败 {type(exc).__name__}")
            continue

        template = existing_metadata(document.id)
        snapshot = collection.get(where={"document_id": document.id}, include=["documents", "embeddings", "metadatas"])
        old_ids = snapshot.get("ids") or []
        total_old += len(old_ids)
        total_new += len(chunks)
        average = sum(len(chunk) for chunk in chunks) / len(chunks) if chunks else 0
        print(f"{document.filename:<34}{len(old_ids):>7}{len(chunks):>7}  {average:>6.0f}")

        if dry_run or not chunks:
            continue

        base = dict(template or {
            "document_id": document.id,
            "filename": document.filename,
            "file_type": path.suffix.lstrip("."),
            "status": "indexed",
        })
        try:
            if old_ids:
                collection.delete(ids=old_ids)
            from app.services.embedding_service import encode_texts

            ids = [f"{document.id}:{index}" for index in range(len(chunks))]
            metadatas = []
            for index in range(len(chunks)):
                metadata = dict(base)
                metadata.update({"chunk_id": ids[index], "chunk_index": index, "chunk_count": len(chunks)})
                metadatas.append(metadata)
            collection.add(ids=ids, documents=chunks, embeddings=encode_texts(chunks).tolist(), metadatas=metadatas)
        except Exception as exc:  # noqa: BLE001 - restore below
            failures.append(f"{document.filename}: 写入失败 {type(exc).__name__}")
            try:
                if snapshot.get("ids"):
                    collection.add(
                        ids=snapshot["ids"],
                        documents=snapshot["documents"],
                        embeddings=snapshot["embeddings"],
                        metadatas=snapshot["metadatas"],
                    )
            except Exception as restore_exc:  # noqa: BLE001
                failures.append(f"{document.filename}: 回滚失败 {type(restore_exc).__name__}")
            continue

    print("-" * 66)
    print(f"文档 {len(documents)} 篇，块数 {total_old} → {total_new}" + ("（dry-run，未写入）" if dry_run else ""))
    if failures:
        print("异常：")
        for failure in failures:
            print("  -", failure)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="按当前切片大小重建向量索引")
    parser.add_argument("--dry-run", action="store_true")
    arguments = parser.parse_args()
    return reindex(arguments.dry_run)


if __name__ == "__main__":
    sys.exit(main())
