"""API客户端模块。

提供与社区服务端交互的接口，包含模拟数据用于演示。
"""

import json
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from tabulate import tabulate

from .config import ConfigManager

console = Console()

MOCK_POSTS: List[Dict[str, Any]] = [
    {
        "id": "post_001",
        "author": "admin",
        "author_name": "社区管理员",
        "author_avatar": "👑",
        "content": "今天社区迎来了第10万位用户！感谢大家一路以来的支持和陪伴。我们将继续努力，打造更好的AI交流平台。🎉 #社区动态 #里程碑",
        "tags": ["社区动态", "里程碑"],
        "likes": 1258,
        "comments": 256,
        "shares": 89,
        "views": 12580,
        "created_at": (datetime.now() - timedelta(hours=3)).isoformat(),
        "updated_at": (datetime.now() - timedelta(hours=3)).isoformat(),
        "versions": [
            {"version": 1, "content": "今天社区迎来了第10万位用户！", "created_at": (datetime.now() - timedelta(hours=5)).isoformat()},
            {"version": 2, "content": "今天社区迎来了第10万位用户！感谢大家一路以来的支持和陪伴。", "created_at": (datetime.now() - timedelta(hours=4)).isoformat()},
        ],
        "is_liked": False,
        "is_favorited": False,
        "status": "published",
    },
    {
        "id": "post_002",
        "author": "writer",
        "author_name": "专业写手",
        "author_avatar": "✍️",
        "content": "分享一个超实用的Prompt模板：用于生成结构化的技术文档。\n\n[系统设定]\n你是资深技术写作专家...\n\n[任务描述]\n请根据以下技术要点生成文档...\n\n效果真的很棒，文档产出效率提升了3倍！ #Prompt技巧 #效率工具",
        "tags": ["Prompt技巧", "效率工具"],
        "likes": 892,
        "comments": 134,
        "shares": 256,
        "views": 8920,
        "created_at": (datetime.now() - timedelta(hours=8)).isoformat(),
        "updated_at": (datetime.now() - timedelta(hours=8)).isoformat(),
        "versions": [],
        "is_liked": True,
        "is_favorited": True,
        "status": "published",
    },
    {
        "id": "post_003",
        "author": "demo",
        "author_name": "演示用户",
        "author_avatar": "🧪",
        "content": "问个问题：大家平时用AI最主要是做什么？我先来：写代码辅助、文案润色、翻译。最近在尝试用AI做数据分析，效果出乎意料地好！#讨论 #AI应用",
        "tags": ["讨论", "AI应用"],
        "likes": 356,
        "comments": 478,
        "shares": 12,
        "views": 5680,
        "created_at": (datetime.now() - timedelta(days=1)).isoformat(),
        "updated_at": (datetime.now() - timedelta(days=1)).isoformat(),
        "versions": [],
        "is_liked": False,
        "is_favorited": False,
        "status": "published",
    },
    {
        "id": "post_004",
        "author": "writer",
        "author_name": "专业写手",
        "author_avatar": "✍️",
        "content": "新长文草稿已提交审核：《从零开始构建企业级AI应用的10个最佳实践》，预计周末发布，敬请期待！\n\n主要内容预告：\n1. 架构设计原则\n2. 数据治理方案\n3. 安全合规要点\n4. 性能优化技巧\n#长文预告 #AI工程",
        "tags": ["长文预告", "AI工程"],
        "likes": 678,
        "comments": 89,
        "shares": 134,
        "views": 6780,
        "created_at": (datetime.now() - timedelta(days=2)).isoformat(),
        "updated_at": (datetime.now() - timedelta(days=2)).isoformat(),
        "versions": [],
        "is_liked": True,
        "is_favorited": False,
        "status": "published",
    },
    {
        "id": "post_005",
        "author": "admin",
        "author_name": "社区管理员",
        "author_avatar": "👑",
        "content": "【官方公告】新功能上线：Prompt广场！大家可以分享和发现高质量的AI提示词，支持收藏、导出、评分。快来体验吧~ 🚀\n入口：主页 -> Prompt广场 #官方公告 #新功能",
        "tags": ["官方公告", "新功能"],
        "likes": 2345,
        "comments": 567,
        "shares": 456,
        "views": 23450,
        "created_at": (datetime.now() - timedelta(days=3)).isoformat(),
        "updated_at": (datetime.now() - timedelta(days=3)).isoformat(),
        "versions": [],
        "is_liked": False,
        "is_favorited": True,
        "status": "published",
    },
]

