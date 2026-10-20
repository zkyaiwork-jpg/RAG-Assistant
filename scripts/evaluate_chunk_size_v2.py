"""Chunk-size sweep on the 300 + 100 question set, judged at clause level.

Differences from the v1 sweep:
  * positive hits are judged at clause level (the retrieved chunk must contain the
    gold 第N条), because document-level Top1 is meaningless with a small corpus;
  * negatives are reported overall and per stratum (near / mid / far);
  * one unfiltered retrieval pass per question yields raw top1 distances, so the
    positive/negative separation (AUC) can be reported independently of the 0.8 cut.
"""
from __future__ import annotations

import csv
import logging
import re
import statistics
import sys
from datetime import datetime
from pathlib import Path

import chromadb
from sqlalchemy import select

from app.database.database import SessionLocal
from app.models.document import Document

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCUMENT_DIR = PROJECT_ROOT / "data" / "documents"
POSITIVE_DATASET = PROJECT_ROOT / "evals" / "questions_v2_positive.csv"
NEGATIVE_DATASET = PROJECT_ROOT / "evals" / "questions_v2_negative.csv"
RESULT_DIR = PROJECT_ROOT / "evals" / "results"
DETAIL_OUTPUT = RESULT_DIR / "rag_chunk_size_v2_detail.csv"
SUMMARY_OUTPUT = RESULT_DIR / "rag_chunk_size_v2_summary.csv"

CHUNK_SIZES = (100, 200, 300, 400)
TOP_K = 3
DISTANCE_THRESHOLD = 0.8
RAW_THRESHOLD = 10.0
CLAUSE_PATTERN = re.compile(r"第([一二三四五六七八九十百零]+)条")
DIGITS = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}


def parse_number(text: str) -> int:
    if text == "十":
        return 10
    if "十" in text:
        tens, _, ones = text.partition("十")
        return (DIGITS[tens] if tens else 1) * 10 + (DIGITS[ones] if ones else 0)
    return DIGITS[text]


def clauses_in(chunk: str) -> set[int]:
    return {parse_number(match) for match in CLAUSE_PATTERN.findall(chunk)}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return [{key: (value or "").strip() for key, value in row.items()} for row in csv.DictReader(source)]


def load_document_ids() -> dict[str, int]:
    with SessionLocal() as database:
        rows = database.execute(select(Document.id, Document.filename)).all()
    return {filename: document_id for document_id, filename in rows}


def build_collection(chunk_size: int, document_ids: dict[str, int]):
    from app.services.embedding_service import encode_texts
    from app.services.parsers.parser_factory import get_parser
    from app.services.text_splitter import split_text

    client = chromadb.EphemeralClient()
    collection = client.create_collection(name=f"v2_{chunk_size}")
    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []
    lengths: list[int] = []
    for filename, document_id in document_ids.items():
        path = DOCUMENT_DIR / filename
        text = get_parser(path).parse(path)
        for index, chunk in enumerate(split_text(text, chunk_size=chunk_size)):
            ids.append(f"{document_id}:{index}")
            documents.append(chunk)
            lengths.append(len(chunk))
            metadatas.append({
                "document_id": document_id,
                "filename": filename,
                "chunk_index": index,
            })
    collection.add(ids=ids, documents=documents, embeddings=encode_texts(documents).tolist(), metadatas=metadatas)
    return collection, len(ids), statistics.mean(lengths)


def auc(positives: list[float], negatives: list[float]) -> float:
    """Probability that a positive ranks closer than a negative (Mann-Whitney)."""
    if not positives or not negatives:
        return float("nan")
    wins = 0.0
    for positive in positives:
        for negative in negatives:
            if positive < negative:
                wins += 1
            elif positive == negative:
                wins += 0.5
    return wins / (len(positives) * len(negatives))


def run(chunk_size: int, collection, positives, negatives, allowed_ids) -> list[dict]:
    from app.services import search_service

    previous = search_service.collection
    search_service.collection = collection
    logging.getLogger("app.services.search_service").setLevel(logging.CRITICAL)
    rows: list[dict] = []
    try:
        for question in positives:
            results = search_service.search_documents(
                question["question"], top_k=TOP_K,
                allowed_document_ids=allowed_ids,
                rejection_mode="none",
            ).get("results") or []
            kept = [item for item in results if item["distance"] < DISTANCE_THRESHOLD]
            gold_clause = int(question["expected_clause"])
            gold_filename = question["expected_filename"]
            doc_hits = [item["filename"] == gold_filename for item in kept[:TOP_K]]
            clause_hits = [
                item["filename"] == gold_filename and gold_clause in clauses_in(item["content"])
                for item in kept[:TOP_K]
            ]
            rows.append({
                "chunk_size": chunk_size,
                "kind": "positive",
                "question_id": question["question_id"],
                "question": question["question"],
                "expected_filename": gold_filename,
                "expected_clause": gold_clause,
                "result_count": len(kept),
                "top1_filename": kept[0]["filename"] if kept else "",
                "top1_clauses": "|".join(str(value) for value in sorted(clauses_in(kept[0]["content"]))) if kept else "",
                "top1_distance": round(results[0]["distance"], 4) if results else "",
                "doc_top1_hit": int(bool(doc_hits) and doc_hits[0]),
                "doc_top3_hit": int(any(doc_hits)),
                "clause_top1_hit": int(bool(clause_hits) and clause_hits[0]),
                "clause_top3_hit": int(any(clause_hits)),
                "rejected": int(not kept),
            })
        for question in negatives:
            results = search_service.search_documents(
                question["question"], top_k=TOP_K,
                allowed_document_ids=allowed_ids,
                rejection_mode="none",
            ).get("results") or []
            kept = [item for item in results if item["distance"] < DISTANCE_THRESHOLD]
            rows.append({
                "chunk_size": chunk_size,
                "kind": f"negative_{question['question_type']}",
                "question_id": question["question_id"],
                "question": question["question"],
                "expected_filename": "",
                "expected_clause": "",
                "result_count": len(kept),
                "top1_filename": kept[0]["filename"] if kept else "",
                "top1_clauses": "",
                "top1_distance": round(results[0]["distance"], 4) if results else "",
                "doc_top1_hit": "",
                "doc_top3_hit": "",
                "clause_top1_hit": "",
                "clause_top3_hit": "",
                "rejected": int(not kept),
            })
    finally:
        search_service.collection = previous
    return rows


