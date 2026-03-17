#!/usr/bin/env python3
"""
构建BM25索引并测试（修正版）
"""

from bm25_indexer import DailyFileIndexer, MemoryFileIndexer
from datetime import datetime, timedelta
import os
import sys
import pickle

def main():
    print("=" * 60)
    print("构建BM25索引（修正版）")
    print("=" * 60)

    # 初始化索引器
    daily_indexer = DailyFileIndexer()
    memory_indexer = MemoryFileIndexer()

    daily_dir = "/root/.openclaw/workspace/memory"
    memory_md_path = "/root/.openclaw/workspace/memory/MEMORY.md"

    # Part 1: 索引最近7天的Daily文件
    print("\n📚 Part 1: 索引Daily文件")
    print("-" * 60)
    daily_indexed_count = 0
    for day_offset in range(7):
        date = (datetime.now() - timedelta(days=day_offset)).strftime('%Y-%m-%d')
        file_path = os.path.join(daily_dir, f"{date}.md")

        if os.path.exists(file_path):
            print(f"索引Daily文件: {file_path}")
            daily_indexer.index_file(file_path)
            daily_indexed_count += 1
        else:
            print(f"⚠️  文件不存在: {file_path}")

    print(f"✅ Daily文件索引完成，共{daily_indexed_count}个文件")

    # Part 2: 索引MEMORY.md
    print("\n📚 Part 2: 索引MEMORY.md")
    print("-" * 60)
    if os.path.exists(memory_md_path):
        print(f"索引MEMORY.md: {memory_md_path}")
        memory_indexer.index_file(memory_md_path)
        print("✅ MEMORY.md索引完成")
    else:
        print("⚠️  MEMORY.md不存在，跳过")

    # Part 3: 构建索引
    print("\n🔧 Part 3: 构建索引")
    print("-" * 60)
    try:
        daily_indexer.build_index()
        print("✅ Daily文件BM25索引构建成功")
    except Exception as e:
        print(f"❌ Daily文件索引构建失败: {e}")

    try:
        memory_indexer.build_index()
        print("✅ MEMORY.md BM25索引构建成功")
    except Exception as e:
        print(f"❌ MEMORY.md索引构建失败: {e}")

    # Part 4: 测试BM25索引
    print("\n🧪 Part 4: 测试BM25索引")
    print("-" * 60)
    test_queries = [
        "OpenClaw的项目架构",
        "Chroma向量数据库",
        "混合记忆系统",
        "BM25索引器"
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        print("-" * 40)
        
        # 搜索Daily文件
        print("Daily文件结果:")
        try:
            daily_results = daily_indexer.search(query, top_k=3)
            for i, result in enumerate(daily_results, 1):
                content_preview = result['content'][:60].replace('\n', ' ')
                print(f"  {i}. {content_preview}... (score={result['score']:.2f})")
        except Exception as e:
            print(f"  ❌ 搜索失败: {e}")
        
        # 搜索MEMORY.md
        print("MEMORY.md结果:")
        try:
            memory_results = memory_indexer.search(query, top_k=3)
            for i, result in enumerate(memory_results, 1):
                content_preview = result['content'][:60].replace('\n', ' ')
                print(f"  {i}. {content_preview}... (score={result['score']:.2f})")
        except Exception as e:
            print(f"  ❌ 搜索失败: {e}")
    
    # Part 5: 获取统计信息
    print("\n📊 Part 5: 索引统计信息")
    print("-" * 60)
    
    daily_stats = daily_indexer.get_stats()
    print(f"\nDaily文件索引统计:")
    print(f"  总文档数: {daily_stats['total_documents']}")
    print(f"  总Token数: {daily_stats['total_tokens']}")
    print(f"  索引状态: {'已构建' if daily_stats['index_built'] else '未构建'}")
    
    memory_stats = memory_indexer.get_stats()
    print(f"\nMEMORY.md索引统计:")
    print(f"  总文档数: {memory_stats['total_documents']}")
    print(f"  总Token数: {memory_stats['total_tokens']}")
    print(f"  索引状态: {'已构建' if memory_stats['index_built'] else '未构建'}")
    
    # 保存索引到缓存
    print("\n💾 Part 6: 保存索引到缓存")
    print("-" * 60)
    cache_dir = "./bm25_cache"
    os.makedirs(cache_dir, exist_ok=True)
    
    try:
        with open(os.path.join(cache_dir, "daily_indexer.pkl"), "wb") as f:
            pickle.dump(daily_indexer, f)
        print("✅ Daily文件索引器已保存")
    except Exception as e:
        print(f"❌ 保存Daily文件索引器失败: {e}")
    
    try:
        with open(os.path.join(cache_dir, "memory_indexer.pkl"), "wb") as f:
            pickle.dump(memory_indexer, f)
        print("✅ MEMORY.md索引器已保存")
    except Exception as e:
        print(f"❌ 保存MEMORY.md索引器失败: {e}")
    
    # 保存统一索引器（供HybridMemoryRouter使用）
    print("\n💾 Part 7: 保存统一索引器")
    print("-" * 60)
    try:
        with open(os.path.join(cache_dir, "indexer.pkl"), "wb") as f:
            pickle.dump(daily_indexer, f)
        print("✅ 统一索引器已保存")
    except Exception as e:
        print(f"❌ 保存统一索引器失败: {e}")
    
    print("\n" + "=" * 60)
    print("✅ BM25索引构建完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()
