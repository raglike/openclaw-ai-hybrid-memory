#!/usr/bin/env python3
"""
混合记忆路由器 - 整合Chroma、Daily文件、MEMORY.md
Hybrid Memory Router - Chroma + Daily Files + MEMORY.md Integration

Phase 2 - Day 2更新:
- 集成DailyIndexer实现语义检索
- 集成MemoryIndexer实现MEMORY.md语义检索
- 集成LRU Cache提升性能
- 支持批量向量化和异步并发

M-Flow升级 (Phase 4):
- 集成SceneEntityIndexer的tunnel_index.json
- EntityBundle跨场景聚合
- GraphFusion路径成本重排
"""

from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
import os
import glob
import sys
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

# 添加父目录到路径，以便导入依赖模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chroma_store import ChromaStore
from embedding_service import get_embedding_service
from daily_indexer import DailyIndexer
from memory_indexer import MemoryIndexer
from cache import get_query_cache, get_embedding_cache, LRUCache
from bm25_indexer import DailyFileIndexer
from hybrid_fusion import triple_fusion

# 导入图谱模块
from graph_config import GRAPH_CONFIG, FEATURE_FLAGS, is_graph_enabled, is_auto_extract_enabled, is_fusion_enabled
from graph_adapter import GraphAdapter
from triple_extractor import TripleExtractor
from graph_fusion import GraphFusion
from scene_entity_indexer import SceneEntityIndexer
from feedback import RetrievalFeedback


