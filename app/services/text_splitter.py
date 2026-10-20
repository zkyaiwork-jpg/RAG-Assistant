"""按行聚合的定长切片。

chunk_size=100 来自评测结论：在 29 篇 / 308 道片段级正向题的对照实验中，
100 字切片的片段 Top1 比 200 字高 10.4 个百分点、负向分离度（AUC）最高，
详见 evals/results/rag_chunk_size_v2_summary.csv。
"""


def split_text(
        text: str,
        chunk_size: int = 100
):
    chunks = []

    current_chunk = ""


    paragraphs = text.split("\n")


    for paragraph in paragraphs:

        paragraph = paragraph.strip()


        if not paragraph:
            continue


        # 如果当前块加上新段落没有超过限制
        if len(current_chunk) + len(paragraph) < chunk_size:

            current_chunk += paragraph + "\n"


        else:

            # 保存当前块
            if current_chunk:
                chunks.append(current_chunk)


            # 开始新的块
            current_chunk = paragraph + "\n"


    # 保存最后一个块
    if current_chunk:
        chunks.append(current_chunk)


    return chunks
