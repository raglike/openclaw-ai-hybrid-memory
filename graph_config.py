"""
图谱模块配置
包含特性开关和配置参数
"""

import os

# 图谱配置
GRAPH_CONFIG = {
    # 基础配置
    "enabled": True,  # 图谱功能总开关
    "embedding_dim": 64,  # 嵌入维度
    "codebook_size": 256,  # 码本大小

    # 存储配置
    "storage_path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "graph_cache"),
    "backup_path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups"),

    # 性能配置
    "cache_size": 1000,
    "max_depth": 3,

    # 融合配置
    "fusion_weight": 0.2,  # 图谱权重 (0.0 - 1.0)
    "top_k": 10,
}

# 特性开关
FEATURE_FLAGS = {
    "enable_graph": True,  # 图谱功能总开关
    "enable_auto_extract": True,  # 自动三元组提取
    "enable_fusion": True,  # 结果融合
    "enable_graph_cache": True,  # 图谱缓存
}

# 性能限制
PERFORMANCE_LIMITS = {
    "max_storage_mb": 20,  # 最大存储 (MB)
    "max_memory_mb": 50,  # 最大内存 (MB)
    "max_latency_ms": 100,  # 最大延迟 (ms)
}

# 备份配置
BACKUP_CONFIG = {
    "enabled": True,
    "max_backups": 5,
    "auto_backup_interval": 100,  # 每N次操作备份一次
}


def is_graph_enabled() -> bool:
    """检查图谱功能是否启用"""
    return FEATURE_FLAGS.get("enable_graph", False) and GRAPH_CONFIG.get("enabled", False)


def is_auto_extract_enabled() -> bool:
    """检查自动三元组提取是否启用"""
    return FEATURE_FLAGS.get("enable_auto_extract", False)


def is_fusion_enabled() -> bool:
    """检查结果融合是否启用"""
    return FEATURE_FLAGS.get("enable_fusion", False)


def get_graph_weight() -> float:
    """获取图谱融合权重"""
    return GRAPH_CONFIG.get("fusion_weight", 0.2)


def get_storage_path() -> str:
    """获取图谱存储路径"""
    path = GRAPH_CONFIG.get("storage_path", "./graph_cache")
    os.makedirs(path, exist_ok=True)
    return path


def get_backup_path() -> str:
    """获取备份路径"""
    path = GRAPH_CONFIG.get("backup_path", "./backups")
    os.makedirs(path, exist_ok=True)
    return path
