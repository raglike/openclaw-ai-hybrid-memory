#!/usr/bin/env python3
"""
三重融合测试脚本
Triple Fusion Test Script
"""

from hybrid_router import HybridMemoryRouter
import time

def main():
    print("=" * 60)
    print("三重融合测试")
    print("=" * 60)

    # 初始化
    print("\n初始化混合路由器...")
    router = HybridMemoryRouter()
    print("✅ 初始化完成")

    # 测试三重融合
    test_queries = [
        "OpenClaw的项目架构",
        "Chroma向量数据库",
        "混合记忆系统",
        "BM25索引器"
    ]

    all_results = []

    for query in test_queries:
        print(f"\n查询: {query}")
        print("=" * 60)

        # 记录开始时间
        start_time = time.time()

        # 三重融合检索（使用关键词模式，确保触发三重融合）
        results = router.retrieve(query, max_results=5, use_semantic=False)

        # 记录结束时间
        end_time = time.time()
        elapsed_time = end_time - start_time

        print(f"找到 {len(results)} 条结果 (耗时: {elapsed_time:.2f}秒)\n")

        for i, result in enumerate(results, 1):
            print(f"{i}. 评分: {result['score']:.2f}")
            print(f"   向量分: {result.get('vector_score', 0):.2f}")
            print(f"   BM25分: {result.get('bm25_score', 0):.2f}")
            print(f"   简单分: {result.get('simple_score', 0):.2f}")
            print(f"   出现次数: {result.get('appearance_count', 0)}")
            content_preview = result['content'][:80].replace('\n', ' ')
            print(f"   内容: {content_preview}...")
            print()

        # 保存结果
        all_results.append({
            'query': query,
            'results': results,
            'elapsed_time': elapsed_time
        })

    # 性能统计
    print("\n" + "=" * 60)
    print("性能统计")
    print("=" * 60)

    total_queries = len(all_results)
    total_time = sum(r['elapsed_time'] for r in all_results)
    avg_time = total_time / total_queries
    total_results = sum(len(r['results']) for r in all_results)
    avg_results = total_results / total_queries

    print(f"总查询数: {total_queries}")
    print(f"总耗时: {total_time:.2f}秒")
    print(f"平均查询时间: {avg_time:.2f}秒")
    print(f"总结果数: {total_results}")
    print(f"平均结果数: {avg_results:.2f}")

    # 准确率分析（基于出现次数）
    print("\n" + "=" * 60)
    print("准确率分析（基于出现次数）")
    print("=" * 60)

    appearance_stats = {
        1: 0,  # 只出现在1个结果中
        2: 0,  # 出现在2个结果中
        3: 0   # 出现在3个结果中
    }

    for query_result in all_results:
        for result in query_result['results']:
            appearance_count = result.get('appearance_count', 1)
            appearance_stats[appearance_count] = appearance_stats.get(appearance_count, 0) + 1

    total_appearance = sum(appearance_stats.values())

    for count, num in appearance_stats.items():
        if total_appearance > 0:
            percentage = (num / total_appearance) * 100
            print(f"出现{count}次: {num}条 ({percentage:.1f}%)")

    print("\n✅ 三重融合测试完成")
    print("=" * 60)

    return all_results

if __name__ == "__main__":
    main()
