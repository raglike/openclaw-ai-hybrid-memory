# OpenClaw AI Hybrid Memory System

A hybrid memory system combining Chroma vector embeddings, BM25 keyword matching, and triple fusion for enhanced retrieval accuracy.

## Features

- **Chroma Vector Store**: Semantic similarity search using vector embeddings
- **BM25 Indexer**: Keyword-based retrieval with TF-IDF weighting
- **Hybrid Fusion**: Three-tier fusion strategy (Reciprocal Rank Fusion, Score Fusion, Adaptive Fusion)
- **Memory Router**: Intelligent routing between retrieval methods based on query characteristics
- **Daily Indexer**: Automatic daily memory organization and indexing
- **Cache Layer**: Efficient caching for frequently accessed memories

## Installation

```bash
pip install chromadb rank-bm25 numpy
```

## Quick Start

```python
from hybrid_fusion import HybridMemoryFusion
from embedding_service import EmbeddingService

# Initialize
embedding_service = EmbeddingService()
fusion = HybridMemoryFusion(embedding_service)

# Add memories
fusion.add_memory("Meeting tomorrow at 3 PM")
fusion.add_memory("Project deadline is Friday")

# Search
results = fusion.search("What meetings do I have?")
```

## Core Components

### 1. Chroma Store (`chroma_store.py`)
Vector database integration for semantic search.

### 2. BM25 Indexer (`bm25_indexer.py`)
Keyword-based retrieval with BM25 scoring.

### 3. Hybrid Fusion (`hybrid_fusion.py`)
Multi-strategy fusion combining vector and keyword results.

### 4. Hybrid Router (`hybrid_router.py`)
Intelligent routing system for optimal retrieval method selection.

### 5. Daily Indexer (`daily_indexer.py`)
Automatic organization of memories by date.

## Architecture

```
Memory Input
    ↓
[Memory Router]
    ↓         ↓
[Chroma]  [BM25]
    ↓         ↓
[Hybrid Fusion]
    ↓
Ranked Results
```

## Performance

- **Reciprocal Rank Fusion**: Best for diverse result sets
- **Score Fusion**: Best when combining similar ranking systems
- **Adaptive Fusion**: Automatically selects optimal strategy

## Testing

```bash
# Test individual components
python test_hybrid_router.py
python test_bm25_indexer.py
python test_triple_fusion.py

# Run full integration test
python integration_test.py

# Performance benchmark
python performance_benchmark.py
```

## Documentation

- [BM25 Enhancement Evaluation](BM25_ENHANCEMENT_EVALUATION.md)
- [Hybrid Router Implementation](hybrid_router_implementation_report.md)
- [Integration Guide](INTEGRATION_GUIDE.md)
- [Keyword Retrieval Comparison](KEYWORD_RETRIEVAL_COMPARISON.md)
- [Performance Optimization](performance_optimization_report.md)

## License

MIT License

## Contributing

This is part of the OpenClaw AI project.