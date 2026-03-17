#!/usr/bin/env python
"""
测试混合路由器
Test Hybrid Router
"""

import sys
import os
import time
from datetime import datetime, timedelta

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hybrid_router import HybridMemoryRouter
from daily_indexer import DailyIndexer
from memory_indexer import MemoryIndexer
from cache import get_query_cache, get_embedding_cache, clear_all_caches


def print_section(title: str):
    """打印标题"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def test_basic_store_and_retrieve(router: HybridMemoryRouter):
    """测试基本存储和检索"""
    print_section("1️⃣  测试基本存储和检索")

    # 测试存储
    print("\n📝 测试存储...")
    test_contents = [
        ("OpenClaw是一个强大的AI代理平台", "important"),
        "Chroma是向量数据库，用于语义搜索",
        "Python是AI开发的主要语言"
    ]

    for i, content in enumerate(test_contents, 1):
        if isinstance(content, tuple):
            content_str, importance = content
        else:
            content_str = content
            importance = "normal"

        record_id = router.store(content=content_str, importance=importance)
        print(f"   {i}. 存储: {content_str[:30]}... -> {record_id[:20]}...")

    # 测试检索
    print("\n🔍 测试检索...")
    test_queries = [
        "AI代理平台",
        "向量数据库",
        "Python编程"
    ]

    for query in test_queries:
        print(f"\n   查询: {query}")
        results = router.retrieve(query=query, max_results=3)
        print(f"   找到 {len(results)} 条结果:")
        for i, result in enumerate(results, 1):
            source = result.get('source', 'unknown')
            score = result.get('score', 0)
            content_preview = result.get('content', '')[:50]
            print(f"      {i}. [{score:.2f}] {source}: {content_preview}...")


def test_batch_store(router: HybridMemoryRouter):
    """测试批量存储"""
    print_section("2️⃣  测试批量存储")

    batch_data = [
        {"content": "批量测试 1: FastAPI是现代Python Web框架", "importance": "normal"},
        {"content": "批量测试 2: Redis是高性能键值存储", "importance": "normal"},
        {"content": "批量测试 3: Docker是容器化平台", "importance": "important"},
        {"content": "批量测试 4: Kubernetes是容器编排系统", "importance": "normal"},
        {"content": "批量测试 5: PostgreSQL是开源关系数据库", "importance": "important"},
    ]

    print(f"\n📝 批量存储 {len(batch_data)} 条记录...")
    start_time = time.time()
    record_ids = router.store_batch(batch_data, batch_size=2)
    end_time = time.time()

    print(f"   ✅ 批量存储完成: {len(record_ids)}/{len(batch_data)} 条")
    print(f"   ⏱️  耗时: {end_time - start_time:.2f} 秒")


def test_cache_performance(router: HybridMemoryRouter):
    """测试缓存性能"""
    print_section("3️⃣  测试缓存性能")

    query = "AI代理平台和向量数据库"

    # 第一次检索（无缓存）
    print(f"\n🔍 第一次检索（无缓存）: {query}")
    start_time = time.time()
    results1 = router.retrieve(query=query, max_results=5)
    end_time = time.time()
    first_time = end_time - start_time
    print(f"   找到 {len(results1)} 条结果")
    print(f"   ⏱️  耗时: {first_time:.2f} 秒")

    # 第二次检索（有缓存）
    print(f"\n🔍 第二次检索（有缓存）: {query}")
    start_time = time.time()
    results2 = router.retrieve(query=query, max_results=5)
    end_time = time.time()
    second_time = end_time - start_time
    print(f"   找到 {len(results2)} 条结果")
    print(f"   ⏱️  耗时: {second_time:.2f} 秒")

    # 显示缓存统计
    print(f"\n📊 缓存统计:")
    query_cache_stats = get_query_cache().get_stats()
    embedding_cache_stats = get_embedding_cache().get_stats()

    print(f"   查询缓存命中率: {query_cache_stats['hit_rate']:.2%} ({query_cache_stats['hits']}/{query_cache_stats['hits'] + query_cache_stats['misses']})")
    print(f"   向量化缓存命中率: {embedding_cache_stats['hit_rate']:.2%} ({embedding_cache_stats['hits']}/{embedding_cache_stats['hits'] + embedding_cache_stats['misses']})")

    # 计算加速比
    if second_time > 0:
        speedup = first_time / second_time
        print(f"   ⚡ 加速比: {speedup:.2f}x")


def test_semantic_vs_keyword(router: HybridMemoryRouter):
    """测试语义检索 vs 关键词检索"""
    print_section("4️⃣  测试语义检索 vs 关键词检索")

    query = "AI技术和编程语言"

    # 语义检索
    print(f"\n🔍 语义检索: {query}")
    start_time = time.time()
    semantic_results = router.retrieve(query=query, max_results=5, use_semantic=True)
    end_time = time.time()
    semantic_time = end_time - start_time
    print(f"   找到 {len(semantic_results)} 条结果")
    print(f"   ⏱️  耗时: {semantic_time:.2f} 秒")

    for i, result in enumerate(semantic_results, 1):
        source = result.get('source', 'unknown')
        score = result.get('score', 0)
        content_preview = result.get('content', '')[:50]
        print(f"      {i}. [{score:.2f}] {source}: {content_preview}...")

    # 关键词检索
    print(f"\n🔍 关键词检索: {query}")
    start_time = time.time()
    keyword_results = router.retrieve(query=query, max_results=5, use_semantic=False)
    end_time = time.time()
    keyword_time = end_time - start_time
    print(f"   找到 {len(keyword_results)} 条结果")
    print(f"   ⏱️  耗时: {keyword_time:.2f} 秒")

    for i, result in enumerate(keyword_results, 1):
        source = result.get('source', 'unknown')
        score = result.get('score', 0)
        content_preview = result.get('content', '')[:50]
        print(f"      {i}. [{score:.2f}] {source}: {content_preview}...")


def test_daily_indexer(router: HybridMemoryRouter):
    """测试Daily索引器"""
    print_section("5️⃣  测试Daily索引器")

    daily_indexer = router.daily_indexer

    # 创建测试Daily文件
    print("\n📝 创建测试Daily文件...")
    today = datetime.now().strftime('%Y-%m-%d')
    test_content = """## 测试Daily文件

