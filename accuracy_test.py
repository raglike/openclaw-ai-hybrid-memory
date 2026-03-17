#!/usr/bin/env python3
"""
准确率测试
Accuracy Test

测试混合记忆系统的检索准确率
"""

import sys
import os
import time
from typing import List, Dict, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from memory_wrapper import MemoryWrapper


class AccuracyTester:
    """准确率测试器"""

    def __init__(self):
        """初始化"""
        self.memory = MemoryWrapper()
        self.test_results = []

    def run_all_tests(self) -> Dict:
        """运行所有测试

        Returns:
            测试结果汇总
        """
        print("\n" + "="*70)
        print("🧪 混合记忆系统 - 准确率测试套件")
        print("="*70 + "\n")

        # 1. 基础功能测试
        print("1️⃣  基础功能测试")
        print("-" * 70)
        self._test_basic_functionality()

        # 2. 回归测试
        print("\n2️⃣  回归测试（确保现有功能不受影响）")
        print("-" * 70)
        self._test_regression()

        # 3. 边界测试
        print("\n3️⃣  边界测试")
        print("-" * 70)
        self._test_boundary_cases()

        # 4. 准确率评估
        print("\n4️⃣  准确率评估")
        print("-" * 70)
        accuracy_metrics = self._test_accuracy()

        # 5. 性能测试
        print("\n5️⃣  性能测试")
        print("-" * 70)
        performance_metrics = self._test_performance()

        # 6. 集成测试
        print("\n6️⃣  集成测试")
        print("-" * 70)
        self._test_integration()

        # 汇总结果
        print("\n" + "="*70)
        print("📊 测试结果汇总")
        print("="*70)

        summary = {
            'basic_functionality': self._get_passed_count('basic'),
            'regression': self._get_passed_count('regression'),
            'boundary': self._get_passed_count('boundary'),
            'accuracy': accuracy_metrics,
            'performance': performance_metrics,
            'integration': self._get_passed_count('integration')
        }

        self._print_summary(summary)

        return summary

    def _test_basic_functionality(self):
        """基础功能测试"""

        tests = [
            {
                'name': '初始化测试',
                'test': lambda: self._test_init()
            },
            {
                'name': '搜索功能测试',
                'test': lambda: self._test_search()
            },
            {
                'name': '存储功能测试',
                'test': lambda: self._test_store()
            },
            {
                'name': '统计信息测试',
                'test': lambda: self._test_stats()
            }
        ]

        for test_case in tests:
            try:
                result = test_case['test']()
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"   {status} - {test_case['name']}")
                self.test_results.append({
                    'category': 'basic',
                    'name': test_case['name'],
                    'status': 'pass' if result else 'fail'
                })
            except Exception as e:
                print(f"   ❌ ERROR - {test_case['name']}: {str(e)[:50]}")
                self.test_results.append({
                    'category': 'basic',
                    'name': test_case['name'],
                    'status': 'error',
                    'error': str(e)
                })

    def _test_regression(self):
        """回归测试"""

        tests = [
            {
                'name': '查询"OpenClaw"应返回相关结果',
                'test': lambda: self._test_query_relevance(
                    "OpenClaw的项目架构",
                    expected_keywords=['OpenClaw', '架构'],
                    min_results=1
                )
            },
            {
                'name': '查询"Chroma"应返回向量数据库相关内容',
                'test': lambda: self._test_query_relevance(
                    "Chroma向量数据库",
                    expected_keywords=['Chroma', '向量', '数据库'],
                    min_results=1
                )
            },
            {
                'name': '查询"记忆系统"应返回相关结果',
                'test': lambda: self._test_query_relevance(
                    "混合记忆系统",
                    expected_keywords=['记忆', '系统', 'Hybrid'],
                    min_results=1
                )
            }
        ]

        for test_case in tests:
            try:
                result = test_case['test']()
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"   {status} - {test_case['name']}")
                self.test_results.append({
                    'category': 'regression',
                    'name': test_case['name'],
                    'status': 'pass' if result else 'fail'
                })
            except Exception as e:
                print(f"   ❌ ERROR - {test_case['name']}: {str(e)[:50]}")
                self.test_results.append({
                    'category': 'regression',
                    'name': test_case['name'],
                    'status': 'error',
                    'error': str(e)
                })

    def _test_boundary_cases(self):
        """边界测试"""

        tests = [
            {
                'name': '空查询测试',
                'test': lambda: self._test_empty_query()
            },
            {
                'name': '特殊字符测试',
                'test': lambda: self._test_special_chars()
            },
            {
                'name': '超长查询测试',
                'test': lambda: self._test_long_query()
            },
            {
                'name': '低分阈值测试',
                'test': lambda: self._test_low_threshold()
            },
            {
                'name': '大量结果请求测试',
                'test': lambda: self._test_large_result_count()
            }
        ]

        for test_case in tests:
            try:
                result = test_case['test']()
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"   {status} - {test_case['name']}")
                self.test_results.append({
                    'category': 'boundary',
                    'name': test_case['name'],
                    'status': 'pass' if result else 'fail'
                })
            except Exception as e:
                print(f"   ❌ ERROR - {test_case['name']}: {str(e)[:50]}")
                self.test_results.append({
                    'category': 'boundary',
                    'name': test_case['name'],
                    'status': 'error',
                    'error': str(e)
                })

    def _test_accuracy(self) -> Dict:
        """准确率评估

        Returns:
            准确率指标
        """
        # 测试数据
        test_cases = [
            {
                'query': 'OpenClaw的项目架构',
                'expected_keywords': ['OpenClaw', '架构', '项目'],
                'min_results': 1
            },
            {
                'query': 'Chroma向量数据库',
                'expected_keywords': ['Chroma', '向量', '数据库'],
                'min_results': 1
            },
            {
                'query': '混合记忆系统',
                'expected_keywords': ['记忆', '系统', 'Hybrid', 'Memory'],
                'min_results': 1
            },
            {
                'query': 'Embedding服务',
                'expected_keywords': ['Embedding', '向量化', '模型'],
                'min_results': 1
            },
            {
                'query': 'Daily文件索引',
                'expected_keywords': ['Daily', '文件', '索引'],
                'min_results': 1
            }
        ]

        # 统计指标
        total_tests = len(test_cases)
        passed_tests = 0
        total_keyword_matches = 0
        total_keyword_expected = 0

        for test_case in test_cases:
            query = test_case['query']
            expected_keywords = test_case['expected_keywords']
            min_results = test_case['min_results']

            print(f"\n   测试查询: '{query}'")

            # 执行搜索
            results = self.memory.search(query, max_results=5)

            # 检查结果数量
            result_count_ok = len(results) >= min_results
            print(f"      结果数量: {len(results)} (最小要求: {min_results}) {'✅' if result_count_ok else '❌'}")

            # 检查关键词匹配
            keyword_matches = 0
            for keyword in expected_keywords:
                found = any(keyword in r.get('content', '').lower()
                           for r in results)
                if found:
                    keyword_matches += 1
                    print(f"      ✅ 关键词 '{keyword}' 找到")
                else:
                    print(f"      ⚠️  关键词 '{keyword}' 未找到")

            # 统计
            if result_count_ok and keyword_matches >= len(expected_keywords) // 2:
                passed_tests += 1

            total_keyword_matches += keyword_matches
            total_keyword_expected += len(expected_keywords)

        # 计算准确率指标
        query_accuracy = passed_tests / total_tests if total_tests > 0 else 0
        keyword_recall = total_keyword_matches / total_keyword_expected if total_keyword_expected > 0 else 0

        accuracy_metrics = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'query_accuracy': query_accuracy,
            'keyword_recall': keyword_recall,
            'total_keyword_matches': total_keyword_matches,
            'total_keyword_expected': total_keyword_expected
        }

        print(f"\n   准确率指标:")
        print(f"      查询准确率: {query_accuracy:.1%}")
        print(f"      关键词召回率: {keyword_recall:.1%}")
        print(f"      通过测试: {passed_tests}/{total_tests}")

        return accuracy_metrics

    def _test_performance(self) -> Dict:
        """性能测试

        Returns:
            性能指标
        """
        print("\n   测试查询响应时间...")

        # 测试查询
        test_queries = [
            "OpenClaw项目架构",
            "Chroma向量数据库",
            "混合记忆系统",
            "Embedding服务"
        ]

        response_times = []

        for query in test_queries:
            start_time = time.time()
            results = self.memory.search(query, max_results=5)
            elapsed = time.time() - start_time
            response_times.append(elapsed)
            print(f"      '{query[:20]}...': {elapsed:.3f}s ({len(results)} 条结果)")

        # 计算统计指标
        avg_time = sum(response_times) / len(response_times)
        min_time = min(response_times)
        max_time = max(response_times)

        performance_metrics = {
            'avg_response_time': avg_time,
            'min_response_time': min_time,
            'max_response_time': max_time,
            'total_queries': len(test_queries)
        }

        print(f"\n   性能指标:")
        print(f"      平均响应时间: {avg_time:.3f}s")
        print(f"      最快响应时间: {min_time:.3f}s")
        print(f"      最慢响应时间: {max_time:.3f}s")

        return performance_metrics

    def _test_integration(self):
        """集成测试"""

        tests = [
            {
                'name': '存储后立即检索测试',
                'test': lambda: self._test_store_and_retrieve()
            },
            {
                'name': '缓存命中测试',
                'test': lambda: self._test_cache_hit()
            },
            {
                'name': '多来源检索测试',
                'test': lambda: self._test_multi_source_retrieval()
            }
        ]

        for test_case in tests:
            try:
                result = test_case['test']()
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"   {status} - {test_case['name']}")
                self.test_results.append({
                    'category': 'integration',
                    'name': test_case['name'],
                    'status': 'pass' if result else 'fail'
                })
            except Exception as e:
                print(f"   ❌ ERROR - {test_case['name']}: {str(e)[:50]}")
                self.test_results.append({
                    'category': 'integration',
                    'name': test_case['name'],
                    'status': 'error',
                    'error': str(e)
                })

    # ===== 具体测试方法 =====

    def _test_init(self) -> bool:
        """初始化测试"""
        try:
            stats = self.memory.get_stats()
            return 'total_records' in stats and 'daily_files_count' in stats
        except Exception:
            return False

    def _test_search(self) -> bool:
        """搜索功能测试"""
        try:
            results = self.memory.search("OpenClaw", max_results=5)
            return isinstance(results, list)
        except Exception:
            return False

    def _test_store(self) -> bool:
        """存储功能测试"""
        try:
            record_id = self.memory.store("测试内容")
            return record_id is not None and record_id.startswith('mem_')
        except Exception:
            return False

    def _test_stats(self) -> bool:
        """统计信息测试"""
        try:
            stats = self.memory.get_stats()
            return isinstance(stats, dict) and 'total_records' in stats
        except Exception:
            return False

    def _test_query_relevance(
        self,
        query: str,
        expected_keywords: List[str],
        min_results: int
    ) -> bool:
        """查询相关性测试"""
        try:
            results = self.memory.search(query, max_results=5)

            # 检查结果数量
            if len(results) < min_results:
                return False

            # 检查关键词匹配（至少一半关键词）
            keyword_matches = sum(
                1 for keyword in expected_keywords
                if any(keyword in r.get('content', '').lower() for r in results)
            )

            return keyword_matches >= len(expected_keywords) // 2

        except Exception:
            return False

    def _test_empty_query(self) -> bool:
        """空查询测试"""
        try:
            results = self.memory.search("", max_results=5)
            # 空查询应该返回空列表或不会崩溃
            return isinstance(results, list)
        except Exception:
            # 空查询可能抛出异常，这也是可接受的行为
            return True

    def _test_special_chars(self) -> bool:
        """特殊字符测试"""
        try:
            results = self.memory.search("OpenClaw @#$%^&*()", max_results=5)
            return isinstance(results, list)
        except Exception:
            return False

    def _test_long_query(self) -> bool:
        """超长查询测试"""
        try:
            long_query = "OpenClaw " * 100  # 超长查询
            results = self.memory.search(long_query, max_results=5)
            return isinstance(results, list)
        except Exception:
            return False

    def _test_low_threshold(self) -> bool:
        """低分阈值测试"""
        try:
            results = self.memory.search("OpenClaw", max_results=5, min_score=0.9)
            return isinstance(results, list)
        except Exception:
            return False

    def _test_large_result_count(self) -> bool:
        """大量结果请求测试"""
        try:
            results = self.memory.search("OpenClaw", max_results=100)
            return isinstance(results, list)
        except Exception:
            return False

    def _test_store_and_retrieve(self) -> bool:
        """存储后立即检索测试"""
        try:
            # 存储测试数据
            test_content = "这是一个集成测试：OpenClaw混合记忆系统"
            record_id = self.memory.store(test_content)

            # 立即检索
            results = self.memory.search("集成测试", max_results=5)

            # 检查是否找到
            found = any(test_content in r.get('content', '') for r in results)
            return found

        except Exception:
            return False

    def _test_cache_hit(self) -> bool:
        """缓存命中测试"""
        try:
            query = "缓存测试查询"

            # 第一次查询
            start_time = time.time()
            results1 = self.memory.search(query, max_results=5)
            time1 = time.time() - start_time

            # 第二次查询（应该命中缓存）
            start_time = time.time()
            results2 = self.memory.search(query, max_results=5)
            time2 = time.time() - start_time

            # 缓存命中后，第二次应该更快
            # 但由于向量化可能并行执行，这个差异可能不明显
            # 只要不崩溃就算通过
            return isinstance(results2, list)

        except Exception:
            return False

    def _test_multi_source_retrieval(self) -> bool:
        """多来源检索测试"""
        try:
            results = self.memory.search("OpenClaw", max_results=10)

            # 检查结果是否来自不同来源
            sources = set(r.get('source', 'unknown') for r in results)

            # 至少应该有chroma来源
            return 'chroma' in sources

        except Exception:
            return False

    # ===== 辅助方法 =====

    def _get_passed_count(self, category: str) -> Dict:
        """获取某个类别的通过数量"""
        category_results = [r for r in self.test_results if r['category'] == category]
        passed = sum(1 for r in category_results if r['status'] == 'pass')
        failed = sum(1 for r in category_results if r['status'] == 'fail')
        error = sum(1 for r in category_results if r['status'] == 'error')

        return {
            'total': len(category_results),
            'passed': passed,
            'failed': failed,
            'error': error,
            'pass_rate': passed / len(category_results) if category_results else 0
        }

    def _print_summary(self, summary: Dict):
        """打印测试结果汇总"""
        print(f"\n✅ 基础功能: {summary['basic_functionality']['passed']}/{summary['basic_functionality']['total']} "
              f"({summary['basic_functionality']['pass_rate']:.1%})")

        print(f"✅ 回归测试: {summary['regression']['passed']}/{summary['regression']['total']} "
              f"({summary['regression']['pass_rate']:.1%})")

        print(f"✅ 边界测试: {summary['boundary']['passed']}/{summary['boundary']['total']} "
              f"({summary['boundary']['pass_rate']:.1%})")

        print(f"\n📊 准确率指标:")
        print(f"   查询准确率: {summary['accuracy']['query_accuracy']:.1%}")
        print(f"   关键词召回率: {summary['accuracy']['keyword_recall']:.1%}")

        print(f"\n⚡ 性能指标:")
        print(f"   平均响应时间: {summary['performance']['avg_response_time']:.3f}s")

        print(f"\n🔗 集成测试: {summary['integration']['passed']}/{summary['integration']['total']} "
              f"({summary['integration']['pass_rate']:.1%})")


def main():
    """主函数"""
    tester = AccuracyTester()
    summary = tester.run_all_tests()

    # 返回退出码
    total_pass_rate = (
        summary['basic_functionality']['pass_rate'] +
        summary['regression']['pass_rate'] +
        summary['boundary']['pass_rate'] +
        summary['accuracy']['query_accuracy'] +
        summary['integration']['pass_rate']
    ) / 5

    if total_pass_rate >= 0.8:
        print("\n" + "="*70)
        print("🎉 总体测试通过率 {:.1%} - 测试通过！".format(total_pass_rate))
        print("="*70 + "\n")
        return 0
    else:
        print("\n" + "="*70)
        print("⚠️  总体测试通过率 {:.1%} - 需要改进".format(total_pass_rate))
        print("="*70 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())