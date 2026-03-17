#!/usr/bin/env python3
"""
Daily文件索引器 - 向量化并索引Daily文件
Daily File Indexer - Vectorize and Index Daily Files
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import os
import re
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chroma_store import ChromaStore
from embedding_service import get_embedding_service


class DailyIndexer:
    """Daily文件索引器"""

    def __init__(
        self,
        daily_dir: str = "/root/.openclaw/workspace/memory",
        chroma_collection: str = "daily_files"
    ):
        """初始化索引器

        Args:
            daily_dir: Daily文件目录
            chroma_collection: Chroma集合名称
        """
        self.daily_dir = daily_dir
        self.chroma_collection = chroma_collection

        # 初始化服务
        self.embedding_service = get_embedding_service(use_remote=True)
        self.chroma_store = ChromaStore(collection_name=chroma_collection)

        # 缓存文件索引
        self._index_cache = {}

        print("✅ DailyIndexer initialized")
        print(f"   Daily Dir: {daily_dir}")
        print(f"   Chroma Collection: {chroma_collection}")

    def index_daily_file(self, date: str) -> int:
        """索引单个Daily文件

        Args:
            date: 日期 (YYYY-MM-DD)

        Returns:
            索引的段落数量
        """
        file_path = os.path.join(self.daily_dir, f"{date}.md")

        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            return 0

        print(f"📄 索引文件: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            return 0

        # 分段处理
        paragraphs = self._split_into_paragraphs(content)
        print(f"   找到 {len(paragraphs)} 个段落")

        # 向量化并存储
        indexed_count = 0
        for i, paragraph in enumerate(paragraphs):
            if len(paragraph.strip()) < 10:  # 跳过过短的段落
                continue

            try:
                vector = self.embedding_service.embed(paragraph)

                metadata = {
                    "date": date,
                    "date_iso": datetime.strptime(date, '%Y-%m-%d').isoformat(),
                    "paragraph_index": i,
                    "source": "daily_file",
                    "file_path": file_path
                }

                record_id = self.chroma_store.store(
                    content=paragraph,
                    embedding=vector,
                    metadata=metadata
                )

                indexed_count += 1

            except Exception as e:
                print(f"   ⚠️  索引段落 {i} 失败: {e}")
                continue

        print(f"   ✅ 索引完成: {indexed_count} 个段落")
        return indexed_count

    def index_all_daily_files(self, days: int = 30) -> int:
        """索引所有Daily文件

        Args:
            days: 索引最近N天

        Returns:
            总共索引的段落数量
        """
        print(f"\n📚 索引最近 {days} 天的Daily文件...")

        total_indexed = 0
        today = datetime.now()

        for day_offset in range(days):
            date = (today - timedelta(days=day_offset)).strftime('%Y-%m-%d')
            indexed = self.index_daily_file(date)
            total_indexed += indexed

        print(f"\n✅ 全部索引完成: {total_indexed} 个段落")
        return total_indexed

    def search_daily_files(self, query: str, top_k: int = 5) -> List[Dict]:
        """语义搜索Daily文件

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            搜索结果列表
        """
        print(f"\n🔍 搜索Daily文件: {query[:100]}...")

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
                result['source'] = 'daily'
                result['date'] = metadata.get('date', 'unknown')
                result['days_ago'] = self._calculate_days_ago(metadata.get('date_iso'))

            print(f"   ✅ 找到 {len(results)} 条结果")
            return results

        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            return []

    def rebuild_index(self, days: int = 30) -> int:
        """重建索引（清除旧数据后重新索引）

        Args:
            days: 索引最近N天

        Returns:
            总共索引的段落数量
        """
        print(f"\n🔄 重建索引...")

        # 清除Chroma集合
        try:
            self.chroma_store.clear_collection()
            print("   ✅ 清除旧索引")
        except Exception as e:
            print(f"   ⚠️  清除失败: {e}")

        # 重新索引
        return self.index_all_daily_files(days=days)

    def get_index_stats(self) -> Dict:
        """获取索引统计

        Returns:
            统计信息字典
        """
        stats = self.chroma_store.get_stats()

        # 统计Daily文件数量
        daily_files = len(glob.glob(os.path.join(self.daily_dir, "*.md")))
        stats['daily_files_count'] = daily_files

        return stats

    def _split_into_paragraphs(self, content: str) -> List[str]:
        """将内容分割成段落

        Args:
            content: 文本内容

        Returns:
            段落列表
        """
        # 按标题分割
        paragraphs = re.split(r'\n##+\s*', content)

        # 过滤空段落
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        return paragraphs

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

    parser = argparse.ArgumentParser(description='Daily文件索引器')
    parser.add_argument('command', choices=['index', 'search', 'rebuild', 'stats'],
                        help='命令: index/search/rebuild/stats')
    parser.add_argument('--date', type=str, help='日期 (YYYY-MM-DD)')
    parser.add_argument('--days', type=int, default=30, help='索引天数')
    parser.add_argument('--query', type=str, help='查询文本')
    parser.add_argument('--top-k', type=int, default=5, help='返回结果数量')

    args = parser.parse_args()

    # 创建索引器实例
    indexer = DailyIndexer()

    if args.command == 'index':
        if args.date:
            indexed = indexer.index_daily_file(args.date)
        else:
            indexed = indexer.index_all_daily_files(days=args.days)
        print(f"✅ 索引完成: {indexed} 个段落")

    elif args.command == 'search':
        if not args.query:
            print("❌ 请提供 --query 参数")
            sys.exit(1)

        results = indexer.search_daily_files(args.query, top_k=args.top_k)
        print(f"\n📊 搜索结果 ({len(results)} 条):")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. 日期: {result.get('date', 'unknown')}")
            print(f"   距离: {result.get('distance', 0):.3f}")
            print(f"   相关性: {1.0 - result.get('distance', 1.0):.3f}")
            print(f"   内容: {result.get('content', '')[:100]}...")

    elif args.command == 'rebuild':
        indexed = indexer.rebuild_index(days=args.days)
        print(f"✅ 重建完成: {indexed} 个段落")

    elif args.command == 'stats':
        stats = indexer.get_index_stats()
        print(f"\n📊 索引统计:")
        print(f"   总记录数: {stats.get('total_records', 0)}")
        print(f"   Daily文件数: {stats.get('daily_files_count', 0)}")
        print(f"   集合名称: {stats.get('collection_name', 'N/A')}")
