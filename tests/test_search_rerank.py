from types import SimpleNamespace


class StaticCollection:
    def __init__(self, documents, distances, metadatas):
        self.documents = documents
        self.distances = distances
        self.metadatas = metadatas
        self.query_calls = []

    def query(self, **kwargs):
        self.query_calls.append(kwargs)
        return {
            "documents": [self.documents],
            "distances": [self.distances],
            "metadatas": [self.metadatas],
        }


def _prepare_search(monkeypatch, collection):
    from app.services import search_service

    monkeypatch.setattr(search_service, "collection", collection)
    monkeypatch.setattr(
        search_service,
        "encode_texts",
        lambda values: SimpleNamespace(tolist=lambda: [[0.0, 0.0]]),
    )
    return search_service


def test_search_calls_reranker_after_permission_check_and_before_threshold(monkeypatch):
    collection = StaticCollection(
        documents=["within threshold", "above threshold"],
        distances=[0.2, 0.9],
        metadatas=[
            {"document_id": 1, "filename": "first.docx"},
            {"document_id": 2, "filename": "second.docx"},
        ],
    )
    search_service = _prepare_search(monkeypatch, collection)
    captured = {}

    def recording_rerank(question, documents):
        captured["question"] = question
        captured["documents"] = documents
        return [
            {**document, "rerank_score": float(index)}
            for index, document in enumerate(reversed(documents), start=1)
        ]

    monkeypatch.setattr(
        search_service.reranker_service,
        "rerank_documents",
        recording_rerank,
    )

    result = search_service.search_documents(
        "policy question",
        allowed_document_ids={1, 2},
    )

    assert captured["question"] == "policy question"
    assert [item["filename"] for item in captured["documents"]] == [
        "first.docx",
        "second.docx",
    ]
    # 阈值只用于整体拒答：候选池最近距离 0.2 通过后，重排结果整体返回，
    # 距离 0.9 的同问题候选不会再被单独剔除（伪造的重排器按倒序返回，不做排序）。
    assert [item["filename"] for item in result["results"]] == [
        "second.docx",
        "first.docx",
    ]
    assert result["results"][1]["rerank_score"] == 2.0


def test_search_returns_reranked_order_and_preserves_existing_fields(monkeypatch):
    collection = StaticCollection(
        documents=["original first", "more relevant"],
        distances=[0.1, 0.2],
        metadatas=[
            {"document_id": 1, "filename": "original.docx", "chunk_index": 0},
            {"document_id": 2, "filename": "correct.docx", "chunk_index": 3},
        ],
    )
    search_service = _prepare_search(monkeypatch, collection)

    def reverse_with_scores(question, documents):
        return [
            {**documents[1], "rerank_score": 0.95},
            {**documents[0], "rerank_score": 0.10},
        ]

    monkeypatch.setattr(
        search_service.reranker_service,
        "rerank_documents",
        reverse_with_scores,
    )

    results = search_service.search_documents(
        "bad case",
        allowed_document_ids={1, 2},
    )["results"]

    assert [item["filename"] for item in results] == [
        "correct.docx",
        "original.docx",
    ]
    assert results[0]["content"] == "more relevant"
    assert results[0]["distance"] == 0.2
    assert results[0]["chunk_index"] == 3
    assert results[0]["metadata"]["document_id"] == 2
    assert results[0]["embedding_model"] == "BAAI/bge-small-zh-v1.5"
    assert results[0]["vector_database"] == "ChromaDB"
    assert results[0]["rerank_score"] == 0.95


def test_unauthorized_chroma_result_never_reaches_reranker(monkeypatch):
    collection = StaticCollection(
        documents=["allowed content", "forbidden secret content"],
        distances=[0.2, 0.1],
        metadatas=[
            {"document_id": 1, "filename": "allowed.docx"},
            {"document_id": 999, "filename": "forbidden.docx"},
        ],
    )
    search_service = _prepare_search(monkeypatch, collection)
    captured = {}

    def recording_rerank(question, documents):
        captured["documents"] = documents
        return [{**documents[0], "rerank_score": 0.5}]

    monkeypatch.setattr(
        search_service.reranker_service,
        "rerank_documents",
        recording_rerank,
    )

    results = search_service.search_documents(
        "policy",
        allowed_document_ids={1},
    )["results"]

    assert [item["filename"] for item in captured["documents"]] == ["allowed.docx"]
    assert [item["filename"] for item in results] == ["allowed.docx"]
    assert "forbidden secret content" not in [
        item["content"] for item in captured["documents"]
    ]


def test_reranker_failure_falls_back_to_original_chroma_order(monkeypatch, caplog):
    collection = StaticCollection(
        documents=["first", "second", "filtered"],
        distances=[0.2, 0.3, 0.9],
        metadatas=[
            {"document_id": 1, "filename": "first.docx"},
            {"document_id": 2, "filename": "second.docx"},
            {"document_id": 3, "filename": "filtered.docx"},
        ],
    )
    search_service = _prepare_search(monkeypatch, collection)

    def failing_rerank(question, documents):
        raise RuntimeError("sensitive internal failure")

    monkeypatch.setattr(
        search_service.reranker_service,
        "rerank_documents",
        failing_rerank,
    )

    results = search_service.search_documents(
        "policy",
        allowed_document_ids={1, 2, 3},
    )["results"]

    assert [item["filename"] for item in results] == ["first.docx", "second.docx", "filtered.docx"]
    assert all("rerank_score" not in item for item in results)
    assert "fallback=chroma_order" in caplog.text
    assert "sensitive internal failure" not in caplog.text