MOCK_DRAFTS: List[Dict[str, Any]] = [
    {
        "id": "draft_001",
        "title": "从零开始构建企业级AI应用的10个最佳实践",
        "author": "writer",
        "content": "# 从零开始构建企业级AI应用的10个最佳实践\n\n## 1. 架构设计原则\n\n在设计企业级AI应用架构时，需要考虑可扩展性、可维护性和可靠性...\n\n## 2. 数据治理方案\n\n数据是AI应用的核心资产。良好的数据治理方案包括...\n\n## 3. 安全合规要点\n\n企业级AI应用必须遵守数据隐私法规...\n",
        "tags": ["AI工程", "最佳实践", "企业应用"],
        "category": "技术深度",
        "summary": "本文总结了构建企业级AI应用的10个核心最佳实践，涵盖架构、数据、安全、性能等关键领域。",
        "word_count": 12580,
        "created_at": (datetime.now() - timedelta(days=5)).isoformat(),
        "updated_at": (datetime.now() - timedelta(days=1)).isoformat(),
        "synced_at": (datetime.now() - timedelta(days=1)).isoformat(),
        "status": "reviewing",
        "is_local": True,
        "is_synced": True,
    },
    {
        "id": "draft_002",
        "title": "我的AI学习之路：从入门到独立开发",
        "author": "demo",
        "content": "# 我的AI学习之路：从入门到独立开发\n\n## 初遇AI\n\n那是2023年的春天，我第一次接触到了GPT...\n\n## 学习资源\n\n推荐几个对我帮助很大的学习资源...\n",
        "tags": ["学习分享", "成长记录", "AI入门"],
        "category": "个人成长",
        "summary": "一个普通开发者的AI学习历程分享，包含学习方法、资源推荐和踩坑经验。",
        "word_count": 4560,
        "created_at": (datetime.now() - timedelta(days=3)).isoformat(),
        "updated_at": (datetime.now() - timedelta(hours=5)).isoformat(),
        "synced_at": None,
        "status": "draft",
        "is_local": True,
        "is_synced": False,
    },
]

MOCK_PROMPTS: List[Dict[str, Any]] = [
    {
        "id": "prompt_001",
        "title": "结构化技术文档生成器",
        "author": "writer",
        "author_name": "专业写手",
        "content": """[系统设定]
你是一位拥有10年经验的资深技术写作专家，擅长将复杂的技术概念转化为清晰易懂的文档。

[任务描述]
请根据以下技术要点，生成一份结构完整的技术文档：
1. 首先生成文档大纲
2. 然后按大纲逐步展开详细内容
3. 每个章节包含：概念说明、应用场景、代码示例（如适用）、注意事项

[输出要求]
- 使用Markdown格式
- 包含目录
- 代码示例需指定语言
- 字数不少于1000字

技术要点：{technical_points}""",
        "category": "写作辅助",
        "tags": ["技术文档", "写作", "结构化"],
        "model": "GPT-4",
        "rating": 4.8,
        "usage_count": 5680,
        "favorites": 890,
        "created_at": (datetime.now() - timedelta(days=10)).isoformat(),
        "updated_at": (datetime.now() - timedelta(days=2)).isoformat(),
        "is_public": True,
        "is_favorited": True,
        "violation_check": "passed",
    },
    {
        "id": "prompt_002",
        "title": "代码审查专家",
        "author": "admin",
        "author_name": "社区管理员",
        "content": """[系统设定]
你是一位严格但公正的高级代码审查员，拥有丰富的软件工程经验。

[审查维度]
1. 代码正确性：是否存在逻辑错误、边界条件问题
2. 代码风格：是否符合项目规范、命名是否清晰
3. 性能：是否存在明显的性能问题
4. 安全性：是否存在安全漏洞
5. 可维护性：是否易于理解和修改

[输出格式]
### 总体评价
[整体评分和简要评价]

### 发现的问题
**严重程度：[高/中/低]**
- **问题描述**：...
- **位置**：第X行
- **建议修复**：...

### 改进建议
...

待审查代码：
```{language}
{code}
```""",
        "category": "编程辅助",
        "tags": ["代码审查", "质量控制", "最佳实践"],
        "model": "GPT-4 Turbo",
        "rating": 4.9,
        "usage_count": 12500,
        "favorites": 2340,
        "created_at": (datetime.now() - timedelta(days=15)).isoformat(),
        "updated_at": (datetime.now() - timedelta(days=5)).isoformat(),
        "is_public": True,
        "is_favorited": True,
        "violation_check": "passed",
    },
    {
        "id": "prompt_003",
        "title": "小红书爆款文案生成",
        "author": "demo",
        "author_name": "演示用户",
        "content": """[人设]
你是一位小红书资深内容运营，熟悉平台流量密码。

[任务]
请根据以下产品/主题，生成一篇小红书风格的爆款文案：

[要求]
1. 标题要有吸引力，使用emoji
2. 开头3秒抓眼球
3. 内容分点清晰，使用数字
4. 结尾引导互动
5. 加上相关话题标签

主题/产品：{topic}
目标人群：{audience}""",
        "category": "营销文案",
        "tags": ["小红书", "营销", "社交媒体"],
        "model": "GPT-3.5",
        "rating": 4.5,
        "usage_count": 8900,
        "favorites": 1560,
        "created_at": (datetime.now() - timedelta(days=8)).isoformat(),
        "updated_at": (datetime.now() - timedelta(days=1)).isoformat(),
        "is_public": True,
        "is_favorited": False,
        "violation_check": "passed",
    },
]

