#!/usr/bin/env python3
"""
单元测试: GraphAdapter
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph_adapter import GraphAdapter


class TestGraphAdapter(unittest.TestCase):
    """GraphAdapter 单元测试"""

    def setUp(self):
        """测试前准备"""
        self.config = {
            "enabled": True,
            "embedding_dim": 64,
            "codebook_size": 256,
            "storage_path": "./graph_cache",
        }
        self.graph = GraphAdapter(self.config)
        self.graph.initialize()

    def test_initialize(self):
        """测试初始化"""
        self.assertIsNotNone(self.graph.graph)
        self.assertIsNotNone(self.graph.codebook)
        self.assertEqual(self.graph.dim, 64)
        self.assertEqual(self.graph.codebook_size, 256)

    def test_add_triplet(self):
        """测试添加三元组"""
        self.graph.add_triplet("A", "朋友", "B")
        self.assertIn("A", self.graph.entity_codes)
        self.assertIn("B", self.graph.entity_codes)
        self.assertIn("朋友", self.graph.relation_codes)
        self.assertEqual(self.graph.stats["triplet_count"], 1)

    def test_add_triplets(self):
        """测试批量添加三元组"""
        triplets = [
            ("A", "朋友", "B"),
            ("B", "朋友", "C"),
            ("A", "同事", "D"),
        ]
        self.graph.add_triplets(triplets)
        self.assertEqual(self.graph.stats["triplet_count"], 3)

    def test_get_neighbors(self):
        """测试获取邻居"""
        self.graph.add_triplet("A", "朋友", "B")
        self.graph.add_triplet("A", "同事", "C")
        neighbors = self.graph.get_neighbors("A")
        self.assertIn("B", neighbors)
        self.assertIn("C", neighbors)

    def test_get_neighbors_with_relation(self):
        """测试按关系获取邻居"""
        self.graph.add_triplet("A", "朋友", "B")
        self.graph.add_triplet("A", "同事", "C")
        neighbors = self.graph.get_neighbors("A", relation="朋友")
        self.assertIn("B", neighbors)
        self.assertNotIn("C", neighbors)

    def test_traverse(self):
        """测试路径遍历"""
        self.graph.add_triplet("A", "朋友", "B")
        self.graph.add_triplet("B", "朋友", "C")
        self.graph.add_triplet("C", "朋友", "D")
        paths = self.graph.traverse("A", depth=2)
        path_dict = dict(paths)
        self.assertIn("B", path_dict)
        self.assertIn("C", path_dict)
        self.assertNotIn("D", path_dict)

    def test_get_subgraph(self):
        """测试获取子图"""
        self.graph.add_triplet("A", "朋友", "B")
        self.graph.add_triplet("B", "朋友", "C")
        self.graph.add_triplet("D", "朋友", "E")
        subgraph = self.graph.get_subgraph("A", radius=1)
        self.assertIn("A", subgraph.nodes())
        self.assertIn("B", subgraph.nodes())
        self.assertNotIn("C", subgraph.nodes())
        self.assertNotIn("D", subgraph.nodes())

    def test_query_related(self):
        """测试相关实体查询"""
        self.graph.add_triplet("A", "朋友", "B")
        self.graph.add_triplet("B", "同事", "C")
        results = self.graph.query_related("A", top_k=10)
        self.assertGreater(len(results), 0)
        entities = [r["entity"] for r in results]
        self.assertIn("B", entities)

    def test_get_embedding(self):
        """测试获取嵌入向量"""
        self.graph.add_triplet("A", "朋友", "B")
        emb = self.graph.get_embedding("A")
        self.assertEqual(len(emb), 64)

    def test_get_embedding_nonexistent(self):
        """测试获取不存在实体的嵌入"""
        emb = self.graph.get_embedding("NONEXISTENT")
        self.assertEqual(len(emb), 64)
        self.assertTrue(all(v == 0 for v in emb))

    def test_predict_tail(self):
        """测试预测尾实体"""
        self.graph.add_triplet("A", "朋友", "B")
        self.graph.add_triplet("A", "朋友", "C")
        self.graph.add_triplet("A", "同事", "D")
        predictions = self.graph.predict_tail("A", "朋友", top_k=3)
        self.assertIsInstance(predictions, list)
        self.assertLessEqual(len(predictions), 3)

    def test_save_load(self):
        """测试保存和加载"""
        self.graph.add_triplet("A", "朋友", "B")
        path = "./graph_cache/test_graph.pkl"

        os.makedirs("./graph_cache", exist_ok=True)
        self.graph.save(path)

        # 加载到新实例
        new_graph = GraphAdapter(self.config)
        new_graph.load(path)

        self.assertEqual(new_graph.stats["triplet_count"], 1)
        self.assertIn("A", new_graph.entity_codes)

        # 清理
        if os.path.exists(path):
            os.remove(path)
        if os.path.exists(path + ".graph"):
            os.remove(path + ".graph")

    def test_get_storage_size(self):
        """测试存储大小计算"""
        self.graph.add_triplet("A", "朋友", "B")
        self.graph.add_triplet("B", "同事", "C")
        size = self.graph.get_storage_size()
        self.assertGreater(size, 0)

    def test_get_stats(self):
        """测试统计信息"""
        self.graph.add_triplet("A", "朋友", "B")
        stats = self.graph.get_stats()
        self.assertIn("entity_count", stats)
        self.assertIn("triplet_count", stats)
        self.assertIn("storage_bytes", stats)
        self.assertEqual(stats["triplet_count"], 1)

    def test_clear(self):
        """测试清空图谱"""
        self.graph.add_triplet("A", "朋友", "B")
        self.graph.clear()
        self.assertEqual(self.graph.stats["triplet_count"], 0)
        self.assertEqual(len(self.graph.entity_codes), 0)


class TestGraphAdapterDisabled(unittest.TestCase):
    """测试禁用状态的 GraphAdapter"""

    def test_disabled_no_effect(self):
        """测试禁用时不生效"""
        config = {"enabled": False}
        graph = GraphAdapter(config)
        graph.initialize()
        graph.add_triplet("A", "朋友", "B")
        self.assertEqual(graph.stats["triplet_count"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
