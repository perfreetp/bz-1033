"""配置管理模块。

负责管理用户配置、本地存储路径、偏好设置等。
"""

import json
import os
import pathlib
from typing import Any, Dict, Optional
import yaml

from rich.console import Console

console = Console()

DEFAULT_CONFIG_DIR = os.path.join(pathlib.Path.home(), ".aicommunity")
DEFAULT_CONFIG_FILE = os.path.join(DEFAULT_CONFIG_DIR, "config.yaml")
DEFAULT_DRAFTS_DIR = os.path.join(DEFAULT_CONFIG_DIR, "drafts")
DEFAULT_PROMPTS_DIR = os.path.join(DEFAULT_CONFIG_DIR, "prompts")
DEFAULT_EXPORT_DIR = os.path.join(DEFAULT_CONFIG_DIR, "exports")
DEFAULT_CACHE_FILE = os.path.join(DEFAULT_CONFIG_DIR, "cache.json")

DEFAULT_CONFIG = {
    "api_base_url": "https://api.aicommunity.example.com/v1",
    "username": None,
    "token": None,
    "expires_at": None,
    "preferences": {
        "theme": "dark",
        "page_size": 20,
        "auto_sync_drafts": True,
        "notify_sound": False,
    },
    "violation_keywords": [
        "违规词1",
        "敏感词",
        "广告",
        "诈骗",
        "赌博",
        "色情",
        "暴力",
        "血腥",
        "毒品",
        "武器",
    ],
}


class ConfigManager:
    """配置管理器。"""

    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = config_dir or DEFAULT_CONFIG_DIR
        self.config_file = os.path.join(self.config_dir, "config.yaml")
        self.drafts_dir = os.path.join(self.config_dir, "drafts")
        self.prompts_dir = os.path.join(self.config_dir, "prompts")
        self.export_dir = os.path.join(self.config_dir, "exports")
        self.cache_file = os.path.join(self.config_dir, "cache.json")
        self._config: Dict[str, Any] = {}
        self._ensure_dirs()
        self._load_config()

    def _ensure_dirs(self) -> None:
        """确保必要的目录和文件存在。"""
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.drafts_dir, exist_ok=True)
        os.makedirs(self.prompts_dir, exist_ok=True)
        os.makedirs(self.export_dir, exist_ok=True)

    def _load_config(self) -> None:
        """加载配置文件。"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self._config = yaml.safe_load(f) or {}
            except (yaml.YAMLError, IOError) as e:
                console.print(f"[yellow]警告：无法读取配置文件，使用默认配置 ({e})[/yellow]")
                self._config = DEFAULT_CONFIG.copy()
        else:
            self._config = DEFAULT_CONFIG.copy()
            self.save_config()

        for key, value in DEFAULT_CONFIG.items():
            if key not in self._config:
                self._config[key] = value

    def save_config(self) -> None:
        """保存配置到文件。"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
        except IOError as e:
            console.print(f"[red]错误：无法保存配置文件 ({e})[/red]")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项。"""
        keys = key.split(".")
        value: Any = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """设置配置项。"""
        keys = key.split(".")
        config = self._config
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save_config()

    def delete(self, key: str) -> bool:
        """删除配置项。"""
        keys = key.split(".")
        config = self._config
        for k in keys[:-1]:
            if isinstance(config, dict) and k in config:
                config = config[k]
            else:
                return False
        if isinstance(config, dict) and keys[-1] in config:
            del config[keys[-1]]
            self.save_config()
            return True
        return False

    def is_logged_in(self) -> bool:
        """检查用户是否已登录。"""
        return bool(self.get("token")) and bool(self.get("username"))

    def get_auth_headers(self) -> Dict[str, str]:
        """获取认证请求头。"""
        token = self.get("token")
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    def load_cache(self) -> Dict[str, Any]:
        """加载缓存数据。"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def save_cache(self, data: Dict[str, Any]) -> None:
        """保存缓存数据。"""
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            console.print(f"[red]错误：无法保存缓存 ({e})[/red]")

    def get_violation_keywords(self) -> list:
        """获取违规词列表。"""
        return self.get("violation_keywords", DEFAULT_CONFIG["violation_keywords"])

    def set_violation_keywords(self, keywords: list) -> None:
        """设置违规词列表。"""
        self.set("violation_keywords", keywords)

    def add_violation_keyword(self, keyword: str) -> None:
        """添加违规词。"""
        keywords = self.get_violation_keywords()
        if keyword not in keywords:
            keywords.append(keyword)
            self.set_violation_keywords(keywords)

    def remove_violation_keyword(self, keyword: str) -> bool:
        """移除违规词。"""
        keywords = self.get_violation_keywords()
        if keyword in keywords:
            keywords.remove(keyword)
            self.set_violation_keywords(keywords)
            return True
        return False
