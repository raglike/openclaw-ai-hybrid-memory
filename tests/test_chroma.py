#!/usr/bin/env python3
"""
ChromaStore单元测试
Unit Tests for ChromaStore
"""

import unittest
import sys
import os
import tempfile
import shutil

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chroma_store import ChromaStore


class TestChromaStore(unittest.TestCase):
    """ChromaStore单元测试"""

    def setUp(self):
        """测试前准备"""
        # 创建临时目录
        self.test_dir = tempfile.mkdtemp(prefix="test_chroma_")
        self.store = ChromaStore(persist_directory=self.test_dir)

    def tearDown(self):
        """测试后清理"""
        # 删除临时目录
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.store)
        self.assertIsNotNone(self.store.collection)
        self.assertEqual(self.store.collection.name, "openclaw_memory")

    def test_store_and_retrieve(self):
        """测试存储和检索"""
        # 存储测试数据
        embedding = [0.1, 0.2, 0.3] * 100  # 300维向量
        content = "测试记忆内容"
        metadata = {"source": "test", "importance": "normal"}

        record_id = self.store.store(
            content=content,
            embedding=embedding,
            metadata=metadata
        )

        # 验证返回的ID
        self.assertIsNotNone(record_id)
        self.assertTrue(record_id.startswith("mem_"))

        # 检索数据
        results = self.store.retrieve(
            query_embedding=embedding,
            n_results=1
        )

        # 验证检索结果
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], record_id)
        self.assertEqual(results[0]['content'], content)
        self.assertEqual(results[0]['metadata'], metadata)

    def test_store_multiple(self):
        """测试批量存储"""
        embeddings = [
            [0.1, 0.2, 0.3] * 100,
            [0.4, 0.5, 0.6] * 100,
            [0.7, 0.8, 0.9] * 100,
        ]

        contents = [
            "第一条记忆",
            "第二条记忆",
            "第三条记忆",
        ]

        record_ids = []
        for embedding, content in zip(embeddings, contents):
            record_id = self.store.store(
                content=content,
                embedding=embedding
            )
            record_ids.append(record_id)

        # 验证存储数量
        stats = self.store.get_stats()
        self.assertEqual(stats['total_records'], 3)

    def test_retrieve_with_metadata_filter(self):
        """测试元数据过滤检索"""
        # 存储不同元数据的数据
        embedding1 = [0.1, 0.2, 0.3] * 100
        embedding2 = [0.4, 0.5, 0.6] * 100

        self.store.store(
            content="重要记忆",
            embedding=embedding1,
            metadata={"importance": "important"}
        )

        self.store.store(
            content="普通记忆",
            embedding=embedding2,
            metadata={"importance": "normal"}
        )

        # 使用元数据过滤检索
        results = self.store.retrieve(
            query_embedding=embedding1,
            n_results=10,
            where={"importance": "important"}
        )

        # 验证只返回重要记忆
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['metadata']['importance'], "important")

    def test_retrieve_by_id(self):
        """测试通过ID检索"""
        embedding = [0.1, 0.2, 0.3] * 100
        content = "测试记忆"

        record_id = self.store.store(
            content=content,
            embedding=embedding
        )

        # 通过ID检索
        result = self.store.retrieve_by_id(record_id)

        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], record_id)
        self.assertEqual(result['content'], content)

    def test_update_metadata(self):
        """测试更新元数据"""
        embedding = [0.1, 0.2, 0.3] * 100
        content = "测试记忆"

        record_id = self.store.store(
            content=content,
            embedding=embedding,
            metadata={"importance": "normal"}
        )

        # 更新元数据
        success = self.store.update_metadata(
            record_id=record_id,
            metadata={"importance": "important", "updated": True}
        )

        self.assertTrue(success)

        # 验证更新后的元数据
        result = self.store.retrieve_by_id(record_id)
        self.assertEqual(result['metadata']['importance'], "important")
        self.assertTrue(result['metadata']['updated'])

    def test_delete(self):
        """测试删除记录"""
        embedding = [0.1, 0.2, 0.3] * 100
        content = "测试记忆"

        record_id = self.store.store(
            content=content,
            embedding=embedding
        )

        # 删除记录
        success = self.store.delete(record_id)

        self.assertTrue(success)

        # 验证已删除
        result = self.store.retrieve_by_id(record_id)
        self.assertIsNone(result)

    def test_stats(self):
        """测试统计信息"""
        stats = self.store.get_stats()

        self.assertIn('total_records', stats)
        self.assertIn('persist_directory', stats)
        self.assertIn('collection_name', stats)

    def test_reset(self):
        """测试重置数据库"""
        # 存储一些数据
        embedding = [0.1, 0.2, 0.3] * 100
        self.store.store(
            content="测试记忆",
            embedding=embedding
        )

        # 重置
        success = self.store.reset()

        self.assertTrue(success)

        # 验证数据已清空
        stats = self.store.get_stats()
        self.assertEqual(stats['total_records'], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)