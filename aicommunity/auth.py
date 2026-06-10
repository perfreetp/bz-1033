"""认证模块。

处理用户登录、登出、Token管理等认证相关功能。
"""

import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple

from rich.console import Console
from rich.panel import Panel

from .config import ConfigManager

console = Console()

MOCK_USERS_DB = {
    "admin": {
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "display_name": "社区管理员",
        "email": "admin@aicommunity.example.com",
        "bio": "AI社区的管理员，致力于打造高质量的AI交流社区。",
        "avatar": "👑",
        "created_at": "2024-01-01T00:00:00",
        "followers": 12580,
        "following": 42,
        "level": 99,
        "points": 999999,
    },
    "demo": {
        "password_hash": hashlib.sha256("demo1234".encode()).hexdigest(),
        "display_name": "演示用户",
        "email": "demo@aicommunity.example.com",
        "bio": "这是一个演示账号，用于测试CLI工具的各种功能。",
        "avatar": "🧪",
        "created_at": "2024-06-01T12:00:00",
        "followers": 128,
        "following": 56,
        "level": 12,
        "points": 8600,
    },
    "writer": {
        "password_hash": hashlib.sha256("write2024".encode()).hexdigest(),
        "display_name": "专业写手",
        "email": "writer@aicommunity.example.com",
        "bio": "资深内容创作者，专注于AI应用案例写作。",
        "avatar": "✍️",
        "created_at": "2024-03-15T09:30:00",
        "followers": 3560,
        "following": 128,
        "level": 35,
        "points": 125800,
    },
}


def generate_token(username: str, ttl_hours: int = 24 * 7) -> Tuple[str, str]:
    """生成访问Token。

    Args:
        username: 用户名
        ttl_hours: Token有效期（小时）

    Returns:
        (token, expires_at) Token字符串和过期时间
    """
    token_data = f"{username}.{secrets.token_hex(32)}.{int(time.time())}"
    token = hashlib.sha256(token_data.encode()).hexdigest()
    expires_at = (datetime.now() + timedelta(hours=ttl_hours)).isoformat()
    return token, expires_at


def verify_password(username: str, password: str) -> bool:
    """验证用户密码。

    Args:
        username: 用户名
        password: 密码

    Returns:
        是否验证通过
    """
    if username not in MOCK_USERS_DB:
        return False
    input_hash = hashlib.sha256(password.encode()).hexdigest()
    return MOCK_USERS_DB[username]["password_hash"] == input_hash


def get_user_info(username: str) -> Optional[dict]:
    """获取用户信息。

    Args:
        username: 用户名

    Returns:
        用户信息字典，用户不存在返回None
    """
    if username not in MOCK_USERS_DB:
        return None
    user_data = MOCK_USERS_DB[username].copy()
    del user_data["password_hash"]
    user_data["username"] = username
    return user_data


