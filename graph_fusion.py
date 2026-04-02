"""
图谱融合模块
将图谱检索结果与向量/BM25结果融合
"""

from typing import List, Dict, Optional


class GraphFusion:
    """
    图谱融合模块
    将图谱检索结果与向量/BM25结果融合
    """

    def __init__(self, graph_adapter=None, weight: float = 0.2):
        self.graph = graph_adapter
        self.weight = weight  # 图谱权重
        self.vector_weight = 1.0 - weight
        self.bm25_weight = (1.0 - weight) * 0.5

    def fuse_results(
        self,
        vector_results: List[Dict],
        bm25_results: List[Dict],
        graph_results: List[Dict],
        top_k: int = 10
    ) -> List[Dict]:
        """
        融合多路检索结果

        Args:
            vector_results: 向量检索结果
            bm25_results: BM25检索结果
            graph_results: 图谱检索结果
            top_k: 返回结果数

        Returns:
            融合后的排序结果
        """
        if not graph_results:
            # 无图谱结果时，回退到向量+BM25融合
            return self._fuse_without_graph(vector_results, bm25_results, top_k)

        # 1. 归一化分数
        vector_scores = self._normalize(vector_results, score_key="similarity")
        bm25_scores = self._normalize(bm25_results, score_key="score")
        graph_scores = self._normalize(graph_results, score_key="score")

        # 2. 合并分数
        combined = {}

        for item in vector_scores:
            key = item.get("id", item.get("content", ""))
            if key:
                combined[key] = combined.get(key, 0) + item["score"] * self.vector_weight

        for item in bm25_scores:
            key = item.get("id", item.get("content", ""))
            if key:
                combined[key] = combined.get(key, 0) + item["score"] * self.bm25_weight

        for item in graph_scores:
            key = item.get("entity", item.get("content", ""))
            if key:
                combined[key] = combined.get(key, 0) + item["score"] * self.weight

        # 3. 排序返回
        sorted_results = sorted(combined.items(), key=lambda x: -x[1])
        return [{"id": k, "score": v, "source": "fused"} for k, v in sorted_results[:top_k]]

    def _fuse_without_graph(
        self,
        vector_results: List[Dict],
        bm25_results: List[Dict],
        top_k: int = 10
    ) -> List[Dict]:
        """无图谱结果的融合"""
        vector_scores = self._normalize(vector_results, score_key="similarity")
        bm25_scores = self._normalize(bm25_results, score_key="score")

        combined = {}

        for item in vector_scores:
            key = item.get("id", item.get("content", ""))
            if key:
                combined[key] = combined.get(key, 0) + item["score"] * 0.6

        for item in bm25_scores:
            key = item.get("id", item.get("content", ""))
            if key:
                combined[key] = combined.get(key, 0) + item["score"] * 0.4

        sorted_results = sorted(combined.items(), key=lambda x: -x[1])
        return [{"id": k, "score": v, "source": "fused"} for k, v in sorted_results[:top_k]]

    def _normalize(self, results: List[Dict], score_key: str = "score") -> List[Dict]:
        """归一化分数到 [0, 1]"""
        if not results:
            return []

        scores = []
        for r in results:
            score = r.get("score", 0)
            if score_key == "similarity":
                score = r.get("similarity", score)
            scores.append(score)

        min_s, max_s = min(scores), max(scores)

        if max_s == min_s:
            return [{**r, "score": 1.0 if scores[i] > 0 else 0.0} for i, r in enumerate(results)]

        return [
            {**r, "score": (scores[i] - min_s) / (max_s - min_s)}
            for i, r in enumerate(results)
        ]

    def set_graph_weight(self, weight: float) -> None:
        """设置图谱权重"""
        self.weight = max(0.0, min(1.0, weight))
        self.vector_weight = 1.0 - self.weight
        self.bm25_weight = self.vector_weight * 0.5

    def get_config(self) -> Dict:
        """获取融合配置"""
        return {
            "weight": self.weight,
            "vector_weight": self.vector_weight,
            "bm25_weight": self.bm25_weight,
        }
