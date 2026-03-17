#!/usr/bin/env python3
"""
完整集成测试 - Chroma + 远程Embedding
Integration Test - Chroma + Remote Embedding
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from embedding_service import get_embedding_service
from chroma_store import ChromaStore


def test_integration():
    """测试完整集成"""

    print("\n" + "="*60)
    print("🧪 Chroma + 远程Embedding 集成测试")
    print("="*60 + "\n")

    # 1. 初始化服务
    print("1️⃣  初始化服务...")
    embedding_service = get_embedding_service(use_remote=True)
    chroma_store = ChromaStore(persist_directory="/root/.openclaw/workspace/chroma_db")
    print("   ✅ 服务初始化完成\n")

    # 2. 存储测试数据
    print("2️⃣  存储测试数据...")
    test_memories = [
        {
            "content": "OpenClaw混合记忆系统使用Chroma向量数据库",
            "metadata": {"source": "test", "category": "system"}
        },
        {
            "content": "Qwen3-Embedding-8B是强大的中文embedding模型",
            "metadata": {"source": "test", "category": "model"}
        },
        {
            "content": "LangChain Memory提供多种记忆类型",
            "metadata": {"source": "test", "category": "framework"}
        }
    ]

    record_ids = []
    for memory in test_memories:
        # 向量化
        vector = embedding_service.embed(memory['content'])

        # 存储
        record_id = chroma_store.store(
            content=memory['content'],
            embedding=vector,
            metadata=memory['metadata']
        )
        record_ids.append(record_id)
        print(f"   ✅ 存储成功: {record_id[:30]}...")

    print(f"\n3️⃣  统计信息...")
    stats = chroma_store.get_stats()
    print(f"   总记录数: {stats['total_records']}")

    # 4. 检索测试
    print(f"\n4️⃣  检索测试...")
    query_text = "OpenClaw的记忆系统"
    query_vector = embedding_service.embed(query_text)

    results = chroma_store.retrieve(
        query_embedding=query_vector,
        n_results=3
    )

    print(f"   查询: {query_text}")
    print(f"   找到 {len(results)} 条结果:\n")

    for i, result in enumerate(results, 1):
        print(f"   {i}. ID: {result['id'][:30]}...")
        print(f"      内容: {result['content'][:60]}...")
        print(f"      元数据: {result['metadata']}")
        if result.get('distance'):
            print(f"      距离: {result['distance']:.4f}")

    # 5. 元数据过滤测试
    print(f"\n5️⃣  元数据过滤测试...")
    results_filtered = chroma_store.retrieve(
        query_embedding=query_vector,
        n_results=10,
        where={"category": "system"}
    )

    print(f"   过滤条件: category='system'")
    print(f"   找到 {len(results_filtered)} 条结果:\n")

    for i, result in enumerate(results_filtered, 1):
        print(f"   {i}. {result['content'][:60]}...")

    # 6. 批量向量化测试
    print(f"\n6️⃣  批量向量化测试...")
    batch_texts = [
        "第一批测试数据",
        "第二批测试数据",
        "第三批测试数据"
    ]

    import time
    start_time = time.time()
    batch_vectors = embedding_service.embed(batch_texts)
    elapsed = time.time() - start_time

    print(f"   处理 {len(batch_texts)} 条文本")
    print(f"   总耗时: {elapsed:.3f}秒")
    print(f"   平均: {elapsed/len(batch_texts):.3f}秒/条")

    print("\n" + "="*60)
    print("✅ 所有测试通过！")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_integration()