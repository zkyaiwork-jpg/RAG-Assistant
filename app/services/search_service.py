import chromadb
import logging
from app.core.paths import VECTOR_DB_DIR
from app.services.embedding_service import MODEL_NAME, encode_texts
from app.services import answerability_service, reranker_service

logger = logging.getLogger(__name__)

client = chromadb.PersistentClient(
    path=str(VECTOR_DB_DIR)
)


collection = client.get_or_create_collection(
    name="enterprise_documents"
)


# 拒答的三段式判定（评测见 evals/results/rejection_signals.json）：
#   最近距离 < AUTO_PASS     → 直接回答
#   AUTO_PASS ~ AUTO_REJECT  → 模型判定片段能否支撑回答
#   最近距离 >= AUTO_REJECT   → 直接拒答
# 判定器不可用时退回 FALLBACK_PASS 这条纯距离规则。
DEFAULT_DISTANCE_THRESHOLD = 0.75
AUTO_PASS_DISTANCE = 0.65
AUTO_REJECT_DISTANCE = 0.85
FALLBACK_PASS_DISTANCE = 0.70
# 候选池宽度。重排只在候选里排序，池子太窄会让正确片段根本进不了重排。
# 评测（308 道片段级题）显示：池 3 → 池 10 使片段 Top1 从 91.2% 升到 94.5%。
CANDIDATE_POOL = 10


def search_documents(
    query: str,
    top_k: int = 3,
    folder_id: int | None = None,
    file_type: str | None = None,
    allowed_document_ids: set[int] | None = None,
    distance_threshold: float = DEFAULT_DISTANCE_THRESHOLD,
    rejection_mode: str = "cascade",
):
    logger.info("Knowledge search started top_k=%s", top_k)

    if not allowed_document_ids:
        logger.info(
            "Knowledge search skipped missing_or_empty_permission_scope=true"
        )
        return {"results": []}

    n_results = max(CANDIDATE_POOL, top_k * 3)
    try:
        query_vector = encode_texts([query])
        filters = []
        if folder_id is not None:
            filters.append({"folder_id": folder_id})
        if file_type:
            filters.append({"file_type": file_type.lower()})
        filters.append({
            "document_id": {
                "$in": sorted(allowed_document_ids),
            }
        })
        where = None
        if len(filters) == 1:
            where = filters[0]
        elif filters:
            where = {"$and": filters}

        query_kwargs = {
            "query_embeddings": query_vector.tolist(),
            "n_results": n_results,
        }
        if where:
            query_kwargs["where"] = where
        result = collection.query(
            **query_kwargs
        )
    except Exception as exc:
        logger.error("Knowledge search failed top_k=%s error_type=%s", top_k, type(exc).__name__)
        raise

    authorized_candidates = []

    for doc, distance, metadata in zip(
            result["documents"][0],
            result["distances"][0],
            result["metadatas"][0]
    ):
        metadata_document_id = metadata.get("document_id")
        try:
            metadata_document_id = int(metadata_document_id)
        except (TypeError, ValueError):
            logger.warning("Knowledge search discarded invalid document_id metadata")
            continue
        if metadata_document_id not in allowed_document_ids:
            logger.warning(
                "Knowledge search discarded result outside permission scope document_id=%s",
                metadata_document_id,
            )
            continue

        authorized_candidates.append(
            {
                "content": doc,
                "distance": distance,
                "filename": metadata.get("filename"),
                "folder_id": metadata.get("folder_id"),
                "folder_name": metadata.get("folder_name"),
                "file_type": metadata.get("file_type"),
                # chunk_index 直接来自 Chroma metadata，供 RAG 返回精确引用来源。
                "chunk_index": metadata.get("chunk_index"),
                "metadata": metadata,
                "embedding_model": MODEL_NAME,
                "vector_database": "ChromaDB",
            }
        )

    if not authorized_candidates:
        logger.info("Knowledge search completed top_k=%s result_count=0", top_k)
        return {"results": []}

    best_distance = min(item["distance"] for item in authorized_candidates)

    if rejection_mode == "none":
        pass
    elif rejection_mode == "distance":
        if best_distance >= distance_threshold:
            logger.info(
                "Knowledge search rejected mode=distance best_distance=%s threshold=%s",
                round(best_distance, 4), distance_threshold,
            )
            return {"results": []}
    else:
        if best_distance >= AUTO_REJECT_DISTANCE:
            logger.info(
                "Knowledge search rejected mode=cascade stage=hard best_distance=%s",
                round(best_distance, 4),
            )
            return {"results": []}

    ranked_candidates = authorized_candidates
    try:
        ranked_candidates = reranker_service.rerank_documents(
            query,
            authorized_candidates,
        )
    except Exception as exc:
        # Rerank is an ordering enhancement. Preserve the permission-safe
        # Chroma order when loading or inference fails; never log content.
        logger.error(
            "Knowledge search rerank failed fallback=chroma_order "
            "candidate_count=%s error_type=%s",
            len(authorized_candidates),
            type(exc).__name__,
        )

    if rejection_mode == "cascade" and best_distance >= AUTO_PASS_DISTANCE:
        # 模糊带：距离不足以直接回答，也没有远到该拒答，交给模型看片段能否支撑回答。
        verdict = answerability_service.answerable(
            query,
            [item["content"] for item in ranked_candidates[:3]],
        )
        if verdict is False:
            logger.info(
                "Knowledge search rejected mode=cascade stage=judge best_distance=%s",
                round(best_distance, 4),
            )
            return {"results": []}
        if verdict is None and best_distance >= FALLBACK_PASS_DISTANCE:
            logger.info(
                "Knowledge search rejected mode=cascade stage=fallback best_distance=%s",
                round(best_distance, 4),
            )
            return {"results": []}

    results = ranked_candidates[:top_k]

    logger.info(
        "Knowledge search completed top_k=%s result_count=%s best_distance=%s mode=%s",
        top_k, len(results), round(best_distance, 4), rejection_mode,
    )
    return {
        "results": results
    }
