#!/usr/bin/env python3
"""
数据迁移脚本
从现有记忆文件提取三元组，构建初始图谱
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph_adapter import GraphAdapter
from triple_extractor import TripleExtractor
from graph_config import GRAPH_CONFIG
import glob


def migrate_from_memory_files():
    """从记忆文件迁移数据到图谱"""
    print("=" * 60)
    print("数据迁移: 记忆文件 -> 图谱")
    print("=" * 60)

    # 初始化
    graph = GraphAdapter(GRAPH_CONFIG)
    graph.initialize()
    extractor = TripleExtractor()

    # 扫描记忆文件
    memory_files = []

    # 1. 扫描 workspace/memory 目录
    memory_dir = "/root/.openclaw/workspace/memory"
    if os.path.exists(memory_dir):
        memory_files.extend(glob.glob(os.path.join(memory_dir, "**/*.md"), recursive=True))

    # 2. 扫描 workspace 根目录
    workspace_dir = "/root/.openclaw/workspace"
    if os.path.exists(workspace_dir):
        memory_files.extend(glob.glob(os.path.join(workspace_dir, "MEMORY.md")))
        memory_files.extend(glob.glob(os.path.join(workspace_dir, "**/MEMORY.md"), recursive=True))

    # 去重
    memory_files = list(set(memory_files))

    print(f"\n找到 {len(memory_files)} 个记忆文件")

    # 提取三元组
    all_triplets = []
    for file_path in memory_files:
        if not os.path.exists(file_path):
            continue

        try:
            triples = extractor.extract_from_memory_file(file_path)
            triplet_tuples = [t.to_tuple() for t in triples]
            all_triplets.extend(triplet_tuples)
            print(f"  {os.path.basename(file_path)}: {len(triplet_tuples)}  triplets")
        except Exception as e:
            print(f"  ⚠️  {file_path}: {e}")

    print(f"\n共提取 {len(all_triplets)} 个三元组")

    # 添加到图谱
    graph.add_triplets(all_triplets)
    print(f"图谱统计: {graph.stats}")

    # 保存
    storage_path = GRAPH_CONFIG.get("storage_path", "./graph_cache")
    os.makedirs(storage_path, exist_ok=True)
    graph_path = os.path.join(storage_path, "graph_data.pkl")
    graph.save(graph_path)

    size_mb = graph.get_storage_size() / (1024 * 1024)
    print(f"\n✅ 迁移完成!")
    print(f"   存储位置: {graph_path}")
    print(f"   存储大小: {size_mb:.4f} MB")
    print(f"   实体数: {graph.stats['entity_count']}")
    print(f"   关系数: {graph.stats['relation_count']}")
    print(f"   三元组数: {graph.stats['triplet_count']}")

    return graph


def main():
    migrate_from_memory_files()


if __name__ == "__main__":
    main()
