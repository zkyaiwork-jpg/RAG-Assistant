"""Validate and materialise the 300 + 100 question set.

Positives are declared as (document, clause number, question, keyword). This builder
re-reads the indexed DOCX files, extracts the numbered clauses, and asserts that the
keyword really occurs inside the declared clause, so a wrong clause index fails loudly
instead of silently producing a wrong gold label.
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

from docx import Document

from q_batch_1 import QUESTIONS as Q1
from q_batch_2 import QUESTIONS as Q2
from q_batch_3 import QUESTIONS as Q3
from q_batch_4 import QUESTIONS as Q4
from q_batch_5 import QUESTIONS as Q5
from q_negative import NEGATIVES as NEGATIVES_1
from q_negative_2 import NEGATIVES as NEGATIVES_2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCUMENT_DIR = PROJECT_ROOT / "data" / "documents"
POSITIVE_OUTPUT = PROJECT_ROOT / "evals" / "questions_v2_positive.csv"
NEGATIVE_OUTPUT = PROJECT_ROOT / "evals" / "questions_v2_negative.csv"

CLAUSE_PATTERN = re.compile(r"^\s*第([一二三四五六七八九十百零]+)条[　\s]*(.*)$")
DIGITS = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}


def parse_number(text: str) -> int:
    if text == "十":
        return 10
    if "十" in text:
        tens, _, ones = text.partition("十")
        return (DIGITS[tens] if tens else 1) * 10 + (DIGITS[ones] if ones else 0)
    return DIGITS[text]


def load_clauses(path: Path) -> list[str]:
    document = Document(str(path))
    clauses: list[str] = []
    for paragraph in document.paragraphs:
        match = CLAUSE_PATTERN.match(paragraph.text)
        if match:
            clauses.append(match.group(2).strip())
    return clauses


def main() -> int:
    positives = [*Q1, *Q2, *Q3, *Q4, *Q5]
    documents = {path.name: path for path in DOCUMENT_DIR.glob("*.docx")}
    cache: dict[str, list[str]] = {}
    problems: list[str] = []
    rows: list[dict] = []

    seen_questions: set[str] = set()
    for index, (filename, clause_number, question, keyword) in enumerate(positives, start=1):
        if question in seen_questions:
            problems.append(f"重复问题：{question}")
        seen_questions.add(question)
        path = documents.get(filename)
        if path is None:
            problems.append(f"文档不在知识库中：{filename}")
            continue
        if filename not in cache:
            cache[filename] = load_clauses(path)
        clauses = cache[filename]
        if not 1 <= clause_number <= len(clauses):
            problems.append(f"{filename} 条款号越界：{clause_number}（共 {len(clauses)} 条）")
            continue
        clause_text = clauses[clause_number - 1]
        if keyword not in clause_text:
            problems.append(
                f"{filename} 第 {clause_number} 条不含关键词“{keyword}”，实际内容：{clause_text[:60]}"
            )
            continue
        rows.append({
            "question_id": index,
            "question": question,
            "expected_filename": filename,
            "expected_clause": clause_number,
            "expected_keyword": keyword,
            "expected_span": clause_text,
            "question_type": "clause_fact",
        })

    if problems:
        print(f"校验失败 {len(problems)} 处：")
        for problem in problems:
            print("  -", problem)
        return 1

    POSITIVE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with POSITIVE_OUTPUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    negative_rows = [
        {
            "question_id": 1000 + index,
            "question": question,
            "question_type": stratum,
            "expected_result": "no_relevant_document",
        }
        for index, (question, stratum) in enumerate([*NEGATIVES_1, *NEGATIVES_2], start=1)
    ]
    if len(negative_rows) != len({row["question"] for row in negative_rows}):
        print("负向题存在重复问题")
        return 1
    with NEGATIVE_OUTPUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(negative_rows[0]))
        writer.writeheader()
        writer.writerows(negative_rows)

    by_document: dict[str, int] = {}
    for row in rows:
        by_document[row["expected_filename"]] = by_document.get(row["expected_filename"], 0) + 1
    stratum_counts: dict[str, int] = {}
    for row in negative_rows:
        stratum_counts[row["question_type"]] = stratum_counts.get(row["question_type"], 0) + 1

    print(f"正向题 {len(rows)} 道，覆盖 {len(by_document)} 篇文档")
    print(f"负向题 {len(negative_rows)} 道，分档：{dict(sorted(stratum_counts.items()))}")
    print("每题文档分布：")
    for filename, count in sorted(by_document.items(), key=lambda item: -item[1]):
        print(f"  {filename:<32}{count:>3}")
    print(f"\n输出：{POSITIVE_OUTPUT}\n      {NEGATIVE_OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
