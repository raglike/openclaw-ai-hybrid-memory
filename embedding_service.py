#!/usr/bin/env python3
"""
远程向量化服务（使用OpenClaw配置）
Remote Embedding Service using OpenClaw Configuration
"""

import json
import os
from typing import List, Union
import requests


class RemoteEmbeddingService:
    """远程向量化服务类（使用OpenClaw配置）"""

    def __init__(self, config_path: str = "/root/.openclaw/openclaw.json"):
        """初始化远程向量化服务

        Args:
            config_path: OpenClaw配置文件路径
        """
        # 加载OpenClaw配置
        with open(config_path, 'r') as f:
            config = json.load(f)

        # 获取memorySearch配置
        memory_search_config = config['agents']['defaults']['memorySearch']

        # 获取provider配置
        provider = memory_search_config['provider']
        model = memory_search_config['model']

        provider_config = config['models']['providers'][provider]

        self.base_url = provider_config['baseUrl']
        self.api_key = provider_config['apiKey']
        self.model = model

        self.embedding_dim = 4096  # Qwen3-Embedding-8B的实际维度

        print(f"✅ RemoteEmbeddingService initialized")
        print(f"   Provider: {provider}")
        print(f"   Model: {model}")
        print(f"   Base URL: {self.base_url}")
        print(f"   Embedding Dim: {self.embedding_dim}")

    def embed(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """将文本转换为向量

        Args:
            text: 文本或文本列表

        Returns:
            向量或向量列表
        """
        # 准备请求数据
        is_batch = isinstance(text, list)
        input_data = text if is_batch else [text]

        # 调用API
        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "input": input_data
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        # 解析响应
        result = response.json()
        embeddings = [item['embedding'] for item in result['data']]

        if is_batch:
            return embeddings
        else:
            return embeddings[0]

    def get_embedding_dim(self) -> int:
        """获取向量维度"""
        return self.embedding_dim


class MockEmbeddingService:
    """模拟向量化服务（用于离线测试）"""

    def __init__(self, dim: int = 1024):
        """初始化模拟服务

        Args:
            dim: 向量维度
        """
        self.dim = dim
        print(f"✅ MockEmbeddingService initialized (dim={dim})")

    def embed(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """模拟向量化

        Args:
            text: 文本或文本列表

        Returns:
            模拟向量或向量列表
        """
        import hashlib

        if isinstance(text, str):
            # 使用文本hash生成确定性的向量
            hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
            vector = [(hash_val % 100) / 100.0 for _ in range(self.dim)]
            return vector
        else:
            # 批量处理
            return [self.embed(t) for t in text]

    def get_embedding_dim(self) -> int:
        """获取向量维度"""
        return self.dim


def get_embedding_service(use_remote: bool = True) -> Union[RemoteEmbeddingService, MockEmbeddingService]:
    """获取向量化服务（自动选择）

    Args:
        use_remote: 是否尝试使用远程服务

    Returns:
        向量化服务实例
    """
    if use_remote:
        try:
            return RemoteEmbeddingService()
        except Exception as e:
            print(f"⚠️  无法初始化远程服务: {e}")
            print(f"   使用模拟服务")
            return MockEmbeddingService()
    else:
        return MockEmbeddingService()


# CLI接口
if __name__ == "__main__":
    import sys

    # 创建服务
    service = get_embedding_service(use_remote=True)

    # 测试
    if len(sys.argv) > 1:
        test_text = ' '.join(sys.argv[1:])
    else:
        test_text = "这是一条测试文本：OpenClaw混合记忆系统"

    print(f"\n🧪 测试文本: {test_text}")

    # 向量化
    vector = service.embed(test_text)

    print(f"✅ 向量化完成")
    print(f"   向量维度: {len(vector)}")
    print(f"   前5个值: {vector[:5]}")
    print(f"   后5个值: {vector[-5:]}")

    # 批量测试
    texts = [
        "OpenClaw混合记忆系统",
        "Chroma向量数据库",
        "LangChain Memory"
    ]

    print(f"\n🧪 批量测试 ({len(texts)} 条)")
    vectors = service.embed(texts)

    for i, (text, vec) in enumerate(zip(texts, vectors), 1):
        print(f"   {i}. {text}: dim={len(vec)}")