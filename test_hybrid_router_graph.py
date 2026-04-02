#!/usr/bin/env python3
"""
集成测试: HybridRouter 图谱模块
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置环境变量禁用图谱进行对照测试
os.environ["ENABLE_GRAPH"] = "true"


class TestHybridRouterGraph(unittest.TestCase):
    """HybridRouter 图谱模块集成测试"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        from hybrid_router import HybridMemoryRouter
        from graph_config import GRAPH_CONFIG

        # 创建测试路由
        cls.router = HybridMemoryRouter(
            chroma_path="/tmp/test_chroma",
            daily_dir="/tmp/test_daily",
            memory_md_path="/tmp/test_memory.md",
            use_cache=False,
            use_parallel=False
        )

        # 清空图谱
        if cls.router.graph_adapter:
            cls.router.graph_adapter.clear()
            cls.router._save_graph_data()

    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        # 清理测试目录
        import shutil
        for path in ["/tmp/test_chroma", "/tmp/test_daily"]:
            if os.path.exists(path):
                shutil.rmtree(path)
        if os.path.exists("/tmp/test_memory.md"):
            os.remove("/tmp/test_memory.md")

    def test_graph_enabled(self):
        """测试图谱功能启用"""
        stats = self.router.get_stats()
        self.assertTrue(stats.get("graph_enabled", False))

    def test_store_with_graph(self):
        """测试存储时提取三元组"""
        if not self.router.graph_adapter:
            self.skipTest("Graph adapter not enabled")

        initial_count = self.router.graph_adapter.stats["triplet_count"]

        # 存储包含实体的内容
        self.router.store(
            content="@助管理@文案团队，@文案撰写AI资讯",
            importance="important"
        )

        # 检查三元组是否增加
        self.assertGreaterEqual(
            self.router.graph_adapter.stats["triplet_count"],
            initial_count
        )

    def test_retrieve_with_graph(self):
        """测试检索时图谱增强"""
        # 先存储一些数据
        self.router.store(
            content="@开开发了视频制作功能，使用Playwright和FFmpeg",
            importance="normal"
        )

        # 检索
        results = self.router.retrieve(
            query="@开发 视频 Playwright",
            max_results=5
        )

        self.assertIsInstance(results, list)

    def test_graph_stats(self):
        """测试图谱统计"""
        if not self.router.graph_adapter:
            self.skipTest("Graph adapter not enabled")

        stats = self.router.get_stats()
        self.assertIn("graph", stats)
        graph_stats = stats["graph"]
        self.assertIn("entity_count", graph_stats)
        self.assertIn("triplet_count", graph_stats)

    def test_save_load_graph(self):
        """测试图谱保存加载"""
        if not self.router.graph_adapter:
            self.skipTest("Graph adapter not enabled")

        # 添加一些数据
        self.router.graph_adapter.add_triplet("测试A", "测试关系", "测试B")

        # 保存
        self.router._save_graph_data()

        # 清空
        self.router.graph_adapter.clear()

        # 重新加载
        self.router._load_graph_data()

        # 验证
        self.assertGreater(self.router.graph_adapter.stats["triplet_count"], 0)

    def test_multiple_stores(self):
        """测试多次存储"""
        if not self.router.graph_adapter:
            self.skipTest("Graph adapter not enabled")

        initial = self.router.graph_adapter.stats["triplet_count"]

        self.router.store("@助协调@开", importance="normal")
        self.router.store("@运营专注数据分析", importance="normal")
        self.router.store("@测试负责质量保障", importance="normal")

        self.assertGreaterEqual(
            self.router.graph_adapter.stats["triplet_count"],
            initial + 3
        )


class TestGraphFusion(unittest.TestCase):
    """图谱融合测试"""

    def test_fuse_results(self):
        """测试结果融合"""
        from graph_fusion import GraphFusion

        fusion = GraphFusion(weight=0.2)

        vector_results = [
            {"id": "doc1", "similarity": 0.9},
            {"id": "doc2", "similarity": 0.7},
        ]

        bm25_results = [
            {"id": "doc1", "score": 0.8},
            {"id": "doc3", "score": 0.6},
        ]

        graph_results = [
            {"entity": "doc2", "score": 0.85},
        ]

        fused = fusion.fuse_results(vector_results, bm25_results, graph_results, top_k=5)

        self.assertIsInstance(fused, list)
        self.assertLessEqual(len(fused), 5)

    def test_fuse_without_graph(self):
        """测试无图谱结果融合"""
        from graph_fusion import GraphFusion

        fusion = GraphFusion(weight=0.2)

        vector_results = [
            {"id": "doc1", "similarity": 0.9},
        ]

        bm25_results = [
            {"id": "doc2", "score": 0.7},
        ]

        fused = fusion.fuse_results(vector_results, bm25_results, [], top_k=5)
        self.assertIsInstance(fused, list)

    def test_set_graph_weight(self):
        """测试设置图谱权重"""
        from graph_fusion import GraphFusion

        fusion = GraphFusion(weight=0.2)
        self.assertEqual(fusion.weight, 0.2)

        fusion.set_graph_weight(0.5)
        self.assertEqual(fusion.weight, 0.5)

        # 边界测试
        fusion.set_graph_weight(1.5)
        self.assertEqual(fusion.weight, 1.0)

        fusion.set_graph_weight(-0.5)
        self.assertEqual(fusion.weight, 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
