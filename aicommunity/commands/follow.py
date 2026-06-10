"""follow 命令组。

提供关注作者、查看社区活动时间线等功能。
"""

import click
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from tabulate import tabulate

from ..config import ConfigManager
from ..auth import AuthManager
from ..api_client import APIClient
from .post import _format_time

console = Console()

ACTION_ICONS = {
    "发布了新帖子": "📝",
    "上传了新提示词": "✨",
    "赞了": "❤️",
    "评论了": "💬",
    "关注了": "👥",
    "收藏了": "⭐",
    "分享了": "🔄",
}


@click.group()
def follow():
    """关注与社区动态。

    关注感兴趣的作者，浏览社区活动时间线。
    """
    pass


@follow.command("list")
@click.pass_context
def list_following(ctx):
    """列出我关注的作者。

    示例:\n
        aicomm follow list
    """
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return

    client = APIClient(config)
    following = client.list_following()

    if not following:
        console.print(Panel.fit(
            "[yellow]还没有关注任何人[/yellow]\n\n"
            "[dim]💡 使用 aicomm follow add <用户名> 关注感兴趣的作者[/dim]",
            title="我的关注",
            border_style="yellow",
        ))
        return

    table_data = []
    for f in following:
        table_data.append({
            "头像": f.get("avatar", "👤"),
            "用户名": f["username"],
            "显示名称": f["display_name"],
            "简介": (f.get("bio", "")[:30] + "...") if len(f.get("bio", "")) > 30 else f.get("bio", ""),
            "关注时间": _format_time(f["followed_at"]),
        })

    console.print()
    console.print(Panel.fit(
        tabulate(table_data, headers="keys", tablefmt="rounded_outline"),
        title=f"👥 我的关注（共 {len(following)} 人）",
        border_style="cyan",
    ))


@follow.command("add")
@click.argument("username")
@click.pass_context
def add_follow(ctx, username):
    """关注一个作者。

    示例:\n
        aicomm follow add writer\n
        aicomm follow add admin
    """
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return

    current_user = config.get("username")
    if username == current_user:
        console.print("[yellow]不能关注自己哦~[/yellow]")
        return

    client = APIClient(config)
    result = client.follow_user(username)

    if result:
        console.print()
        console.print(Panel.fit(
            f"[green]✓ 关注成功！[/green]\n\n"
            f"{result.get('avatar', '👤')} [bold]{result['display_name']}[/bold] (@{username})\n"
            f"[dim]{result.get('bio', '')}[/dim]\n\n"
            f"[cyan]关注时间:[/cyan] {_format_time(result['followed_at'])}",
            title="关注作者",
            border_style="green",
        ))
    else:
        console.print(f"[yellow]已关注用户 {username} 或用户不存在[/yellow]")


@follow.command("remove")
@click.argument("username")
@click.option("-y", "--yes", is_flag=True, help="跳过确认")
@click.pass_context
def remove_follow(ctx, username, yes):
    """取消关注一个作者。

    示例:\n
        aicomm follow remove demo\n
        aicomm follow remove writer -y
    """
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return

    if not yes:
        if not click.confirm(f"确认取消关注 @{username} 吗？"):
            return

    client = APIClient(config)
    removed = client.unfollow_user(username)

    if removed:
        console.print(f"[green]✓ 已取消关注 @{username}[/green]")
    else:
        console.print(f"[yellow]未关注用户 {username}[/yellow]")


