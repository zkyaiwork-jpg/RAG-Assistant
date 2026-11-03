from pathlib import Path


PROJECT_ROOT = Path(__file__).parents[1]


def test_search_preview_uses_clean_content_and_exposes_no_raw_chunk_panel():
    view = (PROJECT_ROOT / "frontend" / "src" / "views" / "SearchView.vue").read_text(
        encoding="utf-8"
    )

    assert "function cleanContent" in view
    assert "{{ cleanContent(item.content) }}" in view
    # 技术详情面板已按产品要求移除：检索卡片不再直接渲染原始 chunk 与距离明细。
    assert "原始Chunk内容" not in view
    assert "查看技术详情" not in view
    assert "{{ item.content }}" not in view


def test_rag_prompt_still_prohibits_internal_and_retrieval_markers():
    rag_service = (PROJECT_ROOT / "app" / "services" / "rag_service.py").read_text(
        encoding="utf-8"
    )

    assert "RULE 编号、章节编号" in rag_service
    assert "不要输出 Chunk 编号" in rag_service
    assert "不要描述向量检索过程" in rag_service
