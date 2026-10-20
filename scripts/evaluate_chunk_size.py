"""Compare retrieval quality across text chunk sizes on the production code path.

For every chunk size the three policy documents are parsed, re-split and embedded
into a throw-away Chroma collection, then ``search_documents()`` is called with that
collection swapped in. TopK, reranker and the distance threshold therefore stay
identical to production, so the numbers are directly comparable. Production data is
never modified.

Metrics per chunk size:
  Top1 / Top3 hit rate on the positive set
  rejection rate on the negative set (no chunk passes the distance threshold)

Both passes run twice: with the production reranker, and with rerank disabled so the
raw Chroma order is measured as a control.
"""
from __future__ import annotations

import csv
import logging
import statistics
from datetime import datetime
from pathlib import Path

import chromadb
from sqlalchemy import select

from app.database.database import SessionLocal
from app.models.document import Document


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCUMENT_DIR = PROJECT_ROOT / "data" / "documents"
POSITIVE_DATASET = PROJECT_ROOT / "evals" / "chunk_size_questions.csv"
NEGATIVE_DATASET = PROJECT_ROOT / "evals" / "chunk_size_negative_questions.csv"
RESULT_DIR = PROJECT_ROOT / "evals" / "results"
DETAIL_OUTPUT = RESULT_DIR / "rag_chunk_size_detail_v1.csv"
SUMMARY_OUTPUT = RESULT_DIR / "rag_chunk_size_summary_v1.csv"

CHUNK_SIZES = (100, 200, 300, 400)
TOP_K = 3
DISTANCE_THRESHOLD = 0.8
TARGET_FILENAMES = ("公司规章制度.docx", "公司报销流程.docx", "公司请假流程.docx")


def read_questions(path: Path, required: set[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path.name} 缺少字段：{', '.join(sorted(missing))}")
        return [
            {key: (value or "").strip() for key, value in row.items()}
            for row in reader
        ]


def load_document_ids() -> dict[str, int]:
    with SessionLocal() as database:
        rows = database.execute(select(Document.id, Document.filename)).all()
    mapping = {filename: document_id for document_id, filename in rows}
    missing = [name for name in TARGET_FILENAMES if name not in mapping]
    if missing:
        raise RuntimeError(f"SQL 中缺少文档：{missing}")
    return mapping


def build_chunks(chunk_size: int) -> dict[str, list[str]]:
    """Re-parse and re-split every target document at the requested chunk size."""
    from app.services.parsers.parser_factory import get_parser
    from app.services.text_splitter import split_text

    result: dict[str, list[str]] = {}
    for filename in TARGET_FILENAMES:
        path = DOCUMENT_DIR / filename
        text = get_parser(path).parse(path)
        result[filename] = split_text(text, chunk_size=chunk_size)
    return result


def build_collection(chunk_size: int, document_ids: dict[str, int], chunks: dict[str, list[str]]):
    """Embed and index one chunk size into an isolated in-memory collection."""
    from app.services.embedding_service import encode_texts

    client = chromadb.EphemeralClient()
    collection = client.create_collection(name=f"chunk_{chunk_size}")

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []
    for filename in TARGET_FILENAMES:
        document_id = document_ids[filename]
        file_type = Path(filename).suffix.lstrip(".")
        chunk_list = chunks[filename]
        for index, text in enumerate(chunk_list):
            ids.append(f"{document_id}:{index}")
            documents.append(text)
            metadatas.append({
                "document_id": document_id,
                "filename": filename,
                "file_type": file_type,
                "chunk_index": index,
                "chunk_count": len(chunk_list),
            })
    embeddings = encode_texts(documents).tolist()
    collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)
    return collection, len(ids), statistics.mean(len(text) for text in documents)


def evaluate_chunk_size(
    chunk_size: int,
    collection,
    positives: list[dict[str, str]],
    negatives: list[dict[str, str]],
    *,
    use_reranker: bool,
) -> list[dict]:
    """Run every question against one collection through the production retrieval path."""
    from app.services import reranker_service, search_service

    allowed_ids = set(int(value) for value in load_document_ids().values())
    previous_collection = search_service.collection
    previous_rerank = reranker_service.rerank_documents

    def _rerank_disabled(*_args, **_kwargs):
        raise RuntimeError("rerank disabled for chunk-size experiment")

    search_service.collection = collection
    if not use_reranker:
        reranker_service.rerank_documents = _rerank_disabled

    logging.getLogger("app.services.search_service").setLevel(logging.CRITICAL)
    rows: list[dict] = []
    try:
        for kind, questions in (("positive", positives), ("negative", negatives)):
            for question in questions:
                results = search_service.search_documents(
                    question["question"],
                    top_k=TOP_K,
                    allowed_document_ids=allowed_ids,
                ).get("results") or []
                filenames = [item.get("filename") or "" for item in results]
                expected = question.get("expected_filename", "")
                top1_hit = int(bool(filenames) and filenames[0] == expected) if kind == "positive" else ""
                top3_hit = int(expected in filenames[:TOP_K]) if kind == "positive" else ""
                rejected = int(not results) if kind == "negative" else ""
                rows.append({
                    "chunk_size": chunk_size,
                    "rerank": "on" if use_reranker else "off",
                    "kind": kind,
                    "question_id": question["question_id"],
                    "question": question["question"],
                    "expected_filename": expected,
                    "result_count": len(results),
                    "top1_filename": filenames[0] if filenames else "",
                    "top1_distance": f"{results[0]['distance']:.4f}" if results else "",
                    "top3_filenames": "|".join(filenames),
                    "top1_hit": top1_hit,
                    "top3_hit": top3_hit,
                    "rejected": rejected,
                })
    finally:
        search_service.collection = previous_collection
        reranker_service.rerank_documents = previous_rerank
    return rows


