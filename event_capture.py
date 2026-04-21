#!/usr/bin/env python3
"""
事件驱动记忆捕获模块 - P2核心组件

功能：
- 监听/接收关键事件（任务完成、决策、配置变更）
- 自动生成结构化记忆片段写入 memory/YYYY-MM-DD.md
- 通过 HEARTBEAT 定期触发检查

触发条件（满足任一即捕获）：
1. 任务从"进行中"变为"已完成"（飞书多维表格状态变更）
2. 重要决策记录（用户说"决定..."）
3. 新技能/Spec创建
4. 重大里程碑达成

写入格式：
```markdown
## [事件] {事件类型} - {时间}

**内容**: ...
**影响**: ...
**关联**: {entity列表}
```
"""

import os
import json
import re
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional


MEMORY_DIR = Path("/root/.openclaw/personalspace/zh-help/memory")
MEMORY_TDAI = Path("/root/.openclaw/memory-tdai")
FEISHU_BITABLE = "一人公司项目管理"  # 多维表格名称（飞书）


class MemoryEventCapture:
    """事件驱动记忆捕获器"""

    def __init__(self):
        self.today = date.today()
        self.event_templates = {
            "task_completed": "## [事件] 任务完成 - {time}\n\n**任务**: {task}\n**结果**: {result}\n**关联**: {entities}\n",
            "decision_made": "## [事件] 重要决策 - {time}\n\n**决策**: {decision}\n**原因**: {reason}\n**影响**: {impact}\n",
            "spec_created": "## [事件] 新Spec创建 - {time}\n\n**名称**: {name}\n**目标**: {goal}\n**关联项目**: {project}\n",
            "milestone_reached": "## [事件] 里程碑达成 - {time}\n\n**里程碑**: {milestone}\n**项目**: {project}\n**意义**: {significance}\n",
            "tool_integrated": "## [事件] 工具集成 - {time}\n\n**工具**: {tool}\n**功能**: {capability}\n**关联**: {entities}\n",
        }

    def _get_today_memory_path(self) -> Path:
        today_str = self.today.strftime("%Y-%m-%d")
        path = MEMORY_DIR / f"{today_str}.md"
        os.makedirs(MEMORY_DIR, exist_ok=True)
        return path

    def _append_to_memory(self, content: str):
        """追加内容到今日记忆文件"""
        path = self._get_today_memory_path()
        try:
            with open(path, 'a', encoding='utf-8') as f:
                f.write(content + "\n")
            print(f"   📝 Event captured: {content[:80]}")
        except Exception as e:
            print(f"   ❌ Failed to write event: {e}")

    def capture_task_completed(
        self,
        task_name: str,
        result: str = "",
        entities: List[str] = None
    ):
        """捕获任务完成事件"""
        template = self.event_templates["task_completed"]
        content = template.format(
            time=datetime.now().strftime("%H:%M"),
            task=task_name,
            result=result or "已完成",
            entities=", ".join(entities or [])
        )
        self._append_to_memory(content)

    def capture_decision(
        self,
        decision: str,
        reason: str = "",
        impact: str = ""
    ):
        """捕获重要决策"""
        template = self.event_templates["decision_made"]
        content = template.format(
            time=datetime.now().strftime("%H:%M"),
            decision=decision,
            reason=reason,
            impact=impact
        )
        self._append_to_memory(content)

    def capture_spec_created(
        self,
        name: str,
        goal: str,
        project: str = ""
    ):
        """捕获新Spec创建"""
        template = self.event_templates["spec_created"]
        content = template.format(
            time=datetime.now().strftime("%H:%M"),
            name=name,
            goal=goal,
            project=project
        )
        self._append_to_memory(content)

    def capture_milestone(
        self,
        milestone: str,
        project: str,
        significance: str = ""
    ):
        """捕获里程碑达成"""
        template = self.event_templates["milestone_reached"]
        content = template.format(
            time=datetime.now().strftime("%H:%M"),
            milestone=milestone,
            project=project,
            significance=significance
        )
        self._append_to_memory(content)

    def capture_from_heartbeat(self) -> int:
        """从HEARTBEAT触发时运行，检查是否有新事件需要捕获

        Returns:
            捕获的事件数量
        """
        captured = 0

        # 检查飞书多维表格中已完成但尚未记录的任务
        # （简化版：只记录，不主动拉取飞书）
        # 实际触发由外部（@助的HEARTBEAT）调用此方法

        # 检查今日memory文件是否已有事件记录
        today_path = self._get_today_memory_path()
        if today_path.exists():
            with open(today_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # 已有事件记录
            if "[事件]" in content:
                pass

        return captured

    def infer_and_capture_from_conversation(self, recent_messages: List[Dict]) -> int:
        """从对话历史中推断事件并捕获

        Args:
            recent_messages: [{"role": "user/assistant", "content": "...", "time": "..."}]

        Returns:
            捕获的事件数量
        """
        captured = 0
        event_patterns = [
            (r"完成了|已经完成|做好了", "task_completed"),
            (r"决定|确定了|就这么办", "decision_made"),
            (r"创建了.*spec|新建.*spec|启动了.*f45", "spec_created"),
            (r"上线了|发布了|完成了.*里程碑", "milestone_reached"),
        ]

        for msg in recent_messages[-5:]:  # 只看最近5条
            content = msg.get('content', '')
            role = msg.get('role', '')

            for pattern, event_type in event_patterns:
                if re.search(pattern, content) and role in ('assistant', 'user'):
                    if event_type == "task_completed":
                        self.capture_task_completed(
                            task_name=content[:60],
                            result="对话中提及"
                        )
                        captured += 1
                    elif event_type == "decision_made":
                        self.capture_decision(
                            decision=content[:80],
                            reason="对话推断"
                        )
                        captured += 1
                    break

        return captured


if __name__ == "__main__":
    capture = MemoryEventCapture()
    capture.capture_task_completed(
        task_name="记忆系统4.0 EntityBundle开发",
        result="Phase1-4全部完成",
        entities=["hybrid_memory", "scene_entity_indexer"]
    )
    print("✅ Event capture test done")