MOCK_NOTIFICATIONS: List[Dict[str, Any]] = [
    {
        "id": "notif_001",
        "type": "like",
        "content": "专业写手 赞了你的帖子《新长文草稿已提交审核》",
        "from_user": "writer",
        "from_user_name": "专业写手",
        "from_user_avatar": "✍️",
        "target_id": "post_004",
        "target_type": "post",
        "read": False,
        "created_at": (datetime.now() - timedelta(minutes=30)).isoformat(),
    },
    {
        "id": "notif_002",
        "type": "comment",
        "content": "admin 评论了你的帖子：\"期待大作！建议加入模型选型章节~\"",
        "from_user": "admin",
        "from_user_name": "社区管理员",
        "from_user_avatar": "👑",
        "target_id": "post_004",
        "target_type": "post",
        "read": False,
        "created_at": (datetime.now() - timedelta(hours=2)).isoformat(),
    },
    {
        "id": "notif_003",
        "type": "follow",
        "content": "有5位新用户关注了你",
        "from_user": None,
        "from_user_name": None,
        "from_user_avatar": None,
        "target_id": None,
        "target_type": None,
        "extra": {"count": 5},
        "read": False,
        "created_at": (datetime.now() - timedelta(hours=5)).isoformat(),
    },
    {
        "id": "notif_004",
        "type": "favorite",
        "content": "demo 收藏了你的提示词《结构化技术文档生成器》",
        "from_user": "demo",
        "from_user_name": "演示用户",
        "from_user_avatar": "🧪",
        "target_id": "prompt_001",
        "target_type": "prompt",
        "read": True,
        "created_at": (datetime.now() - timedelta(days=1)).isoformat(),
    },
    {
        "id": "notif_005",
        "type": "mention",
        "content": "writer 在评论中@了你：\"@demo 要不要一起写个系列？\"",
        "from_user": "writer",
        "from_user_name": "专业写手",
        "from_user_avatar": "✍️",
        "target_id": "comment_123",
        "target_type": "comment",
        "read": True,
        "created_at": (datetime.now() - timedelta(days=2)).isoformat(),
    },
    {
        "id": "notif_006",
        "type": "system",
        "content": "恭喜！你的等级已提升至 Lv.35，解锁更多社区权益",
        "from_user": None,
        "from_user_name": None,
        "from_user_avatar": None,
        "target_id": None,
        "target_type": None,
        "read": True,
        "created_at": (datetime.now() - timedelta(days=3)).isoformat(),
    },
]

MOCK_COMMENTS: Dict[str, List[Dict[str, Any]]] = {
    "post_004": [
        {
            "id": "comment_001",
            "author": "admin",
            "author_name": "社区管理员",
            "author_avatar": "👑",
            "content": "期待大作！建议加入模型选型章节~",
            "likes": 45,
            "created_at": (datetime.now() - timedelta(hours=2)).isoformat(),
            "replies": [
                {
                    "id": "comment_001_1",
                    "author": "writer",
                    "author_name": "专业写手",
                    "author_avatar": "✍️",
                    "content": "好建议！已经加到大纲里了，感谢🙏",
                    "likes": 12,
                    "created_at": (datetime.now() - timedelta(hours=1, minutes=30)).isoformat(),
                },
            ],
        },
        {
            "id": "comment_002",
            "author": "demo",
            "author_name": "演示用户",
            "author_avatar": "🧪",
            "content": "先关注了，出了第一时间看！另外有没有考虑写成本控制相关的内容？",
            "likes": 23,
            "created_at": (datetime.now() - timedelta(hours=4)).isoformat(),
            "replies": [],
        },
    ],
}

MOCK_FOLLOWING: List[Dict[str, Any]] = [
    {"username": "writer", "display_name": "专业写手", "avatar": "✍️", "bio": "资深内容创作者", "followed_at": (datetime.now() - timedelta(days=20)).isoformat()},
    {"username": "admin", "display_name": "社区管理员", "avatar": "👑", "bio": "AI社区的管理员", "followed_at": (datetime.now() - timedelta(days=30)).isoformat()},
]

