#!/usr/bin/env python3
"""
Scene Entity Indexer - M-Flow范式核心组件
从scene_blocks抽取实体和三元组，构建知识图谱

功能：
1. 读取 /root/.openclaw/memory-tdai/scene_blocks/ 下所有 .md 文件
2. 从每个文件的 META 头提取 entities 列表（如有）
3. 用规则抽取三元组，调用 GraphAdapter 存储
4. 构建 entity_scene_map 导出到 tunnel_index.json
"""

import os
import re
import glob
import json
import sys
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, asdict

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph_adapter import GraphAdapter
from triple_extractor import TripleExtractor
from graph_config import GRAPH_CONFIG, is_graph_enabled


@dataclass
class SceneMeta:
    """场景文件META信息"""
    created: str = ""
    updated: str = ""
    summary: str = ""
    heat: int = 0
    entities: List[str] = None

    def __post_init__(self):
        if self.entities is None:
            self.entities = []


class SceneEntityIndexer:
    """
    场景实体索引器
    从scene_blocks抽取实体和三元组，构建知识图谱
    """

    def __init__(
        self,
        scene_blocks_dir: str = "/root/.openclaw/memory-tdai/scene_blocks",
        tunnel_index_path: str = None,
        graph_adapter: GraphAdapter = None
    ):
        self.scene_blocks_dir = scene_blocks_dir
        self.tunnel_index_path = tunnel_index_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "tunnel_index.json"
        )
        self.triple_extractor = TripleExtractor()

        # 初始化图谱适配器
        if graph_adapter is None:
            self.graph_adapter = GraphAdapter(GRAPH_CONFIG)
            self.graph_adapter.initialize()
        else:
            self.graph_adapter = graph_adapter

        # 统计
        self.stats = {
            "files_processed": 0,
            "entities_found": 0,
            "triples_extracted": 0,
            "scenes_indexed": 0,
        }

    def parse_scene_file(self, file_path: str) -> Tuple[SceneMeta, str]:
        """解析场景文件，提取META和内容"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取META块
        meta_match = re.search(
            r'-----META-START-----(.*?)-----META-END-----',
            content,
            re.DOTALL
        )

        meta = SceneMeta()
        body = content

        if meta_match:
            meta_text = meta_match.group(1)
            body = content[meta_match.end():].strip()

            # 解析META字段
            created_match = re.search(r'created:\s*(.+)', meta_text)
            if created_match:
                meta.created = created_match.group(1).strip()

            updated_match = re.search(r'updated:\s*(.+)', meta_text)
            if updated_match:
                meta.updated = updated_match.group(1).strip()

            summary_match = re.search(r'summary:\s*(.+)', meta_text)
            if summary_match:
                meta.summary = summary_match.group(1).strip()

            heat_match = re.search(r'heat:\s*(\d+)', meta_text)
            if heat_match:
                meta.heat = int(heat_match.group(1))

            entities_match = re.search(r'entities:\s*\[(.*?)\]', meta_text, re.DOTALL)
            if entities_match:
                entities_str = entities_match.group(1)
                meta.entities = [e.strip().strip('"\'') for e in entities_str.split(',') if e.strip()]

        # 从文件名提取场景名
        filename = os.path.basename(file_path)
        scene_name = os.path.splitext(filename)[0]

        return meta, body, scene_name

    def extract_entities_from_text(self, text: str) -> List[str]:
        """从文本提取实体"""
        entities = set()

        # 使用TripleExtractor提取
        triples = self.triple_extractor.extract_from_text(text)
        for triple in triples:
            entities.add(triple.head)
            entities.add(triple.tail)

        # 提取@提及
        mention_pattern = r'@([\w\u4e00-\u9fa5]+)'
        mentions = re.findall(mention_pattern, text)
        entities.update(mentions)

        # 提取中文词组（2-5字）
        word_pattern = r'[\u4e00-\u9fa5]{2,5}'
        words = re.findall(word_pattern, text)
        entities.update(words)

        # 过滤停用词
        stopwords = {'的', '了', '是', '在', '和', '与', '或', '以及', '等', '个', '以', '及', '为', '对', '这', '那', '有', '我', '你', '他', '她', '它', '们', '将', '被', '把', '向', '从', '到', '给', '用', '于', '因', '但', '而', '如果', '则', '就', '都', '也', '还', '又', '只', '要', '会', '能', '可', '应该', '可能', '必须', '需要', '知道', '认为', '觉得', '希望', '可以'}
        entities = {e for e in entities if e not in stopwords and len(e) >= 2}

        return list(entities)

    def extract_triples_from_text(self, text: str) -> List[Tuple[str, str, str]]:
        """从文本提取三元组"""
        triples = self.triple_extractor.extract_from_text(text)
        return [t.to_tuple() for t in triples]

    def index_scene_file(self, file_path: str) -> Dict:
        """索引单个场景文件"""
        meta, body, scene_name = self.parse_scene_file(file_path)

        # 提取实体
        text_entities = self.extract_entities_from_text(body)
        all_entities = list(set(meta.entities + text_entities))
        self.stats["entities_found"] += len(all_entities)

        # 提取三元组
        triples = self.extract_triples_from_text(body)
        self.stats["triples_extracted"] += len(triples)

        # 添加三元组到图谱
        for head, relation, tail in triples:
            self.graph_adapter.add_triplet(head, relation, tail)

        # 构建场景实体映射
        scene_info = {
            "file": os.path.basename(file_path),
            "scene_name": scene_name,
            "entities": all_entities,
            "entity_count": len(all_entities),
            "triple_count": len(triples),
            "created": meta.created,
            "updated": meta.updated,
            "heat": meta.heat,
        }

        self.stats["scenes_indexed"] += 1

        return scene_info

    def build_entity_scene_map(self, scene_infos: List[Dict]) -> Dict[str, List[str]]:
        """构建entity到scene的反向索引"""
        entity_scene_map = {}

        for scene_info in scene_infos:
            scene_name = scene_info["scene_name"]
            for entity in scene_info["entities"]:
                if entity not in entity_scene_map:
                    entity_scene_map[entity] = []
                if scene_name not in entity_scene_map[entity]:
                    entity_scene_map[entity].append(scene_name)

        return entity_scene_map

    def build_index(self, only_scenes: List[str] = None) -> Dict:
        """索引场景文件（增量更新入口）"""
        return self.index_all(only_scenes=only_scenes)

    def index_all(self, only_scenes: List[str] = None) -> Dict:
        """索引场景文件

        Args:
            only_scenes: 如果指定，只索引这些场景名（不含扩展名）。
                       用于增量更新。
        """
        print(f"🔍 开始索引场景文件: {self.scene_blocks_dir}")

        # 获取所有.md文件
        pattern = os.path.join(self.scene_blocks_dir, "*.md")
        files = glob.glob(pattern)

        # 增量更新：只处理指定的场景
        if only_scenes:
            files = [
                f for f in files
                if os.path.splitext(os.path.basename(f))[0] in set(only_scenes)
            ]
            print(f"   🎯 增量模式: 只索引 {len(files)} 个变化的场景")

        if not files:
            print(f"⚠️  未找到场景文件: {pattern}")
            return {}

        print(f"📁 找到 {len(files)} 个场景文件")

        scene_infos = []

        for file_path in sorted(files):
            print(f"\n📄 处理: {os.path.basename(file_path)}")
            try:
                scene_info = self.index_scene_file(file_path)
                scene_infos.append(scene_info)
                print(f"   ✅ 实体: {scene_info['entity_count']}, 三元组: {scene_info['triple_count']}")
                self.stats["files_processed"] += 1
            except Exception as e:
                print(f"   ❌ 处理失败: {e}")

        # 构建entity_scene_map
        entity_scene_map = self.build_entity_scene_map(scene_infos)

        # 收集 scene_mtimes（用于增量更新）
        scene_mtimes = {}
        for file_path in files:
            scene_name = os.path.splitext(os.path.basename(file_path))[0]
            scene_mtimes[scene_name] = os.path.getmtime(file_path)

        # 构建tunnel_index
        tunnel_index = {
            "version": "4.0",
            "schema": "M-Flow entity_scene_map",
            "generated": self._get_timestamp(),
            "stats": self.stats,
            "entity_scene_map": entity_scene_map,
            "scenes": scene_infos,
            "scene_mtimes": scene_mtimes,
            "graph_stats": self.graph_adapter.get_stats(),
        }

        # 保存tunnel_index.json
        self._save_tunnel_index(tunnel_index)

        # 保存图谱数据
        self._save_graph_data()

        self._print_summary(tunnel_index)

        return tunnel_index

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()

    def _save_tunnel_index(self, tunnel_index: Dict) -> None:
        """保存tunnel_index.json"""
        os.makedirs(os.path.dirname(self.tunnel_index_path) or ".", exist_ok=True)
        with open(self.tunnel_index_path, 'w', encoding='utf-8') as f:
            json.dump(tunnel_index, f, ensure_ascii=False, indent=2)
        print(f"\n💾 tunnel_index.json 已保存: {self.tunnel_index_path}")

    def _save_graph_data(self) -> None:
        """保存图谱数据"""
        storage_path = GRAPH_CONFIG.get("storage_path", "./graph_cache")
        os.makedirs(storage_path, exist_ok=True)
        graph_path = os.path.join(storage_path, "graph_data.pkl")
        self.graph_adapter.save(graph_path)
        print(f"💾 图谱数据已保存: {graph_path}")

    def _print_summary(self, tunnel_index: Dict) -> None:
        """打印索引摘要"""
        print("\n" + "="*60)
        print("📊 SceneEntityIndexer 索引摘要")
        print("="*60)
        print(f"文件处理: {self.stats['files_processed']}")
        print(f"实体发现: {self.stats['entities_found']}")
        print(f"三元组抽取: {self.stats['triples_extracted']}")
        print(f"场景索引: {self.stats['scenes_indexed']}")
        print(f"\n图谱统计:")
        graph_stats = tunnel_index.get("graph_stats", {})
        print(f"  实体数: {graph_stats.get('entity_count', 0)}")
        print(f"  关系数: {graph_stats.get('relation_count', 0)}")
        print(f"  三元组数: {graph_stats.get('triplet_count', 0)}")
        print(f"  图节点: {graph_stats.get('graph_nodes', 0)}")
        print(f"  图边数: {graph_stats.get('graph_edges', 0)}")
        print(f"\n实体-场景映射: {len(tunnel_index.get('entity_scene_map', {}))} 个实体")
        print(f"tunnel_index: {self.tunnel_index_path}")
        print("="*60)

    def query_entity_scenes(self, entity: str) -> List[str]:
        """查询实体关联的场景"""
        if not os.path.exists(self.tunnel_index_path):
            return []

        with open(self.tunnel_index_path, 'r', encoding='utf-8') as f:
            tunnel_index = json.load(f)

        entity_scene_map = tunnel_index.get("entity_scene_map", {})
        return entity_scene_map.get(entity, [])

    def get_graph_adapter(self) -> GraphAdapter:
        """获取图谱适配器"""
        return self.graph_adapter


def main():
    """主函数 - 独立运行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='SceneEntityIndexer - 场景实体索引器')
    parser.add_argument('--dir', type=str,
                       default='/root/.openclaw/memory-tdai/scene_blocks',
                       help='场景文件目录')
    parser.add_argument('--output', type=str,
                       default=None,
                       help='tunnel_index.json输出路径')

    args = parser.parse_args()

    print("🚀 SceneEntityIndexer 启动")
    print(f"   场景目录: {args.dir}")

    indexer = SceneEntityIndexer(
        scene_blocks_dir=args.dir,
        tunnel_index_path=args.output
    )

    result = indexer.index_all()

    if result:
        print("\n✅ 索引完成!")
    else:
        print("\n❌ 索引失败")
        sys.exit(1)


if __name__ == "__main__":
    main()