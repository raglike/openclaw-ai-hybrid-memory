#!/usr/bin/env python3
"""
性能基准测试: 图谱模块
验证存储 < 20MB，延迟 < 100ms
"""

import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph_adapter import GraphAdapter
from triple_extractor import TripleExtractor
from graph_config import GRAPH_CONFIG
import numpy as np


def benchmark_graph_adapter():
    """GraphAdapter 性能测试"""
    print("\n" + "=" * 60)
    print("GraphAdapter 性能基准测试")
    print("=" * 60)

    config = {
        "enabled": True,
        "embedding_dim": 64,
        "codebook_size": 256,
        "storage_path": "./graph_cache",
    }

    graph = GraphAdapter(config)
    graph.initialize()

    # 生成测试三元组
    entities = [f"Entity_{i}" for i in range(100)]
    relations = ["使用", "开发", "设计", "管理", "协作", "属于", "集成"]
    triplets = []
    for i in range(500):
        e1 = entities[i % len(entities)]
        e2 = entities[(i + 1) % len(entities)]
        r = relations[i % len(relations)]
        triplets.append((e1, r, e2))

    # 添加三元组
    print(f"\n[1] 添加 {len(triplets)} 个三元组...")
    start = time.perf_counter()
    graph.add_triplets(triplets)
    add_time = time.perf_counter() - start
    print(f"    添加时间: {add_time*1000:.2f}ms")

    # 查询性能
    print(f"\n[2] 查询性能测试 (100次查询)...")
    query_entities = entities[:20]
    start = time.perf_counter()
    for _ in range(100):
        for entity in query_entities:
            graph.query_related(entity, top_k=10)
    query_time = time.perf_counter() - start
    avg_query_ms = (query_time / 100) * 1000
    print(f"    总时间: {query_time*1000:.2f}ms")
    print(f"    平均延迟: {avg_query_ms:.2f}ms")

    # 存储大小
    print(f"\n[3] 存储大小测试...")
    storage_bytes = graph.get_storage_size()
    storage_mb = storage_bytes / (1024 * 1024)
    print(f"    存储大小: {storage_mb:.4f} MB")

    # 预测性能
    print(f"\n[4] 预测性能测试...")
    start = time.perf_counter()
    for _ in range(50):
        graph.predict_tail("Entity_0", "使用", top_k=5)
    predict_time = time.perf_counter() - start
    avg_predict_ms = (predict_time / 50) * 1000
    print(f"    平均延迟: {avg_predict_ms:.2f}ms")

    # 保存测试
    print(f"\n[5] 保存/加载测试...")
    save_path = "./graph_cache/benchmark_graph.pkl"
    start = time.perf_counter()
    graph.save(save_path)
    save_time = time.perf_counter() - start
    print(f"    保存时间: {save_time*1000:.2f}ms")

    start = time.perf_counter()
    graph.load(save_path)
    load_time = time.perf_counter() - start
    print(f"    加载时间: {load_time*1000:.2f}ms")

    # 清理
    if os.path.exists(save_path):
        os.remove(save_path)
    if os.path.exists(save_path + ".graph"):
        os.remove(save_path + ".graph")

    # 验收检查
    print("\n" + "=" * 60)
    print("验收标准检查")
    print("=" * 60)
    storage_pass = storage_mb < 20
    latency_pass = avg_query_ms < 100
    print(f"  存储 < 20MB: {storage_mb:.4f} MB {'✅ PASS' if storage_pass else '❌ FAIL'}")
    print(f"  延迟 < 100ms: {avg_query_ms:.2f}ms {'✅ PASS' if latency_pass else '❌ FAIL'}")

    return {
        "storage_mb": storage_mb,
        "avg_query_ms": avg_query_ms,
        "avg_predict_ms": avg_predict_ms,
        "storage_pass": storage_pass,
        "latency_pass": latency_pass,
    }


def benchmark_triple_extractor():
    """TripleExtractor 性能测试"""
    print("\n" + "=" * 60)
    print("TripleExtractor 性能基准测试")
    print("=" * 60)

    extractor = TripleExtractor()

    # 测试文本
    test_texts = [
        "@助管理@文案团队，@文案撰写AI资讯，使用Python和Chroma",
        "@运营专注数据分析，@开开发视频制作功能，使用Playwright",
        "西部证券投标AI知识库项目，团队使用FFmpeg进行视频编码",
        "@测试负责质量保障，@产品分析用户需求，@小U设计UI界面",
    ]

    # 重复文本以增加处理量
    full_text = " ".join(test_texts * 25)  # 100条文本

    print(f"\n[1] 提取性能测试 ({len(test_texts) * 25} 条文本)...")
    start = time.perf_counter()
    for _ in range(10):
        triples = extractor.extract_from_text(full_text)
    extract_time = time.perf_counter() - start
    avg_extract_ms = (extract_time / 10) * 1000
    print(f"    提取时间: {avg_extract_ms:.2f}ms")
    print(f"    提取三元组数: {len(triples)}")

    # 验收
    print("\n" + "=" * 60)
    print("验收标准检查")
    print("=" * 60)
    print(f"  提取延迟 < 100ms: {avg_extract_ms:.2f}ms {'✅ PASS' if avg_extract_ms < 100 else '❌ FAIL'}")

    return {
        "avg_extract_ms": avg_extract_ms,
        "triples_count": len(triples),
    }