MOCK_ACTIVITIES: List[Dict[str, Any]] = [
    {"id": "act_001", "user": "writer", "user_name": "专业写手", "user_avatar": "✍️", "action": "发布了新帖子", "target": "《企业级AI应用监控方案》", "target_type": "post", "target_id": "post_xxx", "created_at": (datetime.now() - timedelta(minutes=15)).isoformat()},
    {"id": "act_002", "user": "admin", "user_name": "社区管理员", "user_avatar": "👑", "action": "上传了新提示词", "target": "《API接口文档自动生成器》", "target_type": "prompt", "target_id": "prompt_xxx", "created_at": (datetime.now() - timedelta(hours=1)).isoformat()},
    {"id": "act_003", "user": "writer", "user_name": "专业写手", "user_avatar": "✍️", "action": "赞了", "target": "admin的帖子《社区运营数据周报》", "target_type": "post", "target_id": "post_yyy", "created_at": (datetime.now() - timedelta(hours=3)).isoformat()},
    {"id": "act_004", "user": "admin", "user_name": "社区管理员", "user_avatar": "👑", "action": "评论了", "target": "writer的帖子《Prompt设计的艺术》", "target_type": "post", "target_id": "post_zzz", "created_at": (datetime.now() - timedelta(hours=6)).isoformat()},
    {"id": "act_005", "user": "demo", "user_name": "演示用户", "user_avatar": "🧪", "action": "关注了", "target": "writer", "target_type": "user", "target_id": "writer", "created_at": (datetime.now() - timedelta(days=1)).isoformat()},
]

MOCK_FAVORITES: Dict[str, List[str]] = {
    "posts": ["post_002", "post_005"],
    "prompts": ["prompt_001", "prompt_002"],
    "comments": [],
}


