#!/usr/bin/env python3
"""
单元测试: TripleExtractor
"""

import unittest
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from triple_extractor import TripleExtractor, Triple, extract_triplets


class TestTripleExtractor(unittest.TestCase):
    """TripleExtractor 单元测试"""

    def setUp(self):
        """测试前准备"""
        self.extractor = TripleExtractor()

    def test_extract_by_rules(self):
        """测试规则提取"""
        text = "@助管理@文案，@文案撰写AI资讯"
        triples = self.extractor.extract_from_text(text)

        self.assertGreater(len(triples), 0)
        # 检查是否有管理关系
        relations = [t.relation for t in triples]
        self.assertTrue(any("管理" in r for r in relations))

    def test_extract_entities(self):
        """测试实体提取"""
        text = "@助和@文案一起工作，使用Chroma和NetworkX"
        entities = self.extractor._extract_entities(text)

        self.assertIn("@助", entities)
        self.assertIn("@文案", entities)
        self.assertIn("Chroma", entities)
        self.assertIn("NetworkX", entities)

    def test_infer_relation(self):
        """测试关系推断"""
        text1 = "使用Python开发AI应用"
        entities1 = ["Python", "AI应用"]
        rel1 = self.extractor._infer_relation(text1, entities1)
        self.assertEqual(rel1, "使用")

        text2 = "开发视频制作系统"
        entities2 = ["视频制作", "系统"]
        rel2 = self.extractor._infer_relation(text2, entities2)
        self.assertEqual(rel2, "开发")

    def test_deduplicate(self):
        """测试去重"""
        triples = [
            Triple("A", "朋友", "B", 0.8),
            Triple("A", "朋友", "B", 0.9),  # 重复
            Triple("B", "朋友", "C", 0.7),
        ]
        unique = self.extractor._deduplicate(triples)
        self.assertEqual(len(unique), 2)

    def test_extract_from_text_no_entities(self):
        """测试无实体文本"""
        text = "这是一段没有任何实体的纯文本"
        triples = self.extractor.extract_from_text(text)
        # 共现提取可能产生结果，但规则提取不会
        self.assertIsInstance(triples, list)

    def test_extract_from_text_with_agent_mentions(self):
        """测试带@提及的文本"""
        text = "@助协调@开和@测试，@开开发了视频制作功能"
        triples = self.extractor.extract_from_text(text)
        self.assertGreater(len(triples), 0)

    def test_triple_to_tuple(self):
        """测试Triple转元组"""
        triple = Triple("A", "朋友", "B", 0.8)
        tup = triple.to_tuple()
        self.assertEqual(tup, ("A", "朋友", "B"))

    def test_triple_to_dict(self):
        """测试Triple转字典"""
        triple = Triple("A", "朋友", "B", 0.8, "rule")
        d = triple.to_dict()
        self.assertEqual(d["head"], "A")
        self.assertEqual(d["relation"], "朋友")
        self.assertEqual(d["tail"], "B")
        self.assertEqual(d["confidence"], 0.8)
        self.assertEqual(d["source"], "rule")

    def test_extract_from_memory_file(self):
        """测试从文件提取"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("@助负责团队管理\n")
            f.write("@开开发视频制作\n")
            f.write("使用Python和FFmpeg\n")
            f.flush()
            temp_path = f.name

        try:
            triples = self.extractor.extract_from_memory_file(temp_path)
            self.assertGreater(len(triples), 0)
        finally:
            os.unlink(temp_path)

    def test_extract_from_nonexistent_file(self):
        """测试从不存在文件提取"""
        triples = self.extractor.extract_from_memory_file("/nonexistent/file.md")
        self.assertEqual(len(triples), 0)

    def test_extract_triplets_as_tuples(self):
        """测试便捷函数"""
        text = "@助管理@文案"
        tuples = self.extractor.extract_triplets_as_tuples(text)
        self.assertIsInstance(tuples, list)
        for t in tuples:
            self.assertEqual(len(t), 3)

    def test_min_confidence_filter(self):
        """测试最小置信度过滤"""
        extractor = TripleExtractor(min_confidence=0.9)
        text = "@助管理@文案"  # 规则提取置信度0.8
        triples = extractor.extract_from_text(text)
        # 低置信度的共现三元组可能被过滤
        self.assertIsInstance(triples, list)

    def test_get_stats(self):
        """测试统计信息"""
        stats = self.extractor.get_stats()
        self.assertIn("min_confidence", stats)
        self.assertIn("relation_patterns", stats)


class TestExtractTriplets(unittest.TestCase):
    """便捷函数测试"""

    def test_extract_triplets_function(self):
        """测试extract_triplets函数"""
        text = "@助管理@文案"
        tuples = extract_triplets(text)
        self.assertIsInstance(tuples, list)
        for t in tuples:
            self.assertIsInstance(t, tuple)
            self.assertEqual(len(t), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