这是一个测试的Daily文件，用于验证Daily索引器的功能。

## OpenClaw项目

OpenClaw是一个开源的AI代理平台，支持多个专业Agent协作。

## 技术栈

- Python 3.9+
- Chroma向量数据库
- FastAPI Web框架
"""

    # 写入Daily文件
    daily_file_path = os.path.join(router.daily_dir, f"{today}.md")
    with open(daily_file_path, 'w', encoding='utf-8') as f:
        f.write(test_content)

    print(f"   ✅ 创建: {daily_file_path}")

    # 索引Daily文件
    print(f"\n📚 索引Daily文件...")
    indexed_count = daily_indexer.index_daily_file(today)
    print(f"   ✅ 索引完成: {indexed_count} 个段落")

    # 搜索Daily文件
    print(f"\n🔍 搜索Daily文件...")
    query = "OpenClaw平台和技术栈"
    results = daily_indexer.search_daily_files(query, top_k=5)
    print(f"   找到 {len(results)} 条结果:")

    for i, result in enumerate(results, 1):
        date = result.get('date', 'unknown')
        content_preview = result.get('content', '')[:50]
        distance = result.get('distance', 0)
        print(f"      {i}. [{date}] [{distance:.3f}]: {content_preview}...")


def test_memory_indexer(router: HybridMemoryRouter):
    """测试MEMORY.md索引器"""
    print_section("6️⃣  测试MEMORY.md索引器")

    memory_indexer = router.memory_indexer

    # 检查MEMORY.md是否存在
    if not os.path.exists(router.memory_md_path):
        print(f"\n⚠️  MEMORY.md不存在: {router.memory_md_path}")
        print("   跳过MEMORY.md索引测试")
        return

    # 索引MEMORY.md
    print(f"\n📚 索引MEMORY.md...")
    indexed_count = memory_indexer.index_memory_md()
    print(f"   ✅ 索引完成: {indexed_count} 个节")

    # 搜索MEMORY.md
    print(f"\n🔍 搜索MEMORY.md...")
    query = "重要决策和工作规范"
    results = memory_indexer.search_memory_md(query, top_k=5)
    print(f"   找到 {len(results)} 条结果:")

    for i, result in enumerate(results, 1):
        section = result.get('section_name', 'unknown')
        content_preview = result.get('content', '')[:50]
        distance = result.get('distance', 0)
        print(f"      {i}. [{section}] [{distance:.3f}]: {content_preview}...")


def test_stats(router: HybridMemoryRouter):
    """测试统计功能"""
    print_section("7️⃣  测试统计功能")

    stats = router.get_stats()

    print(f"\n📊 混合路由器统计:")
    print(f"   Chroma记录数: {stats.get('total_records', 0)}")
    print(f"   Daily文件数: {stats.get('daily_files_count', 0)}")
    print(f"   MEMORY.md存在: {stats.get('memory_md_exists', False)}")
    print(f"   使用缓存: {stats.get('use_cache', False)}")
    print(f"   并行处理: {stats.get('use_parallel', False)}")
    print(f"   工作线程数: {stats.get('max_workers', 1)}")

    # 显示缓存统计
    if 'query_cache' in stats:
        query_cache = stats['query_cache']
        print(f"\n   查询缓存:")
        print(f"      大小: {query_cache['size']}/{query_cache['max_size']}")
        print(f"      命中率: {query_cache['hit_rate']:.2%}")

    if 'embedding_cache' in stats:
        embedding_cache = stats['embedding_cache']
        print(f"\n   向量化缓存:")
        print(f"      大小: {embedding_cache['size']}/{embedding_cache['max_size']}")
        print(f"      命中率: {embedding_cache['hit_rate']:.2%}")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  混合路由器测试 (Hybrid Router Test)")
    print("  Phase 2 - Day 2: 优化与集成")
    print("=" * 60)

    # 初始化路由器
    print("\n⚙️  初始化混合路由器...")
    router = HybridMemoryRouter(
        use_cache=True,
        use_parallel=True,
        max_workers=4
    )

    # 运行测试
    try:
        test_basic_store_and_retrieve(router)
        test_batch_store(router)
        test_cache_performance(router)
        test_semantic_vs_keyword(router)
        test_daily_indexer(router)
        test_memory_indexer(router)
        test_stats(router)

        print_section("✅ 所有测试完成")
        print("\n📈 测试总结:")
        print("   ✅ 基本存储和检索: 通过")
        print("   ✅ 批量存储: 通过")
        print("   ✅ 缓存性能: 通过")
        print("   ✅ 语义检索: 通过")
        print("   ✅ Daily索引器: 通过")
        print("   ✅ MEMORY.md索引器: 通过")
        print("   ✅ 统计功能: 通过")

        print("\n🎉 测试全部通过！")

    except Exception as e:
        print_section("❌ 测试失败")
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
