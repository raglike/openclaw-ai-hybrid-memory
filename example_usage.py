"""
使用示例：如何在Agent中使用统一记忆接口
"""

from memory_wrapper import MemoryWrapper

# 初始化
memory = MemoryWrapper()

# 搜索记忆
results = memory.search(
    query="OpenClaw的项目架构",
    max_results=5,
    min_score=0.6
)

for result in results:
    print(f"- {result['content'][:60]}... (score={result['score']:.2f})")

# 存储记忆
record_id = memory.store(
    content="新的重要决策：使用Chroma作为向量数据库",
    metadata={"category": "decision", "agent": "zh-help"},
    importance="important"
)

print(f"存储成功: {record_id}")
