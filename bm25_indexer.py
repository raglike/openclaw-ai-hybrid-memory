#!/usr/bin/env python3
"""
BM25索引器
用于基于BM25算法的文本检索
"""

import jieba
import os
from rank_bm25 import BM25Okapi
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta


class BM25Indexer:
    """BM25索引器类"""
    
    # 中文停用词
    STOP_WORDS = {
        '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
        '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
        '自己', '这', '那', '里', '我们', '时候', '什么', '这个', '这些', '那个', '那些',
        '可以', '因为', '所以', '如果', '但是', '或者', '而且', '然后', '虽然', '已经',
        '还', '把', '让', '给', '才', '对', '吗', '啊', '吧', '呢', '哦', '嗯', '哇',
        '他', '她', '它', '他们', '它们', '你们', '咱们', '大家', '每', '各', '这种',
        '来', '用', '做', '但', '如', '只', '能', '过', '下', '比', '最', '些', '些',
        '更', '被', '从', '以', '为', '而', '及', '与', '于', '之', '等', '或', '并',
        '此', '该', '其', '如', '若', '即', '则', '虽', '虽', '然', '当', '若', '其',
        '至', '于', '且', '之', '亦', '乃', '因', '故', '若', '果', '如', '倘', '若'
    }
    
    def __init__(self):
        """初始化BM25索引器"""
        self.documents = []
        self.doc_ids = []
        self.corpus = []
        self.bm25 = None
        self.doc_metadata = {}  # 存储文档元数据
        
    def tokenize(self, text: str) -> List[str]:
        """
        使用jieba进行分词，去除停用词
        
        Args:
            text: 输入文本
            
        Returns:
            分词后的token列表
        """
        # 使用jieba进行分词
        tokens = jieba.lcut(text)
        
        # 去除停用词和空白字符
        tokens = [token for token in tokens 
                 if token.strip() and token not in self.STOP_WORDS]
        
        return tokens
    
    def index_document(self, doc_id: str, content: str, metadata: Optional[Dict] = None):
        """
        索引单个文档
        
        Args:
            doc_id: 文档ID
            content: 文档内容
            metadata: 文档元数据（可选）
        """
        # 分词
        tokens = self.tokenize(content)
        
        if tokens:  # 只有当有有效token时才添加
            self.doc_ids.append(doc_id)
            self.documents.append(content)
            self.corpus.append(tokens)
            
            # 存储元数据
            self.doc_metadata[doc_id] = {
                'content': content,
                'tokens_count': len(tokens),
                'metadata': metadata or {}
            }
    
    def index_file(self) -> None:
        """
        索引文件，按段落分块
        注意：此方法需要在子类中实现具体逻辑
        """
        raise NotImplementedError("index_file需要在子类中实现")
    
    def build_index(self):
        """构建BM25索引"""
        if self.corpus:
            self.bm25 = BM25Okapi(self.corpus)
        else:
            raise ValueError("没有可索引的文档")
    
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        搜索，返回Top-K结果
        
        Args:
            query: 搜索查询
            top_k: 返回结果数量
            
        Returns:
            搜索结果列表，每个元素包含文档信息和相似度分数
        """
        if self.bm25 is None:
            raise ValueError("BM25索引未构建，请先调用build_index()")
        
        # 分词查询
        query_tokens = self.tokenize(query)
        
        if not query_tokens:
            return []
        
        # 获取Top-K结果
        scores = self.bm25.get_scores(query_tokens)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        # 构建结果
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # 只返回有分数的结果
                doc_id = self.doc_ids[idx]
                results.append({
                    'doc_id': doc_id,
                    'score': float(scores[idx]),
                    'content': self.documents[idx],
                    'metadata': self.doc_metadata[doc_id]
                })
        
        return results
    
    def get_stats(self) -> Dict:
        """获取索引统计信息"""
        return {
            'total_documents': len(self.documents),
            'total_tokens': sum(len(tokens) for tokens in self.corpus),
            'doc_ids': self.doc_ids,
            'index_built': self.bm25 is not None
        }


class DailyFileIndexer(BM25Indexer):
    """Daily文件索引器"""
    
    def index_file(self, file_path: str):
        """
        索引Daily文件，按段落分块
        
        Args:
            file_path: 文件路径
        """
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 按段落分块（以空行分割）
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        # 如果没有段落，按行分块
        if not paragraphs:
            paragraphs = [line.strip() for line in content.split('\n') if line.strip()]
        
        # 为每个段落建立索引
        filename = os.path.basename(file_path)
        for i, paragraph in enumerate(paragraphs):
            doc_id = f"{filename}_paragraph_{i}"
            metadata = {
                'file_path': file_path,
                'filename': filename,
                'paragraph_index': i,
                'total_paragraphs': len(paragraphs)
            }
            self.index_document(doc_id, paragraph, metadata)
        
        print(f"已索引文件: {filename} (共{len(paragraphs)}个段落)")


class MemoryFileIndexer(BM25Indexer):
    """MEMORY.md文件索引器"""
    
    def index_file(self, file_path: str):
        """
        索引MEMORY.md文件，按标题块分块
        
        Args:
            file_path: 文件路径
        """
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 按一级标题分块（## 开头）
        sections = []
        lines = content.split('\n')
        current_section = []
        current_title = "前言"
        
        for line in lines:
            if line.startswith('## ') and line.strip():
                # 保存前一个section
                if current_section:
                    sections.append({
                        'title': current_title,
                        'content': '\n'.join(current_section).strip()
                    })
                # 开始新的section
                current_title = line.strip().replace('## ', '')
                current_section = [line]
            else:
                current_section.append(line)
        
        # 保存最后一个section
        if current_section:
            sections.append({
                'title': current_title,
                'content': '\n'.join(current_section).strip()
            })
        
        # 为每个section建立索引
        filename = os.path.basename(file_path)
        for i, section in enumerate(sections):
            doc_id = f"{filename}_section_{i}"
            metadata = {
                'file_path': file_path,
                'filename': filename,
                'section_title': section['title'],
                'section_index': i,
                'total_sections': len(sections)
            }
            self.index_document(doc_id, section['content'], metadata)
        
        print(f"已索引文件: {filename} (共{len(sections)}个章节)")
