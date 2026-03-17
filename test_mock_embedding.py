"""
测试模拟向量化服务
"""
from mock_embedding_service import MockEmbeddingService
import time

# 初始化
print("=" * 60)
print("🚀 开始模拟向量化服务测试")
print("=" * 60)

service = MockEmbeddingService()

# 测试单个文本
print("\n📝 测试 1: 单文本向量化")
text = "这是一条测试文本：OpenClaw混合记忆系统"
start_time = time.time()
vector = service.embed(text)
elapsed = time.time() - start_time

print(f"文本: {text}")
print(f"向量维度: {len(vector)}")
print(f"向量前5个值: {vector[:5]}")
print(f"处理时间: {elapsed:.6f}秒")

# 测试批量文本
print("\n📝 测试 2: 批量文本向量化")
texts = [
    "OpenClaw混合记忆系统",
    "Chroma向量数据库",
    "LangChain Memory"
]
start_time = time.time()
vectors = service.embed(texts)
elapsed = time.time() - start_time

print(f"批量处理 {len(texts)} 条文本")
print(f"向量维度: {service.get_embedding_dim()}")
print(f"平均处理时间: {elapsed/len(texts):.6f}秒/条")
print(f"总处理时间: {elapsed:.6f}秒")

# 验证文本的向量是否是确定性的
print("\n📝 测试 3: 确定性验证")
same_text = "这是一条测试文本：OpenClaw混合记忆系统"
same_vector = service.embed(same_text)
vectors_match = vector == same_vector
print(f"相同文本产生相同向量: {vectors_match}")

# 验收标准检查
print("\n" + "=" * 60)
print("✅ 验收标准检查")
print("=" * 60)

checks = [
    ("向量化服务初始化成功", hasattr(service, 'embedding_dim') and service.embedding_dim > 0),
    ("单文本向量化成功", isinstance(vector, list) and len(vector) > 0),
    ("批量文本向量化成功", isinstance(vectors, list) and len(vectors) == len(texts)),
    ("向量维度正确（384维）", service.get_embedding_dim() == 384),
    ("向量是确定性的", vectors_match)
]

all_passed = True
for check_name, check_result in checks:
    status = "✅" if check_result else "❌"
    print(f"{status} {check_name}")
    if not check_result:
        all_passed = False

print("\n" + "=" * 60)
if all_passed:
    print("🎉 所有测试通过！")
else:
    print("❌ 部分测试失败！")
print("=" * 60)
