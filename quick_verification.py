#!/usr/bin/env python3
"""
快速验证BM25检索和三重融合效果
Quick Verification of BM25 and Triple Fusion
"""

from bm25_indexer import BM25Indexer

# 加载BM25索引器
try:
    import pickle
    with open('./bm25_cache/indexer.pkl', 'rb') as f:
        indexer = pickle.load(f)
    print("✅ BM25索引器已加载")
except:
    # 创建新的索引器
    indexer = BM25Indexer()
    print("⚠️  未找到保存的索引器，使用新的")

# 获取统计
stats = indexer.get_stats()
print(f"\n📊 BM25索引统计:")
print(f"   总文档数: {stats['total_documents']}")
print(f"   索引状态: {'已构建' if stats['index_built'] else '未构建'}")

# 测试BM25检索
test_queries = [
    "OpenClaw",
    "Chroma",
    "混合记忆",
    "BM25",
    "向量"
]

print(f"\n🧪 BM25检索测试:\n")

for query in test_queries:
    results = indexer.search(query, top_k=3)
    print(f"查询: {query}")
    print(f"   找到 {len(results)} 条结果")
    for i, result in enumerate(results, 1):
        content_preview = result['content'][:60].replace('\n', ' ')
        print(f"   {i}. {content_preview}... (score={result['score']:.2f})")
    print()

# 测试三重融合
try:
    from hybrid_router import HybridMemoryRouter
    router = HybridMemoryRouter()
    
    print("🧪 三重融合测试:\n")
    
    query = "OpenClaw的项目架构"
    print(f"查询: {query}")
    print("=" * 60)
    
    results = router.retrieve(query, max_results=5)
    
    print(f"找到 {len(results)} 条结果:\n")
    
    for i, result in enumerate(results, 1):
        vector_score = result.get('vector_score', 0)
        bm25_score = result.get('bm25_score', 0)
        simple_score = result.get('simple_score', 0)
        appearance = result.get('appearance_count', 0)
        
        print(f"{i}. 综合评分: {result.get('score', 0):.2f}")
        print(f"   向量分: {vector_score:.2f}")
        print(f"   BM25分: {bm25_score:.2f}")
        print(f"   简单分: {simple_score:.2f}")
        print(f"   出现次数: {appearance}")
        print(f"   内容: {result['content'][:80].replace(chr(10), ' ')}...")
        print()
    
    print("✅ 三重融合测试完成")
    
except Exception as e:
    print(f"❌ 三重融合测试失败: {e}")

print("\n" + "=" * 60)
print("验证完成")
print("=" * 60)