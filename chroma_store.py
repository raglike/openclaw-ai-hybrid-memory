#!/usr/bin/env python3
"""
Chroma向量存储基础实现
Chroma Vector Store - Basic Implementation
"""

import chromadb
from chromadb.config import Settings
from typing import Dict, List, Optional, Any
import time
import json


class ChromaStore:
    """Chroma向量存储类"""

    def __init__(self, persist_directory: str = "./chroma_db", collection_name: str = "openclaw_memory"):
        """初始化Chroma存储

        Args:
            persist_directory: 持久化目录路径
            collection_name: Collection名称
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name

        # 初始化Chroma客户端（持久化模式）
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # 获取或创建collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={
                "description": "OpenClaw混合记忆系统",
                "version": "1.0.0",
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S UTC")
            }
        )

        print(f"✅ ChromaStore initialized: {persist_directory}")

    def store(
        self,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """存储记忆

        Args:
            content: 记忆内容
            embedding: 向量表示
            metadata: 元数据（可选）

        Returns:
            str: 记录ID
        """
        # 生成唯一ID
        record_id = f"mem_{int(time.time() * 1000)}_{id(content)}"

        # 确保metadata不为空（Chroma要求）
        if metadata is None:
            metadata = {"_auto": True}
        elif not metadata:
            metadata = {"_auto": True}

        # 添加到collection
        self.collection.add(
            ids=[record_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[metadata]
        )

        print(f"✅ Stored: {record_id} (len={len(embedding)})")
        return record_id

    def retrieve(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """检索记忆

        Args:
            query_embedding: 查询向量
            n_results: 返回结果数量
            where: 元数据过滤条件（可选）

        Returns:
            List[Dict]: 检索结果列表
        """
        # 执行查询
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )

        # 格式化结果
        return self._format_results(results)

    def retrieve_by_id(
        self,
        record_id: str
    ) -> Optional[Dict[str, Any]]:
        """通过ID检索记忆

        Args:
            record_id: 记录ID

        Returns:
            Optional[Dict]: 记忆内容或None
        """
        try:
            results = self.collection.get(ids=[record_id], include=['documents', 'embeddings', 'metadatas'])

            if not results['ids'] or not results['ids'][0]:
                return None

            return {
                'id': results['ids'][0],
                'content': results['documents'][0] if results.get('documents') else None,
                'embedding': results['embeddings'][0] if results.get('embeddings') else None,
                'metadata': results['metadatas'][0] if results.get('metadatas') else None
            }
        except Exception as e:
            print(f"❌ Error retrieving by ID: {e}")
            import traceback
            traceback.print_exc()
            return None

    def update_metadata(
        self,
        record_id: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """更新元数据

        Args:
            record_id: 记录ID
            metadata: 新的元数据

        Returns:
            bool: 是否成功
        """
        try:
            self.collection.update(
                ids=[record_id],
                metadatas=[metadata]
            )
            print(f"✅ Updated metadata: {record_id}")
            return True
        except Exception as e:
            print(f"❌ Error updating metadata: {e}")
            return False

    def delete(self, record_id: str) -> bool:
        """删除记录

        Args:
            record_id: 记录ID

        Returns:
            bool: 是否成功
        """
        try:
            self.collection.delete(ids=[record_id])
            print(f"✅ Deleted: {record_id}")
            return True
        except Exception as e:
            print(f"❌ Error deleting: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            Dict: 统计信息
        """
        try:
            count = self.collection.count()

            return {
                "total_records": count,
                "persist_directory": self.persist_directory,
                "collection_name": self.collection_name
            }
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return {"error": str(e)}

    def reset(self) -> bool:
        """重置数据库（删除所有数据）

        Returns:
            bool: 是否成功
        """
        try:
            self.client.reset()
            # 重新创建collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={
                    "description": "OpenClaw混合记忆系统",
                    "version": "1.0.0",
                    "created_at": time.strftime("%Y-%m-%d %H:%M:%S UTC")
                }
            )
            print("✅ Database reset")
            return True
        except Exception as e:
            print(f"❌ Error resetting: {e}")
            return False

    def _format_results(self, results: Dict) -> List[Dict[str, Any]]:
        """格式化查询结果

        Args:
            results: Chroma查询结果

        Returns:
            List[Dict]: 格式化后的结果
        """
        formatted = []

        if not results['ids'] or not results['ids'][0]:
            return formatted

        for i in range(len(results['ids'][0])):
            formatted.append({
                'id': results['ids'][0][i],
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None
            })

        return formatted

    def __repr__(self) -> str:
        stats = self.get_stats()
        return f"ChromaStore(records={stats.get('total_records', 0)})"


# CLI接口
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python chroma_store.py stats")
        print("  python chroma_store.py reset")
        sys.exit(1)

    command = sys.argv[1]

    # 创建存储实例
    store = ChromaStore(persist_directory="/root/.openclaw/workspace/chroma_db")

    if command == "stats":
        stats = store.get_stats()
        print(f"\n📊 ChromaStore统计:")
        print(f"   总记录数: {stats.get('total_records', 0)}")
        print(f"   持久化目录: {stats.get('persist_directory', 'N/A')}")
        print(f"   Collection: {stats.get('collection_name', 'N/A')}")

    elif command == "reset":
        confirm = input("⚠️  确认重置数据库？(yes/no): ")
        if confirm.lower() == "yes":
            if store.reset():
                print("✅ 数据库已重置")
            else:
                print("❌ 重置失败")
        else:
            print("❌ 已取消")

    else:
        print(f"❌ 未知命令: {command}")