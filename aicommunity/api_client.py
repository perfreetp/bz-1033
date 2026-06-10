"""API客户端模块。

提供与社区服务端交互的接口，包含模拟数据用于演示。
"""

import csv
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
        "status": "transferred",
        "is_local": True,
        "is_synced": True,
        "reviewer": "admin",
        "review_comments": [
            {"id": "rc_001", "reviewer": "admin", "comment": "架构章节讲得不错，数据治理部分请补充更多实战案例。",
             "created_at": (datetime.now() - timedelta(hours=8)).isoformat()}
        ],
        "audit_history": [
            {"action": "create", "actor": "writer", "time": (datetime.now() - timedelta(days=5)).isoformat(), "detail": "创建草稿"},
            {"action": "edit", "actor": "writer", "time": (datetime.now() - timedelta(days=2)).isoformat(), "detail": "更新正文"},
            {"action": "submit_for_review", "actor": "writer", "time": (datetime.now() - timedelta(days=1)).isoformat(), "detail": "提交审核"},
            {"action": "transfer", "actor": "writer", "time": (datetime.now() - timedelta(hours=10)).isoformat(),
             "detail": "转让审阅给admin"},
        ],
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
        "reviewer": None,
        "review_comments": [],
        "audit_history": [
            {"action": "create", "actor": "demo", "time": (datetime.now() - timedelta(days=3)).isoformat(), "detail": "创建草稿"},
        ],
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
    """社区API客户端（包含模拟数据和本地持久化）。"""

    CACHE_KEY = "aicommunity_state_v2"  # v2: 支持多用户profile隔离
    LEGACY_CACHE_KEY = "aicommunity_state_v1"

    def __init__(self, config: ConfigManager):
        self.config = config
        self._load_state()

    def _current_user(self) -> str:
        """获取当前登录用户名（未登录用 anonymous）。"""
        return self.config.get("username") or "anonymous"

    def _get_user_profile(self, username: Optional[str] = None) -> Dict[str, Any]:
        """获取指定（或当前）用户的私有profile数据。不存在则创建默认结构。"""
        user = username or self._current_user()
        if user not in self._user_profiles:
            self._user_profiles[user] = {
                "liked_posts": [],
                "favorites": {"posts": [], "prompts": [], "comments": []},
                "following": [],
                "read_notifications": [],
            }
        return self._user_profiles[user]

    def _migrate_v1_to_v2(self, v1_state: Dict[str, Any], cache: Dict[str, Any]) -> None:
        """迁移旧版v1缓存到新版v2结构，迁移前生成备份。"""
        # 备份
        backup_key = f"aicommunity_state_v1_backup_{int(time.time())}"
        cache[backup_key] = json.loads(json.dumps(v1_state))  # 深拷贝备份

        # 全局共享数据直接迁移
        self._posts = v1_state.get("posts", [p.copy() for p in MOCK_POSTS])
        self._drafts = v1_state.get("drafts", [d.copy() for d in MOCK_DRAFTS])
        self._prompts = v1_state.get("prompts", [p.copy() for p in MOCK_PROMPTS])
        self._notifications = v1_state.get("notifications", [n.copy() for n in MOCK_NOTIFICATIONS])
        self._comments = v1_state.get("comments", {k: [c.copy() for c in v] for k, v in MOCK_COMMENTS.items()})
        self._activities = v1_state.get("activities", [a.copy() for a in MOCK_ACTIVITIES])

        # 给每篇草稿补 versions 字段（若没有）
        for d in self._drafts:
            if "versions" not in d:
                d["versions"] = [{
                    "version": 1,
                    "title": d.get("title", ""),
                    "content": d.get("content", ""),
                    "summary": d.get("summary", ""),
                    "created_at": d.get("created_at", datetime.now().isoformat()),
                }]
            if "reviewer" not in d:
                d["reviewer"] = None
            if "review_comments" not in d:
                d["review_comments"] = []
            if "audit_history" not in d:
                d["audit_history"] = [{
                    "action": "create",
                    "actor": d.get("author", ""),
                    "time": d.get("created_at", datetime.now().isoformat()),
                    "detail": "创建草稿（迁移补全）",
                }]

        # 给每个提示词补 is_public 字段（默认 True）
        for p in self._prompts:
            if "is_public" not in p:
                p["is_public"] = True
            if "approval_status" not in p:
                p["approval_status"] = "approved" if p.get("is_public") else "none"
            if "rejection_reason" not in p:
                p["rejection_reason"] = None
            if "approval_history" not in p:
                p["approval_history"] = []
            if "is_favorited" in p:
                del p["is_favorited"]  # 移除废弃字段，改用user_profiles存储

        # 迁移用户私有状态到 writer（兼容旧版默认在 writer 登录下修改）
        writer_profile = self._get_user_profile("writer")
        writer_profile["liked_posts"] = v1_state.get("liked_posts", [p["id"] for p in self._posts if p.get("is_liked")])
        writer_profile["favorites"] = v1_state.get("favorites", {"posts": [], "prompts": [], "comments": []})
        writer_profile["following"] = v1_state.get("following", [])
        writer_profile["read_notifications"] = [n["id"] for n in self._notifications if n.get("read")]

        # 清理 posts 中被用户状态覆盖的废弃字段（is_liked/is_favorited由视图注入）
        for p in self._posts:
            p.pop("is_liked", None)
            p.pop("is_favorited", None)

        # 同步给 admin 和 demo 用户默认空结构，避免切换时报无版本问题
        self._get_user_profile("admin")
        self._get_user_profile("demo")
        self._audit_logs = []

        # 保存备份key提示
        self.config.set("last_migration_backup", backup_key)
        console.print(f"[dim]🔄 检测到旧版v1缓存，已自动迁移到v2结构（备份key: {backup_key}）[/dim]")

    def _load_state(self) -> None:
        """从本地cache加载状态，支持v1→v2自动迁移，若无则使用默认mock数据。"""
        cache = self.config.load_cache()

        # 先尝试加载新版 v2
        state = cache.get(self.CACHE_KEY, None)

        if state is None and self.LEGACY_CACHE_KEY in cache:
            # === 触发 v1 → v2 迁移 ===
            v1_state = cache[self.LEGACY_CACHE_KEY]
            self._user_profiles: Dict[str, Dict[str, Any]] = {}
            self._migrate_v1_to_v2(v1_state, cache)
            # 迁移完成后写入新结构
            self.save()
            return

        if state:
            # 全局共享数据（所有用户可见）
            self._posts = state.get("posts", [])
            self._drafts = state.get("drafts", [])
            self._prompts = state.get("prompts", [])
            self._notifications = state.get("notifications", [])
            self._comments = state.get("comments", {})
            self._activities = state.get("activities", [])
            self._audit_logs = state.get("audit_logs", [])
            # 按用户隔离的数据
            self._user_profiles = state.get("user_profiles", {})
            return

        # 完全没有缓存：初始化为默认mock数据
        self._posts = [p.copy() for p in MOCK_POSTS]
        self._drafts = [d.copy() for d in MOCK_DRAFTS]
        self._prompts = [p.copy() for p in MOCK_PROMPTS]
        self._notifications = [n.copy() for n in MOCK_NOTIFICATIONS]
        self._comments = {k: [c.copy() for c in v] for k, v in MOCK_COMMENTS.items()}
        self._activities = [a.copy() for a in MOCK_ACTIVITIES]

        # 初始化草稿版本号（mock数据可能没有versions）
        for d in self._drafts:
            if "versions" not in d:
                d["versions"] = [{
                    "version": 1,
                    "title": d.get("title", ""),
                    "content": d.get("content", ""),
                    "summary": d.get("summary", ""),
                    "created_at": d.get("created_at", datetime.now().isoformat()),
                }]
            if "reviewer" not in d:
                d["reviewer"] = None
            if "review_comments" not in d:
                d["review_comments"] = []
            if "audit_history" not in d:
                d["audit_history"] = []

        for p in self._prompts:
            if "approval_status" not in p:
                p["approval_status"] = "approved" if p.get("is_public") else "none"
            if "rejection_reason" not in p:
                p["rejection_reason"] = None
            if "approval_history" not in p:
                p["approval_history"] = []

        # 按用户隔离：默认writer用户有一些初始状态（匹配MOCK数据）
        self._user_profiles: Dict[str, Dict[str, Any]] = {}
        writer_profile = self._get_user_profile("writer")
        writer_profile["liked_posts"] = ["post_002", "post_004"]
        writer_profile["favorites"] = {"posts": ["post_002"], "prompts": ["prompt_001", "prompt_002"], "comments": []}
        writer_profile["following"] = [f.copy() for f in MOCK_FOLLOWING]
        writer_profile["read_notifications"] = []

        admin_profile = self._get_user_profile("admin")
        admin_profile["favorites"] = {"posts": ["post_005"], "prompts": ["prompt_002"], "comments": []}
        admin_profile["liked_posts"] = ["post_005"]
        admin_profile["following"] = []
        admin_profile["read_notifications"] = []

        self._get_user_profile("demo")
        self._audit_logs = []
        self.save()

    def save(self) -> None:
        """将当前状态保存到本地cache。"""
        cache = self.config.load_cache()
        cache[self.CACHE_KEY] = {
            # 全局共享数据
            "posts": self._posts,
            "drafts": self._drafts,
            "prompts": self._prompts,
            "notifications": self._notifications,
            "comments": self._comments,
            "activities": self._activities,
            "audit_logs": self._audit_logs,
            # 按用户隔离数据
            "user_profiles": self._user_profiles,
        }
        self.config.save_cache(cache)

    def _inject_user_view_flags(self, item: Dict[str, Any], item_type: str) -> Dict[str, Any]:
        """给一条帖子/提示词注入当前用户的 is_liked / is_favorited 视图标记。"""
        profile = self._get_user_profile()
        item = item.copy()
        if item_type == "post":
            item["is_liked"] = item["id"] in profile["liked_posts"]
            item["is_favorited"] = item["id"] in profile["favorites"].get("posts", [])
        elif item_type == "prompt":
            item["is_favorited"] = item["id"] in profile["favorites"].get("prompts", [])
        return item

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
        self.save()
        self._log_audit("create_post", "post", new_post["id"], f"发布帖子，标签={tags or []}")
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
        # 注入当前用户视图标记
        result = [self._inject_user_view_flags(p, "post") for p in posts[start:start + page_size]]
        return result, total

    def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        """获取帖子详情（带当前用户视图标记）。"""
        for post in self._posts:
            if post["id"] == post_id:
                return self._inject_user_view_flags(post, "post")
        return None

    def get_post_raw(self, post_id: str) -> Optional[Dict[str, Any]]:
        """获取帖子原始数据（不注入视图标记，供内部修改使用）。"""
        for post in self._posts:
            if post["id"] == post_id:
                return post
        return None

    def get_post_versions(self, post_id: str) -> List[Dict[str, Any]]:
        """获取帖子版本记录。"""
        post = self.get_post_raw(post_id)
        if post:
            return post.get("versions", [])
        return []

    def like_post(self, post_id: str) -> bool:
        """点赞帖子（切换状态）。更新全局likes计数和当前用户的点赞列表。"""
        post = self.get_post_raw(post_id)
        if not post:
            return False
        profile = self._get_user_profile()
        liked = post_id in profile["liked_posts"]
        if liked:
            profile["liked_posts"].remove(post_id)
            post["likes"] = max(0, post.get("likes", 0) - 1)
            action = "unlike"
            msg = "取消点赞"
        else:
            profile["liked_posts"].append(post_id)
            post["likes"] = post.get("likes", 0) + 1
            action = "like"
            msg = "点赞"
        self.save()
        self._log_audit(action, "post", post_id, msg)
        return True

    # ==================== 草稿相关 ====================

    def list_drafts(self, status: Optional[str] = None, author: Optional[str] = None,
                    sort_by: str = "updated_at",
                    days: Optional[int] = None,
                    from_date: Optional[str] = None,
                    to_date: Optional[str] = None,
                    only_local: bool = False,
                    mine_only: bool = True) -> List[Dict[str, Any]]:
        """列出草稿，支持状态、作者、时间、同步状态多维筛选。

        - mine_only=True 默认只看当前用户的草稿（设为False可看所有）
        - days: 最近N天（按updated_at）
        - from_date/to_date: YYYY-MM-DD 起止日期（按updated_at）
        - only_local: 仅本地未同步的（is_synced=False）
        """
        drafts = list(self._drafts)

        # 作者/我自己筛选
        if mine_only:
            username = self._current_user()
            drafts = [d for d in drafts if d.get("author") == username]
        elif author:
            drafts = [d for d in drafts if d.get("author") == author]

        if status:
            drafts = [d for d in drafts if d["status"] == status]
        if only_local:
            drafts = [d for d in drafts if not d.get("is_synced", False)]

        # 时间筛选
        from datetime import datetime as _dt, timedelta as _td
        now = _dt.now()
        if days:
            cutoff = now - _td(days=days)
            drafts = [d for d in drafts if _dt.fromisoformat(d.get("updated_at", now.isoformat())) >= cutoff]
        if from_date:
            try:
                start = _dt.fromisoformat(f"{from_date}T00:00:00")
                drafts = [d for d in drafts if _dt.fromisoformat(d.get("updated_at", start.isoformat())) >= start]
            except (ValueError, TypeError):
                pass
        if to_date:
            try:
                end = _dt.fromisoformat(f"{to_date}T23:59:59")
                drafts = [d for d in drafts if _dt.fromisoformat(d.get("updated_at", end.isoformat())) <= end]
            except (ValueError, TypeError):
                pass

        # 默认按更新时间倒序（新→旧）
        drafts.sort(key=lambda d: d.get(sort_by, ""), reverse=True)
        return drafts

    def get_draft(self, draft_id: str) -> Optional[Dict[str, Any]]:
        """获取草稿详情。"""
        for draft in self._drafts:
            if draft["id"] == draft_id:
                return draft
        return None

    def get_draft_versions(self, draft_id: str) -> List[Dict[str, Any]]:
        """获取草稿的编辑历史版本列表（最近在前）。"""
        draft = self.get_draft(draft_id)
        if draft:
            return list(reversed(draft.get("versions", [])))
        return []

    def create_draft(self, title: str, content: str, tags: Optional[List[str]] = None,
                     category: Optional[str] = None, summary: Optional[str] = None) -> Dict[str, Any]:
        """创建新草稿，自动记录初始版本。"""
        username = self.config.get("username", "anonymous")
        now = datetime.now().isoformat()
        new_draft = {
            "id": f"draft_{int(time.time())}",
            "title": title,
            "author": username,
            "content": content,
            "tags": tags or [],
            "category": category or "未分类",
            "summary": summary or "",
            "word_count": len(content),
            "created_at": now,
            "updated_at": now,
            "synced_at": None,
            "status": "draft",
            "is_local": True,
            "is_synced": False,
            "versions": [
                {"version": 1, "title": title, "content": content, "created_at": now, "summary": summary or ""}
            ],
        }
        self._drafts.insert(0, new_draft)
        self._save_draft_to_local(new_draft)
        self.save()
        return new_draft

    def update_draft(self, draft_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """更新草稿，修改前先推入版本栈。"""
        draft = self.get_draft(draft_id)
        if draft:
            # 修改前把当前状态记录为一个版本（只有改了title/content/summary才记录）
            has_substantial_change = any(k in kwargs for k in ("title", "content", "summary"))
            old_title = draft.get("title", "")
            old_content = draft.get("content", "")
            old_summary = draft.get("summary", "")
            for key, value in kwargs.items():
                if key in draft and value is not None:
                    draft[key] = value
            draft["updated_at"] = datetime.now().isoformat()
            draft["is_synced"] = False
            if "content" in kwargs:
                draft["word_count"] = len(kwargs["content"])
            if has_substantial_change:
                next_ver = len(draft.get("versions", [])) + 1
                draft.setdefault("versions", []).append({
                    "version": next_ver,
                    "title": old_title,
                    "content": old_content,
                    "summary": old_summary,
                    "created_at": datetime.now().isoformat(),
                })
            self._save_draft_to_local(draft)
            self.save()
            return draft
        return None

    def rollback_draft(self, draft_id: str, version: int) -> Optional[Dict[str, Any]]:
        """回滚草稿到指定版本号。"""
        draft = self.get_draft(draft_id)
        if not draft:
            return None
        versions = draft.get("versions", [])
        target = next((v for v in versions if v["version"] == version), None)
        if not target:
            return None
        # 先将当前状态推入新版本
        next_ver = len(versions) + 1
        versions.append({
            "version": next_ver,
            "title": draft.get("title", ""),
            "content": draft.get("content", ""),
            "summary": draft.get("summary", ""),
            "created_at": datetime.now().isoformat(),
        })
        # 恢复目标版本
        draft["title"] = target["title"]
        draft["content"] = target["content"]
        draft["summary"] = target.get("summary", "")
        draft["word_count"] = len(draft["content"])
        draft["updated_at"] = datetime.now().isoformat()
        draft["is_synced"] = False
        self._save_draft_to_local(draft)
        self.save()
        return draft

    def submit_draft(self, draft_id: str) -> Optional[Dict[str, Any]]:
        """提交草稿审核。"""
        draft = self.get_draft(draft_id)
        if draft and draft["status"] == "draft":
            draft["status"] = "reviewing"
            draft["updated_at"] = datetime.now().isoformat()
            self.save()
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
        if synced > 0:
            self.save()
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
                     sort_by: str = "rating", mine_only: bool = False,
                     only_favorites: bool = False, only_public: bool = False) -> Tuple[List[Dict[str, Any]], int]:
        """列出提示词（严格可见性控制）。

        - 公共浏览（非mine）：只能看到 公开(is_public=True) 的所有提示词
        - 我的(mine_only=True)：可看到自己全部（含私有）
        - 同时 only_public 会再过滤（只看公开）
        - 永远不会看到他人的私有提示词
        """
        username = self._current_user()
        profile = self._get_user_profile()
        prompts = list(self._prompts)

        # === 可见性核心过滤：他人私有一律拦截 ===
        if not mine_only:
            prompts = [p for p in prompts if p.get("is_public", True)]
        else:
            # 只看我的（含我自己的私有内容）
            prompts = [p for p in prompts if p.get("author") == username]

        if category:
            prompts = [p for p in prompts if p.get("category") == category]
        if only_favorites:
            fav_ids = profile["favorites"].get("prompts", [])
            prompts = [p for p in prompts if p["id"] in fav_ids]
        if only_public:
            prompts = [p for p in prompts if p.get("is_public", True)]
        prompts.sort(key=lambda p: p.get(sort_by, 0), reverse=True)
        total = len(prompts)
        start = (page - 1) * page_size
        result = [self._inject_user_view_flags(p, "prompt") for p in prompts[start:start + page_size]]
        return result, total

    def get_prompt(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """获取提示词详情（含权限校验：他人私有提示词返回None）。"""
        username = self._current_user()
        for prompt in self._prompts:
            if prompt["id"] == prompt_id:
                # 他人私有 → 拦截（假装不存在）
                if not prompt.get("is_public", True) and prompt.get("author") != username:
                    return None
                return self._inject_user_view_flags(prompt, "prompt")
        return None

    def _get_prompt_raw_unchecked(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """内部使用：原始数据获取（不做权限校验，仅用于edit/delete前查找）。"""
        for prompt in self._prompts:
            if prompt["id"] == prompt_id:
                return prompt
        return None

    def get_prompt_raw(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """获取提示词原始数据（供内部修改，含权限校验）。"""
        username = self._current_user()
        for prompt in self._prompts:
            if prompt["id"] == prompt_id:
                if not prompt.get("is_public", True) and prompt.get("author") != username:
                    return None
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
            "violation_check": "passed",
        }
        self._prompts.insert(0, new_prompt)
        prompt_file = os.path.join(self.config.prompts_dir, f"{new_prompt['id']}.json")
        try:
            with open(prompt_file, "w", encoding="utf-8") as f:
                json.dump(new_prompt, f, ensure_ascii=False, indent=2)
        except IOError:
            pass
        self.save()
        return new_prompt

    def edit_prompt(self, prompt_id: str, **kwargs) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """编辑提示词。

        可改字段：title, content, category, tags, model, is_public。
        只能修改自己上传的。
        Returns: (success, message, prompt_or_None)
        """
        username = self._current_user()
        prompt = self.get_prompt_raw(prompt_id)
        if not prompt:
            return False, "提示词不存在", None
        if prompt.get("author") != username:
            return False, "只能编辑自己上传的提示词", None
        allowed_keys = {"title", "content", "category", "tags", "model", "is_public"}
        modified = False
        for k, v in kwargs.items():
            if k in allowed_keys and v is not None:
                prompt[k] = v
                modified = True
        if modified:
            prompt["updated_at"] = datetime.now().isoformat()
            # 同步保存到prompts目录的json
            prompt_file = os.path.join(self.config.prompts_dir, f"{prompt_id}.json")
            try:
                with open(prompt_file, "w", encoding="utf-8") as f:
                    json.dump(prompt, f, ensure_ascii=False, indent=2)
            except IOError:
                pass
            self.save()
            return True, "编辑成功", prompt
        return False, "没有需要修改的内容", None

    def delete_prompt(self, prompt_id: str) -> Tuple[bool, str]:
        """删除提示词。只能删除自己上传的。"""
        username = self._current_user()
        prompt = self.get_prompt_raw(prompt_id)
        if not prompt:
            return False, "提示词不存在"
        if prompt.get("author") != username:
            return False, "只能删除自己上传的提示词"
        self._prompts.remove(prompt)
        # 从每个用户的收藏列表中移除
        for profile in self._user_profiles.values():
            if prompt_id in profile["favorites"].get("prompts", []):
                profile["favorites"]["prompts"].remove(prompt_id)
        # 删除prompts目录的本地文件
        prompt_file = os.path.join(self.config.prompts_dir, f"{prompt_id}.json")
        if os.path.exists(prompt_file):
            try:
                os.remove(prompt_file)
            except OSError:
                pass
        self.save()
        return True, "删除成功"

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
        """搜索内容（提示词严格按可见性过滤，草稿只搜自己的）。"""
        results = []
        query_lower = query.lower()
        username = self._current_user()

        if content_type in ("all", "posts"):
            for post in self._posts:
                match = query_lower in post["content"].lower() or any(query_lower in t.lower() for t in post.get("tags", []))
                if tag and tag not in post.get("tags", []):
                    match = False
                if post.get("likes", 0) < min_likes:
                    match = False
                if match:
                    item = self._inject_user_view_flags(post, "post")
                    item["_type"] = "post"
                    results.append(item)

        if content_type in ("all", "prompts"):
            for prompt in self._prompts:
                # === 提示词可见性过滤：他人私有一律排除 ===
                is_private = not prompt.get("is_public", True)
                if is_private and prompt.get("author") != username:
                    continue
                match = (query_lower in prompt["title"].lower() or
                         query_lower in prompt["content"].lower() or
                         any(query_lower in t.lower() for t in prompt.get("tags", [])))
                if tag and tag not in prompt.get("tags", []):
                    match = False
                if prompt.get("favorites", 0) < min_likes:
                    match = False
                if match:
                    item = self._inject_user_view_flags(prompt, "prompt")
                    item["_type"] = "prompt"
                    item["likes"] = item.get("favorites", 0)
                    results.append(item)

        if content_type in ("all", "drafts"):
            # 草稿只搜索自己的
            for draft in self._drafts:
                if draft.get("author") != username:
                    continue
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
        """列出当前用户的关注列表。"""
        profile = self._get_user_profile()
        return profile["following"]

    def follow_user(self, username_to_follow: str) -> Optional[Dict[str, Any]]:
        """关注用户。"""
        profile = self._get_user_profile()
        for f in profile["following"]:
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
            profile["following"].append(follow_info)

            current_user = self.config.get("username", "anonymous")
            current_info = self.config.get("user_info") or {}
            self._add_activity(current_user, current_info.get("display_name", current_user),
                              current_info.get("avatar", "👤"), "关注了", info["display_name"], "user", username_to_follow)
            self.save()
            self._log_audit("follow", "user", username_to_follow, f"关注了{info['display_name']}")
            return follow_info
        return None

    def unfollow_user(self, username: str) -> bool:
        """取消关注。"""
        profile = self._get_user_profile()
        for i, f in enumerate(profile["following"]):
            if f["username"] == username:
                del profile["following"][i]
                self.save()
                self._log_audit("unfollow", "user", username, f"取消关注{f.get('display_name', username)}")
                return True
        return False

    def list_activities(self, page: int = 1, page_size: int = 20,
                        following_only: bool = True) -> Tuple[List[Dict[str, Any]], int]:
        """获取社区活动。"""
        activities = self._activities
        if following_only:
            profile = self._get_user_profile()
            following_usernames = [f["username"] for f in profile["following"]]
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
        self.save()

    # ==================== 通知相关 ====================

    def list_notifications(self, unread_only: bool = False,
                           notif_type: Optional[str] = None,
                           page: int = 1, page_size: int = 20) -> Tuple[List[Dict[str, Any]], int, int]:
        """列出通知（已读/未读状态按当前用户隔离）。"""
        profile = self._get_user_profile()
        read_ids = set(profile["read_notifications"])
        # 生成带当前用户is_read标记的通知副本
        notifs = []
        for n in self._notifications:
            n_copy = n.copy()
            n_copy["read"] = n["id"] in read_ids
            notifs.append(n_copy)
        if unread_only:
            notifs = [n for n in notifs if not n["read"]]
        if notif_type:
            notifs = [n for n in notifs if n["type"] == notif_type]
        unread_count = sum(1 for n in notifs if not n["read"])
        # 这里unread_count应该是全局当前用户的总未读数，不是筛选后的
        total_unread = sum(1 for n in self._notifications if n["id"] not in read_ids)
        total = len(notifs)
        start = (page - 1) * page_size
        return notifs[start:start + page_size], total, total_unread

    def mark_notification_read(self, notif_id: str) -> bool:
        """标记通知已读（仅影响当前用户）。"""
        for notif in self._notifications:
            if notif["id"] == notif_id:
                profile = self._get_user_profile()
                if notif_id not in profile["read_notifications"]:
                    profile["read_notifications"].append(notif_id)
                    self.save()
                return True
        return False

    def mark_all_read(self) -> int:
        """标记所有通知已读（仅影响当前用户）。"""
        profile = self._get_user_profile()
        count = 0
        for notif in self._notifications:
            if notif["id"] not in profile["read_notifications"]:
                profile["read_notifications"].append(notif["id"])
                count += 1
        if count > 0:
            self.save()
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
                    self.save()
                    return new_comment
        else:
            self._comments[target_id].append(new_comment)
            # 更新帖子的评论计数（用raw避免循环注入）
            post = self.get_post_raw(target_id)
            if post:
                post["comments"] = post.get("comments", 0) + 1
            self.save()
            return new_comment
        return None

    def list_comments(self, target_id: str) -> List[Dict[str, Any]]:
        """列出评论。"""
        return self._comments.get(target_id, [])

    def toggle_favorite(self, content_type: str, content_id: str) -> Tuple[bool, bool, str]:
        """切换收藏状态。

        Returns:
            (操作是否成功, 是否已收藏, 提示消息)
        """
        profile = self._get_user_profile()
        fav_store = profile["favorites"]
        if content_type not in fav_store:
            fav_store[content_type] = []

        # 先校验内容是否存在
        content_exists = False
        if content_type == "posts":
            content_exists = self.get_post_raw(content_id) is not None
        elif content_type == "prompts":
            content_exists = self.get_prompt_raw(content_id) is not None
        elif content_type == "comments":
            # 评论存在性校验（遍历所有帖子的评论）
            for comment_list in self._comments.values():
                if any(c["id"] == content_id for c in comment_list):
                    content_exists = True
                    break
        if not content_exists:
            return False, False, f"未找到对应内容（类型={content_type}, id={content_id}）"

        fav_list = fav_store[content_type]
        if content_id in fav_list:
            fav_list.remove(content_id)
            favorited = False
            msg = "已取消收藏"
        else:
            fav_list.append(content_id)
            favorited = True
            msg = "收藏成功"

        # 同步更新全局收藏计数器
        if content_type == "posts":
            post = self.get_post_raw(content_id)
            if post:
                post["favorites"] = max(0, post.get("favorites", 0) + (1 if favorited else -1))
        elif content_type == "prompts":
            prompt = self.get_prompt_raw(content_id)
            if prompt:
                prompt["favorites"] = max(0, prompt.get("favorites", 0) + (1 if favorited else -1))

        self.save()
        action_name = "favorite" if favorited else "unfavorite"
        self._log_audit(action_name, content_type, content_id, msg)
        return True, favorited, msg

    def list_favorites(self, content_type: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """列出当前用户的收藏内容。"""
        profile = self._get_user_profile()
        fav_store = profile["favorites"]
        result = {}
        types_to_check = [content_type] if content_type else ["posts", "prompts", "comments"]

        if "posts" in types_to_check:
            result["posts"] = [self.get_post(pid) for pid in fav_store.get("posts", []) if self.get_post(pid)]
        if "prompts" in types_to_check:
            result["prompts"] = [self.get_prompt(pid) for pid in fav_store.get("prompts", []) if self.get_prompt(pid)]
        if "comments" in types_to_check:
            result["comments"] = []

        return result

    # ==================== 导出相关 ====================

    def get_user_stats(self, months: int = 1) -> Dict[str, Any]:
        """获取用户统计数据（基于当前profile，切换账号各自独立）。"""
        username = self._current_user()
        profile = self._get_user_profile()
        user_info = self.config.get("user_info") or {}

        start_date = datetime.now() - timedelta(days=30 * months)
        user_posts = [p for p in self._posts if p["author"] == username and datetime.fromisoformat(p["created_at"]) >= start_date]
        user_prompts = [p for p in self._prompts if p["author"] == username and datetime.fromisoformat(p["created_at"]) >= start_date]
        user_drafts = [d for d in self._drafts if d["author"] == username and datetime.fromisoformat(d["updated_at"]) >= start_date]
        all_user_prompts = [p for p in self._prompts if p["author"] == username]
        all_user_drafts = [d for d in self._drafts if d["author"] == username]

        total_likes = sum(p.get("likes", 0) for p in user_posts)
        total_comments = sum(p.get("comments", 0) for p in user_posts)
        total_views = sum(p.get("views", 0) for p in user_posts)
        total_prompt_usage = sum(p.get("usage_count", 0) for p in user_prompts)
        total_words = sum(d.get("word_count", 0) for d in user_drafts)

        # 草稿版本总数（每个草稿versions数组长度求和）
        draft_version_count = sum(len(d.get("versions", [])) for d in all_user_drafts)

        # 提示词公私数量
        public_prompts = sum(1 for p in all_user_prompts if p.get("is_public", True))
        private_prompts = sum(1 for p in all_user_prompts if not p.get("is_public", True))

        # 点赞数 = profile中liked_posts的长度（当前用户赞了多少帖子）
        liked_count = len(profile.get("liked_posts", []))

        # 收藏数（我收藏了多少）
        my_fav_posts = len(profile["favorites"].get("posts", []))
        my_fav_prompts = len(profile["favorites"].get("prompts", []))
        my_fav_total = my_fav_posts + my_fav_prompts

        # 我的内容被收藏总数（别人收藏了我多少）
        post_favorited_by_others = sum(p.get("favorites", 0) for p in user_posts)
        prompt_favorited_by_others = sum(p.get("favorites", 0) for p in user_prompts)

        # 关注数 = profile中following的长度
        following_count = len(profile.get("following", []))

        return {
            "period": f"{months}个月",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": datetime.now().strftime("%Y-%m-%d"),
            "user": {
                "username": username,
                "display_name": user_info.get("display_name", username),
                "avatar": user_info.get("avatar", "👤"),
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
                "public": public_prompts,
                "private": private_prompts,
                "total_usage": total_prompt_usage,
                "total_favorites": prompt_favorited_by_others,
            },
            "drafts": {
                "count": len(user_drafts),
                "total_words": total_words,
                "total_versions": draft_version_count,
            },
            "engagement": {
                "my_likes": liked_count,                    # 我赞了多少帖子
                "my_favorites": my_fav_total,               # 我收藏了多少内容
                "my_favorites_posts": my_fav_posts,         # 我收藏的帖子数
                "my_favorites_prompts": my_fav_prompts,     # 我收藏的提示词数
                "my_posts_favorited": post_favorited_by_others,   # 我的帖子被收藏数
            },
            "following": following_count,
            "followers": user_info.get("followers", 0),
            "notifications_received": len([n for n in self._notifications if datetime.fromisoformat(n["created_at"]) >= start_date]),
        }

    def export_prompts(self, output_dir: str, format_type: str = "json",
                       only_public: bool = False, only_favorites: bool = False,
                       category: Optional[str] = None,
                       tag: Optional[str] = None) -> Tuple[int, str]:
        """批量导出提示词（支持公开/私有、收藏状态、分类、标签组合筛选）。"""
        username = self.config.get("username", "anonymous")
        profile = self._get_user_profile()
        prompts = [p for p in self._prompts if p["author"] == username]
        if only_public:
            prompts = [p for p in prompts if p.get("is_public", True)]
        if only_favorites:
            fav_ids = profile["favorites"].get("prompts", [])
            prompts = [p for p in prompts if p["id"] in fav_ids]
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
                f.write(f"- **🌐 公开数量：** {stats['prompts']['public']} 个\n")
                f.write(f"- **🔒 私有数量：** {stats['prompts']['private']} 个\n")
                f.write(f"- **总使用次数：** {stats['prompts']['total_usage']:,}\n")
                f.write(f"- **被收藏总数：** {stats['prompts']['total_favorites']:,}\n\n")

                f.write("### 长文草稿\n\n")
                f.write(f"- **活跃草稿：** {stats['drafts']['count']} 篇\n")
                f.write(f"- **总字数：** {stats['drafts']['total_words']:,} 字\n")
                f.write(f"- **📜 编辑版本总数：** {stats['drafts']['total_versions']} 次\n\n")

                eng = stats["engagement"]
                f.write("## 🤝 社交互动\n\n")
                f.write(f"- **❤️ 我赞过的帖子：** {eng['my_likes']} 篇\n")
                f.write(f"- **⭐ 我收藏的帖子：** {eng['my_favorites_posts']} 篇\n")
                f.write(f"- **⭐ 我收藏的提示词：** {eng['my_favorites_prompts']} 个\n")
                f.write(f"- **📦 我收藏总数量：** {eng['my_favorites']} 条\n")
                f.write(f"- **🔥 我的帖子被收藏总数：** {eng['my_posts_favorited']} 次\n\n")

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


    # ============ 操作审计日志 ============
    def _log_audit(self, action, target_type, target_id='', detail=''):
        username = self.config.get('username', 'anonymous')
        log_entry = {
            'id': 'audit_' + str(int(time.time())) + '_' + str(len(self._audit_logs)+1).zfill(4),
            'timestamp': datetime.now().isoformat(),
            'user': username,
            'action': action,
            'target_type': target_type,
            'target_id': target_id,
            'detail': detail,
            'ip': '127.0.0.1',
        }
        self._audit_logs.append(log_entry)
        self.save()

    def export_audit(self, output_dir, format_type='csv', actions=None, days=None, from_date=None, to_date=None):
        username = self.config.get('username', 'anonymous')
        logs = [l for l in self._audit_logs if l['user'] == username]
        if actions:
            logs = [l for l in logs if l['action'] in actions]
        now = datetime.now()
        cutoff = now - timedelta(days=days) if days else None
        start_dt = datetime.fromisoformat(from_date) if from_date else None
        end_dt = datetime.fromisoformat(to_date) if to_date else None
        if cutoff or start_dt or end_dt:
            filtered = []
            for l in logs:
                lt = datetime.fromisoformat(l['timestamp'])
                if cutoff and lt < cutoff: continue
                if start_dt and lt < start_dt: continue
                if end_dt and lt > end_dt: continue
                filtered.append(l)
            logs = filtered
        os.makedirs(output_dir, exist_ok=True)
        ts = now.strftime('%Y%m%d_%H%M%S')
        if format_type == 'json':
            fn = 'audit_logs_' + ts + '.json'
            fp = os.path.join(output_dir, fn)
            with open(fp, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
        else:
            fn = 'audit_logs_' + ts + '.csv'
            fp = os.path.join(output_dir, fn)
            with open(fp, 'w', encoding='utf-8-sig', newline='') as f:
                w = csv.writer(f)
                w.writerow(['审计ID','时间','操作人','动作','对象类型','对象ID','详情','IP'])
                for l in logs:
                    w.writerow([l['id'], l['timestamp'], l['user'], l['action'], l['target_type'], l['target_id'], l['detail'], l['ip']])
        return len(logs), fp

    # ============ 草稿协作流转 ============
    def transfer_draft(self, draft_id, reviewer, note=''):
        from .auth import MOCK_USERS_DB
        username = self.config.get('username', 'anonymous')
        draft = self.get_draft(draft_id)
        if not draft: return False, '草稿不存在', None
        if draft['author'] != username: return False, '只有作者本人可以转让审阅', None
        if reviewer not in MOCK_USERS_DB: return False, '审阅人 ' + reviewer + ' 不存在', None
        draft['reviewer'] = reviewer
        draft['status'] = 'transferred'
        if 'review_comments' not in draft: draft['review_comments'] = []
        if 'audit_history' not in draft: draft['audit_history'] = []
        if note:
            draft['review_comments'].append({
                'id': 'rc_' + str(int(time.time())),
                'reviewer': username, 'comment': note,
                'created_at': datetime.now().isoformat(),
            })
        draft['audit_history'].append({'action': 'transfer', 'actor': username, 'time': datetime.now().isoformat(),
                                       'detail': '转让审阅给 ' + reviewer + ((': '+note) if note else '')})
        self.save()
        self._log_audit('transfer_draft', 'draft', draft_id, 'reviewer=' + reviewer)
        return True, '已转让给' + MOCK_USERS_DB[reviewer]['display_name'] + '审阅', draft

    def review_draft(self, draft_id, action, comment='', reason=''):
        username = self.config.get('username', 'anonymous')
        draft = self.get_draft(draft_id)
        if not draft: return False, '草稿不存在', None
        if draft.get('reviewer') != username:
            return False, '只有当前审阅人（' + str(draft.get('reviewer','未指定')) + '）可审阅此草稿', None
        if 'review_comments' not in draft: draft['review_comments'] = []
        if 'audit_history' not in draft: draft['audit_history'] = []
        if comment:
            draft['review_comments'].append({'id': 'rc_'+str(int(time.time())), 'reviewer': username, 'comment': comment,
                                             'created_at': datetime.now().isoformat()})
        if action == 'comment':
            draft['audit_history'].append({'action':'review_comment','actor':username,'time':datetime.now().isoformat(),
                                           'detail':'添加批注: '+comment[:50]})
            self.save()
            self._log_audit('comment_draft', 'draft', draft_id, comment[:80])
            return True, '批注已添加', draft
        if action == 'approve':
            draft['status'] = 'approved'
            draft['audit_history'].append({'action':'approve','actor':username,'time':datetime.now().isoformat(),
                                           'detail':'批准发布'})
            self.save()
            self._log_audit('approve_draft', 'draft', draft_id, comment[:80] or '批准发布')
            return True, '草稿已批准，可提交发布', draft
        if action == 'reject':
            draft['status'] = 'rejected'
            if reason:
                draft['review_comments'].append({'id':'rc_'+str(int(time.time())),'reviewer':username,
                                                 'comment':'【退回原因】'+reason,
                                                 'created_at':datetime.now().isoformat()})
            draft['audit_history'].append({'action':'reject','actor':username,'time':datetime.now().isoformat(),
                                           'detail':'退回: '+(reason or comment)[:80]})
            self.save()
            self._log_audit('reject_draft', 'draft', draft_id, reason or comment)
            return True, '已退回草稿：'+(reason or comment), draft
        return False, 'action 必须是 approve/reject/comment 之一', None

    def list_drafts(self, page=1, page_size=20, status=None, author=None, category=None, days=None,
                    from_date=None, to_date=None, only_local=False, mine_only=False, perspective=None):
        username = self.config.get('username', 'anonymous')
        drafts = list(self._drafts)
        if perspective == 'pending_me':
            drafts = [d for d in drafts if d.get('reviewer') == username and d.get('status') == 'transferred']
        elif perspective == 'my_initiated':
            drafts = [d for d in drafts if d['author'] == username]
        elif perspective == 'rejected_to_me':
            drafts = [d for d in drafts if d['author'] == username and d.get('status') == 'rejected']
        elif perspective == 'rejected':
            drafts = [d for d in drafts if d.get('status') == 'rejected']
        elif perspective == 'transferred':
            drafts = [d for d in drafts if d.get('status') == 'transferred']
        elif perspective == 'approved':
            drafts = [d for d in drafts if d.get('status') == 'approved']
        if mine_only:
            drafts = [d for d in drafts if d['author'] == username]
        if status: drafts = [d for d in drafts if d.get('status') == status]
        if author: drafts = [d for d in drafts if d.get('author') == author]
        if category: drafts = [d for d in drafts if d.get('category') == category]
        if days:
            cutoff = datetime.now() - timedelta(days=days)
            drafts = [d for d in drafts if datetime.fromisoformat(d['updated_at']) >= cutoff]
        if from_date:
            sd = datetime.fromisoformat(from_date)
            drafts = [d for d in drafts if datetime.fromisoformat(d['updated_at']) >= sd]
        if to_date:
            ed = datetime.fromisoformat(to_date)
            drafts = [d for d in drafts if datetime.fromisoformat(d['updated_at']) <= ed]
        if only_local: drafts = [d for d in drafts if not d.get('is_synced', False)]
        total = len(drafts)
        start = (page - 1) * page_size
        return drafts[start:start+page_size], total

    # ============ 提示词发布审核 ============
    def submit_prompt_for_approval(self, prompt_id):
        username = self.config.get('username', 'anonymous')
        prompt = self._get_prompt_raw_unchecked(prompt_id)
        if not prompt: return False, '提示词不存在', None
        if prompt['author'] != username: return False, '只有作者本人可以申请公开', None
        if prompt.get('approval_status') == 'approved': return False, '提示词已经是公开状态，无需再次申请', None
        if 'approval_history' not in prompt: prompt['approval_history'] = []
        prompt['approval_status'] = 'pending_review'
        prompt['rejection_reason'] = None
        prompt['approval_history'].append({'action':'submit','actor':username,'time':datetime.now().isoformat(),
                                            'detail':'提交公开审核申请'})
        self.save()
        self._log_audit('submit_prompt', 'prompt', prompt_id, '申请公开')
        return True, '已提交公开审核，请等待管理员批准', prompt

    def approve_prompt_public(self, prompt_id, comment=''):
        username = self.config.get('username', 'anonymous')
        if username != 'admin': return False, '只有管理员可以批准', None
        prompt = self._get_prompt_raw_unchecked(prompt_id)
        if not prompt: return False, '提示词不存在', None
        if prompt.get('approval_status') != 'pending_review':
            return False, '当前状态=' + str(prompt.get('approval_status')) + '，不是待审核状态', None
        if 'approval_history' not in prompt: prompt['approval_history'] = []
        prompt['approval_status'] = 'approved'
        prompt['is_public'] = True
        prompt['rejection_reason'] = None
        prompt['approval_history'].append({'action':'approve','actor':username,'time':datetime.now().isoformat(),
                                            'detail':'管理员批准公开 '+comment})
        self.save()
        self._log_audit('approve_prompt', 'prompt', prompt_id, comment or '管理员批准')
        return True, '提示词已批准公开，已进入公共广场', prompt

    def reject_prompt_public(self, prompt_id, reason):
        username = self.config.get('username', 'anonymous')
        if username != 'admin': return False, '只有管理员可以拒绝', None
        prompt = self._get_prompt_raw_unchecked(prompt_id)
        if not prompt: return False, '提示词不存在', None
        if prompt.get('approval_status') != 'pending_review':
            return False, '当前状态=' + str(prompt.get('approval_status')) + '，不是待审核状态', None
        if 'approval_history' not in prompt: prompt['approval_history'] = []
        prompt['approval_status'] = 'rejected'
        prompt['is_public'] = False
        prompt['rejection_reason'] = reason
        prompt['approval_history'].append({'action':'reject','actor':username,'time':datetime.now().isoformat(),
                                            'detail':'管理员拒绝: '+reason})
        self.save()
        self._log_audit('reject_prompt', 'prompt', prompt_id, reason)
        return True, '已拒绝公开：' + reason + '，提示词退回私有状态', prompt

    def list_prompts(self, page=1, page_size=10, category=None, author=None, tag=None, sort_by='popular',
                     mine_only=False, only_favorites=False, only_public=False, status_filter=None):
        username = self.config.get('username', 'anonymous')
        prompts = list(self._prompts)
        filtered = []
        for p in prompts:
            is_owner = p['author'] == username
            approval = p.get('approval_status', 'approved')
            if not (is_owner or username == 'admin') and approval != 'approved':
                continue
            filtered.append(p)
        if author: filtered = [p for p in filtered if p['author'] == author]
        if status_filter == 'pending_review':
            filtered = [p for p in filtered if p.get('approval_status') == 'pending_review']
        elif status_filter == 'rejected':
            filtered = [p for p in filtered if p.get('approval_status') == 'rejected']
        elif status_filter == 'approved':
            filtered = [p for p in filtered if p.get('approval_status') == 'approved']
        if mine_only: filtered = [p for p in filtered if p['author'] == username]
        if only_favorites:
            profile = self._get_user_profile()
            fav_ids = set(profile['favorites'].get('prompts', []))
            filtered = [p for p in filtered if p['id'] in fav_ids]
        if only_public: filtered = [p for p in filtered if p.get('is_public', True)]
        if category: filtered = [p for p in filtered if p.get('category') == category]
        if tag: filtered = [p for p in filtered if tag in p.get('tags', [])]
        def sort_key(p):
            if sort_by == 'latest': return p.get('created_at', '')
            elif sort_by == 'rating': return p.get('rating', 0)
            else: return p.get('usage_count', 0)
        filtered.sort(key=sort_key, reverse=(sort_by != 'oldest'))
        total = len(filtered)
        start = (page-1) * page_size
        result = filtered[start:start+page_size]
        for r in result: self._inject_user_view_flags(r, 'prompt')
        return result, total

    def get_prompt(self, prompt_id):
        prompt = self._get_prompt_raw_unchecked(prompt_id)
        if not prompt: return None
        username = self.config.get('username', 'anonymous')
        is_owner = prompt['author'] == username
        approval = prompt.get('approval_status', 'approved')
        if not is_owner and username != 'admin' and approval != 'approved':
            return None
        if not is_owner and not prompt.get('is_public', True):
            return None
        result = prompt.copy()
        self._inject_user_view_flags(result, 'prompt')
        return result

    # ============ 备份管理 ============
    def create_backup(self, reason='手动备份'):
        username = self.config.get('username', 'anonymous')
        cache = self.config.load_cache()
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_key = 'backup_' + ts + '_' + username
        payload = {
            '_meta': {
                'backup_key': backup_key,
                'created_at': datetime.now().isoformat(),
                'created_by': username,
                'reason': reason,
                'schema_version': self.CACHE_KEY,
            },
            'posts': json.loads(json.dumps(self._posts)),
            'drafts': json.loads(json.dumps(self._drafts)),
            'prompts': json.loads(json.dumps(self._prompts)),
            'notifications': json.loads(json.dumps(self._notifications)),
            'comments': json.loads(json.dumps(self._comments)),
            'activities': json.loads(json.dumps(self._activities)),
            'audit_logs': json.loads(json.dumps(self._audit_logs)),
            'user_profiles': json.loads(json.dumps(self._user_profiles)),
        }
        cache[backup_key] = payload
        self.config.save_cache(cache)
        self._log_audit('backup', 'backup', backup_key, reason)
        return True, backup_key, '备份完成（key=' + backup_key + '）'

    def list_backups(self):
        cache = self.config.load_cache()
        backups = []
        for key, val in cache.items():
            if not (key.startswith('backup_') or key.startswith('aicommunity_state_v1_backup_')):
                continue
            meta = val.get('_meta', {}) if isinstance(val, dict) else {}
            posts_count = len(val.get('posts', [])) if isinstance(val, dict) else 0
            drafts_count = len(val.get('drafts', [])) if isinstance(val, dict) else 0
            prompts_count = len(val.get('prompts', [])) if isinstance(val, dict) else 0
            created_at = meta.get('created_at', 'N/A')
            created_by = meta.get('created_by', 'system')
            if key.startswith('aicommunity_state_v1_backup_'):
                t = key.replace('aicommunity_state_v1_backup_', '')
                try:
                    created_at = datetime.fromtimestamp(int(t)).isoformat()
                except Exception:
                    created_at = 'N/A'
            backups.append({
                'key': key, 'created_at': created_at, 'created_by': created_by,
                'reason': meta.get('reason', ('v1迁移备份' if '_v1_backup_' in key else '未知')),
                'schema': meta.get('schema_version', ('v1' if '_v1_backup_' in key else '?')),
                'posts_count': posts_count, 'drafts_count': drafts_count, 'prompts_count': prompts_count,
            })
        backups.sort(key=lambda b: b['created_at'], reverse=True)
        return backups

    def get_backup_info(self, backup_key):
        cache = self.config.load_cache()
        backup = cache.get(backup_key)
        if backup is None: return None
        meta = backup.get('_meta') if isinstance(backup, dict) else None
        if meta:
            return {
                'key': backup_key, 'meta': meta,
                'posts_count': len(backup.get('posts', [])),
                'drafts_count': len(backup.get('drafts', [])),
                'prompts_count': len(backup.get('prompts', [])),
                'notifications_count': len(backup.get('notifications', [])),
                'user_profiles': list(backup.get('user_profiles', {}).keys()),
                'audit_logs_count': len(backup.get('audit_logs', [])),
            }
        return {
            'key': backup_key,
            'meta': {'created_by':'system','reason':'v1自动迁移备份','schema_version':'v1'},
            'posts_count': len(backup.get('posts', [])),
            'drafts_count': len(backup.get('drafts', [])),
            'prompts_count': len(backup.get('prompts', [])),
            'user_profiles': ['(writer默认，需迁移)'],
            'audit_logs_count': 0,
        }

    def restore_backup(self, backup_key):
        username = self.config.get('username', 'anonymous')
        cache = self.config.load_cache()
        backup = cache.get(backup_key)
        if backup is None: return False, '备份 ' + backup_key + ' 不存在'
        pre_restore_key = 'backup_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + username + '_pre_restore'
        cache[pre_restore_key] = {
            '_meta': {
                'backup_key': pre_restore_key,
                'created_at': datetime.now().isoformat(),
                'created_by': username,
                'reason': '恢复' + backup_key + '前自动备份',
                'schema_version': self.CACHE_KEY,
            },
            'posts': json.loads(json.dumps(self._posts)),
            'drafts': json.loads(json.dumps(self._drafts)),
            'prompts': json.loads(json.dumps(self._prompts)),
            'notifications': json.loads(json.dumps(self._notifications)),
            'comments': json.loads(json.dumps(self._comments)),
            'activities': json.loads(json.dumps(self._activities)),
            'audit_logs': json.loads(json.dumps(self._audit_logs)),
            'user_profiles': json.loads(json.dumps(self._user_profiles)),
        }
        if '_meta' not in backup or backup['_meta'].get('schema_version') != self.CACHE_KEY:
            self._user_profiles = {}
            self._migrate_v1_to_v2(backup, cache)
            self.save()
            self._log_audit('restore', 'backup', backup_key, 'v1迁移恢复到v2，恢复前备份=' + pre_restore_key)
            return True, 'v1备份恢复成功（已迁移到v2），恢复前备份key=' + pre_restore_key
        self._posts = json.loads(json.dumps(backup['posts']))
        self._drafts = json.loads(json.dumps(backup['drafts']))
        self._prompts = json.loads(json.dumps(backup['prompts']))
        self._notifications = json.loads(json.dumps(backup['notifications']))
        self._comments = json.loads(json.dumps(backup['comments']))
        self._activities = json.loads(json.dumps(backup['activities']))
        self._audit_logs = json.loads(json.dumps(backup['audit_logs']))
        self._user_profiles = json.loads(json.dumps(backup['user_profiles']))
        self.save()
        self._log_audit('restore', 'backup', backup_key, 'v2直接恢复，恢复前备份=' + pre_restore_key)
        self.config.save_cache(cache)
        return True, '恢复成功，恢复前备份key=' + pre_restore_key
