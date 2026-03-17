#!/usr/bin/env python3
"""
压力测试
Stress Test for Memory System
Phase 4 - Day 1
"""

import time
import sys
import os
import random
from typing import List, Dict
from statistics import mean, median

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from memory_wrapper import MemoryWrapper


class StressTest:
    """压力测试"""
    
    def __init__(self):
        """初始化"""
        self.memory = MemoryWrapper()
    
    def generate_test_data(self, count: int = 1000) -> List[str]:
        """生成测试数据
        
        Args:
            count: 数据条数
            
        Returns:
            测试数据列表
        """
        test_data = []
        
        # 主题列表
        topics = [
            "OpenClaw",
            "混合记忆系统",
            "Chroma向量数据库",
            "缓存机制",
            "向量化服务",
            "Agent协作",
            "性能优化",
            "自动化测试",
            "知识管理",
            "项目架构"
        ]
        
        # 动作列表
        actions = [
            "实现",
            "优化",
            "测试",
            "部署",
            "配置",
            "集成",
            "重构",
            "分析",
            "设计",
            "监控"
        ]
        
        for i in range(count):
            topic = random.choice(topics)
            action = random.choice(actions)
            content = f"{action}{topic}的功能和性能。这是第{i+1}条测试数据。"
            test_data.append(content)
        
        return test_data
    
    def test_insert_performance(
        self,
        data_count: int = 1000,
        batch_size: int = 10
    ) -> Dict:
        """测试插入性能
        
        Args:
            data_count: 数据条数
            batch_size: 批量大小
            
        Returns:
            测试结果
        """
        print(f"\n📝 测试插入性能: {data_count}条数据（批量大小={batch_size}）")
        
        # 生成测试数据
        test_data = self.generate_test_data(data_count)
        
        # 测试插入性能
        insert_times = []
        success_count = 0
        
        for i in range(0, len(test_data), batch_size):
            batch = test_data[i:i+batch_size]
            start = time.time()
            
            for content in batch:
                try:
                    self.memory.store(content, importance="normal")
                    success_count += 1
                except Exception as e:
                    print(f"   ❌ 插入失败: {e}")
            
            elapsed = time.time() - start
            insert_times.append(elapsed)
            
            if (i // batch_size + 1) % (len(test_data) // batch_size // 10) == 0:
                progress = (i + batch_size) / len(test_data) * 100
                print(f"   进度: {progress:.0f}%")
        
        if not insert_times:
            return {
                'data_count': data_count,
                'success_count': 0,
                'error': 'All inserts failed'
            }
        
        return {
            'data_count': data_count,
            'success_count': success_count,
            'batch_size': batch_size,
            'total_time': sum(insert_times),
            'avg_batch_time': mean(insert_times),
            'max_batch_time': max(insert_times),
            'throughput': success_count / sum(insert_times),
            'success_rate': success_count / data_count
        }
    
    def test_search_performance(
        self,
        data_count: int = 1000,
        query_count: int = 100
    ) -> Dict:
        """测试检索性能
        
        Args:
            data_count: 数据条数（仅用于报告）
            query_count: 查询次数
            
        Returns:
            测试结果
        """
        print(f"\n🔍 测试检索性能: {query_count}次查询（数据量={data_count}）")
        
        # 生成测试查询
        test_queries = self.generate_test_data(query_count)
        
        # 测试检索性能
        search_times = []
        result_counts = []
        success_count = 0
        
        for i, query in enumerate(test_queries):
            start = time.time()
            
            try:
                results = self.memory.search(query, max_results=5)
                elapsed = time.time() - start
                search_times.append(elapsed * 1000)  # 转换为毫秒
                result_counts.append(len(results))
                success_count += 1
            except Exception as e:
                print(f"   ❌ 查询失败: {e}")
                continue
            
            if (i + 1) % (query_count // 10) == 0:
                progress = (i + 1) / query_count * 100
                print(f"   进度: {progress:.0f}%")
        
        if not search_times:
            return {
                'data_count': data_count,
                'query_count': query_count,
                'success_count': 0,
                'error': 'All queries failed'
            }
        
        return {
            'data_count': data_count,
            'query_count': query_count,
            'success_count': success_count,
            'avg_latency_ms': mean(search_times),
            'median_latency_ms': median(search_times),
            'min_latency_ms': min(search_times),
            'max_latency_ms': max(search_times),
            'avg_result_count': mean(result_counts),
            'qps': success_count / sum(search_times) * 1000,  # queries per second
            'success_rate': success_count / query_count
        }
    
    def test_concurrent_search(
        self,
        data_count: int = 1000,
        concurrent_queries: int = 10,
        iterations: int = 100
    ) -> Dict:
        """测试并发检索性能
        
        Args:
            data_count: 数据条数
            concurrent_queries: 并发查询数
            iterations: 迭代次数
            
        Returns:
            测试结果
        """
        print(f"\n⚡ 测试并发检索: {concurrent_queries}并发 × {iterations}次（数据量={data_count}）")
        
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        # 生成测试查询
        test_queries = self.generate_test_data(iterations)
        
        # 并发测试
        search_times = []
        success_count = 0
        
        def concurrent_search(query: str) -> Dict:
            """并发搜索函数"""
            start = time.time()
            try:
                results = self.memory.search(query, max_results=5)
                elapsed = time.time() - start
                return {
                    'latency_ms': elapsed * 1000,
                    'result_count': len(results),
                    'success': True
                }
            except Exception as e:
                return {
                    'latency_ms': 0,
                    'result_count': 0,
                    'success': False,
                    'error': str(e)
                }
        
        total_start = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_queries) as executor:
            futures = [executor.submit(concurrent_search, query) for query in test_queries]
            
            for i, future in enumerate(as_completed(futures), 1):
                result = future.result()
                
                if result['success']:
                    search_times.append(result['latency_ms'])
                    success_count += 1
                
                if i % (iterations // 10) == 0:
                    progress = i / iterations * 100
                    print(f"   进度: {progress:.0f}%")
        
        total_time = time.time() - total_start
        
        if not search_times:
            return {
                'data_count': data_count,
                'concurrent_queries': concurrent_queries,
                'iterations': iterations,
                'success_count': 0,
                'error': 'All queries failed'
            }
        
        return {
            'data_count': data_count,
            'concurrent_queries': concurrent_queries,
            'iterations': iterations,
            'success_count': success_count,
            'total_time': total_time,
            'avg_latency_ms': mean(search_times),
            'median_latency_ms': median(search_times),
            'min_latency_ms': min(search_times),
            'max_latency_ms': max(search_times),
            'throughput_qps': success_count / total_time,
            'success_rate': success_count / iterations
        }
    
    def print_report(self, results: Dict):
        """打印测试报告
        
        Args:
            results: 测试结果
        """
        test_type = results.get('test_type', 'Unknown')
        
        print("\n" + "=" * 60)
        print(f"📊 压力测试报告: {test_type}")
        print("=" * 60)
        
        if 'error' in results:
            print(f"   ❌ 错误: {results['error']}")
            return
        
        print(f"\n📈 测试参数:")
        if 'data_count' in results:
            print(f"   数据量: {results['data_count']} 条")
        if 'query_count' in results:
            print(f"   查询数: {results['query_count']} 次")
        if 'iterations' in results:
            print(f"   迭代数: {results['iterations']} 次")
        if 'concurrent_queries' in results:
            print(f"   并发数: {results['concurrent_queries']}")
        if 'batch_size' in results:
            print(f"   批量大小: {results['batch_size']}")
        
        print(f"\n✅ 测试结果:")
        if 'success_count' in results:
            print(f"   成功数: {results['success_count']}")
        if 'success_rate' in results:
            print(f"   成功率: {results['success_rate']:.1%}")
        
        print(f"\n⚡ 性能指标:")
        if 'avg_latency_ms' in results:
            print(f"   平均延迟: {results['avg_latency_ms']:.2f}ms")
        if 'median_latency_ms' in results:
            print(f"   中位数延迟: {results['median_latency_ms']:.2f}ms")
        if 'min_latency_ms' in results:
            print(f"   最小延迟: {results['min_latency_ms']:.2f}ms")
        if 'max_latency_ms' in results:
            print(f"   最大延迟: {results['max_latency_ms']:.2f}ms")
        if 'qps' in results:
            print(f"   QPS: {results['qps']:.2f}")
        if 'throughput_qps' in results:
            print(f"   吞吐量: {results['throughput_qps']:.2f} QPS")
        if 'throughput' in results:
            print(f"   吞吐量: {results['throughput']:.2f} 条/秒")


def main():
    """主函数"""
    # 初始化测试器
    stress_test = StressTest()
    
    print("=" * 60)
    print("🚀 压力测试开始")
    print("=" * 60)
    
    # 测试1: 1000条数据下的检索性能
    print("\n" + "=" * 60)
    print("测试1: 1000条数据")
    print("=" * 60)
    
    # 首先插入1000条数据
    insert_result = stress_test.test_insert_performance(data_count=1000, batch_size=10)
    insert_result['test_type'] = '插入性能 (1000条)'
    stress_test.print_report(insert_result)
    
    # 测试检索性能
    search_result_1000 = stress_test.test_search_performance(data_count=1000, query_count=100)
    search_result_1000['test_type'] = '检索性能 (1000条)'
    stress_test.print_report(search_result_1000)
    
    # 测试2: 并发查询性能
    print("\n" + "=" * 60)
    print("测试2: 并发查询")
    print("=" * 60)
    
    concurrent_result = stress_test.test_concurrent_search(
        data_count=1000,
        concurrent_queries=10,
        iterations=100
    )
    concurrent_result['test_type'] = '并发查询 (10并发)'
    stress_test.print_report(concurrent_result)
    
    # 测试3: 10000条数据下的检索性能
    print("\n" + "=" * 60)
    print("测试3: 10000条数据")
    print("=" * 60)
    
    # 插入10000条数据
    insert_result_10k = stress_test.test_insert_performance(data_count=9000, batch_size=50)
    insert_result_10k['test_type'] = '插入性能 (10000条)'
    stress_test.print_report(insert_result_10k)
    
    # 测试检索性能
    search_result_10k = stress_test.test_search_performance(data_count=10000, query_count=100)
    search_result_10k['test_type'] = '检索性能 (10000条)'
    stress_test.print_report(search_result_10k)
    
    print("\n" + "=" * 60)
    print("✅ 压力测试完成")
    print("=" * 60)
    
    return {
        'insert_1000': insert_result,
        'search_1000': search_result_1000,
        'concurrent': concurrent_result,
        'insert_10000': insert_result_10k,
        'search_10000': search_result_10k
    }


if __name__ == "__main__":
    main()
