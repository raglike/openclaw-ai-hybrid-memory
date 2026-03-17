# 混合记忆系统集成指南

## 快速开始

### 1. 基础使用

```python
from memory_wrapper import MemoryWrapper

memory = MemoryWrapper()

# 搜索
results = memory.search("查询内容")

# 存储
memory.store("记忆内容")
```

### 2. Agent集成

在Agent的代码中：

```python
# 替换现有的memory_search工具
from memory_wrapper import MemoryWrapper

class MyAgent:
    def __init__(self):
        self.memory = MemoryWrapper()
    
    def search_memory(self, query):
        return self.memory.search(query)
    
    def save_memory(self, content, importance="normal"):
        return self.memory.store(content, importance=importance)
```

### 3. 配置选项

所有配置在 `/root/.openclaw/openclaw.json` 中：

```json
{
  "agents": {
    "defaults": {
      "memorySearch": {
        "enabled": true,
        "provider": "openai",
        "model": "Qwen/Qwen3-Embedding-8B"
      }
    }
  }
}
```

## 向后兼容

- ✅ 保留现有memory_search接口
- ✅ 无缝替换底层实现
- ✅ 支持所有现有参数

## 监控和日志

查看统计信息：

```python
stats = memory.get_stats()
print(stats)
```

输出：
```json
{
  "total_records": 26,
  "daily_files_count": 78,
  "cache_hit_rate": 0.14
}
```