def summarize(rows: list[dict]) -> list[dict]:
    summary: list[dict] = []
    for chunk_size in CHUNK_SIZES:
        for rerank in ("on", "off"):
            subset = [row for row in rows if row["chunk_size"] == chunk_size and row["rerank"] == rerank]
            positives = [row for row in subset if row["kind"] == "positive"]
            negatives = [row for row in subset if row["kind"] == "negative"]
            top1 = sum(int(row["top1_hit"]) for row in positives)
            top3 = sum(int(row["top3_hit"]) for row in positives)
            rejected = sum(int(row["rejected"]) for row in negatives)
            summary.append({
                "chunk_size": chunk_size,
                "rerank": rerank,
                "positive_count": len(positives),
                "top1_hits": top1,
                "top1_rate": f"{top1 / len(positives):.4f}",
                "top3_hits": top3,
                "top3_rate": f"{top3 / len(positives):.4f}",
                "negative_count": len(negatives),
                "negative_rejects": rejected,
                "negative_reject_rate": f"{rejected / len(negatives):.4f}",
            })
    return summary


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def print_table(summary: list[dict], chunk_stats: dict[int, tuple[int, float]]) -> None:
    print("\nchunk  分块数  平均长度 | 重排  Top1        Top3        负向拒答")
    print("-" * 78)
    for row in summary:
        chunk_count, average_length = chunk_stats[row["chunk_size"]]
        print(
            f"{row['chunk_size']:>5}  {chunk_count:>6}  {average_length:>7.0f} | "
            f"{row['rerank']:>4}  "
            f"{row['top1_hits']:>2}/{row['positive_count']} {float(row['top1_rate']):>6.1%}  "
            f"{row['top3_hits']:>2}/{row['positive_count']} {float(row['top3_rate']):>6.1%}  "
            f"{row['negative_rejects']:>2}/{row['negative_count']} {float(row['negative_reject_rate']):>6.1%}"
        )


def main() -> int:
    positives = read_questions(POSITIVE_DATASET, {"question_id", "question", "expected_filename"})
    negatives = read_questions(NEGATIVE_DATASET, {"question_id", "question", "expected_result"})
    print(f"正向题 {len(positives)} 道，负向题 {len(negatives)} 道；TopK={TOP_K}，distance<{DISTANCE_THRESHOLD}")

    document_ids = load_document_ids()
    detail: list[dict] = []
    chunk_stats: dict[int, tuple[int, float]] = {}

    for chunk_size in CHUNK_SIZES:
        chunks = build_chunks(chunk_size)
        collection, chunk_count, average_length = build_collection(chunk_size, document_ids, chunks)
        chunk_stats[chunk_size] = (chunk_count, average_length)
        print(f"\nchunk_size={chunk_size}: {chunk_count} 个分块，平均 {average_length:.0f} 字"
              f"（{', '.join(f'{name}:{len(chunks[name])}' for name in TARGET_FILENAMES)}）")
        for use_reranker in (True, False):
            rows = evaluate_chunk_size(
                chunk_size, collection, positives, negatives, use_reranker=use_reranker,
            )
            detail.extend(rows)
            positive_rows = [row for row in rows if row["kind"] == "positive"]
            negative_rows = [row for row in rows if row["kind"] == "negative"]
            print(f"  重排{'开' if use_reranker else '关'}: "
                  f"Top1={sum(int(r['top1_hit']) for r in positive_rows)}/{len(positive_rows)} "
                  f"Top3={sum(int(r['top3_hit']) for r in positive_rows)}/{len(positive_rows)} "
                  f"负向拒答={sum(int(r['rejected']) for r in negative_rows)}/{len(negative_rows)}")

    summary = summarize(detail)
    write_csv(DETAIL_OUTPUT, detail, list(detail[0].keys()))
    write_csv(SUMMARY_OUTPUT, summary, list(summary[0].keys()))
    print_table(summary, chunk_stats)
    print(f"\n明细：{DETAIL_OUTPUT}\n汇总：{SUMMARY_OUTPUT}")
    print(f"评测时间：{datetime.now().astimezone().isoformat(timespec='seconds')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
