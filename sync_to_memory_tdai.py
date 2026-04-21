#!/usr/bin/env python3
"""
Bridge: hybrid-memory → memory-tdai tunnel_index.json 同步脚本

将 hybrid-memory 的 EntityBundle 数据同步到 memory-tdai 的 tunnel_index.json，
让 OpenClaw 内置检索能够读取增强后的场景关联数据。

用法:
    python3 sync_to_memory_tdai.py        # 一次性同步
    python3 sync_to_memory_tdai.py --watch  # 监控变化
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

HYBRID_TUNNEL = "/root/.openclaw/workspace/memory/hybrid-memory/tunnel_index.json"
MEMORY_TDAI_TUNNEL = "/root/.openclaw/memory-tdai/tunnel_index.json"
SCENE_BLOCKS_DIR = "/root/.openclaw/memory-tdai/scene_blocks"


def load_hybrid_tunnel() -> dict:
    """加载 hybrid-memory tunnel 数据"""
    if not os.path.exists(HYBRID_TUNNEL):
        print(f"❌ hybrid-memory tunnel not found: {HYBRID_TUNNEL}")
        return {}
    with open(HYBRID_TUNNEL, 'r', encoding='utf-8') as f:
        return json.load(f)


def infer_tunnels_from_entities(scenes: list) -> dict:
    """从实体共享关系推断 tunnel（bidirectional）

    如果场景A和场景B共享同一个实体（非短词），则推断它们相关。
    结果写入 memory-tdai 格式: {scene: {declared, derived, all}}
    """
    # 建立 entity → set(scenes) 反向索引
    entity_to_scenes = {}
    scene_entities = {}  # scene_name → list of clean entity names

    for scene in scenes:
        sname = scene.get('scene_name', '')
        entities = scene.get('entities', [])
        # 清洗实体：去除噪声，保留有意义的
        clean_entities = [
            e.strip() for e in entities
            if e and len(e.strip()) >= 2
            and not e.strip().endswith('。')
            and not e.strip().startswith('。')
        ][:30]  # 最多30个，避免噪声
        scene_entities[sname] = set(clean_entities)

        for e in clean_entities:
            if e not in entity_to_scenes:
                entity_to_scenes[e] = set()
            entity_to_scenes[e].add(sname)

    # 构建 tunnel 字典
    tunnel_dict = {}

    for sname, sentities in scene_entities.items():
        declared = []
        derived = []

        for entity, related_scenes in entity_to_scenes.items():
            if sname in related_scenes and len(related_scenes) > 1:
                # 找同实体的其他场景
                for other in related_scenes:
                    if other != sname and other not in declared:
                        declared.append(other)

        # 去重
        declared = list(dict.fromkeys(declared))[:10]

        tunnel_dict[sname] = {
            "declared": declared,
            "derived": derived,
            "all": list(dict.fromkeys(declared + derived))[:10]
        }

    return tunnel_dict


def infer_tunnels_from_triples(scenes: list) -> dict:
    """从三元组关系推断 tunnel

    如果场景A中提到"@开负责PixelForge"，而场景B中也提到PixelForge，
    则A和B通过项目"PixelForge"形成tunnel。
    """
    import re

    # 提取场景中的项目/工具名词（粗略）
    PROJECT_PATTERNS = [
        r'([A-Za-z0-9\u4e00-\u9fa5]{2,20}(?:项目|系统|平台|工具|课程|流水线|方案|流程|规范|模块))',
        r'([A-Za-z0-9\u4e00-\u9fa5]{2,20}(?:Agent|agent))',
        r'@(.*?)(?:\s|，|,|$)',
    ]

    def extract_key_entities(content: str) -> set:
        entities = set()
        for pat in PROJECT_PATTERNS:
            for m in re.finditer(pat, content):
                e = m.group(1).strip()
                if len(e) >= 2:
                    entities.add(e)
        return entities

    # 加载场景内容
    scene_key_entities = {}
    for scene in scenes:
        sname = scene.get('scene_name', '')
        fname = scene.get('file', '')
        fpath = os.path.join(SCENE_BLOCKS_DIR, fname)
        if os.path.exists(fpath):
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            scene_key_entities[sname] = extract_key_entities(content)
        else:
            scene_key_entities[sname] = set()

    # 实体→场景映射
    entity_to_scenes = {}
    for sname, entities in scene_key_entities.items():
        for e in entities:
            if e not in entity_to_scenes:
                entity_to_scenes[e] = set()
            entity_to_scenes[e].add(sname)

    # 构建 tunnel
    tunnel_dict = {}
    for sname, entities in scene_key_entities.items():
        related = []
        for e in entities:
            for other in entity_to_scenes.get(e, []):
                if other != sname and other not in related:
                    related.append(other)
        tunnel_dict[sname] = {
            "declared": [],
            "derived": list(dict.fromkeys(related))[:10],
            "all": list(dict.fromkeys(related))[:10]
        }

    return tunnel_dict


def convert_to_memory_tdai_format(hybrid_data: dict) -> dict:
    """将 hybrid-memory 格式转换为 memory-tdai tunnel_index 格式"""
    scenes = hybrid_data.get('scenes', [])
    if not scenes:
        return {"version": "1.0", "created": datetime.now().isoformat(), "scenes": {}, "total_scenes": 0}

    # 方法1：从实体共享推断tunnel
    entity_tunnels = infer_tunnels_from_entities(scenes)

    # 方法2：从三元组关键词推断tunnel（补充）
    try:
        triple_tunnels = infer_tunnels_from_triples(scenes)
        # 合并
        for sname in triple_tunnels:
            if sname not in entity_tunnels:
                entity_tunnels[sname] = triple_tunnels[sname]
            else:
                # 合并all
                existing = set(entity_tunnels[sname].get('all', []))
                existing.update(triple_tunnels[sname].get('all', []))
                entity_tunnels[sname]['all'] = list(existing)[:10]
    except Exception as e:
        print(f"   ⚠️ triple tunnel inference failed: {e}")

    # 转换为 memory-tdai 格式
    result_scenes = {}
    for sname, tunnels in entity_tunnels.items():
        result_scenes[sname] = {
            "declared": tunnels.get('declared', []),
            "derived": tunnels.get('derived', []),
            "all": tunnels.get('all', [])
        }

    return {
        "version": "4.0-hybrid",
        "created": datetime.now().isoformat(),
        "scenes": result_scenes,
        "total_scenes": len(result_scenes),
        "source": "hybrid-memory EntityBundle",
        "stats": {
            "entities_in_map": len(hybrid_data.get('entity_scene_map', {})),
            "scenes_indexed": len(scenes),
            "triplets": hybrid_data.get('stats', {}).get('triples_extracted', 0),
        }
    }


def sync():
    """执行同步"""
    print(f"🔄 Syncing hybrid-memory → memory-tdai tunnel_index")

    hybrid_data = load_hybrid_tunnel()
    if not hybrid_data:
        print("❌ No hybrid-memory data to sync")
        return False

    # 转换格式
    memory_tdai_data = convert_to_memory_tdai_format(hybrid_data)

    # 写入
    os.makedirs(os.path.dirname(MEMORY_TDAI_TUNNEL), exist_ok=True)
    with open(MEMORY_TDAI_TUNNEL, 'w', encoding='utf-8') as f:
        json.dump(memory_tdai_data, f, ensure_ascii=False, indent=2)

    scenes_with_tunnels = sum(1 for v in memory_tdai_data['scenes'].values() if v['all'])
    print(f"   ✅ Synced: {len(memory_tdai_data['scenes'])} scenes, {scenes_with_tunnels} with tunnels")
    print(f"   📄 Written to: {MEMORY_TDAI_TUNNEL}")

    return True


if __name__ == "__main__":
    if "--watch" in sys.argv:
        import time
        print("👀 Watch mode: monitoring hybrid-memory tunnel_index for changes...")
        last_mtime = 0
        while True:
            try:
                mtime = os.path.getmtime(HYBRID_TUNNEL)
                if mtime != last_mtime:
                    last_mtime = mtime
                    sync()
                time.sleep(60)
            except KeyboardInterrupt:
                print("\n👋 Stopped.")
                break
    else:
        sync()
