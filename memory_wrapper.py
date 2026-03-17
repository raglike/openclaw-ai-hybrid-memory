"""
统一记忆接口包装层
兼容OpenClaw现有的memory_search工具
"""

from typing import List, Dict, Optional
from hybrid_router import HybridMemoryRouter


class MemoryWrapper:
    """统一记忆接口包装层"""
    
    def __init__(self):
        """初始化"""
        self.router = HybridMemoryRouter()
        print("✅ MemoryWrapper initialized")
    
    def search(
        self,
        query: str,
        max_results: int = 10,
        min_score: float = 0.5,
        **kwargs
    ) -> List[Dict]:
        """搜索记忆（兼容OpenClaw接口）
        
        Args:
            query: 查询文本
            max_results: 最大返回结果数
            min_score: 最低分数
            **kwargs: 其他参数
            
        Returns:
            搜索结果列表
        """
        return self.router.retrieve(
            query=query,
            max_results=max_results,
            min_score=min_score,
            **kwargs
        )
    
    def store(
        self,
        content: str,
        metadata: Optional[Dict] = None,
        importance: str = "normal"
    ) -> str:
        """存储记忆
        
        Args:
            content: 记忆内容
            metadata: 元数据
            importance: 重要性
            
        Returns:
            记录ID
        """
        return self.router.store(
            content=content,
            metadata=metadata,
            importance=importance
        )
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.router.get_stats()
