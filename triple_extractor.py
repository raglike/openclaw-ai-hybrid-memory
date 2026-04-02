"""
三元组提取器
从记忆文本中提取知识三元组
支持规则 + 实体共现模式
"""

import re
from typing import List, Tuple, Optional
from dataclasses import dataclass, asdict
import os
import glob


@dataclass
class Triple:
    """知识三元组"""
    head: str
    relation: str
    tail: str
    confidence: float = 1.0
    source: str = "rule"

    def to_tuple(self) -> Tuple[str, str, str]:
        return (self.head, self.relation, self.tail)

    def to_dict(self) -> dict:
        return asdict(self)


class TripleExtractor:
    """
    从记忆文本中提取三元组
    支持规则 + LLM混合模式
    """

    # 预定义关系模板 (pattern -> relation_name)
    # Agent mention: @(?:助|文案|开|...) or @[A-Za-z]+
    AGENT_RE = r'@(?:助|文案|开|运营|测试|产品|小U|配管|生活管家|投资|法务|[A-Za-z][A-Za-z0-9_]*)'

    # 格式: (head_pattern)(relation_keyword)(tail_pattern)
    # 所有pattern必须有两个捕获组: (head, tail)
    RELATION_PATTERNS = {
        # 协作关系 (@A 协作 @B)
        rf'({AGENT_RE})(?:协作|合作|配合)({AGENT_RE})': '协作',
        rf'({AGENT_RE})(?:使用|集成|接入)({AGENT_RE})': '使用',
        rf'({AGENT_RE})(?:上传|写入)({AGENT_RE})': '上传到',

        # 角色关系 (@A 负责 X)
        rf'({AGENT_RE})负责([\w]+)': '负责',
        rf'({AGENT_RE})(?:角色|身份)是([\w]+)': '角色是',

        # 团队关系 (@A 属于 团队)
        rf'({AGENT_RE})属于(团队)': '属于团队',
        rf'({AGENT_RE})管理(团队)': '管理团队',

        # 项目关系
        r'([\w]+)(?:投标|参与)([\w]+)': '投标',
        r'([\w]+)(?:开发|构建|建设)([\w]+)': '开发',
        r'([\w]+)(?:设计|规划)([\w]+)': '设计',

        # 工具关系
        r'([\w]+)使用([\w]+)': '使用',
        r'([\w]+)(?:用于|用来)([\w]+)': '用于',
        r'([\w]+)(?:版本|版本号)是([\w\d.]+)': '版本',

        # 存储关系
        r'([\w]+)(?:存储|写入|保存在)([\w]+)': '存储在',
        r'([\w]+)(?:包含|包括)([\w]+)': '包含',

        # 成本/性能
        r'([\w]+)(?:成本|费用|价格)是([\w]+)': '成本',
        r'([\w]+)(?:成功率|准确率|效率)是([\w%]+)': '性能',
    }

    # 常见关系类型
    COMMON_RELATIONS = [
        "属于", "属于团队", "角色是", "负责", "使用", "上传到",
        "存储在", "包含", "协作", "开发", "设计", "用于",
        "集成", "管理", "协调", "监督"
    ]

    def __init__(self, min_confidence: float = 0.5):
        self.min_confidence = min_confidence
        self.entity_cache = {}
        # 已知Agent名称 (用于精确匹配 @提及)
        self._known_agents = {
            '助', '文案', '运营', '测试', '产品', '开', '小U', '配管', '生活管家', '投资', '法务'
        }
        # @提及模式: @ + 已知agent名 或 @ + ASCII
        agent_pattern = '|'.join(re.escape(a) for a in self._known_agents)
        self._mention_pattern = re.compile(
            r'@(?:' + agent_pattern + r')|@[a-zA-Z0-9_]+'
        )
        # 中文词组模式
        self._word_pattern = re.compile(
            r'[\u4e00-\u9fa5]{2,5}(?:管理|设计|开发|运营|测试|产品|文案|配置)?|'
            r'[A-Z][a-zA-Z]+'
        )

    def extract_from_text(self, text: str) -> List[Triple]:
        """从文本提取三元组"""
        triples = []

        # 1. 规则提取
        rule_triples = self._extract_by_rules(text)
        triples.extend(rule_triples)

        # 2. 实体共现（简单启发式）
        cooccurrence_triples = self._extract_by_cooccurrence(text)
        triples.extend(cooccurrence_triples)

        # 3. 去重
        triples = self._deduplicate(triples)

        return [t for t in triples if t.confidence >= self.min_confidence]

    def _extract_by_rules(self, text: str) -> List[Triple]:
        """基于规则提取三元组"""
        triples = []

        for pattern, relation in self.RELATION_PATTERNS.items():
            try:
                matches = re.finditer(pattern, text)
                for match in matches:
                    groups = match.groups()
                    if len(groups) >= 2:
                        head, tail = groups[0], groups[1]
                        head, tail = head.strip(), tail.strip()
                        if head and tail and head != tail:
                            triples.append(Triple(
                                head=head,
                                relation=relation,
                                tail=tail,
                                confidence=0.8,
                                source="rule"
                            ))
            except re.error:
                continue

        return triples

    def _extract_by_cooccurrence(self, text: str) -> List[Triple]:
        """基于实体共现提取三元组"""
        triples = []

        # 提取实体
        entities = self._extract_entities(text)
        if len(entities) < 2:
            return triples

        # 提取关键词推断关系
        relation = self._infer_relation(text, entities)

        # 添加共现关系
        for i, e1 in enumerate(entities):
            for e2 in entities[i+1:]:
                if e1 != e2:
                    triples.append(Triple(
                        head=e1,
                        relation=relation,
                        tail=e2,
                        confidence=0.4,
                        source="cooccurrence"
                    ))

        return triples

    def _extract_entities(self, text: str) -> List[str]:
        """提取实体"""
        entities = set()

        # 提取 @ 开头 的提及 (pattern already includes @ in match)
        mentions = self._mention_pattern.findall(text)
        entities.update(mentions)  # Don't prepend @ - pattern includes it

        # 提取中文词组和英文词组
        words = self._word_pattern.findall(text)
        entities.update(words)

        return list(entities)

    def _infer_relation(self, text: str, entities: List[str]) -> str:
        """推断关系类型"""
        text_lower = text.lower()

        relation_hints = [
            ("使用", ["使用", "使用着", "用到", "使用开源"]),
            ("开发", ["开发", "构建", "建设", "创建"]),
            ("设计", ["设计", "规划", "策划"]),
            ("上传", ["上传", "写入", "存储"]),
            ("集成", ["集成", "接入", "对接"]),
            ("管理", ["管理", "负责", "主管"]),
            ("协作", ["协作", "合作", "配合"]),
            ("属于", ["属于", "位于", "在团队"]),
        ]

        for relation, keywords in relation_hints:
            for keyword in keywords:
                if keyword in text_lower:
                    return relation

        return "相关"

    def _deduplicate(self, triples: List[Triple]) -> List[Triple]:
        """去重"""
        seen = set()
        unique = []

        for triple in triples:
            key = (triple.head, triple.relation, triple.tail)
            if key not in seen:
                seen.add(key)
                unique.append(triple)

        return unique

    def extract_from_memory_file(self, file_path: str) -> List[Triple]:
        """从记忆文件提取"""
        if not os.path.exists(file_path):
            return []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.extract_from_text(content)
        except Exception as e:
            print(f"⚠️  读取文件失败 {file_path}: {e}")
            return []

    def extract_from_directory(self, dir_path: str, pattern: str = "**/*.md") -> List[Triple]:
        """从目录扫描所有markdown文件"""
        all_triples = []
        files = glob.glob(os.path.join(dir_path, pattern), recursive=True)

        for file_path in files:
            triples = self.extract_from_memory_file(file_path)
            all_triples.extend(triples)

        return self._deduplicate(all_triples)

    def extract_triplets_as_tuples(self, text: str) -> List[Tuple[str, str, str]]:
        """提取三元组并返回为元组列表"""
        triples = self.extract_from_text(text)
        return [t.to_tuple() for t in triples]

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "min_confidence": self.min_confidence,
            "relation_patterns": len(self.RELATION_PATTERNS),
            "common_relations": len(self.COMMON_RELATIONS),
        }


# 便捷函数
def extract_triplets(text: str) -> List[Tuple[str, str, str]]:
    """从文本提取三元组（便捷函数）"""
    extractor = TripleExtractor()
    triples = extractor.extract_from_text(text)
    return [t.to_tuple() for t in triples]
