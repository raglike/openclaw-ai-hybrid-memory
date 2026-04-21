#!/usr/bin/env python3
"""
检索反馈模块 - P2核心组件

功能：
- 记录每次检索结果的质量反馈（thumbs up/down）
- 基于反馈调整结果排序（相关结果boost）
- 持久化到 feedback.jsonl
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


FEEDBACK_DIR = Path("/root/.openclaw/memory-tdai")
FEEDBACK_FILE = FEEDBACK_DIR / "retrieval_feedback.jsonl"
BOOST_CACHE_FILE = FEEDBACK_DIR / "feedback_boost.json"


class RetrievalFeedback:
    """检索反馈记录器"""

    def __init__(self):
        self.boost_cache: Dict[str, float] = self._load_boost_cache()
        self._seen_queries: Dict[str, set] = {}  # query → {result_keys}

    def _load_boost_cache(self) -> Dict[str, float]:
        if BOOST_CACHE_FILE.exists():
            try:
                with open(BOOST_CACHE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_boost_cache(self):
        try:
            with open(BOOST_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.boost_cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def mark_relevant(self, query: str, result_content: str, feedback: str = "relevant"):
        """标记某条结果对查询"有用"

        Args:
            query: 查询文本
            result_content: 结果内容（用于唯一标识）
            feedback: 'relevant' | 'irrelevant'
        """
        self._record_feedback(query, result_content, feedback)

    def mark_irrelevant(self, query: str, result_content: str):
        self._record_feedback(query, result_content, "irrelevant")

    def _record_feedback(self, query: str, result_content: str, feedback: str):
        """写一条反馈到 jsonl"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "result_key": hash(result_content[:200]) % 10**10,
            "result_preview": result_content[:100],
            "feedback": feedback,
        }

        try:
            os.makedirs(FEEDBACK_DIR, exist_ok=True)
            with open(FEEDBACK_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            pass

        # 更新 boost 缓存
        key = f"{query[:50]}::{result_content[:100]}"
        if feedback == "relevant":
            self.boost_cache[key] = self.boost_cache.get(key, 0) + 0.5
        else:
            self.boost_cache[key] = self.boost_cache.get(key, 0) - 0.5

        self.boost_cache[key] = max(-1.0, min(2.0, self.boost_cache[key]))
        self._save_boost_cache()

    def get_boost(self, query: str, result_content: str) -> float:
        """获取某结果的boost分数"""
        key = f"{query[:50]}::{result_content[:100]}"
        return self.boost_cache.get(key, 0.0)

    def apply_boost(self, results: List[Dict], query: str) -> List[Dict]:
        """对检索结果应用反馈boost"""
        for r in results:
            content = r.get('content', '')
            boost = self.get_boost(query, content)
            if boost != 0:
                r['feedback_boost'] = boost
                r['score'] = r.get('score', 0) + boost
        return results

    def get_stats(self) -> Dict:
        """获取反馈统计"""
        if not FEEDBACK_FILE.exists():
            return {"total": 0, "relevant": 0, "irrelevant": 0}

        total = relevant = irrelevant = 0
        try:
            with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                        total += 1
                        if rec.get('feedback') == 'relevant':
                            relevant += 1
                        else:
                            irrelevant += 1
                    except Exception:
                        pass
        except Exception:
            pass

        return {"total": total, "relevant": relevant, "irrelevant": irrelevant}
