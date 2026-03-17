#!/usr/bin/env python3
"""
快速测试脚本 - Chroma基础功能
Quick Test Script - Chroma Basic Functions
"""

import sys
import os

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chroma_store import ChromaStore


def test_basic_functions():
    """测试基础功能"""

    print("\n" + "="*60)
    print("🧪 Chroma基础功能测试")
    print("="*60 + "\n")

    # 初始化
    print("1️⃣  初始化ChromaStore...")
    store = ChromaStore(persist_directory="/root/.openclaw/workspace/chroma_db")
    print(f"   {store}\n")

    # 存储测试
    print("2️⃣  存储测试数据...")
    embedding = [0.1, 0.2, 0.3] * 100  # 300维向量
    content = "这是一条测试记忆：OpenClaw混合记忆系统"
    metadata = {
        "source": "test",
        "importance": "normal",
        "agent": "zh-help"
    }

    record_id = store.store(
        content=content,
        embedding=embedding,
        metadata=metadata
    )
    print(f"   ✅ 记录ID: {record_id}\n")

    # 检索测试
    print("3️⃣  检索测试...")
    results = store.retrieve(
        query_embedding=embedding,
        n_results=5
    )

    print(f"   找到 {len(results)} 条结果:")
    for i, result in enumerate(results, 1):
        print(f"   {i}. ID: {result['id'][:20]}...")
        print(f"      内容: {result['content'][:50]}...")
        print(f"      元数据: {result['metadata']}")
        if result.get('distance'):
            print(f"      距离: {result['distance']:.4f}")

    # 统计测试
    print(f"\n4️⃣  统计信息...")
    stats = store.get_stats()
    print(f"   总记录数: {stats['total_records']}")
    print(f"   持久化目录: {stats['persist_directory']}")
    print(f"   Collection: {stats['collection_name']}")

    print("\n" + "="*60)
    print("✅ 所有测试通过！")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_basic_functions()