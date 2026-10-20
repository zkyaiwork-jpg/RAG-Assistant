"""判定检索片段里是否真的包含回答问题所需的信息。

用于拒答的第二层：当最近候选的距离落在"模糊带"（既不够近也不够远）时，
由模型直接判断片段能否支撑回答。这一层只在模糊带触发，绝大多数请求不会
产生额外调用。

失败原则是"降级而非中断"：模型未配置、网络异常或输出不可解析时返回 None，
由调用方按更保守的距离规则处理，绝不因为判定器不可用而让检索直接失败。
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = "你是检索结果判定器。只能输出一个字：有 或 无。"
MAX_CHUNK_CHARS = 400
MAX_CHUNKS = 3

USER_PROMPT = (
    "问题：{question}\n\n"
    "检索片段：\n{chunks}\n\n"
    "这些片段中是否包含回答该问题所需的具体信息？只输出“有”或“无”。"
)


def _resolve_config(database: Session | None):
    from app.services.model_config_service import resolve_runtime_model_config

    if database is not None:
        return resolve_runtime_model_config(database)

    from app.database.database import SessionLocal

    with SessionLocal() as session:
        return resolve_runtime_model_config(session)


def answerable(
    question: str,
    chunks: list[str],
    database: Session | None = None,
) -> bool | None:
    """Return True/False when the model judges the chunks, None when unavailable."""
    texts = [text.strip()[:MAX_CHUNK_CHARS] for text in chunks[:MAX_CHUNKS] if text and text.strip()]
    if not question.strip() or not texts:
        return None

    try:
        from app.services.model_config_service import create_model_client

        config = _resolve_config(database)
        client = create_model_client(config)
        body = "\n\n".join(f"[{index + 1}] {text}" for index, text in enumerate(texts))
        response = client.chat.completions.create(
            model=config.model_name,
            temperature=0,
            max_tokens=4,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT.format(question=question.strip(), chunks=body)},
            ],
        )
        answer = (response.choices[0].message.content or "").strip()
    except Exception as exc:
        logger.warning(
            "Answerability check unavailable error_type=%s",
            type(exc).__name__,
        )
        return None

    if answer.startswith("无"):
        return False
    if answer.startswith("有"):
        return True
    logger.warning("Answerability check returned unexpected value")
    return None
