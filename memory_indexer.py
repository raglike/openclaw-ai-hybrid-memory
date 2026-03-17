#!/usr/bin/env python3
"""
MEMORY.md索引器 - 向量化并索引MEMORY.md
MEMORY.md Indexer - Vectorize and Index MEMORY.md
"""

from typing import List, Dict, Optional
from datetime import datetime
import os
import re
import sys
import glob

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chroma_store import ChromaStore
from embedding_service import get_embedding_service


class MemoryIndexer:
    """MEMORY.md索引器"""

    def __init__(
        self,
        memory_md_path: str = "/root/.openclaw/workspace/MEMORY.md",
        chroma_collection: str = "memory_md"
    ):
        """初始化索引器

        Args:
            memory_md_path: MEMORY.md文件路径
            chroma_collection: Chroma集合名称
        """
        self.memory_md_path = memory_md_path
        self.chroma_collection = chroma_collection

        # 初始化服务
        self.embedding_service = get_embedding_service(use_remote=True)
        self.chroma_store = ChromaStore(collection_name=chroma_collection)

        print("✅ MemoryIndexer initialized")
        print(f"   MEMORY.md: {memory_md_path}")
        print(f"   Chroma Collection: {chroma_collection}")

    def index_memory_md(self) -> int:
        """索引MEMORY.md

        Returns:
            索引的段落数量
        """
        if not os.path.exists(self.memory_md_path):
            print(f"❌ 文件不存在: {self.memory_md_path}")
            return 0

        print(f"📄 索引文件: {self.memory_md_path}")

        try:
            with open(self.memory_md_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            return 0

        # 分段处理
        sections = self._split_into_sections(content)
        print(f"   找到 {len(sections)} 个节")

        # 向量化并存储
        indexed_count = 0
        for i, (section_name, section_content) in enumerate(sections):
            if len(section_content.strip()) < 10:  # 跳过过短的节
                continue

            try:
                vector = self.embedding_service.embed(section_content)

                metadata = {
                    "section_name": section_name,
                    "section_index": i,
                    "source": "memory_md",
                    "file_path": self.memory_md_path,
                    "updated_at": datetime.now().isoformat()
                }

                record_id = self.chroma_store.store(
                    content=section_content,
                    embedding=vector,
                    metadata=metadata
                )

                indexed_count += 1

            except Exception as e:
                print(f"   ⚠️  索引节 {i} 失败: {e}")
                continue

        print(f"   ✅ 索引完成: {indexed_count} 个节")
        return indexed_count

    def search_memory_md(self, query: str, top_k: int = 5) -> List[Dict]:
        """语义搜索MEMORY.md

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            搜索结果列表
        """
        print(f"\n🔍 搜索MEMORY.md: {query[:100]}...")

        try:
            # 向量化查询
            query_vector = self.embedding_service.embed(query)

            # 在Chroma中搜索
            results = self.chroma_store.retrieve(
                query_embedding=query_vector,
                n_results=top_k
            )

            # 添加额外信息
            for result in results:
                metadata = result.get('metadata', {})
                result['source'] = 'memory_md'
                result['section_name'] = metadata.get('section_name', 'unknown')
                result['days_ago'] = 999  # 长期记忆

            print(f"   ✅ 找到 {len(results)} 条结果")
            return results

        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            return []

    def rebuild_index(self) -> int:
        """重建索引（清除旧数据后重新索引）

        Returns:
            索引的段落数量
        """
        print(f"\n🔄 重建索引...")

        # 清除Chroma集合
        try:
            self.chroma_store.clear_collection()
            print("   ✅ 清除旧索引")
        except Exception as e:
            print(f"   ⚠️  清除失败: {e}")

        # 重新索引
        return self.index_memory_md()

    def get_index_stats(self) -> Dict:
        """获取索引统计

        Returns:
            统计信息字典
        """
        stats = self.chroma_store.get_stats()

        # 添加MEMORY.md状态
        stats['memory_md_exists'] = os.path.exists(self.memory_md_path)
        stats['memory_md_size'] = os.path.getsize(self.memory_md_path) if os.path.exists(self.memory_md_path) else 0

        return stats

    def _split_into_sections(self, content: str) -> List[tuple]:
        """将内容分割成节

        Args:
            content: 文本内容

        Returns:
            节列表 (section_name, section_content)
        """
        # 按一级标题分割
        sections = re.split(r'\n#+\s+', content)

        # 第一个通常是文件名或空行，跳过
        if sections:
            sections[0] = ("Introduction", sections[0].strip())

        # 处理每个节
        result = []
        for i, section in enumerate(sections):
            if isinstance(section, str):
                # 标题和内容
                lines = section.strip().split('\n', 1)
                if len(lines) == 2:
                    title, content = lines
                else:
                    title = f"Section {i}"
                    content = lines[0]

                result.append((title.strip(), content.strip()))

        return result

    def _calculate_days_ago(self, date_iso: Optional[str]) -> int:
        """计算从日期到现在的天数

        Args:
            date_iso: ISO格式的时间字符串

        Returns:
            天数
        """
        if not date_iso:
            return 0

        try:
            date = datetime.fromisoformat(date_iso)
            days_ago = (datetime.now() - date).days
            return max(0, days_ago)
        except Exception:
            return 0


# CLI接口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='MEMORY.md索引器')
    parser.add_argument('command', choices=['index', 'search', 'rebuild', 'stats'],
                        help='命令: index/search/rebuild/stats')
    parser.add_argument('--query', type=str, help='查询文本')
    parser.add_argument('--top-k', type=int, default=5, help='返回结果数量')

    args = parser.parse_args()

    # 创建索引器实例
    indexer = MemoryIndexer()

    if args.command == 'index':
        indexed = indexer.index_memory_md()
        print(f"✅ 索引完成: {indexed} 个节")

    elif args.command == 'search':
        if not args.query:
            print("❌ 请提供 --query 参数")
            sys.exit(1)

        results = indexer.search_memory_md(args.query, top_k=args.top_k)
        print(f"\n📊 搜索结果 ({len(results)} 条):")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. 节名: {result.get('section_name', 'unknown')}")
            print(f"   距离: {result.get('distance', 0):.3f}")
            print(f"   相关性: {1.0 - result.get('distance', 1.0):.3f}")
            print(f"   内容: {result.get('content', '')[:100]}...")

    elif args.command == 'rebuild':
        indexed = indexer.rebuild_index()
        print(f"✅ 重建完成: {indexed} 个节")

    elif args.command == 'stats':
        stats = indexer.get_index_stats()
        print(f"\n📊 索引统计:")
        print(f"   总记录数: {stats.get('total_records', 0)}")
        print(f"   MEMORY.md存在: {stats.get('memory_md_exists', False)}")
        print(f"   文件大小: {stats.get('memory_md_size', 0)} 字节")
        print(f"   集合名称: {stats.get('collection_name', 'N/A')}")
