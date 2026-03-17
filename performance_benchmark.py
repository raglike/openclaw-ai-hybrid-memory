#!/usr/bin/env python3
"""
性能基准测试
Performance Benchmark Test
Phase 4 - Day 1
"""

import time
import sys
import os
from typing import List, Dict
from statistics import mean, median, stdev

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from memory_wrapper import MemoryWrapper


class PerformanceBenchmark:
    """性能基准测试"""
    
    def __init__(self):
        """初始化"""
        self.memory = MemoryWrapper()
        self.results = []
    
    def benchmark_search(
        self,
        query: str,
        max_results: int = 5,
        iterations: int = 10
    ) -> Dict:
        """单次搜索基准测试
        
        Args:
            query: 查询文本
            max_results: 最大结果数
            iterations: 迭代次数
            
        Returns:
            基准测试结果
        """
        latencies = []
        result_counts = []
        
        # 预热（跳过第一次的初始化开销）
        try:
            self.memory.search(query, max_results=max_results)
        except:
            pass
        
        # 多次测试
        for i in range(iterations):
            start = time.time()
            try:
                result = self.memory.search(query, max_results=max_results)
                elapsed = time.time() - start
                latencies.append(elapsed * 1000)  # 转换为毫秒
                result_counts.append(len(result))
            except Exception as e:
                print(f"❌ 第{i+1}次查询失败: {e}")
                continue
        
        if not latencies:
            return {
                'query': query,
                'error': 'All queries failed',
                'iterations': 0
            }
        
        return {
            'query': query,
            'iterations': iterations,
            'avg_latency_ms': mean(latencies),
            'median_latency_ms': median(latencies),
            'min_latency_ms': min(latencies),
            'max_latency_ms': max(latencies),
            'std_dev_ms': stdev(latencies) if len(latencies) > 1 else 0,
            'avg_result_count': mean(result_counts),
            'success_rate': len(latencies) / iterations
        }
    
    def run_benchmark_suite(
        self,
        queries: List[str],
        max_results: int = 5,
        iterations: int = 10
    ) -> List[Dict]:
        """运行基准测试套件
        
        Args:
            queries: 查询列表
            max_results: 最大结果数
            iterations: 每个查询的迭代次数
            
        Returns:
            测试结果列表
        """
        print("=" * 60)
        print("🚀 性能基准测试开始")
        print("=" * 60)
        
        results = []
        for i, query in enumerate(queries, 1):
            print(f"\n[{i}/{len(queries)}] 测试查询: {query}")
            result = self.benchmark_search(query, max_results, iterations)
            results.append(result)
            
            if 'error' not in result:
                print(f"   平均延迟: {result['avg_latency_ms']:.2f}ms")
                print(f"   中位数延迟: {result['median_latency_ms']:.2f}ms")
                print(f"   最大延迟: {result['max_latency_ms']:.2f}ms")
                print(f"   标准差: {result['std_dev_ms']:.2f}ms")
                print(f"   成功率: {result['success_rate']:.1%}")
            else:
                print(f"   ❌ 错误: {result['error']}")
        
        return results
    
    def generate_summary(self, results: List[Dict]) -> Dict:
        """生成测试摘要
        
        Args:
            results: 测试结果列表
            
        Returns:
            摘要信息
        """
        valid_results = [r for r in results if 'error' not in r]
        
        if not valid_results:
            return {
                'total_tests': len(results),
                'successful_tests': 0,
                'failed_tests': len(results)
            }
        
        avg_latencies = [r['avg_latency_ms'] for r in valid_results]
        max_latencies = [r['max_latency_ms'] for r in valid_results]
        success_rates = [r['success_rate'] for r in valid_results]
        
        return {
            'total_tests': len(results),
            'successful_tests': len(valid_results),
            'failed_tests': len(results) - len(valid_results),
            'overall_avg_latency': mean(avg_latencies),
            'overall_max_latency': max(max_latencies),
            'overall_success_rate': mean(success_rates),
            'p95_latency': sorted(avg_latencies)[int(len(avg_latencies) * 0.95)] if len(avg_latencies) >= 20 else None
        }
    
    def print_report(self, results: List[Dict]):
        """打印测试报告
        
        Args:
            results: 测试结果列表
        """
        summary = self.generate_summary(results)
        
        print("\n" + "=" * 60)
        print("📊 性能基准测试报告")
        print("=" * 60)
        
        print(f"\n📈 整体统计:")
        print(f"   总测试数: {summary['total_tests']}")
        print(f"   成功测试: {summary['successful_tests']}")
        print(f"   失败测试: {summary['failed_tests']}")
        
        if summary['successful_tests'] > 0:
            print(f"   平均延迟: {summary['overall_avg_latency']:.2f}ms")
            print(f"   最大延迟: {summary['overall_max_latency']:.2f}ms")
            print(f"   成功率: {summary['overall_success_rate']:.1%}")
            
            if summary['p95_latency']:
                print(f"   P95延迟: {summary['p95_latency']:.2f}ms")
        
        print(f"\n📋 详细结果:")
        for i, result in enumerate(results, 1):
            if 'error' not in result:
                print(f"   {i}. {result['query'][:50]}...")
                print(f"      平均: {result['avg_latency_ms']:.2f}ms | "
                      f"中位: {result['median_latency_ms']:.2f}ms | "
                      f"最大: {result['max_latency_ms']:.2f}ms | "
                      f"成功率: {result['success_rate']:.1%}")
            else:
                print(f"   {i}. {result['query'][:50]}... - ❌ {result['error']}")


def main():
    """主函数"""
    # 初始化测试器
    benchmark = PerformanceBenchmark()
    
    # 基准测试查询
    test_queries = [
        "OpenClaw的项目架构",
        "Chroma向量数据库",
        "混合记忆系统的设计",
        "向量化服务的性能",
        "缓存机制的效率"
    ]
    
    # 运行基准测试
    results = benchmark.run_benchmark_suite(
        queries=test_queries,
        max_results=5,
        iterations=10
    )
    
    # 生成报告
    benchmark.print_report(results)
    
    print("\n" + "=" * 60)
    print("✅ 性能基准测试完成")
    print("=" * 60)
    
    return results


if __name__ == "__main__":
    main()