def test_search_queries_a_wider_candidate_pool_than_top_k(monkeypatch):
    collection = StaticCollection(
        documents=["a"],
        distances=[0.2],
        metadatas=[{"document_id": 1, "filename": "a.docx"}],
    )
    search_service = _prepare_search(monkeypatch, collection)
    monkeypatch.setattr(
        search_service.reranker_service,
        "rerank_documents",
        lambda question, documents: [{**documents[0], "rerank_score": 1.0}],
    )

    search_service.search_documents("policy", top_k=3, allowed_document_ids={1})

    assert collection.query_calls[0]["n_results"] == search_service.CANDIDATE_POOL
    assert collection.query_calls[0]["n_results"] > 3


def test_search_rejects_when_best_candidate_exceeds_threshold(monkeypatch):
    collection = StaticCollection(
        documents=["far one", "far two"],
        distances=[0.91, 0.95],
        metadatas=[
            {"document_id": 1, "filename": "one.docx"},
            {"document_id": 2, "filename": "two.docx"},
        ],
    )
    search_service = _prepare_search(monkeypatch, collection)
    calls = []

    def recording_rerank(question, documents):
        calls.append(documents)
        return documents

    monkeypatch.setattr(search_service.reranker_service, "rerank_documents", recording_rerank)

    result = search_service.search_documents("unanswerable", allowed_document_ids={1, 2})

    assert result["results"] == []
    # 硬拒答阶段早于重排，避免对无关候选做无谓推理。
    assert calls == []


def test_cascade_asks_judge_only_in_the_ambiguous_band(monkeypatch):
    collection = StaticCollection(
        documents=["borderline content"],
        distances=[0.78],
        metadatas=[{"document_id": 1, "filename": "border.docx"}],
    )
    search_service = _prepare_search(monkeypatch, collection)
    monkeypatch.setattr(
        search_service.reranker_service,
        "rerank_documents",
        lambda question, documents: [{**documents[0], "rerank_score": 1.0}],
    )
    judged = []

    def fake_answerable(question, chunks, database=None):
        judged.append((question, chunks))
        return True

    monkeypatch.setattr(search_service.answerability_service, "answerable", fake_answerable)

    results = search_service.search_documents("borderline question", allowed_document_ids={1})["results"]

    assert judged and judged[0][0] == "borderline question"
    assert [item["filename"] for item in results] == ["border.docx"]


def test_cascade_rejects_when_judge_says_no(monkeypatch):
    collection = StaticCollection(
        documents=["unrelated text"],
        distances=[0.78],
        metadatas=[{"document_id": 1, "filename": "unrelated.docx"}],
    )
    search_service = _prepare_search(monkeypatch, collection)
    monkeypatch.setattr(
        search_service.reranker_service,
        "rerank_documents",
        lambda question, documents: [{**documents[0], "rerank_score": 1.0}],
    )
    monkeypatch.setattr(search_service.answerability_service, "answerable", lambda *args, **kwargs: False)

    assert search_service.search_documents("no answer", allowed_document_ids={1})["results"] == []


def test_cascade_falls_back_to_distance_when_judge_unavailable(monkeypatch):
    collection = StaticCollection(
        documents=["maybe relevant"],
        distances=[0.66],
        metadatas=[{"document_id": 1, "filename": "maybe.docx"}],
    )
    search_service = _prepare_search(monkeypatch, collection)
    monkeypatch.setattr(
        search_service.reranker_service,
        "rerank_documents",
        lambda question, documents: [{**documents[0], "rerank_score": 1.0}],
    )
    monkeypatch.setattr(search_service.answerability_service, "answerable", lambda *args, **kwargs: None)

    # 0.66 落在模糊带但在兜底阈值 0.70 以内：判定器不可用时仍然回答。
    assert search_service.search_documents("q", allowed_document_ids={1})["results"]

    collection.distances = [0.74]
    assert search_service.search_documents("q", allowed_document_ids={1})["results"] == []


def test_auto_pass_band_skips_the_judge(monkeypatch):
    collection = StaticCollection(
        documents=["very close"],
        distances=[0.30],
        metadatas=[{"document_id": 1, "filename": "close.docx"}],
    )
    search_service = _prepare_search(monkeypatch, collection)
    monkeypatch.setattr(
        search_service.reranker_service,
        "rerank_documents",
        lambda question, documents: [{**documents[0], "rerank_score": 1.0}],
    )
    judged = []
    monkeypatch.setattr(
        search_service.answerability_service,
        "answerable",
        lambda *args, **kwargs: judged.append(1) or True,
    )

    assert search_service.search_documents("q", allowed_document_ids={1})["results"]
    assert judged == []