class HybridMemoryRouter:
    """混合记忆路由器"""

    def __init__(
        self,
        chroma_path: str = "/root/.openclaw/workspace/chroma_db",
        daily_dir: str = "/root/.openclaw/workspace/memory",
        memory_md_path: str = "/root/.openclaw/workspace/MEMORY.md",
        use_cache: bool = True,
        use_parallel: bool = True,
        max_workers: int = 8  # Phase 4 - Day 1优化：从4增加到8
    ):
        """初始化路由器

        Args:
            chroma_path: Chroma数据库持久化目录
            daily_dir: Daily文件目录
            memory_md_path: MEMORY.md文件路径
            use_cache: 是否使用缓存
            use_parallel: 是否并行处理
            max_workers: 最大工作线程数（Phase 4 - Day 1优化：默认值改为8）
        """
        # 初始化服务
        self.embedding_service = get_embedding_service(use_remote=True)
        self.chroma_store = ChromaStore(persist_directory=chroma_path)

        # 初始化索引器（用于语义检索）
        self.daily_indexer = DailyIndexer(daily_dir=daily_dir)
        self.memory_indexer = MemoryIndexer(memory_md_path=memory_md_path)

        # 初始化缓存
        self.use_cache = use_cache
        self.query_cache = get_query_cache() if use_cache else None
        self.embedding_cache = get_embedding_cache() if use_cache else None

        # 并行处理配置
        self.use_parallel = use_parallel
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers) if use_parallel else None

        # 路径配置
        self.daily_dir = daily_dir
        self.memory_md_path = memory_md_path

        # 确保daily目录存在
        os.makedirs(self.daily_dir, exist_ok=True)

        # 初始化BM25索引器
        print("📚 初始化BM25索引器...")
        self.bm25_indexer = DailyFileIndexer()

        # 为Daily文件建立BM25索引
        print("   索引Daily文件...")
        for day_offset in range(7):
            date = (datetime.now() - timedelta(days=day_offset)).strftime('%Y-%m-%d')
            file_path = os.path.join(self.daily_dir, f"{date}.md")
            if os.path.exists(file_path):
                self.bm25_indexer.index_file(file_path)

        # 构建BM25索引
        try:
            self.bm25_indexer.build_index()
            print("   ✅ BM25索引构建完成")
        except Exception as e:
            print(f"   ⚠️  BM25索引构建失败: {e}")

        print("✅ HybridMemoryRouter initialized")
        print(f"   Chroma: {chroma_path}")
        print(f"   Daily Dir: {daily_dir}")
        print(f"   MEMORY.md: {memory_md_path}")
        print(f"   Cache: {use_cache}")
        print(f"   Parallel: {use_parallel} (workers={max_workers})")
        print(f"   BM25: Enabled")

        # ==================== 图谱模块初始化 ====================
        self._init_graph_module()

    def _init_graph_module(self) -> None:
        """初始化图谱模块"""
        if not is_graph_enabled():
            print("   Graph: Disabled (enable_graph=False)")
            self.graph_adapter = None
            self.triple_extractor = None
            self.graph_fusion = None
            self.entity_scene_map = {}
            return

        print("   Graph: Initializing...")

        # 初始化图谱适配器
        self.graph_adapter = GraphAdapter(GRAPH_CONFIG)
        self.graph_adapter.initialize()

        # 初始化三元组提取器
        self.triple_extractor = TripleExtractor()

        # 初始化图谱融合器
        self.graph_fusion = GraphFusion(
            self.graph_adapter,
            weight=GRAPH_CONFIG.get("fusion_weight", 0.2)
        )

        # 初始化检索反馈模块 (P2)
        self.feedback = RetrievalFeedback()

        # 加载已有图谱数据
        self._load_graph_data()

        # 加载tunnel_index.json (M-Flow EntityBundle)
        self._load_tunnel_index()

        print(f"   Graph: Enabled (entities={self.graph_adapter.stats['entity_count']}, "
              f"triplets={self.graph_adapter.stats['triplet_count']})")
        if self.entity_scene_map:
            print(f"   EntityBundle: {len(self.entity_scene_map)} entities mapped")

    def _load_graph_data(self) -> None:
        """加载图谱数据"""
        if not is_graph_enabled() or self.graph_adapter is None:
            return

        graph_path = os.path.join(GRAPH_CONFIG.get("storage_path", "./graph_cache"), "graph_data.pkl")
        try:
            self.graph_adapter.load(graph_path)
            print(f"   ✅ Loaded graph data: {self.graph_adapter.stats}")
        except FileNotFoundError:
            print("   📝 No existing graph data, will build from memory files")

    def _save_graph_data(self) -> None:
        """保存图谱数据"""
        if not is_graph_enabled() or self.graph_adapter is None:
            return

        os.makedirs(GRAPH_CONFIG.get("storage_path", "./graph_cache"), exist_ok=True)
        path = os.path.join(GRAPH_CONFIG.get("storage_path", "./graph_cache"), "graph_data.pkl")
        self.graph_adapter.save(path)

    def _load_tunnel_index(self) -> None:
        """加载tunnel_index.json - M-Flow EntityBundle

        增量更新机制：
        - 每次加载时检查 scene_blocks 目录中所有 .md 文件的 mtime
        - 与 tunnel_index.json 中存储的 scene_mtimes 对比
        - 有变化的场景触发增量重抽，更新 tunnel_index.json
        """
        self.entity_scene_map = {}

        tunnel_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "tunnel_index.json"
        )

        # Step 1: 收集当前 scene_blocks 目录的 mtime
        scene_blocks_dir = "/root/.openclaw/memory-tdai/scene_blocks"
        current_mtimes = {}
        if os.path.exists(scene_blocks_dir):
            for f in glob.glob(os.path.join(scene_blocks_dir, "*.md")):
                scene_name = os.path.splitext(os.path.basename(f))[0]
                current_mtimes[scene_name] = os.path.getmtime(f)

        # Step 2: 如果 tunnel_index.json 存在，加载并做增量对比
        if not os.path.exists(tunnel_path):
            # 从零构建
            print("   📝 No tunnel_index.json found, building from scratch...")
            self._rebuild_tunnel_index(scene_blocks_dir)
            return

        try:
            with open(tunnel_path, 'r', encoding='utf-8') as f:
                tunnel_data = json.load(f)

            stored_mtimes = tunnel_data.get("scene_mtimes", {})
            changed_scenes = [
                name for name, mtime in current_mtimes.items()
                if stored_mtimes.get(name, 0) < mtime
            ]

            self.entity_scene_map = tunnel_data.get("entity_scene_map", {})
            self.tunnel_scenes = {s["scene_name"]: s for s in tunnel_data.get("scenes", [])}

            if changed_scenes:
                print(f"   🔄 Incremental update: {len(changed_scenes)} scenes changed → re-indexing")
                self._incremental_update(scene_blocks_dir, changed_scenes, tunnel_data)
            else:
                print(f"   ✅ Loaded tunnel_index: {len(self.entity_scene_map)} entity-scene mappings (up to date)")

        except Exception as e:
            print(f"   ⚠️  Failed to load tunnel_index.json: {e}, rebuilding...")
            self._rebuild_tunnel_index(scene_blocks_dir)
            self.entity_scene_map = {}
            self.tunnel_scenes = {}

    def _rebuild_tunnel_index(self, scene_blocks_dir: str) -> None:
        """全量重建 tunnel_index.json"""
        try:
            indexer = SceneEntityIndexer(scene_blocks_dir=scene_blocks_dir)
            result = indexer.build_index()

            tunnel_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "tunnel_index.json"
            )
            with open(tunnel_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            self.entity_scene_map = result.get("entity_scene_map", {})
            self.tunnel_scenes = {s["scene_name"]: s for s in result.get("scenes", [])}
            print(f"   ✅ Rebuilt tunnel_index: {len(self.entity_scene_map)} entity-scene mappings")
            self._sync_to_memory_tdai()
        except Exception as e:
            print(f"   ❌ Failed to rebuild tunnel_index: {e}")
            self.entity_scene_map = {}
            self.tunnel_scenes = {}

    def _incremental_update(
        self,
        scene_blocks_dir: str,
        changed_scenes: List[str],
        tunnel_data: Dict
    ) -> None:
        """增量更新：只重抽变化的场景，合并到现有 tunnel_index.json"""
        try:
            indexer = SceneEntityIndexer(scene_blocks_dir=scene_blocks_dir)
            # 只索引变化的场景
            result = indexer.build_index(only_scenes=changed_scenes)

            # 合并 entity_scene_map（替换变化的，保留其他的）
            new_map = tunnel_data.get("entity_scene_map", {})
            new_map.update(result.get("entity_scene_map", {}))

            # 合并 scenes
            old_scenes = {s["scene_name"]: s for s in tunnel_data.get("scenes", [])}
            old_scenes.update({s["scene_name"]: s for s in result.get("scenes", [])})

            # 合并 scene_mtimes
            new_mtimes = tunnel_data.get("scene_mtimes", {})
            new_mtimes.update(result.get("scene_mtimes", {}))

            # 写回 tunnel_index.json
            tunnel_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "tunnel_index.json"
            )
            updated_data = {
                "entity_scene_map": new_map,
                "scenes": list(old_scenes.values()),
                "scene_mtimes": new_mtimes,
                "updated_at": datetime.now().isoformat()
            }
            with open(tunnel_path, 'w', encoding='utf-8') as f:
                json.dump(updated_data, f, ensure_ascii=False, indent=2)

            self.entity_scene_map = new_map
            self.tunnel_scenes = old_scenes
            print(f"   ✅ Incremental update done: {len(self.entity_scene_map)} total mappings")
            self._sync_to_memory_tdai()

        except Exception as e:
            print(f"   ❌ Incremental update failed: {e}, falling back to full rebuild")
            self._rebuild_tunnel_index(scene_blocks_dir)

    def _sync_to_memory_tdai(self) -> None:
        """将 hybrid-memory tunnel_index 同步到 memory-tdai tunnel_index.json

        实现 OpenClaw 内置检索 对增强数据的读取
        """
        import subprocess
        sync_script = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "sync_to_memory_tdai.py"
        )
        try:
            result = subprocess.run(
                ["python3", sync_script],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                print(f"   🔗 Synced to memory-tdai tunnel_index")
            else:
                print(f"   ⚠️ Sync failed: {result.stderr[:100]}")
        except Exception as e:
            print(f"   ⚠️ Sync error: {e}")

    def _expand_entity_bundle(
        self,
        query: str,
        initial_results: List[Dict],
        top_k: int = 5
    ) -> List[Dict]:
        """M-Flow EntityBundle扩展层

        仅从查询本身提取实体，通过entity_scene_map找到相关场景，
        聚合为EntityBundle返回

        Args:
            query: 查询文本
            initial_results: 初始检索结果（未使用，仅保持接口签名）
            top_k: 返回的Bundle数量

        Returns:
            EntityBundle聚合结果
        """
        if not self.entity_scene_map or not self.triple_extractor:
            return []

        # 仅从查询本身提取实体
        query_entities = self.triple_extractor._extract_entities(query)
        if not query_entities:
            return []

        # 通过entity_scene_map扩展场景
        related_scenes = {}

        # P1改进：真实图路径成本计算
        for entity in query_entities:
            # 精确匹配（1跳，权重2.0）
            if entity in self.entity_scene_map:
                for scene_name in self.entity_scene_map[entity]:
                    if scene_name not in related_scenes:
                        related_scenes[scene_name] = {
                            "entities": [], "score": 0.0,
                            "exact_score": 0, "path_cost": 999.0
                        }
                    related_scenes[scene_name]["entities"].append(entity)
                    related_scenes[scene_name]["score"] += 2.0
                    related_scenes[scene_name]["exact_score"] += 1
                    related_scenes[scene_name]["path_cost"] = min(
                        related_scenes[scene_name]["path_cost"], 1.0
                    )

            # 包含匹配（2跳，权重1.0）
            if len(entity) >= 4:
                for mapped_entity, scenes in self.entity_scene_map.items():
                    if entity in mapped_entity and len(mapped_entity) - len(entity) <= 10:
                        for scene_name in scenes:
                            if scene_name not in related_scenes:
                                related_scenes[scene_name] = {
                                    "entities": [], "score": 0.0,
                                    "exact_score": 0, "path_cost": 999.0
                                }
                            related_scenes[scene_name]["entities"].append(mapped_entity)
                            related_scenes[scene_name]["score"] += 0.5
                            related_scenes[scene_name]["path_cost"] = min(
                                related_scenes[scene_name]["path_cost"], 2.0
                            )

            # P1新增：图谱多跳传播
            # 如果GraphAdapter有该实体的邻居，通过邻居找更多场景（3跳）
            if self.graph_adapter and hasattr(self.graph_adapter, 'get_neighbors'):
                neighbors = self.graph_adapter.get_neighbors(entity)
                for neighbor in neighbors[:5]:  # 最多5个邻居
                    if neighbor in self.entity_scene_map:
                        for scene_name in self.entity_scene_map[neighbor]:
                            if scene_name not in related_scenes:
                                related_scenes[scene_name] = {
                                    "entities": [], "score": 0.0,
                                    "exact_score": 0, "path_cost": 999.0
                                }
                            related_scenes[scene_name]["entities"].append(f"{entity}→{neighbor}")
                            related_scenes[scene_name]["score"] += 0.3  # 3跳，低权重
                            related_scenes[scene_name]["path_cost"] = min(
                                related_scenes[scene_name]["path_cost"], 3.0
                            )

        if not related_scenes:
            return []

        # P1改进：综合排序 - 精确匹配数 × 路径成本
        # score = exact_score * 10 - path_cost * 0.5
        bundles = []
        for scene_name, info in sorted(
            related_scenes.items(),
            key=lambda x: (-x[1]["exact_score"], -x[1]["path_cost"])
        )[:top_k]:
            scene_info = self.tunnel_scenes.get(scene_name, {})

            # 获取该场景的摘要信息
            summary = scene_info.get("summary", f"场景: {scene_name}")

            # P1：路径成本归一化作为relevance
            path_cost = info.get("path_cost", 999.0)
            relevance = max(0.0, 1.0 - (path_cost - 1.0) * 0.2) if path_cost < 999.0 else 0.1

            bundle = {
                "id": f"bundle_{scene_name}",
                "content": summary,
                "source": "entity_bundle",
                "scene_name": scene_name,
                "bundle_entities": info["entities"],
                "bundle_score": info["score"],
                "bundle_exact_matches": info["exact_score"],
                "bundle_path_cost": path_cost,
                "relevance": relevance,
                "days_ago": 0,
            }
            bundles.append(bundle)

        print(f"   🔗 EntityBundle: {len(bundles)} scene bundles expanded")
        return bundles

    def _graph_rerank(
        self,
        results: List[Dict],
        query: str,
        top_k: int = 10
    ) -> List[Dict]:
        """GraphFusion路径成本重排

        使用图谱路径成本对结果进行重排

        Args:
            results: 初始排序结果
            query: 查询文本
            top_k: 返回结果数

        Returns:
            重排后的结果
        """
        if not is_fusion_enabled() or self.graph_adapter is None:
            return results

        # 提取查询中的实体
        query_entities = []
        if self.triple_extractor:
            query_entities = self.triple_extractor._extract_entities(query)

        if not query_entities:
            return results

        # 计算每个结果的图谱路径成本
        reranked = []
        for result in results:
            content = result.get('content', '')
            result_entities = []
            if self.triple_extractor:
                result_entities = self.triple_extractor._extract_entities(content)

            # 计算路径成本（与查询实体的连接强度）
            path_cost = 0.0
            for qe in query_entities:
                for re in result_entities:
                    if qe == re or qe in re or re in qe:
                        path_cost += 1.0
                    # 检查图谱中是否有连接
                    neighbors = self.graph_adapter.get_neighbors(qe)
                    if re in neighbors:
                        path_cost += 2.0

            # 综合评分 = 原评分 + 路径成本 * 0.2
            new_score = result.get('score', 0) + path_cost * 0.2
            result['graph_score'] = new_score
            result['path_cost'] = path_cost
            reranked.append(result)

        # 按graph_score排序
        reranked.sort(key=lambda x: -x.get('graph_score', 0))

        return reranked[:top_k]

    def _merge_bundle_results(
        self,
        initial_results: List[Dict],
        bundle_results: List[Dict],
        max_results: int = 10
    ) -> List[Dict]:
        """合并EntityBundle结果与初始结果

        Args:
            initial_results: 初始检索结果
            bundle_results: EntityBundle扩展结果
            max_results: 最大结果数

        Returns:
            合并后的排序结果
        """
        # 使用(content的前100字符)作为唯一标识，避免id为空导致碰撞
        seen_keys = set()
        merged = []

        for i, r in enumerate(initial_results):
            key = r.get('id') or r.get('content', '')[:100] or f'initial_{i}'
            if key not in seen_keys:
                merged.append(r)
                seen_keys.add(key)

        # 添加Bundle结果（标记来源）
        for bundle in bundle_results:
            bundle_id = bundle.get('id', '')
            if bundle_id and bundle_id not in seen_keys:
                merged.append(bundle)
                seen_keys.add(bundle_id)

        # 按分数重新排序
        merged.sort(key=lambda x: x.get('score', 0), reverse=True)

        return merged[:max_results]

    def _graph_search(self, query: str, top_k: int = 10) -> List[Dict]:
        """图谱检索"""
        if not is_graph_enabled() or self.graph_adapter is None:
            return []

        # 提取查询中的实体
        entities = self.triple_extractor._extract_entities(query) if self.triple_extractor else []

        if not entities:
            return []

        # 查找最相关的实体
        results = []
        for entity in entities:
            related = self.graph_adapter.query_related(entity, top_k)
            results.extend(related)

        # 去重并排序
        seen = set()
        unique_results = []
        for r in results:
            if r["entity"] not in seen:
                seen.add(r["entity"])
                unique_results.append(r)

        return sorted(unique_results, key=lambda x: -x["score"])[:top_k]

    def retrieve(
        self,
        query: str,
        max_results: int = 10,
        time_window_days: int = 7,
        min_score: float = 0.3,  # Phase 4 - Day 1优化：从0.5降低到0.3
        use_semantic: bool = True
    ) -> List[Dict]:
        """混合检索

        Args:
            query: 查询文本
            max_results: 最大返回结果数
            time_window_days: 时间窗口（天）
            min_score: 最低分数
            use_semantic: 是否使用语义检索（True=语义, False=关键词）

        Returns:
            排序后的记忆列表
        """
        print(f"\n🔍 检索查询: {query[:100]}...")

        # 检查缓存
        cache_key_params = {
            'max_results': max_results,
            'time_window_days': time_window_days,
            'min_score': min_score,
            'use_semantic': use_semantic
        }

        if self.use_cache:
            cached_results = self.query_cache.get(query, cache_key_params)
            if cached_results is not None:
                print(f"   🎯 缓存命中: {len(cached_results)} 条")
                return cached_results[:max_results]

        # 1. 向量化查询
        try:
            query_vector = self._get_cached_embedding(query)
            print(f"   ✅ 向量化完成: dim={len(query_vector)}")
        except Exception as e:
            print(f"   ❌ 向量化失败: {e}")
            return []

        # 2. 并行检索
        print(f"   📊 并行检索中...")

        if self.use_parallel and use_semantic:
            # 使用语义检索 + 并行处理
            results = self._retrieve_parallel_semantic(
                query=query,
                query_vector=query_vector,
                max_results=max_results,
                time_window_days=time_window_days
            )
        elif use_semantic:
            # 使用语义检索（串行）
            chroma_results = self._retrieve_from_chroma(
                query_vector=query_vector,
                n_results=max_results * 2
            )
            print(f"      Chroma: {len(chroma_results)} 条")

            daily_results = self.daily_indexer.search_daily_files(
                query=query,
                top_k=max_results
            )
            print(f"      Daily (语义): {len(daily_results)} 条")

            memory_md_results = self.memory_indexer.search_memory_md(
                query=query,
                top_k=max_results
            )
            print(f"      MEMORY.md (语义): {len(memory_md_results)} 条")

            results = chroma_results + daily_results + memory_md_results
        else:
            # 使用关键词检索 + BM25 + 三重融合 (Day 2更新)
            # 向量检索
            chroma_results = self._retrieve_from_chroma(
                query_vector=query_vector,
                n_results=max_results * 2
            )
            print(f"      Chroma (向量): {len(chroma_results)} 条")

            # BM25检索
            try:
                bm25_results = self.bm25_indexer.search(query, top_k=max_results * 2)
                # 转换为标准格式
                bm25_results_converted = []
                for result in bm25_results:
                    bm25_results_converted.append({
                        'id': result['doc_id'],
                        'content': result['content'],
                        'score': result['score'],
                        'source': 'bm25'
                    })
                print(f"      BM25: {len(bm25_results_converted)} 条")
            except Exception as e:
                print(f"      BM25检索失败: {e}")
                bm25_results_converted = []

            # 简单关键词检索
            simple_results = self._retrieve_from_daily_keyword(
                query=query,
                days=time_window_days
            )
            print(f"      Daily (简单关键词): {len(simple_results)} 条")

            # 三重融合
            print(f"      🔥 三重融合中...")
            fused_results = triple_fusion(
                vector_results=chroma_results,
                bm25_results=bm25_results_converted,
                simple_results=simple_results,
                vector_weight=0.5,
                bm25_weight=0.3,
                simple_weight=0.2
            )
            print(f"      融合结果: {len(fused_results)} 条")

            results = fused_results

        # 3. 计算综合评分
        for result in results:
            result['score'] = self._calculate_score(result, query)

        # 4. 排序并返回Top-K
        results.sort(key=lambda x: x['score'], reverse=True)

        # 5. 图谱增强（可选）
        if is_graph_enabled() and is_fusion_enabled() and self.graph_adapter is not None:
            graph_results = self._graph_search(query, max_results)
            if graph_results:
                print(f"   🔗 Graph results: {len(graph_results)}")

        # 6. EntityBundle扩展层 (M-Flow)
        if self.entity_scene_map and self.tunnel_scenes:
            bundle_results = self._expand_entity_bundle(query, results, top_k=max_results)
            if bundle_results:
                # 将Bundle结果合并到最终结果
                for bundle in bundle_results:
                    bundle['score'] = self._calculate_score(bundle, query)
                    # 轻微提升Bundle分数以确保在同分时优先展示
                    bundle['score'] += 0.001
                results = self._merge_bundle_results(results, bundle_results)

        # 7. GraphFusion路径成本重排
        if is_graph_enabled() and is_fusion_enabled() and self.graph_adapter is not None:
            results = self._graph_rerank(results, query, top_k=max_results)

        # 8. 过滤低分结果
        filtered_results = [r for r in results if r['score'] >= min_score]

        # 9. 应用检索反馈boost (P2)
        if self.feedback:
            feedback_stats = self.feedback.get_stats()
            if feedback_stats['total'] > 0:
                filtered_results = self.feedback.apply_boost(filtered_results, query)
                filtered_results.sort(key=lambda x: x.get('score', 0), reverse=True)
                print(f"   👍 Feedback applied: {feedback_stats['total']} records (relevant={feedback_stats['relevant']})")

        print(f"   ✅ 最终结果: {len(filtered_results)}/{len(results)} 条 (min_score={min_score})")

        # 缓存结果
        if self.use_cache:
            self.query_cache.put(query, cache_key_params, filtered_results)

        return filtered_results[:max_results]

    def mark_result(self, query: str, result_content: str, relevant: bool = True):
        """标记检索结果质量（用于反馈学习）

        Args:
            query: 查询文本
            result_content: 结果内容
            relevant: True=有用, False=无用
        """
        if not self.feedback:
            return
        if relevant:
            self.feedback.mark_relevant(query, result_content)
        else:
            self.feedback.mark_irrelevant(query, result_content)

    def store(
        self,
        content: str,
        metadata: Optional[Dict] = None,
        importance: str = "normal"
    ) -> str:
        """存储新记忆

        Args:
            content: 记忆内容
            metadata: 元数据
            importance: 重要性 (critical/important/normal)

        Returns:
            记录ID
        """
        print(f"\n💾 存储记忆: {content[:100]}...")

        # 准备元数据
        if metadata is None:
            metadata = {}

        metadata.update({
            "importance": importance,
            "created_at": datetime.now().isoformat()
        })

        # 向量化（带缓存）
        try:
            vector = self._get_cached_embedding(content)
            print(f"   ✅ 向量化完成: dim={len(vector)}")
        except Exception as e:
            print(f"   ❌ 向量化失败: {e}")
            return ""

        # 存储到Chroma
        try:
            record_id = self.chroma_store.store(
                content=content,
                embedding=vector,
                metadata=metadata
            )
            print(f"   ✅ Chroma存储完成: {record_id}")
        except Exception as e:
            print(f"   ❌ Chroma存储失败: {e}")
            return ""

        # 同时写入Daily文件
        self._write_to_daily(content, metadata)

        # ==================== 图谱模块: 提取并存储三元组 ====================
        if is_graph_enabled() and self.graph_adapter is not None and is_auto_extract_enabled():
            triples = self.triple_extractor.extract_from_text(content) if self.triple_extractor else []
            for triple in triples:
                self.graph_adapter.add_triplet(triple.head, triple.relation, triple.tail)

            # 定期保存图谱
            if self.graph_adapter.stats["triplet_count"] % 100 == 0:
                self._save_graph_data()

        print(f"   ✅ 存储完成: {record_id}")

        return record_id

    def store_batch(
        self,
        contents: List[Dict],
        batch_size: int = 10
    ) -> List[str]:
        """批量存储记忆

        Args:
            contents: 记忆列表，每个元素是 {"content": str, "metadata": dict, "importance": str}
            batch_size: 批处理大小

        Returns:
            记录ID列表
        """
        print(f"\n💾 批量存储: {len(contents)} 条记忆")

        record_ids = []

        for i in range(0, len(contents), batch_size):
            batch = contents[i:i+batch_size]
            print(f"\n   处理批次 {i//batch_size + 1}/{(len(contents)-1)//batch_size + 1}: {len(batch)} 条")

            for item in batch:
                content = item.get('content', '')
                metadata = item.get('metadata', {})
                importance = item.get('importance', 'normal')

                record_id = self.store(content, metadata, importance)
                if record_id:
                    record_ids.append(record_id)

        print(f"\n   ✅ 批量存储完成: {len(record_ids)}/{len(contents)} 条")

        return record_ids

    def _retrieve_from_chroma(self, query_vector: List[float], n_results: int) -> List[Dict]:
        """从Chroma检索

        Args:
            query_vector: 查询向量
            n_results: 返回结果数量

        Returns:
            检索结果列表
        """
        try:
            results = self.chroma_store.retrieve(
                query_embedding=query_vector,
                n_results=n_results
            )

            for result in results:
                result['source'] = 'chroma'
                result['relevance'] = 1.0 - (result.get('distance', 1.0))
                result['days_ago'] = self._calculate_days_ago(result.get('metadata', {}).get('created_at'))

            return results
        except Exception as e:
            print(f"   ⚠️  Chroma检索失败: {e}")
            return []

    def _retrieve_from_daily(self, query: str, days: int) -> List[Dict]:
        """从Daily文件检索（语义检索）

        Args:
            query: 查询文本
            days: 搜索天数

        Returns:
            检索结果列表
        """
        # 使用语义检索
        return self.daily_indexer.search_daily_files(query, top_k=days)

    def _retrieve_from_daily_keyword(self, query: str, days: int) -> List[Dict]:
        """从Daily文件检索（关键词匹配）

        Args:
            query: 查询文本
            days: 搜索天数

        Returns:
            检索结果列表
        """
        results = []

        for day_offset in range(days):
            date = (datetime.now() - timedelta(days=day_offset)).strftime('%Y-%m-%d')
            file_path = os.path.join(self.daily_dir, f"{date}.md")

            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # 简单的关键词匹配
                    relevance = self._calculate_keyword_relevance(query, content)

                    if relevance > 0.3:
                        results.append({
                            'content': content[:500],  # 只返回前500字符
                            'source': 'daily',
                            'days_ago': day_offset,
                            'date': date,
                            'relevance': relevance,
                            'file_path': file_path
                        })
                except Exception as e:
                    print(f"   ⚠️  读取Daily文件失败 {date}: {e}")
                    continue

        return results

    def _retrieve_from_memory_md(self, query: str) -> List[Dict]:
        """从MEMORY.md检索（语义检索）

        Args:
            query: 查询文本

        Returns:
            检索结果列表
        """
        # 使用语义检索
        return self.memory_indexer.search_memory_md(query, top_k=5)

    def _retrieve_from_memory_md_keyword(self, query: str) -> List[Dict]:
        """从MEMORY.md检索（关键词匹配）

        Args:
            query: 查询文本

        Returns:
            检索结果列表
        """
        if not os.path.exists(self.memory_md_path):
            return []

        try:
            with open(self.memory_md_path, 'r', encoding='utf-8') as f:
                content = f.read()

            relevance = self._calculate_keyword_relevance(query, content)

            if relevance > 0.3:
                return [{
                    'content': content[:500],
                    'source': 'memory_md',
                    'days_ago': 999,  # 长期记忆
                    'relevance': relevance
                }]
        except Exception as e:
            print(f"   ⚠️  读取MEMORY.md失败: {e}")

        return []

    def _calculate_score(self, result: Dict, query: str) -> float:
        """计算综合评分

        权重（Phase 4 - Day 1优化）：
        - 相关性: 45% ⬆️ (+10%)
        - 匹配度: 25% ⬆️ (+10%)
        - 时间: 15% ⬇️ (-5%)
        - 重要性: 10% ⬇️ (-5%)
        - 来源权重: 5% ⬇️ (-10%)

        Args:
            result: 检索结果
            query: 查询文本

        Returns:
            综合评分 (0.0-1.0)
        """
        score = 0.0
        source = result.get('source', 'unknown')

        # 1. 相关性（45%）⬆️
        relevance = result.get('relevance', 0.5)
        score = relevance * 0.45  # 从0.35改为0.45

        # 2. 时间衰减（15%）⬇️
        days_ago = result.get('days_ago', 0)
        if source == 'memory_md':
            # 长期记忆（MEMORY.md）给予较高时间权重（虽然是旧数据，但重要性高）
            time_score = 0.25
        elif days_ago <= 1:
            time_score = 0.3  # 最近1天
        elif days_ago <= 3:
            time_score = 0.2  # 最近3天
        elif days_ago <= 7:
            time_score = 0.1  # 最近7天
        else:
            time_score = 0.05  # 更早
        score += time_score * 0.15  # 从0.20改为0.15

        # 3. 重要性（10%）⬇️
        importance = result.get('metadata', {}).get('importance', 'normal')
        if importance == 'critical':
            importance_score = 1.0
        elif importance == 'important':
            importance_score = 0.7
        else:
            importance_score = 0.4
        score += importance_score * 0.10  # 从0.15改为0.10

        # 4. 匹配度（25%）⬆️
        keyword_score = result.get('relevance', 0.5)
        score += keyword_score * 0.25  # 从0.15改为0.25

        # 5. 来源权重（5%）⬇️
        if source == 'memory_md':
            # MEMORY.md是长期记忆，给予最高权重
            source_score = 1.0
        elif source == 'chroma':
            # Chroma是结构化存储，给予较高权重
            source_score = 0.8
        elif source == 'daily':
            # Daily文件是临时记录，给予中等权重
            source_score = 0.6
        else:
            source_score = 0.5
        score += source_score * 0.05  # 从0.15改为0.05

        return min(score, 1.0)  # 确保不超过1.0

    def _calculate_keyword_relevance(self, query: str, content: str) -> float:
        """计算关键词相关性（增强版 - Phase 4 - Day 1优化）

        Args:
            query: 查询文本
            content: 内容文本

        Returns:
            相关性分数 (0.0-1.0)
        """
        query_words = set(query.lower().split())
        content_lower = content.lower()

        if not query_words:
            return 0.0

        match_count = 0
        for word in query_words:
            # 完全匹配
            if word in content_lower:
                match_count += 1.0
            # 部分匹配（包含词的一部分）
            elif any(word in w for w in content_lower.split()):
                match_count += 0.5

        # 计算相关性
        relevance = match_count / len(query_words)

        # 如果包含多个查询词，给予额外权重
        if match_count >= 2:
            relevance *= 1.2  # 额外20%权重

        return min(relevance, 1.0)

    def _calculate_days_ago(self, created_at: Optional[str]) -> int:
        """计算从创建时间到现在的天数

        Args:
            created_at: ISO格式的时间字符串

        Returns:
            天数
        """
        if not created_at:
            return 0

        try:
            created_time = datetime.fromisoformat(created_at)
            days_ago = (datetime.now() - created_time).days
            return max(0, days_ago)
        except Exception:
            return 0

    def _write_to_daily(self, content: str, metadata: Dict):
        """写入Daily文件

        Args:
            content: 记忆内容
            metadata: 元数据
        """
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            file_path = os.path.join(self.daily_dir, f"{today}.md")

            timestamp = datetime.now().strftime('%H:%M UTC')
            importance = metadata.get('importance', 'normal')

            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(f"\n## {timestamp} [{importance}]\n\n")
                f.write(f"{content}\n\n")

            print(f"   ✅ Daily文件写入完成: {file_path}")
        except Exception as e:
            print(f"   ⚠️  Daily文件写入失败: {e}")

    def _retrieve_parallel_semantic(
        self,
        query: str,
        query_vector: List[float],
        max_results: int,
        time_window_days: int
    ) -> List[Dict]:
        """并行语义检索

        Args:
            query: 查询文本
            query_vector: 查询向量
            max_results: 最大结果数
            time_window_days: 时间窗口（天）

        Returns:
            检索结果列表
        """
        print(f"   🚀 并行语义检索...")

        # 定义检索任务
        def retrieve_chroma():
            try:
                results = self.chroma_store.retrieve(
                    query_embedding=query_vector,
                    n_results=max_results * 2
                )
                for result in results:
                    result['source'] = 'chroma'
                    result['relevance'] = 1.0 - (result.get('distance', 1.0))
                    result['days_ago'] = self._calculate_days_ago(result.get('metadata', {}).get('created_at'))
                return results
            except Exception as e:
                print(f"   ⚠️  Chroma检索失败: {e}")
                return []

        def retrieve_daily():
            try:
                results = self.daily_indexer.search_daily_files(query, top_k=max_results)
                print(f"      Daily: {len(results)} 条")
                return results
            except Exception as e:
                print(f"   ⚠️  Daily检索失败: {e}")
                return []

        def retrieve_memory_md():
            try:
                results = self.memory_indexer.search_memory_md(query, top_k=max_results)
                print(f"      MEMORY.md: {len(results)} 条")
                return results
            except Exception as e:
                print(f"   ⚠️  MEMORY.md检索失败: {e}")
                return []

        # 并行执行
        if self.executor:
            chroma_future = self.executor.submit(retrieve_chroma)
            daily_future = self.executor.submit(retrieve_daily)
            memory_md_future = self.executor.submit(retrieve_memory_md)

            # 等待所有任务完成
            chroma_results = chroma_future.result()
            daily_results = daily_future.result()
            memory_md_results = memory_md_future.result()
        else:
            # 串行执行
            chroma_results = retrieve_chroma()
            daily_results = retrieve_daily()
            memory_md_results = retrieve_memory_md()

        print(f"      Chroma: {len(chroma_results)} 条")

        return chroma_results + daily_results + memory_md_results

    def _get_cached_embedding(self, text: str) -> List[float]:
        """获取向量化（带缓存）

        Args:
            text: 文本

        Returns:
            向量
        """
        if not self.use_cache or not self.embedding_cache:
            return self.embedding_service.embed(text)

        # 使用文本哈希作为缓存键
        import hashlib
        cache_key = hashlib.md5(text.encode()).hexdigest()

        # 检查缓存
        cached_vector = self.embedding_cache.get(cache_key)
        if cached_vector is not None:
            print(f"   🎯 向量化缓存命中")
            return cached_vector

        # 生成向量
        vector = self.embedding_service.embed(text)

        # 缓存向量
        self.embedding_cache.put(cache_key, vector)

        return vector

    def get_stats(self) -> Dict:
        """获取统计信息

        Returns:
            统计信息字典
        """
        stats = self.chroma_store.get_stats()

        # 添加daily文件统计
        daily_files = glob.glob(os.path.join(self.daily_dir, "*.md"))
        stats['daily_files_count'] = len(daily_files)

        # 添加MEMORY.md状态
        stats['memory_md_exists'] = os.path.exists(self.memory_md_path)

        # 添加缓存统计
        if self.use_cache and self.query_cache:
            stats['query_cache'] = self.query_cache.get_stats()
        if self.use_cache and self.embedding_cache:
            stats['embedding_cache'] = self.embedding_cache.get_stats()

        # 添加配置
        stats['use_cache'] = self.use_cache
        stats['use_parallel'] = self.use_parallel
        stats['max_workers'] = self.max_workers

        # 添加图谱统计
        if is_graph_enabled() and self.graph_adapter is not None:
            stats['graph'] = self.graph_adapter.get_stats()
            stats['graph_enabled'] = True
        else:
            stats['graph_enabled'] = False

        return stats

    def __repr__(self) -> str:
        """字符串表示"""
        stats = self.get_stats()
        return f"HybridMemoryRouter(chroma={stats.get('total_records', 0)} records, daily={stats.get('daily_files_count', 0)} files)"


# CLI接口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='混合记忆路由器')
    parser.add_argument('command', choices=['stats', 'store', 'retrieve', 'test'],
                        help='命令: stats/store/retrieve/test')
    parser.add_argument('--query', type=str, help='检索查询文本')
    parser.add_argument('--content', type=str, help='存储内容')
    parser.add_argument('--importance', type=str, default='normal',
                        choices=['critical', 'important', 'normal'],
                        help='重要性级别')
    parser.add_argument('--max-results', type=int, default=10,
                        help='最大返回结果数')
    parser.add_argument('--time-window', type=int, default=7,
                        help='时间窗口（天）')
    parser.add_argument('--min-score', type=float, default=0.5,
                        help='最低分数')

    args = parser.parse_args()

    # 创建路由器实例
    router = HybridMemoryRouter()

    if args.command == 'stats':
        stats = router.get_stats()
        print(f"\n📊 混合记忆路由器统计:")
        print(f"   Chroma记录数: {stats.get('total_records', 0)}")
        print(f"   Daily文件数: {stats.get('daily_files_count', 0)}")
        print(f"   MEMORY.md存在: {stats.get('memory_md_exists', False)}")
        print(f"   持久化目录: {stats.get('persist_directory', 'N/A')}")

    elif args.command == 'store':
        if not args.content:
            print("❌ 请提供 --content 参数")
            sys.exit(1)

        record_id = router.store(
            content=args.content,
            importance=args.importance
        )

        if record_id:
            print(f"✅ 存储成功: {record_id}")
        else:
            print("❌ 存储失败")

    elif args.command == 'retrieve':
        if not args.query:
            print("❌ 请提供 --query 参数")
            sys.exit(1)

        results = router.retrieve(
            query=args.query,
            max_results=args.max_results,
            time_window_days=args.time_window,
            min_score=args.min_score
        )

        print(f"\n📊 检索结果 ({len(results)} 条):")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. 来源: {result.get('source', 'unknown')}")
            print(f"   分数: {result.get('score', 0):.3f}")
            print(f"   相关性: {result.get('relevance', 0):.3f}")
            print(f"   内容: {result.get('content', '')[:100]}...")

    elif args.command == 'test':
        print("\n🧪 运行集成测试...")

        # 测试1: 存储测试
        print("\n1️⃣  存储测试")
        test_contents = [
            ("OpenClaw是一个强大的AI代理平台", "important"),
            ("Chroma是向量数据库，用于语义搜索", "normal"),
            ("Python是AI开发的主要语言", "normal")
        ]

        for content, importance in test_contents:
            router.store(content=content, importance=importance)

        # 测试2: 检索测试
        print("\n2️⃣  检索测试")
        test_queries = [
            "AI代理平台",
            "向量数据库",
            "Python编程"
        ]

        for query in test_queries:
            print(f"\n🔍 查询: {query}")
            results = router.retrieve(query=query, max_results=3)
            for i, result in enumerate(results, 1):
                print(f"   {i}. [{result.get('score', 0):.2f}] {result.get('source', 'unknown')}: {result.get('content', '')[:50]}...")

        # 测试3: 统计
        print("\n3️⃣  统计测试")
        stats = router.get_stats()
        print(f"   ✅ Chroma记录数: {stats.get('total_records', 0)}")
        print(f"   ✅ Daily文件数: {stats.get('daily_files_count', 0)}")

        print("\n✅ 集成测试完成")
