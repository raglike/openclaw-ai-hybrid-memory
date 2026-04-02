"""
LightKG 图谱适配器
基于码本学习的轻量级知识图谱嵌入
集成 NetworkX 图结构
"""

import numpy as np
import networkx as nx
import pickle
from typing import List, Dict, Tuple, Optional, Any
import os


class GraphAdapter:
    """
    LightKG 图谱适配器
    对接现有 HybridRouter
    支持码本学习 + NetworkX 图结构
    """

    def __init__(self, config: Dict):
        self.config = config
        self.enabled = config.get("enabled", True)
        self.dim = config.get("embedding_dim", 64)
        self.codebook_size = config.get("codebook_size", 256)
        self.storage_path = config.get("storage_path", "./graph_cache")
        self.max_depth = config.get("max_depth", 3)

        # 存储
        self.entity_codes = {}
        self.relation_codes = {}
        self.entity_residuals = {}
        self.relation_residuals = {}
        self.entity_scales = {}
        self.relation_scales = {}
        self.codebook = None

        # NetworkX 图谱
        self.graph = None
        self.metadata = {}

        # 统计
        self.stats = {
            "entity_count": 0,
            "relation_count": 0,
            "triplet_count": 0,
        }

    def initialize(self) -> None:
        """初始化"""
        self.graph = nx.DiGraph()
        self.codebook = np.random.randn(
            self.codebook_size, self.dim
        ).astype(np.float32) * 0.1

        # 归一化码本
        norms = np.linalg.norm(self.codebook, axis=1, keepdims=True)
        norms[norms == 0] = 1
        self.codebook = self.codebook / norms * 0.1

        print(f"✅ GraphAdapter initialized: dim={self.dim}, codebook={self.codebook_size}")

    def add_triplet(self, head: str, relation: str, tail: str, weight: float = 1.0) -> None:
        """添加三元组"""
        if not self.enabled:
            return

        # 添加到图谱
        self.graph.add_edge(head, tail, relation=relation, weight=weight)
        self.metadata[(head, relation, tail)] = {"weight": weight}

        # 分配码本索引
        if head not in self.entity_codes:
            self.entity_codes[head] = hash(head) % self.codebook_size
            self.entity_residuals[head] = np.zeros(self.dim, dtype=np.int8)
            self.entity_scales[head] = 1.0
            self.stats["entity_count"] += 1

        if tail not in self.entity_codes:
            self.entity_codes[tail] = hash(tail) % self.codebook_size
            self.entity_residuals[tail] = np.zeros(self.dim, dtype=np.int8)
            self.entity_scales[tail] = 1.0
            self.stats["entity_count"] += 1

        if relation not in self.relation_codes:
            self.relation_codes[relation] = hash(relation) % self.codebook_size
            self.relation_residuals[relation] = np.zeros(self.dim, dtype=np.int8)
            self.relation_scales[relation] = 1.0
            self.stats["relation_count"] += 1

        self.stats["triplet_count"] += 1

    def add_triplets(self, triplets: List[Tuple[str, str, str]], weights: List[float] = None) -> None:
        """批量添加三元组"""
        for i, (h, r, t) in enumerate(triplets):
            w = weights[i] if weights and i < len(weights) else 1.0
            self.add_triplet(h, r, t, w)

    def get_neighbors(self, entity: str, relation: str = None) -> List[str]:
        """获取邻居节点"""
        if entity not in self.graph:
            return []

        neighbors = []
        for _, tail, data in self.graph.out_edges(entity, data=True):
            if relation is None or data.get("relation") == relation:
                neighbors.append(tail)
        return neighbors

    def traverse(self, start: str, depth: int = 2) -> List[Tuple[str, List[str]]]:
        """路径遍历"""
        try:
            return list(nx.single_source_shortest_path(
                self.graph, start, cutoff=depth
            ).items())
        except:
            return []

    def get_subgraph(self, center: str, radius: int = 2) -> nx.DiGraph:
        """获取子图"""
        if center not in self.graph:
            return nx.DiGraph()

        nodes = {center}
        current_level = {center}

        for _ in range(radius):
            next_level = set()
            for n in current_level:
                next_level.update(self.graph.successors(n))
                next_level.update(self.graph.predecessors(n))
            nodes.update(next_level)
            current_level = next_level

        return self.graph.subgraph(nodes).copy()

    def query_related(self, entity: str, top_k: int = 10) -> List[Dict]:
        """查询相关实体"""
        if entity not in self.graph:
            return []

        # 获取多跳邻居
        related = set()
        paths = self.traverse(entity, depth=2)

        for node, path in paths:
            if node != entity:
                related.add(node)

        # 排序（按路径长度）
        results = []
        for node in related:
            try:
                path_len = len(nx.shortest_path(self.graph, entity, node))
            except:
                path_len = 3
            results.append({
                "entity": node,
                "path_length": path_len,
                "score": 1.0 / path_len
            })

        results.sort(key=lambda x: -x["score"])
        return results[:top_k]

    def get_embedding(self, entity: str) -> np.ndarray:
        """获取实体嵌入向量"""
        if entity not in self.entity_codes or self.codebook is None:
            return np.zeros(self.dim, dtype=np.float32)

        code = self.entity_codes[entity]
        residual = self.entity_residuals[entity].astype(np.float32) / max(self.entity_scales[entity], 1e-8)
        return self.codebook[code] + residual

    def get_relation_embedding(self, relation: str) -> np.ndarray:
        """获取关系嵌入向量"""
        if relation not in self.relation_codes or self.codebook is None:
            return np.zeros(self.dim, dtype=np.float32)

        code = self.relation_codes[relation]
        residual = self.relation_residuals[relation].astype(np.float32) / max(self.relation_scales[relation], 1e-8)
        return self.codebook[code] + residual

    def predict_tail(self, head: str, relation: str, top_k: int = 5) -> List[str]:
        """预测尾实体: head + relation -> ?"""
        if head not in self.entity_codes or relation not in self.relation_codes:
            return []

        h_emb = self.get_embedding(head)
        r_emb = self.get_relation_embedding(relation)

        results = []
        for e in self.entity_codes:
            if e == head:
                continue
            t_emb = self.get_embedding(e)
            score = float(np.abs(h_emb + r_emb - t_emb).sum())
            results.append((e, score))

        results.sort(key=lambda x: x[1])
        return [e for e, _ in results[:top_k]]

    def save(self, path: str) -> None:
        """保存图谱数据"""
        # 确保目录存在
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)

        data = {
            "entity_codes": self.entity_codes,
            "relation_codes": self.relation_codes,
            "entity_residuals": self.entity_residuals,
            "relation_residuals": self.relation_residuals,
            "entity_scales": self.entity_scales,
            "relation_scales": self.relation_scales,
            "codebook": self.codebook,
            "stats": self.stats,
            "metadata": self.metadata,
            "dim": self.dim,
            "codebook_size": self.codebook_size,
        }

        # 保存完整数据
        with open(path, "wb") as f:
            pickle.dump(data, f)

        # 保存图结构（NetworkX）
        graph_path = path + ".graph"
        with open(graph_path, "wb") as f:
            pickle.dump({"graph_adj": nx.to_dict_of_dicts(self.graph), "metadata": self.metadata}, f)

    def load(self, path: str) -> None:
        """加载图谱数据"""
        # 加载完整数据
        if os.path.exists(path):
            with open(path, "rb") as f:
                data = pickle.load(f)

            self.entity_codes = data["entity_codes"]
            self.relation_codes = data["relation_codes"]
            self.entity_residuals = data["entity_residuals"]
            self.relation_residuals = data["relation_residuals"]
            self.entity_scales = data.get("entity_scales", {})
            self.relation_scales = data.get("relation_scales", {})
            self.codebook = data["codebook"]
            self.stats = data["stats"]
            self.metadata = data.get("metadata", {})
            self.dim = data["dim"]
            self.codebook_size = data["codebook_size"]

        # 加载图结构
        graph_path = path + ".graph"
        if os.path.exists(graph_path):
            with open(graph_path, "rb") as f:
                graph_data = pickle.load(f)
            self.graph = nx.from_dict_of_dicts(graph_data["graph_adj"], create_using=nx.DiGraph())
            self.metadata = graph_data.get("metadata", {})
        else:
            self.graph = nx.DiGraph()

    def get_storage_size(self) -> int:
        """获取存储大小（字节）"""
        size = 0
        if self.codebook is not None:
            size += self.codebook.nbytes
        size += len(self.entity_codes) * 4
        size += len(self.relation_codes) * 4
        size += sum(v.nbytes for v in self.entity_residuals.values())
        size += sum(v.nbytes for v in self.relation_residuals.values())
        size += len(self.entity_scales) * 4
        size += len(self.relation_scales) * 4
        return size

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            "storage_bytes": self.get_storage_size(),
            "storage_mb": self.get_storage_size() / (1024 * 1024),
            "graph_nodes": self.graph.number_of_nodes(),
            "graph_edges": self.graph.number_of_edges(),
        }

    def clear(self) -> None:
        """清空图谱"""
        self.graph.clear()
        self.entity_codes.clear()
        self.relation_codes.clear()
        self.entity_residuals.clear()
        self.relation_residuals.clear()
        self.entity_scales.clear()
        self.relation_scales.clear()
        self.metadata.clear()
        self.stats = {
            "entity_count": 0,
            "relation_count": 0,
            "triplet_count": 0,
        }
