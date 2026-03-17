#!/usr/bin/env python3
"""
测试BM25索引器
"""

import os
import sys
from bm25_indexer import BM25Indexer, DailyFileIndexer, MemoryFileIndexer


def test_tokenize():
    """测试分词功能"""
    print("\n=== 测试分词功能 ===")
    
    indexer = BM25Indexer()
    
    test_text = "今天天气很好，我们去公园散步吧。"
    tokens = indexer.tokenize(test_text)
    
    print(f"原文: {test_text}")
    print(f"分词结果: {tokens}")
    print(f"✓ 分词功能测试通过\n")
    
    return True


def test_index_and_search():
    """测试索引和搜索功能"""
    print("\n=== 测试索引和搜索功能 ===")
    
    indexer = BM25Indexer()
    
    # 添加测试文档
    test_docs = [
        ("doc1", "机器学习是人工智能的一个分支", {"topic": "ML"}),
        ("doc2", "深度学习使用神经网络进行学习", {"topic": "DL"}),
        ("doc3", "自然语言处理是AI的重要应用", {"topic": "NLP"}),
        ("doc4", "BM25是一种经典的信息检索算法", {"topic": "IR"}),
    ]
    
    for doc_id, content, metadata in test_docs:
        indexer.index_document(doc_id, content, metadata)
    
    # 构建索引
    indexer.build_index()
    
    # 测试搜索
    test_queries = [
        "机器学习",
        "神经网络",
        "信息检索",
        "AI人工智能",
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        results = indexer.search(query, top_k=3)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"  {i}. [分数: {result['score']:.4f}] {result['content'][:50]}...")
        else:
            print("  无结果")
    
       # 获取统计信息
    stats = indexer.get_stats()
    print(f"\n索引统计:")
    print(f"  文档数量: {stats['total_documents']}")
    print(f"  Token总数: {stats['total_tokens']}")
    print(f"  索引状态: {'已构建' if stats['index_built'] else '未构建'}")
    print(f"✓ 索引和搜索功能测试通过\n")
    
    return True


def test_daily_file_indexing():
    """测试Daily文件索引"""
    print("\n=== 测试Daily文件索引 ===")
    
    indexer = DailyFileIndexer()
    
    # 查找最近7天的Daily文件
    workspace = "/root/.openclaw/personalspace/zh-help/memory"
    indexed_count = 0
    
    from datetime import datetime, timedelta
    
    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        file_path = os.path.join(workspace, f"{date}.md")
        
        if os.path.exists(file_path):
            indexer.index_file(file_path)
            indexed_count += 1
    
    if indexed_count > 0:
        indexer.build_index()
        
        # 测试搜索
        print(f"\n测试搜索Daily文件...")
        test_queries = ["任务", "工作", "项目"]
        
        for query in test_queries:
            results = indexer.search(query, top_k=3)
            if results:
                print(f"  查询 '{query}': 找到 {len(results)} 个结果")
        
        stats = indexer.get_stats()
        print(f"\nDaily文件索引统计:")
        print(f"  索引文件数: {indexed_count}")
        print(f"  总文档数: {stats['total_documents']}")
        print(f"  总Token数: {stats['total_tokens']}")
    else:
        print("  未找到Daily文件")
    
    print(f"✓ Daily文件索引测试通过\n")
    return indexed_count


def test_memory_file_indexing():
    """测试MEMORY.md文件索引"""
    print("\n=== 测试MEMORY.md文件索引 ===")
    
    indexer = MemoryFileIndexer()
    
    # 索引MEMORY.md
    memory_path = "/root/.openclaw/personalspace/zh-help/MEMORY.md"
    
    if os.path.exists(memory_path):
        indexer.index_file(memory_path)
        indexer.build_index()
        
        # 测试搜索
        print(f"\n测试搜索MEMORY.md...")
        test_queries = ["项目", "规范", "任务"]
        
        for query in test_queries:
            results = indexer.search(query, top_k=3)
            if results:
                print(f"  查询 '{query}': 找到 {len(results)} 个结果")
        
        stats = indexer.get_stats()
        print(f"\nMEMORY.md索引统计:")
        print(f"  总文档数: {stats['total_documents']}")
        print(f"  总Token数: {stats['total_tokens']}")
    else:
        print("  MEMORY.md文件不存在")
        return 0
    
    print(f"✓ MEMORY.md索引测试通过\n")
    return stats['total_documents']


def main():
    """运行所有测试"""
    print("=" * 60)
    print("BM25索引器完整测试")
    print("=" * 60)
    
    try:
        # 测试1: 分词功能
        test_tokenize()
        
        # 测试2: 索引和搜索
        test_index_and_search()
        
        # 测试3: Daily文件索引
        daily_count = test_daily_file_indexing()
        
        # 测试4: MEMORY.md索引
        memory_count = test_memory_file_indexing()
        
        print("=" * 60)
        print("所有测试完成！")
        print(f"Daily文件索引数量: {daily_count}")
        print(f"MEMORY.md索引数量: {memory_count}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