def summarize(rows: list[dict], stats: dict[int, tuple[int, float]]) -> list[dict]:
    summary = []
    for chunk_size in CHUNK_SIZES:
        subset = [row for row in rows if row["chunk_size"] == chunk_size]
        positives = [row for row in subset if row["kind"] == "positive"]
        negatives = [row for row in subset if row["kind"].startswith("negative")]
        pos_distances = [float(row["top1_distance"]) for row in positives if row["top1_distance"] != ""]
        neg_distances = [float(row["top1_distance"]) for row in negatives if row["top1_distance"] != ""]
        chunk_count, average_length = stats[chunk_size]
        entry = {
            "chunk_size": chunk_size,
            "chunk_count": chunk_count,
            "avg_chunk_length": round(average_length, 1),
            "positive_count": len(positives),
            "clause_top1": sum(int(row["clause_top1_hit"]) for row in positives),
            "clause_top3": sum(int(row["clause_top3_hit"]) for row in positives),
            "doc_top1": sum(int(row["doc_top1_hit"]) for row in positives),
            "doc_top3": sum(int(row["doc_top3_hit"]) for row in positives),
            "pos_avg_distance": round(statistics.mean(pos_distances), 4) if pos_distances else "",
            "neg_avg_distance": round(statistics.mean(neg_distances), 4) if neg_distances else "",
            "auc": round(auc(pos_distances, neg_distances), 4),
        }
        for stratum in ("near", "mid", "far"):
            group = [row for row in negatives if row["kind"] == f"negative_{stratum}"]
            entry[f"reject_{stratum}"] = f"{sum(int(row['rejected']) for row in group)}/{len(group)}"
        entry["reject_overall"] = f"{sum(int(row['rejected']) for row in negatives)}/{len(negatives)}"
        summary.append(entry)
    return summary


def main() -> int:
    positives = read_csv(POSITIVE_DATASET)
    negatives = read_csv(NEGATIVE_DATASET)
    document_ids = load_document_ids()
    allowed_ids = set(document_ids.values())
    print(f"正向 {len(positives)} 道，负向 {len(negatives)} 道，候选文档 {len(document_ids)} 篇")

    detail: list[dict] = []
    stats: dict[int, tuple[int, float]] = {}
    for chunk_size in CHUNK_SIZES:
        collection, chunk_count, average_length = build_collection(chunk_size, document_ids)
        stats[chunk_size] = (chunk_count, average_length)
        print(f"chunk={chunk_size}: {chunk_count} 块，平均 {average_length:.0f} 字，开始评测…", flush=True)
        detail.extend(run(chunk_size, collection, positives, negatives, allowed_ids))

    summary = summarize(detail, stats)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    with DETAIL_OUTPUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(detail[0]))
        writer.writeheader()
        writer.writerows(detail)
    with SUMMARY_OUTPUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)

    print("\nchunk  块数  均长 | 片段Top1  片段Top3  文档Top1  文档Top3 | 拒答(总) 近 中 远 |  AUC   正/负均值距离")
    print("-" * 128)
    for row in summary:
        total = row["positive_count"]
        print(
            f"{row['chunk_size']:>5} {row['chunk_count']:>5} {row['avg_chunk_length']:>5} | "
            f"{row['clause_top1']:>3}/{total} {row['clause_top1'] / total:>6.1%}  "
            f"{row['clause_top3']:>3}/{total} {row['clause_top3'] / total:>6.1%}  "
            f"{row['doc_top1']:>3}/{total} {row['doc_top1'] / total:>6.1%}  "
            f"{row['doc_top3']:>3}/{total} {row['doc_top3'] / total:>6.1%} | "
            f"{row['reject_overall']:>7}  {row['reject_near']} {row['reject_mid']} {row['reject_far']} | "
            f"{row['auc']:.3f}  {row['pos_avg_distance']:.3f}/{row['neg_avg_distance']:.3f}"
        )
    print(f"\n明细：{DETAIL_OUTPUT}\n汇总：{SUMMARY_OUTPUT}")
    print(f"评测时间：{datetime.now().astimezone().isoformat(timespec='seconds')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