@follow.command("timeline")
@click.option("-a", "--all", "show_all", is_flag=True, help="显示全站动态（不只是关注的人）")
@click.option("-p", "--page", type=int, default=1, show_default=True, help="页码")
@click.option("-s", "--size", type=int, default=20, show_default=True, help="每页数量")
@click.pass_context
def timeline(ctx, show_all, page, size):
    """查看社区活动时间线。

    浏览关注用户的发帖、点赞、评论等动态。

    示例:\n
        aicomm follow timeline\n
        aicomm follow timeline -a --page 2
    """
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return

    client = APIClient(config)
    activities, total = client.list_activities(
        page=page, page_size=size, following_only=not show_all)

    if not activities:
        scope = "关注用户" if not show_all else "全站"
        console.print(f"[yellow]暂无{scope}动态[/yellow]")
        return

    scope_label = "关注动态" if not show_all else "全站动态"

    console.print()
    console.print(f"[bold]🔔 {scope_label} 时间线（第 {page} 页，共 {total} 条）[/bold]")
    console.print("─" * 70)

    for act in activities:
        icon = ACTION_ICONS.get(act["action"], "📌")
        target_type_color = {
            "post": "cyan",
            "prompt": "magenta",
            "user": "yellow",
            "comment": "blue",
        }.get(act.get("target_type", ""), "white")

        line = (
            f"  {act.get('user_avatar', '👤')} "
            f"[cyan]{act['user_name']}[/cyan] "
            f"{icon} "
            f"[bold]{act['action']}[/bold] "
            f"[{target_type_color}]{act['target']}[/{target_type_color}]\n"
            f"      [dim]{_format_time(act['created_at'])}[/dim]"
        )
        console.print(line)
        console.print()

    if total > page * size:
        all_flag = " -a" if show_all else ""
        console.print(f"[dim]💡 下一页: aicomm follow timeline{all_flag} -p {page + 1}[/dim]")


@follow.command("activity")
@click.argument("username", required=False)
@click.option("-p", "--page", type=int, default=1, show_default=True, help="页码")
@click.pass_context
def user_activity(ctx, username, page):
    """查看指定用户的社区活动（默认查看自己）。

    示例:\n
        aicomm follow activity\n
        aicomm follow activity writer
    """
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return

    if not username:
        username = config.get("username", "anonymous")

    client = APIClient(config)
    activities, _ = client.list_activities(page=page, page_size=50, following_only=False)
    user_acts = [a for a in activities if a["user"] == username]

    if not user_acts:
        console.print(f"[yellow]用户 @{username} 暂无活动记录[/yellow]")
        return

    from .auth import get_user_info
    user_info = get_user_info(username)
    if user_info:
        console.print()
        console.print(Panel.fit(
            f"{user_info.get('avatar', '👤')} [bold]{user_info.get('display_name', username)}[/bold] (@{username})\n"
            f"[dim]{user_info.get('bio', '')}[/dim]",
            title="👤 用户档案",
            border_style="cyan",
        ))

    action_counts = {}
    for a in user_acts:
        action_counts[a["action"]] = action_counts.get(a["action"], 0) + 1

    stats_line = " | ".join(f"{ACTION_ICONS.get(k, '📌')} {k}: {v}" for k, v in action_counts.items())
    console.print(f"\n[dim]📊 活动分布：{stats_line}[/dim]")
    console.print("─" * 70)

    for act in user_acts[:20]:
        icon = ACTION_ICONS.get(act["action"], "📌")
        print(
            f"  {icon} [bold]{act['action']}[/bold] "
            f"[cyan]{act['target']}[/cyan]    "
            f"[dim]{_format_time(act['created_at'])}[/dim]"
        )


@follow.command("suggest")
@click.option("-n", type=int, default=5, show_default=True, help="推荐数量")
@click.pass_context
def suggest_users(ctx, n):
    """推荐值得关注的作者。

    示例:\n
        aicomm follow suggest\n
        aicomm follow suggest -n 10
    """
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return

    client = APIClient(config)
    following = [f["username"] for f in client.list_following()]
    current_user = config.get("username")

    from .auth import MOCK_USERS_DB
    suggestions = []
    for uname, info in MOCK_USERS_DB.items():
        if uname in following or uname == current_user:
            continue
        suggestions.append({
            "用户名": uname,
            "显示名称": info["display_name"],
            "头像": info["avatar"],
            "简介": info["bio"][:30] + "..." if len(info["bio"]) > 30 else info["bio"],
            "关注者": f"{info['followers']:,}",
            "等级": f"Lv.{info['level']}",
        })

    suggestions = suggestions[:n]

    if not suggestions:
        console.print("[yellow]暂无推荐作者[/yellow]")
        return

    console.print()
    console.print(Panel.fit(
        tabulate(suggestions, headers="keys", tablefmt="rounded_outline") +
        "\n\n[dim]💡 使用 aicomm follow add <用户名> 关注TA[/dim]",
        title=f"💡 为你推荐（{len(suggestions)} 位作者）",
        border_style="blue",
    ))