class APIClient:
    """社区API客户端（包含模拟数据）。"""

    def __init__(self, config: ConfigManager):
        self.config = config
        self._posts: List[Dict[str, Any]] = [p.copy() for p in MOCK_POSTS]
        self._drafts: List[Dict[str, Any]] = [d.copy() for d in MOCK_DRAFTS]
        self._prompts: List[Dict[str, Any]] = [p.copy() for p in MOCK_PROMPTS]
        self._notifications: List[Dict[str, Any]] = [n.copy() for n in MOCK_NOTIFICATIONS]
        self._comments: Dict[str, List[Dict[str, Any]]] = {k: [c.copy() for c in v] for k, v in MOCK_COMMENTS.items()}
        self._following: List[Dict[str, Any]] = [f.copy() for f in MOCK_FOLLOWING]
        self._activities: List[Dict[str, Any]] = [a.copy() for a in MOCK_ACTIVITIES]
        self._favorites: Dict[str, List[str]] = {k: v.copy() for k, v in MOCK_FAVORITES.items()}

    # ==================== 帖子相关 ====================

    def create_post(self, content: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """发布新短帖。"""
        username = self.config.get("username", "anonymous")
        user_info = self.config.get("user_info") or {}
        new_post = {
            "id": f"post_{int(time.time())}",
            "author": username,
            "author_name": user_info.get("display_name", username),
            "author_avatar": user_info.get("avatar", "👤"),
            "content": content,
            "tags": tags or [],
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "views": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "versions": [],
            "is_liked": False,
            "is_favorited": False,
            "status": "published",
        }
        self._posts.insert(0, new_post)
        self._add_activity(username, user_info.get("display_name", username), user_info.get("avatar", "👤"),
                          "发布了新帖子", content[:30] + "..." if len(content) > 30 else content, "post", new_post["id"])
        return new_post

    def list_posts(self, page: int = 1, page_size: int = 20, author: Optional[str] = None,
                   tag: Optional[str] = None) -> Tuple[List[Dict[str, Any]], int]:
        """列出帖子。"""
        posts = self._posts
        if author:
            posts = [p for p in posts if p["author"] == author]
        if tag:
            posts = [p for p in posts if tag in p.get("tags", [])]
        total = len(posts)
        start = (page - 1) * page_size
        return posts[start:start + page_size], total

    def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        """获取帖子详情。"""
        for post in self._posts:
            if post["id"] == post_id:
                return post
        return None

    def get_post_versions(self, post_id: str) -> List[Dict[str, Any]]:
        """获取帖子版本记录。"""
        post = self.get_post(post_id)
        if post:
            return post.get("versions", [])
        return []

    def like_post(self, post_id: str) -> bool:
        """点赞帖子。"""
        post = self.get_post(post_id)
        if post:
            if post["is_liked"]:
                post["likes"] -= 1
                post["is_liked"] = False
            else:
                post["likes"] += 1
                post["is_liked"] = True
            return True
        return False

    # ==================== 草稿相关 ====================

    def list_drafts(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出草稿。"""
        drafts = self._drafts
        if status:
            drafts = [d for d in drafts if d["status"] == status]
        return drafts

    def get_draft(self, draft_id: str) -> Optional[Dict[str, Any]]:
        """获取草稿详情。"""
        for draft in self._drafts:
            if draft["id"] == draft_id:
                return draft
        return None

    def create_draft(self, title: str, content: str, tags: Optional[List[str]] = None,
                     category: Optional[str] = None, summary: Optional[str] = None) -> Dict[str, Any]:
        """创建新草稿。"""
        username = self.config.get("username", "anonymous")
        new_draft = {
            "id": f"draft_{int(time.time())}",
            "title": title,
            "author": username,
            "content": content,
            "tags": tags or [],
            "category": category or "未分类",
            "summary": summary or "",
            "word_count": len(content),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "synced_at": None,
            "status": "draft",
            "is_local": True,
            "is_synced": False,
        }
        self._drafts.insert(0, new_draft)
        self._save_draft_to_local(new_draft)
        return new_draft

    def update_draft(self, draft_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """更新草稿。"""
        draft = self.get_draft(draft_id)
        if draft:
            for key, value in kwargs.items():
                if key in draft and value is not None:
                    draft[key] = value
            draft["updated_at"] = datetime.now().isoformat()
            draft["is_synced"] = False
            if "content" in kwargs:
                draft["word_count"] = len(kwargs["content"])
            self._save_draft_to_local(draft)
            return draft
        return None

    def submit_draft(self, draft_id: str) -> Optional[Dict[str, Any]]:
        """提交草稿审核。"""
        draft = self.get_draft(draft_id)
        if draft and draft["status"] == "draft":
            draft["status"] = "reviewing"
            draft["updated_at"] = datetime.now().isoformat()
            return draft
        return None

    def sync_drafts(self) -> Tuple[int, int]:
        """同步本地草稿到服务端。"""
        synced = 0
        total = 0
        username = self.config.get("username")
        for draft in self._drafts:
            if draft["author"] == username and not draft["is_synced"]:
                total += 1
                draft["is_synced"] = True
                draft["synced_at"] = datetime.now().isoformat()
                synced += 1
            elif draft["author"] == username:
                total += 1
        return synced, total

    def _save_draft_to_local(self, draft: Dict[str, Any]) -> None:
        """保存草稿到本地文件。"""
        draft_file = os.path.join(self.config.drafts_dir, f"{draft['id']}.json")
        try:
            with open(draft_file, "w", encoding="utf-8") as f:
                json.dump(draft, f, ensure_ascii=False, indent=2)
        except IOError:
            pass

    def load_local_drafts(self) -> int:
        """从本地加载草稿。"""
        loaded = 0
        if os.path.exists(self.config.drafts_dir):
            for filename in os.listdir(self.config.drafts_dir):
                if filename.endswith(".json"):
                    filepath = os.path.join(self.config.drafts_dir, filename)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            draft = json.load(f)
                        existing_ids = [d["id"] for d in self._drafts]
                        if draft["id"] not in existing_ids:
                            self._drafts.append(draft)
                            loaded += 1
                    except (json.JSONDecodeError, IOError):
                        pass
        return loaded

    # ==================== 提示词相关 ====================

    def list_prompts(self, page: int = 1, page_size: int = 20, category: Optional[str] = None,
                     sort_by: str = "rating") -> Tuple[List[Dict[str, Any]], int]:
        """列出提示词。"""
        prompts = sorted(self._prompts, key=lambda p: p.get(sort_by, 0), reverse=True)
        if category:
            prompts = [p for p in prompts if p.get("category") == category]
        total = len(prompts)
        start = (page - 1) * page_size
        return prompts[start:start + page_size], total

    def get_prompt(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """获取提示词详情。"""
        for prompt in self._prompts:
            if prompt["id"] == prompt_id:
                return prompt
        return None

    def upload_prompt(self, title: str, content: str, category: str,
                      tags: Optional[List[str]] = None, model: str = "GPT-4",
                      is_public: bool = True) -> Dict[str, Any]:
        """上传提示词。"""
        username = self.config.get("username", "anonymous")
        user_info = self.config.get("user_info") or {}
        new_prompt = {
            "id": f"prompt_{int(time.time())}",
            "title": title,
            "author": username,
            "author_name": user_info.get("display_name", username),
            "content": content,
            "category": category,
            "tags": tags or [],
            "model": model,
            "rating": 0.0,
            "usage_count": 0,
            "favorites": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "is_public": is_public,
            "is_favorited": False,
            "violation_check": "passed",
        }
        self._prompts.insert(0, new_prompt)
        prompt_file = os.path.join(self.config.prompts_dir, f"{new_prompt['id']}.json")
        try:
            with open(prompt_file, "w", encoding="utf-8") as f:
                json.dump(new_prompt, f, ensure_ascii=False, indent=2)
        except IOError:
            pass
        return new_prompt

    def check_violation(self, content: str) -> Tuple[bool, List[str]]:
        """检查内容中的违规词。"""
        keywords = self.config.get_violation_keywords()
        found = []
        content_lower = content.lower()
        for kw in keywords:
            if kw.lower() in content_lower:
                found.append(kw)
        return (len(found) == 0), found

    # ==================== 搜索相关 ====================

    def search(self, query: str, content_type: str = "all",
               min_likes: int = 0, tag: Optional[str] = None,
               page: int = 1, page_size: int = 20) -> Tuple[List[Dict[str, Any]], int]:
        """搜索内容。"""
        results = []
        query_lower = query.lower()

        if content_type in ("all", "posts"):
            for post in self._posts:
                match = query_lower in post["content"].lower() or any(query_lower in t.lower() for t in post.get("tags", []))
                if tag and tag not in post.get("tags", []):
                    match = False
                if post.get("likes", 0) < min_likes:
                    match = False
                if match:
                    item = post.copy()
                    item["_type"] = "post"
                    results.append(item)

        if content_type in ("all", "prompts"):
            for prompt in self._prompts:
                match = (query_lower in prompt["title"].lower() or
                         query_lower in prompt["content"].lower() or
                         any(query_lower in t.lower() for t in prompt.get("tags", [])))
                if tag and tag not in prompt.get("tags", []):
                    match = False
                if prompt.get("favorites", 0) < min_likes:
                    match = False
                if match:
                    item = prompt.copy()
                    item["_type"] = "prompt"
                    item["likes"] = item.get("favorites", 0)
                    results.append(item)

        if content_type in ("all", "drafts"):
            for draft in self._drafts:
                match = query_lower in draft["title"].lower() or query_lower in draft["content"].lower()
                if tag and tag not in draft.get("tags", []):
                    match = False
                if match:
                    item = draft.copy()
                    item["_type"] = "draft"
                    item["likes"] = 0
                    results.append(item)

        total = len(results)
        start = (page - 1) * page_size
        return results[start:start + page_size], total

    # ==================== 关注相关 ====================

    def list_following(self) -> List[Dict[str, Any]]:
        """列出关注列表。"""
        return self._following

    def follow_user(self, username_to_follow: str) -> Optional[Dict[str, Any]]:
        """关注用户。"""
        for f in self._following:
            if f["username"] == username_to_follow:
                return None

        from .auth import MOCK_USERS_DB
        if username_to_follow in MOCK_USERS_DB:
            info = MOCK_USERS_DB[username_to_follow]
            follow_info = {
                "username": username_to_follow,
                "display_name": info["display_name"],
                "avatar": info["avatar"],
                "bio": info["bio"],
                "followed_at": datetime.now().isoformat(),
            }
            self._following.append(follow_info)

            current_user = self.config.get("username", "anonymous")
            current_info = self.config.get("user_info") or {}
            self._add_activity(current_user, current_info.get("display_name", current_user),
                              current_info.get("avatar", "👤"), "关注了", info["display_name"], "user", username_to_follow)
            return follow_info
        return None

    def unfollow_user(self, username: str) -> bool:
        """取消关注。"""
        for i, f in enumerate(self._following):
            if f["username"] == username:
                del self._following[i]
                return True
        return False

    def list_activities(self, page: int = 1, page_size: int = 20,
                        following_only: bool = True) -> Tuple[List[Dict[str, Any]], int]:
        """获取社区活动。"""
        activities = self._activities
        if following_only:
            following_usernames = [f["username"] for f in self._following]
            activities = [a for a in activities if a["user"] in following_usernames or a["user"] == self.config.get("username")]
        total = len(activities)
        start = (page - 1) * page_size
        return activities[start:start + page_size], total

    def _add_activity(self, user: str, user_name: str, user_avatar: str,
                      action: str, target: str, target_type: str, target_id: str) -> None:
        """添加活动记录。"""
        activity = {
            "id": f"act_{int(time.time())}",
            "user": user,
            "user_name": user_name,
            "user_avatar": user_avatar,
            "action": action,
            "target": target,
            "target_type": target_type,
            "target_id": target_id,
            "created_at": datetime.now().isoformat(),
        }
        self._activities.insert(0, activity)

    # ==================== 通知相关 ====================

    def list_notifications(self, unread_only: bool = False,
                           notif_type: Optional[str] = None,
                           page: int = 1, page_size: int = 20) -> Tuple[List[Dict[str, Any]], int, int]:
        """列出通知。"""
        notifs = self._notifications
        if unread_only:
            notifs = [n for n in notifs if not n["read"]]
        if notif_type:
            notifs = [n for n in notifs if n["type"] == notif_type]
        unread_count = sum(1 for n in self._notifications if not n["read"])
        total = len(notifs)
        start = (page - 1) * page_size
        return notifs[start:start + page_size], total, unread_count

    def mark_notification_read(self, notif_id: str) -> bool:
        """标记通知已读。"""
        for notif in self._notifications:
            if notif["id"] == notif_id:
                notif["read"] = True
                return True
        return False

    def mark_all_read(self) -> int:
        """标记所有通知已读。"""
        count = 0
        for notif in self._notifications:
            if not notif["read"]:
                notif["read"] = True
                count += 1
        return count

    def reply_comment(self, target_id: str, content: str,
                      reply_to_comment_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """回复评论或发布评论。"""
        username = self.config.get("username", "anonymous")
        user_info = self.config.get("user_info") or {}
        new_comment = {
            "id": f"comment_{int(time.time())}",
            "author": username,
            "author_name": user_info.get("display_name", username),
            "author_avatar": user_info.get("avatar", "👤"),
            "content": content,
            "likes": 0,
            "created_at": datetime.now().isoformat(),
            "replies": [],
        }

        if target_id not in self._comments:
            self._comments[target_id] = []

        if reply_to_comment_id:
            for comment in self._comments[target_id]:
                if comment["id"] == reply_to_comment_id:
                    comment["replies"].append(new_comment)
                    return new_comment
        else:
            self._comments[target_id].append(new_comment)
            return new_comment
        return None

    def list_comments(self, target_id: str) -> List[Dict[str, Any]]:
        """列出评论。"""
        return self._comments.get(target_id, [])

    def toggle_favorite(self, content_type: str, content_id: str) -> Tuple[bool, bool]:
        """切换收藏状态。

        Returns:
            (操作是否成功, 是否已收藏)
        """
        if content_type not in self._favorites:
            self._favorites[content_type] = []

        fav_list = self._favorites[content_type]
        if content_id in fav_list:
            fav_list.remove(content_id)
            favorited = False
        else:
            fav_list.append(content_id)
            favorited = True

        if content_type == "posts":
            post = self.get_post(content_id)
            if post:
                post["is_favorited"] = favorited
        elif content_type == "prompts":
            prompt = self.get_prompt(content_id)
            if prompt:
                prompt["is_favorited"] = favorited

        return True, favorited

    def list_favorites(self, content_type: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """列出收藏内容。"""
        result = {}
        types_to_check = [content_type] if content_type else ["posts", "prompts", "comments"]

        if "posts" in types_to_check:
            result["posts"] = [self.get_post(pid) for pid in self._favorites.get("posts", []) if self.get_post(pid)]
        if "prompts" in types_to_check:
            result["prompts"] = [self.get_prompt(pid) for pid in self._favorites.get("prompts", []) if self.get_prompt(pid)]
        if "comments" in types_to_check:
            result["comments"] = []

        return result

    # ==================== 导出相关 ====================

    def get_user_stats(self, months: int = 1) -> Dict[str, Any]:
        """获取用户统计数据（用于月报生成）。"""
        username = self.config.get("username", "anonymous")
        user_info = self.config.get("user_info") or {}

        start_date = datetime.now() - timedelta(days=30 * months)
        user_posts = [p for p in self._posts if p["author"] == username and datetime.fromisoformat(p["created_at"]) >= start_date]
        user_prompts = [p for p in self._prompts if p["author"] == username and datetime.fromisoformat(p["created_at"]) >= start_date]
        user_drafts = [d for d in self._drafts if d["author"] == username and datetime.fromisoformat(d["updated_at"]) >= start_date]

        total_likes = sum(p.get("likes", 0) for p in user_posts)
        total_comments = sum(p.get("comments", 0) for p in user_posts)
        total_views = sum(p.get("views", 0) for p in user_posts)
        total_prompt_usage = sum(p.get("usage_count", 0) for p in user_prompts)
        total_words = sum(d.get("word_count", 0) for d in user_drafts)

        return {
            "period": f"{months}个月",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": datetime.now().strftime("%Y-%m-%d"),
            "user": {
                "username": username,
                "display_name": user_info.get("display_name", username),
                "level": user_info.get("level", 0),
                "points": user_info.get("points", 0),
            },
            "posts": {
                "count": len(user_posts),
                "total_likes": total_likes,
                "total_comments": total_comments,
                "total_views": total_views,
                "avg_likes": round(total_likes / len(user_posts), 1) if user_posts else 0,
            },
            "prompts": {
                "count": len(user_prompts),
                "total_usage": total_prompt_usage,
                "total_favorites": sum(p.get("favorites", 0) for p in user_prompts),
            },
            "drafts": {
                "count": len(user_drafts),
                "total_words": total_words,
            },
            "following": len(self._following),
            "followers": user_info.get("followers", 0),
            "notifications_received": len([n for n in self._notifications if datetime.fromisoformat(n["created_at"]) >= start_date]),
        }

    def export_prompts(self, output_dir: str, format_type: str = "json",
                       include_private: bool = True, category: Optional[str] = None,
                       tag: Optional[str] = None) -> Tuple[int, str]:
        """批量导出提示词。"""
        username = self.config.get("username", "anonymous")
        prompts = [p for p in self._prompts if p["author"] == username]
        if not include_private:
            prompts = [p for p in prompts if p.get("is_public")]
        if category:
            prompts = [p for p in prompts if p.get("category") == category]
        if tag:
            prompts = [p for p in prompts if tag in p.get("tags", [])]

        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format_type == "json":
            filename = f"prompts_export_{timestamp}.json"
            filepath = os.path.join(output_dir, filename)
            export_data = []
            for p in prompts:
                export_data.append({
                    "id": p["id"],
                    "title": p["title"],
                    "content": p["content"],
                    "category": p.get("category", ""),
                    "tags": p.get("tags", []),
                    "model": p.get("model", ""),
                    "created_at": p.get("created_at", ""),
                    "updated_at": p.get("updated_at", ""),
                })
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

        elif format_type == "yaml":
            filename = f"prompts_export_{timestamp}.yaml"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                import yaml
                yaml.dump(prompts, f, default_flow_style=False, allow_unicode=True)

        elif format_type == "markdown":
            filename = f"prompts_export_{timestamp}.md"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# 提示词导出报告\n\n")
                f.write(f"**导出时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"**导出数量：** {len(prompts)} 个\n\n")
                f.write("---\n\n")
                for p in prompts:
                    f.write(f"## {p['title']}\n\n")
                    f.write(f"- **分类：** {p.get('category', '未分类')}\n")
                    f.write(f"- **标签：** {', '.join(p.get('tags', []))}\n")
                    f.write(f"- **模型：** {p.get('model', '通用')}\n")
                    f.write(f"- **创建时间：** {p.get('created_at', '')}\n\n")
                    f.write("### Prompt内容\n\n```\n")
                    f.write(p["content"])
                    f.write("\n```\n\n---\n\n")
        else:
            return 0, ""

        return len(prompts), filepath

    def generate_monthly_report(self, output_dir: str, months: int = 1,
                                format_type: str = "markdown") -> Optional[str]:
        """生成个人月报。"""
        stats = self.get_user_stats(months)
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format_type == "markdown":
            filename = f"monthly_report_{timestamp}.md"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# {stats['user']['display_name']} 的个人月报\n\n")
                f.write(f"**统计周期：** {stats['start_date']} ~ {stats['end_date']} ({stats['period']})\n\n")

                f.write("## 📊 概览\n\n")
                f.write(f"| 指标 | 数值 |\n")
                f.write(f"|------|------|\n")
                f.write(f"| 等级 | Lv.{stats['user']['level']} |\n")
                f.write(f"| 积分 | {stats['user']['points']:,} |\n")
                f.write(f"| 关注者 | {stats['followers']:,} |\n")
                f.write(f"| 正在关注 | {stats['following']} |\n\n")

                f.write("## 📝 内容产出\n\n")
                f.write("### 帖子\n\n")
                f.write(f"- **发布数量：** {stats['posts']['count']} 篇\n")
                f.write(f"- **总点赞数：** {stats['posts']['total_likes']:,}\n")
                f.write(f"- **总评论数：** {stats['posts']['total_comments']:,}\n")
                f.write(f"- **总浏览量：** {stats['posts']['total_views']:,}\n")
                f.write(f"- **平均点赞：** {stats['posts']['avg_likes']}\n\n")

                f.write("### 提示词\n\n")
                f.write(f"- **上传数量：** {stats['prompts']['count']} 个\n")
                f.write(f"- **总使用次数：** {stats['prompts']['total_usage']:,}\n")
                f.write(f"- **总收藏数：** {stats['prompts']['total_favorites']:,}\n\n")

                f.write("### 长文草稿\n\n")
                f.write(f"- **活跃草稿：** {stats['drafts']['count']} 篇\n")
                f.write(f"- **总字数：** {stats['drafts']['total_words']:,} 字\n\n")

                f.write("## 📬 互动情况\n\n")
                f.write(f"- **收到通知：** {stats['notifications_received']} 条\n\n")

                total_score = (
                    stats['posts']['count'] * 10 +
                    stats['posts']['total_likes'] * 1 +
                    stats['prompts']['count'] * 20 +
                    stats['drafts']['total_words'] // 100
                )
                f.write("## 🏆 综合评分\n\n")
                f.write(f"**本月活跃度得分：{total_score}**\n\n")

                if total_score >= 1000:
                    f.write("> 🎉 太棒了！你是社区的核心贡献者，继续保持！\n")
                elif total_score >= 500:
                    f.write("> 💪 做得不错！本月表现很活跃，再接再厉！\n")
                elif total_score >= 100:
                    f.write("> 👍 稳步前进，期待你更多的优质内容！\n")
                else:
                    f.write("> 🌱 这个月稍微安静了些，下个月加油哦！\n")

            return filepath
        return None
