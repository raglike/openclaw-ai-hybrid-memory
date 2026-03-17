#!/usr/bin/env python3
"""
三重融合检索算法
Triple Fusion Retrieval Algorithm
"""

from typing import List, Dict

def triple_fusion(
    vector_results: List[Dict],
    bm25_results: List[Dict],
    simple_results: List[Dict],
    vector_weight: float = 0.5,
    bm25_weight: float = 0.3,
    simple_weight: float = 0.2
) -> List[Dict]:
    """
    三重融合算法
    
    融合向量检索、BM25检索和简单关键词检索的结果。
    
    Args:
        vector_results: 向量检索结果
        bm25_results: BM25检索结果
        simple_results: 简单关键词检索结果
        vector_weight: 向量结果权重
        bm25_weight: BM25结果权重
        simple_weight: 简单关键词结果权重
    
    Returns:
        融合后的结果列表
    """
    merged = {}
    
    # 向量结果
    for result in vector_results:
        result_id = result.get('id', result.get('doc_id', str(id(result))))
        merged[result_id] = {
            'id': result_id,
            'content': result.get('content', ''),
            'vector_score': result.get('score', result.get('relevance', 0)),
            'bm25_score': 0.0,
            'simple_score': 0.0,
            'in_vector': True,
            'in_bm25': False,
            'in_simple': False,
            'vector_metadata': result
        }
    
    # BM25结果
    for result in bm25_results:
        result_id = result.get('id', result.get('doc_id', str(id(result))))
        if result_id in merged:
            merged[result_id]['bm25_score'] = result.get('score', 0)
            merged[result_id]['in_bm25'] = True
            merged[result_id]['bm25_metadata'] = result
        else:
            merged[result_id] = {
                'id': result_id,
                'content': result.get('content', ''),
                'vector_score': 0.0,
                'bm25_score': result.get('score', 0),
                'simple_score': 0.0,
                'in_vector': False,
                'in_bm25': True,
                'in_simple': False,
                'bm25_metadata': result
            }
    
    # 简单关键词结果
    for result in simple_results:
        result_id = result.get('id', result.get('doc_id', str(id(result))))
        if result_id in merged:
            merged[result_id]['simple_score'] = result.get('score', result.get('relevance', 0))
            merged[result_id]['in_simple'] = True
            merged[result_id]['simple_metadata'] = result
        else:
            merged[result_id] = {
                'id': result_id,
                'content': result.get('content', ''),
                'vector_score': 0.0,
                'bm25_score': 0.0,
                'simple_score': result.get('score', result.get('relevance', 0)),
                'in_vector': False,
                'in_bm25': False,
                'in_simple': True,
                'simple_metadata': result
            }
    
    # 融合评分
    final_results = []
    for result_id, scores in merged.items():
        # 基础评分
        base_score = (
            scores['vector_score'] * vector_weight +
            scores['bm25_score'] * bm25_weight +
            scores['simple_score'] * simple_weight
        )
        
        # 额外加分（基于出现在多个结果中的次数）
        appearance_count = sum([
            scores['in_vector'],
            scores['in_bm25'],
            scores['in_simple']
        ])
        
        if appearance_count == 2:
            base_score *= 1.1  # 出现在2个结果中，额外10%加分
        elif appearance_count == 3:
            base_score *= 1.2  # 出现在3个结果中，额外20%加分
        
        final_results.append({
            'id': result_id,
            'content': scores['content'],
            'score': base_score,
            'vector_score': scores['vector_score'],
            'bm25_score': scores['bm25_score'],
            'simple_score': scores['simple_score'],
            'appearance_count': appearance_count,
            'source': 'fusion'
        })
    
    # 按评分排序
    final_results.sort(key=lambda x: x['score'], reverse=True)
    
    return final_results


def dual_fusion(
    results_a: List[Dict],
    results_b: List[Dict],
    weight_a: float = 0.6,
    weight_b: float = 0.4
) -> List[Dict]:
    """
    双重融合算法（简化版本）
    
    Args:
        results_a: 第一组检索结果
        results_b: 第二组检索结果
        weight_a: 第一组结果权重
        weight_b: 第二组结果权重
    
    Returns:
        融合后的结果列表
    """
    merged = {}
    
    # 第一组结果
    for result in results_a:
        result_id = result.get('id', result.get('doc_id', str(id(result))))
        merged[result_id] = {
            'id': result_id,
            'content': result.get('content', ''),
            'score_a': result.get('score', result.get('relevance', 0)),
            'score_b': 0.0,
            'in_a': True,
            'in_b': False
        }
    
    # 第二组结果
    for result in results_b:
        result_id = result.get('id', result.get('doc_id', str(id(result))))
        if result_id in merged:
            merged[result_id]['score_b'] = result.get('score', result.get('relevance', 0))
            merged[result_id]['in_b'] = True
        else:
            merged[result_id] = {
                'id': result_id,
                'content': result.get('content', ''),
                'score_a': 0.0,
                'score_b': result.get('score', result.get('relevance', 0)),
                'in_a': False,
                'in_b': True
            }
    
    # 融合评分
    final_results = []
    for result_id, scores in merged.items():
        # 基础评分
        base_score = (
            scores['score_a'] * weight_a +
            scores['score_b'] * weight_b
        )
        
        # 额外加分（基于出现在两个结果中的情况）
        if scores['in_a'] and scores['in_b']:
            base_score *= 1.1  # 出现在两个结果中，额外10%加分
        
        final_results.append({
            'id': result_id,
            'content': scores['content'],
            'score': base_score,
            'score_a': scores['score_a'],
            'score_b': scores['score_b'],
            'appearance_count': sum([scores['in_a'], scores['in_b']]),
            'source': 'dual_fusion'
        })
    
    # 按评分排序
    final_results.sort(key=lambda x: x['score'], reverse=True)
    
    return final_results


def reciprocal_rank_fusion(
    results_list: List[List[Dict]],
    k: int = 60
) -> List[Dict]:
    """
    倒数排名融合（Reciprocal Rank Fusion, RRF）
    
    这是一种融合多个检索结果的经典算法，不依赖于分数的归一化。
    
    Args:
        results_list: 多个检索结果列表
        k: 常数，用于控制分数的衰减速度（通常使用60）
    
    Returns:
        融合后的结果列表
    """
    # 存储每个文档的RRF分数
    rrf_scores = {}
    
    # 存储每个文档的完整信息
    doc_info = {}
    
    # 遍历所有结果列表
    for results in results_list:
        # 遍历结果，按排名（从1开始）
        for rank, result in enumerate(results, start=1):
            result_id = result.get('id', result.get('doc_id', str(id(result))))
            
            # RRF分数：1 / (k + rank)
            rrf_score = 1.0 / (k + rank)
            
            # 累加分数
            if result_id in rrf_scores:
                rrf_scores[result_id] += rrf_score
            else:
                rrf_scores[result_id] = rrf_score
                # 保存文档信息
                doc_info[result_id] = {
                    'id': result_id,
                    'content': result.get('content', ''),
                    'source': result.get('source', 'unknown')
                }
    
    # 构建最终结果
    final_results = []
    for doc_id, score in rrf_scores.items():
        final_results.append({
            'id': doc_id,
            'content': doc_info[doc_id]['content'],
            'score': score,
            'source': f"rrf_{doc_info[doc_id]['source']}"
        })
    
    # 按分数排序
    final_results.sort(key=lambda x: x['score'], reverse=True)
    
    return final_results
