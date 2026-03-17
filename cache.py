#!/usr/bin/env python3
"""
LRU缓存实现
LRU Cache Implementation
"""

from typing import Any, Optional
from collections import OrderedDict
import hashlib
import json


class LRUCache:
    """LRU缓存（最近最少使用）"""

    def __init__(self, max_size: int = 100):
        """初始化缓存

        Args:
            max_size: 最大缓存条目数
        """
        self.max_size = max_size
        self.cache = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值

        Args:
            key: 键

        Returns:
            缓存值，如果不存在则返回None
        """
        if key in self.cache:
            # 移动到末尾（最近使用）
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]
        else:
            self.misses += 1
            return None

    def put(self, key: str, value: Any) -> None:
        """设置缓存值

        Args:
            key: 键
            value: 值
        """
        # 如果键已存在，删除旧值
        if key in self.cache:
            del self.cache[key]

        # 如果超过最大容量，删除最旧的（第一个）
        elif len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)

        # 添加到末尾
        self.cache[key] = value

    def clear(self) -> None:
        """清除所有缓存"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def get_stats(self) -> dict:
        """获取缓存统计

        Returns:
            统计信息字典
        """
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0.0

        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate
        }

    def __repr__(self) -> str:
        """字符串表示"""
        stats = self.get_stats()
        return f"LRUCache(size={stats['size']}/{stats['max_size']}, hit_rate={stats['hit_rate']:.2%})"


class QueryCache:
    """查询缓存（针对语义检索）"""

    def __init__(self, max_size: int = 50):
        """初始化查询缓存

        Args:
            max_size: 最大缓存条目数
        """
        self.lru = LRUCache(max_size=max_size)

    def _generate_key(self, query: str, params: dict = None) -> str:
        """生成缓存键

        Args:
            query: 查询文本
            params: 其他参数

        Returns:
            缓存键
        """
        key_data = {
            'query': query,
            'params': params or {}
        }

        # 使用MD5哈希生成键
        key_str = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()

        return key_hash

    def get(self, query: str, params: dict = None) -> Optional[Any]:
        """获取缓存结果

        Args:
            query: 查询文本
            params: 其他参数

        Returns:
            缓存结果
        """
        key = self._generate_key(query, params)
        return self.lru.get(key)

    def put(self, query: str, params: dict = None, result: Any = None) -> None:
        """设置缓存结果

        Args:
            query: 查询文本
            params: 其他参数
            result: 结果
        """
        key = self._generate_key(query, params)
        self.lru.put(key, result)

    def clear(self) -> None:
        """清除所有缓存"""
        self.lru.clear()

    def get_stats(self) -> dict:
        """获取缓存统计

        Returns:
            统计信息字典
        """
        return self.lru.get_stats()

    def __repr__(self) -> str:
        """字符串表示"""
        return f"QueryCache({self.lru})"


# 全局缓存实例（Phase 4 - Day 1优化：增加缓存大小）
_query_cache = QueryCache(max_size=200)  # 从50增加到200
_embedding_cache = LRUCache(max_size=1000)  # 从200增加到1000


def get_query_cache() -> QueryCache:
    """获取全局查询缓存实例"""
    return _query_cache


def get_embedding_cache() -> LRUCache:
    """获取全局向量化缓存实例"""
    return _embedding_cache


def clear_all_caches() -> None:
    """清除所有缓存"""
    _query_cache.clear()
    _embedding_cache.clear()


# CLI接口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='LRU缓存测试')
    parser.add_argument('command', choices=['test', 'stats', 'clear'],
                        help='命令: test/stats/clear')

    args = parser.parse_args()

    if args.command == 'test':
        print("\n🧪 缓存测试...")

        # 创建缓存
        cache = LRUCache(max_size=3)

        # 测试1: 添加数据
        print("\n1️⃣  添加数据")
        cache.put('key1', 'value1')
        cache.put('key2', 'value2')
        cache.put('key3', 'value3')
        print(f"   缓存状态: {cache}")

        # 测试2: 获取数据（命中）
        print("\n2️⃣  获取数据（命中）")
        value = cache.get('key1')
        print(f"   key1的值: {value}")
        print(f"   缓存状态: {cache}")

        # 测试3: 添加新数据（驱逐最旧的）
        print("\n3️⃣  添加新数据（驱逐最旧的）")
        cache.put('key4', 'value4')
        print(f"   缓存状态: {cache}")

        # 测试4: 获取数据（未命中）
        print("\n4️⃣  获取数据（未命中）")
        value = cache.get('key2')
        print(f"   key2的值: {value} (应该为None)")
        print(f"   缓存状态: {cache}")

        print("\n✅ 缓存测试完成")

    elif args.command == 'stats':
        query_cache_stats = get_query_cache().get_stats()
        embedding_cache_stats = get_embedding_cache().get_stats()

        print(f"\n📊 缓存统计:")
        print(f"\n   查询缓存: QueryCache(LRUCache(size={query_cache_stats['size']}/{query_cache_stats['max_size']}, hit_rate={query_cache_stats['hit_rate']:.2%}))")
        print(f"      命中: {query_cache_stats['hits']}")
        print(f"      未命中: {query_cache_stats['misses']}")

        print(f"\n   向量化缓存: LRUCache(size={embedding_cache_stats['size']}/{embedding_cache_stats['max_size']}, hit_rate={embedding_cache_stats['hit_rate']:.2%}))")
        print(f"      命中: {embedding_cache_stats['hits']}")
        print(f"      未命中: {embedding_cache_stats['misses']}")

    elif args.command == 'clear':
        clear_all_caches()
        print(f"\n✅ 缓存已清除")