def benchmark_integration():
    """集成性能测试"""
    print("\n" + "=" * 60)
    print("HybridRouter 图谱模块集成测试")
    print("=" * 60)

    from hybrid_router import HybridMemoryRouter

    router = HybridMemoryRouter(
        chroma_path="/tmp/perf_chroma",
        daily_dir="/tmp/perf_daily",
        memory_md_path="/tmp/perf_memory.md",
        use_cache=False,
        use_parallel=False
    )

    # 清空图谱
    if router.graph_adapter:
        router.graph_adapter.clear()

    # 存储测试
    print("\n[1] 存储性能测试 (20条记忆)...")
    contents = [
        f"@助管理@文案团队，使用{chr(65+i%26)}工具进行工作" for i in range(20)
    ]

    start = time.perf_counter()
    for content in contents:
        router.store(content, importance="normal")
    store_time = time.perf_counter() - start
    avg_store_ms = (store_time / 20) * 1000
    print(f"    平均存储延迟: {avg_store_ms:.2f}ms")

    # 检索测试
    print("\n[2] 检索性能测试 (20次查询)...")
    queries = [
        "@助管理 @文案",
        "使用工具 工作",
        "AI 资讯",
    ]

    start = time.perf_counter()
    for _ in range(20):
        for query in queries:
            router.retrieve(query, max_results=10)
    retrieve_time = time.perf_counter() - start
    avg_retrieve_ms = (retrieve_time / 60) * 1000
    print(f"    平均检索延迟: {avg_retrieve_ms:.2f}ms")

    # 图谱统计
    if router.graph_adapter:
        stats = router.graph_adapter.get_stats()
        print(f"\n[3] 图谱统计:")
        print(f"    实体数: {stats['entity_count']}")
        print(f"    三元组数: {stats['triplet_count']}")
        print(f"    存储大小: {stats['storage_mb']:.4f} MB")

    # 清理
    import shutil
    for path in ["/tmp/perf_chroma", "/tmp/perf_daily"]:
        if os.path.exists(path):
            shutil.rmtree(path)
    if os.path.exists("/tmp/perf_memory.md"):
        os.remove("/tmp/perf_memory.md")

    # 验收
    print("\n" + "=" * 60)
    print("验收标准检查")
    print("=" * 60)
    storage_pass = True
    if router.graph_adapter:
        storage_pass = router.graph_adapter.get_storage_size() / (1024 * 1024) < 20
    latency_pass = avg_retrieve_ms < 100
    print(f"  存储 < 20MB: {'✅ PASS' if storage_pass else '❌ FAIL'}")
    print(f"  检索延迟 < 100ms: {avg_retrieve_ms:.2f}ms {'✅ PASS' if latency_pass else '❌ FAIL'}")

    return {
        "avg_store_ms": avg_store_ms,
        "avg_retrieve_ms": avg_retrieve_ms,
        "latency_pass": latency_pass,
    }


def main():
    print("\n" + "=" * 70)
    print("LightKG 集成记忆系统 - 性能基准测试")
    print("=" * 70)

    results = {}

    # 1. GraphAdapter 测试
    results["graph_adapter"] = benchmark_graph_adapter()

    # 2. TripleExtractor 测试
    results["triple_extractor"] = benchmark_triple_extractor()

    # 3. 集成测试
    results["integration"] = benchmark_integration()

    # 总结
    print("\n" + "=" * 70)
    print("性能测试总结")
    print("=" * 70)

    all_pass = True
    all_pass &= results["graph_adapter"]["storage_pass"]
    all_pass &= results["graph_adapter"]["latency_pass"]
    all_pass &= results["integration"]["latency_pass"]

    print(f"\n{'✅ 全部测试通过' if all_pass else '❌ 部分测试失败'}")
    print(f"存储大小: {results['graph_adapter']['storage_mb']:.4f} MB")
    print(f"查询延迟: {results['graph_adapter']['avg_query_ms']:.2f}ms")
    print(f"检索延迟: {results['integration']['avg_retrieve_ms']:.2f}ms")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
