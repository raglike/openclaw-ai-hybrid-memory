"""
模拟向量化服务 - 用于离线演示和测试

注意：这是一个模拟实现，生成的向量不是真实的语义向量。
生产环境应使用真实的sentence-transformers模型。
"""
from typing import List, Union
import hashlib
import random


class MockEmbeddingService:
    """模拟向量化服务类（用于离线演示）"""
    
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2", embedding_dim: int = 384):
        """初始化模拟向量化服务
        
        Args:
            model_name: 模型名称（仅用于记录）
            embedding_dim: 向量维度（默认384）
        """
        self.model_name = model_name
        self.embedding_dim = embedding_dim
        print(f"✅ MockEmbeddingService initialized: {model_name}")
        print(f"⚠️ 注意: 这是模拟实现，需要真实模型请确保网络可访问Hugging Face")
    
    def embed(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """将文本转换为向量（模拟实现）
        
        Args:
            text: 文本或文本列表
            
        Returns:
            向量或向量列表（384维）
        """
        if isinstance(text, str):
            return self._text_to_vector(text)
        else:
            return [self._text_to_vector(t) for t in text]
    
    def _text_to_vector(self, text: str) -> List[float]:
        """将单个文本转换为向量（基于文本哈希）"""
        # 使用文本哈希生成确定性的向量
        hash_obj = hashlib.md5(text.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()
        
        # 将哈希值转换为向量
        vector = []
        for i in range(self.embedding_dim):
            # 组合多个哈希值来生成浮点数
            idx = i % len(hash_hex)
            char_val = int(hash_hex[idx % len(hash_hex)], 16)
            normalized = char_val / 15.0  # 归一化到 [0, 1]
            vector.append(normalized * 2 - 1)  # 缩放到 [-1, 1]
        
        return vector
    
    def get_embedding_dim(self) -> int:
        """获取向量维度"""
        return self.embedding_dim
