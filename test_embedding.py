import time
import os

# 尝试导入真实服务，如果失败则使用模拟服务
try:
    from embedding_service import EmbeddingService
    USE_MOCK = False
    print("💡 使用真实向量化服务（需要网络访问Hugging Face）")
except Exception as e:
    print(f"⚠️ 无法加载真实服务: {e}")
    print("💡 使用模拟向量化服务（离线模式）")
    from mock_embedding_service import MockEmbeddingService
    EmbeddingService = MockEmbeddingService
    USE_MOCK = True

# 初始化
print("=" * 60)
print("🚀 开始向量化服务测试")
print("=" * 60)

if USE_MOCK:
    print("⚠️ 当前使用模拟服务（离线模式）")
    print("   要使用真实服务，请确保网络可访问Hugging Face")
else:
    print("✅ 使用真实向量化服务")

print()

service = EmbeddingService()

# 测试单个文本
print("\n📝 测试 1: 单文本向量化")
text = "这是一条测试文本：OpenClaw混合记忆系统"
start_time = time.time()
vector = service.embed(text)
elapsed = time.time() - start_time

print(f"文本: {text}")
print(f"向量维度: {len(vector)}")
print(f"向量前5个值: {vector[:5]}")
print(f"处理时间: {elapsed:.4f}秒")

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
print(f"平均处理时间: {elapsed/len(texts):.4f}秒/条")
print(f"总处理时间: {elapsed:.4f}秒")

# 验收标准检查
print("\n" + "=" * 60)
print("✅ 验收标准检查")
print("=" * 60)

checks = [
    ("向量化服务初始化成功", hasattr(service, 'model') and service.model is not None),
    ("单文本向量化成功", isinstance(vector, list) and len(vector) > 0),
    ("批量文本向量化成功", isinstance(vectors, list) and len(vectors) == len(texts)),
    ("向量维度正确（384维）", service.get_embedding_dim() == 384)
]

for check_name, check_result in checks:
    status = "✅" if check_result else "❌"
    print(f"{status} {check_name}")

print("\n" + "=" * 60)
print("🎉 测试完成！")
print("=" * 60)