class AuthManager:
    """认证管理器。"""

    def __init__(self, config: ConfigManager):
        self.config = config

    def login(self, username: str, password: str) -> bool:
        """用户登录。

        Args:
            username: 用户名
            password: 密码

        Returns:
            是否登录成功
        """
        if not username or not password:
            console.print("[red]错误：用户名和密码不能为空[/red]")
            return False

        if not verify_password(username, password):
            console.print("[red]错误：用户名或密码不正确[/red]")
            return False

        token, expires_at = generate_token(username)
        user_info = get_user_info(username)

        self.config.set("username", username)
        self.config.set("token", token)
        self.config.set("expires_at", expires_at)
        self.config.set("user_info", user_info)

        console.print()
        console.print(Panel.fit(
            f"[bold green]{user_info['avatar']} {user_info['display_name']}[/bold green]\n\n"
            f"[cyan]用户名：[/cyan]{username}\n"
            f"[cyan]等级：[/cyan]Lv.{user_info['level']}  [cyan]积分：[/cyan]{user_info['points']:,}\n"
            f"[cyan]关注者：[/cyan]{user_info['followers']:,}  [cyan]正在关注：[/cyan]{user_info['following']}\n"
            f"[dim]{user_info['bio']}[/dim]\n\n"
            f"[green]登录成功！Token有效期至：{expires_at}[/green]",
            title="登录成功",
            border_style="green",
        ))
        return True

    def logout(self) -> None:
        """用户登出。"""
        username = self.config.get("username")
        if username:
            console.print(f"[yellow]用户 [{username}] 已登出[/yellow]")
        else:
            console.print("[yellow]当前未登录[/yellow]")

        self.config.delete("token")
        self.config.delete("expires_at")
        self.config.delete("user_info")

    def status(self) -> None:
        """显示当前登录状态。"""
        if not self.config.is_logged_in():
            console.print(Panel.fit(
                "[yellow]未登录[/yellow]\n请使用 [cyan]aicomm login[/cyan] 命令登录账号",
                title="登录状态",
                border_style="yellow",
            ))
            return

        user_info = self.config.get("user_info") or {}
        username = self.config.get("username")
        expires_at = self.config.get("expires_at")

        expires_dt = datetime.fromisoformat(expires_at) if expires_at else None
        is_expired = expires_dt and expires_dt < datetime.now()

        status_text = "[green]正常[/green]" if not is_expired else "[red]已过期[/red]"

        console.print(Panel.fit(
            f"[bold cyan]{user_info.get('avatar', '👤')} {user_info.get('display_name', username)}[/bold cyan]\n\n"
            f"[cyan]用户名：[/cyan]{username}\n"
            f"[cyan]邮箱：[/cyan]{user_info.get('email', 'N/A')}\n"
            f"[cyan]等级：[/cyan]Lv.{user_info.get('level', 0)}  [cyan]积分：[/cyan]{user_info.get('points', 0):,}\n"
            f"[cyan]关注者：[/cyan]{user_info.get('followers', 0):,}  [cyan]正在关注：[/cyan]{user_info.get('following', 0)}\n"
            f"[cyan]Token状态：[/cyan]{status_text}\n"
            f"[cyan]过期时间：[/cyan]{expires_at}\n\n"
            f"[dim]{user_info.get('bio', '')}[/dim]",
            title="当前登录用户",
            border_style="cyan",
        ))

    def require_login(self) -> bool:
        """检查是否已登录，未登录时显示错误信息。

        Returns:
            是否已登录
        """
        if not self.config.is_logged_in():
            console.print(Panel.fit(
                "[red]此操作需要登录后才能执行[/red]\n\n请先使用 [cyan]aicomm login[/cyan] 命令登录账号",
                title="认证失败",
                border_style="red",
            ))
            return False

        expires_at = self.config.get("expires_at")
        if expires_at:
            try:
                expires_dt = datetime.fromisoformat(expires_at)
                if expires_dt < datetime.now():
                    console.print(Panel.fit(
                        "[red]登录状态已过期[/red]\n\n请使用 [cyan]aicomm login[/cyan] 命令重新登录",
                        title="Token过期",
                        border_style="red",
                    ))
                    return False
            except (ValueError, TypeError):
                pass

        return True

    def list_demo_accounts(self) -> None:
        """列出演示账号供用户测试。"""
        accounts_data = []
        for username, info in MOCK_USERS_DB.items():
            accounts_data.append({
                "用户名": username,
                "显示名称": info["display_name"],
                "测试密码": {
                    "admin": "admin123",
                    "demo": "demo1234",
                    "writer": "write2024",
                }.get(username, "?"),
                "等级": f"Lv.{info['level']}",
            })

        from tabulate import tabulate
        console.print()
        console.print(Panel.fit(
            tabulate(accounts_data, headers="keys", tablefmt="rounded_outline"),
            title="演示账号列表（测试用）",
            border_style="blue",
        ))
