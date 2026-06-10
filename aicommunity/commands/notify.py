"""notify 命令组。

提供列出通知、回复评论、收藏内容等功能。
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

NOTIF_TYPE_ICONS = {
    "like": "❤️",
    "comment": "💬",
    "follow": "👥",
    "favorite": "⭐",
    "mention": "@",
    "system": "🔔",
}

NOTIF_TYPE_LABELS = {
    "like": "点赞",
    "comment": "评论",
    "follow": "关注",
    "favorite": "收藏",
    "mention": "@提及",
    "system": "系统",
}

NOTIF_TYPE_COLORS = {
    "like": "red",
    "comment": "cyan",
    "follow": "yellow",
    "favorite": "magenta",
    "mention": "blue",
    "system": "green",
}


@click.group()
def notify():
    """通知与互动管理。

    查看通知、回复评论、管理收藏内容。
    """
    pass


@notify.command("list")
@click.option("-u", "--unread", is_flag=True, help="只显示未读通知")
@click.option("-t", "--type", "notif_type",
              type=click.Choice(["like", "comment", "follow", "favorite", "mention", "system"]),
              help="按通知类型筛选")
@click.option("-p", "--page", type=int, default=1, show_default=True, help="页码")
@click.option("-s", "--size", type=int, default=20, show_default=True, help="每页数量")
@click.pass_context
def list_notifs(ctx, unread, notif_type, page, size):
    """列出我的通知消息。

    示例:\n
        aicomm notify list\n
        aicomm notify list -u -t comment\n
        aicomm notify list -p 2
    """
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return

    client = APIClient(config)
    notifs, total, unread_count = client.list_notifications(
        unread_only=unread, notif_type=notif_type, page=page, page_size=size)

    console.print()
    header = (
        f"[bold]🔔 通知中心[/bold]    "
        f"[red]未读: {unread_count}[/red]    "
        f"共: {total} 条    "
        f"第 {page} 页"
    )
    console.print(header)
    console.print("─" * 70)

    if not notifs:
        console.print("[yellow]暂无通知[/yellow]")
        return

    for i, notif in enumerate(notifs, 1):
        icon = NOTIF_TYPE_ICONS.get(notif["type"], "🔔")
        type_label = NOTIF_TYPE_LABELS.get(notif["type"], notif["type"])
        read_marker = "" if notif["read"] else "[red]●[/red]"
        from_user = notif.get("from_user_name", "")
        from_avatar = notif.get("from_user_avatar", "")

        prefix_parts = [read_marker] if read_marker else []
        if from_avatar:
            prefix_parts.append(from_avatar)
        if from_user:
            prefix_parts.append(f"[cyan]{from_user}[/cyan]")
        prefix = " ".join(prefix_parts)

        type_color = NOTIF_TYPE_COLORS.get(notif["type"], "white")
        extra_info = f"[{type_color}]{icon} {type_label}[/{type_color}]"

        console.print(
            f"  {' '.join(p for p in prefix_parts if p)}    "
            f"{extra_info}    "
            f"[dim]{_format_time(notif['created_at'])}[/dim]\n"
            f"      {notif['content']}\n"
            f"      [dim]ID: {notif['id']}[/dim]\n"
        )

    if total > page * size:
        unread_flag = " -u" if unread else ""
        type_flag = f" -t {notif_type}" if notif_type else ""
        console.print(f"[dim]💡 下一页: aicomm notify list{unread_flag}{type_flag} -p {page + 1}[/dim]")


@notify.command("read")
@click.argument("notif_id", required=False)
@click.option("-a", "--all", "read_all", is_flag=True, help="标记所有通知为已读")
@click.pass_context
def mark_read(ctx, notif_id, read_all):
    """标记通知为已读。

    指定通知ID标记单个，或使用 --all 全部标记。

    示例:\n
        aicomm notify read notif_001\n
        aicomm notify read -a
    """
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return

    client = APIClient(config)

    if read_all:
        count = client.mark_all_read()
        console.print(f"[green]✓ 已将 {count} 条通知标记为已读[/green]")
        return

    if not notif_id:
        console.print("[red]请指定通知ID，或使用 --all 标记全部已读[/red]")
        return

    ok = client.mark_notification_read(notif_id)
    if ok:
        console.print(f"[green]✓ 已标记通知 {notif_id} 为已读[/green]")
    else:
        console.print(f"[yellow]未找到通知 {notif_id}[/yellow]")


@notify.command("reply")
@click.argument("target_id")
@click.argument("content", required=False)
@click.option("--reply-to", "reply_to_comment_id", help="回复指定评论的ID")
@click.option("-f", "--file", "file_path", type=click.Path(exists=True), help="从文件读取回复内容")
@click.pass_context
def reply_comment(ctx, target_id, content, reply_to_comment_id, file_path):
    """回复评论或发表新评论。

    TARGET_ID 是帖子/内容的ID。

    示例:\n
        aicomm notify reply post_004 "非常期待这篇长文！"\n
        aicomm notify reply post_004 --reply-to comment_001 "我也这么觉得"
    """
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return

    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except IOError as e:
            console.print(f"[red]错误：无法读取文件 ({e})[/red]")
            return

    if not content:
        content = click.edit(text="在此输入评论内容...", extension=".txt") or ""
        if not content.strip():
            console.print("[yellow]内容为空，取消回复[/yellow]")
            return

    client = APIClient(config)

    is_valid, found_keywords = client.check_violation(content)
    if not is_valid:
        console.print(Panel.fit(
            "[red]评论中检测到违规词：[/red]\n" +
            "\n".join(f"  ⚠️  {kw}" for kw in found_keywords),
            title="评论失败",
            border_style="red",
        ))
        return

    result = client.reply_comment(target_id, content, reply_to_comment_id=reply_to_comment_id)
    if result:
        scope = f"回复评论 {reply_to_comment_id}" if reply_to_comment_id else f"评论 {target_id}"
        console.print()
        console.print(Panel.fit(
            f"[green]✓ {scope}成功！[/green]\n\n"
            f"[bold]{result['author_avatar']} {result['author_name']}[/bold]\n"
            f"[dim]{_format_time(result['created_at'])}[/dim]\n\n"
            f"{result['content']}",
            title="发表评论",
            border_style="green",
        ))
    else:
        console.print(f"[red]回复失败，请检查目标ID是否正确[/red]")


@notify.command("comments")
@click.argument("target_id")
@click.pass_context
def list_comments(ctx, target_id):
    """查看指定内容的评论列表。

    示例:\n
        aicomm notify comments post_004
    """
    config: ConfigManager = ctx.obj["config"]
    client = APIClient(config)

    comments = client.list_comments(target_id)

    if not comments:
        console.print(f"[yellow]{target_id} 暂无评论[/yellow]")
        return

    console.print()
    console.print(f"[bold]💬 评论列表 - {target_id}（共 {len(comments)} 条）[/bold]")
    console.print("─" * 70)

    for i, comment in enumerate(comments, 1):
        console.print()
        console.print(Panel(
            f"[bold cyan]{comment['author_avatar']} {comment['author_name']}[/bold cyan]    "
            f"[dim]{_format_time(comment['created_at'])}[/dim]    ❤️ {comment['likes']}\n\n"
            f"{comment['content']}\n\n"
            f"[dim]ID: {comment['id']}[/dim]",
            title=f"#{i}",
            border_style="blue",
        ))
        for j, reply in enumerate(comment.get("replies", []), 1):
            console.print(
                f"  ↳ [{j}] [cyan]{reply['author_avatar']} {reply['author_name']}[/cyan] "
                f"[dim]({_format_time(reply['created_at'])})[/dim] ❤️ {reply['likes']}\n"
                f"     {reply['content']}\n"
            )


@notify.command("favorite")
@click.option("-t", "--type", "content_type",
              type=click.Choice(["posts", "prompts"]),
              required=True, help="内容类型")
@click.argument("content_id")
@click.pass_context
def toggle_favorite(ctx, content_type, content_id):
    """收藏/取消收藏内容。

    示例:\n
        aicomm notify favorite -t posts post_001\n
        aicomm notify favorite -t prompts prompt_003
    """
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return

    client = APIClient(config)
    ok, is_fav = client.toggle_favorite(content_type, content_id)

    if ok:
        type_label = {"posts": "帖子", "prompts": "提示词"}.get(content_type, content_type)
        if is_fav:
            console.print(f"[green]⭐ 已收藏此{type_label}（{content_id}）[/green]")
        else:
            console.print(f"[yellow]已取消收藏此{type_label}（{content_id}）[/yellow]")
    else:
        console.print(f"[red]操作失败，请检查内容ID是否正确[/red]")


@notify.command("favorites")
@click.option("-t", "--type", "content_type",
              type=click.Choice(["posts", "prompts", "all"]),
              default="all", show_default=True, help="内容类型")
@click.pass_context
def list_favorites(ctx, content_type):
    """列出我收藏的所有内容。

    示例:\n
        aicomm notify favorites\n
        aicomm notify favorites -t posts
    """
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return

    client = APIClient(config)
    fav_type = None if content_type == "all" else content_type
    favs = client.list_favorites(content_type=fav_type)

    posts = favs.get("posts", [])
    prompts = favs.get("prompts", [])

    console.print()
    console.print(f"[bold]⭐ 我的收藏[/bold]")
    console.print("─" * 70)

    if content_type in ("all", "posts"):
        console.print()
        console.print(f"[bold green]📝 收藏的帖子（{len(posts)} 篇）[/bold green]")
        if posts:
            table_data = []
            for p in posts:
                table_data.append({
                    "ID": p["id"],
                    "作者": f"{p['author_avatar']} {p['author_name']}",
                    "内容": p["content"][:40] + ("..." if len(p["content"]) > 40 else ""),
                    "❤️": f"{p['likes']:,}",
                    "💬": f"{p['comments']:,}",
                    "时间": _format_time(p["created_at"]),
                })
            console.print(tabulate(table_data, headers="keys", tablefmt="rounded_outline"))
        else:
            console.print("  [yellow]暂无收藏的帖子[/yellow]")

    if content_type in ("all", "prompts"):
        console.print()
        console.print(f"[bold magenta]✨ 收藏的提示词（{len(prompts)} 个）[/bold magenta]")
        if prompts:
            table_data = []
            for p in prompts:
                table_data.append({
                    "ID": p["id"],
                    "标题": p["title"][:30] + ("..." if len(p["title"]) > 30 else ""),
                    "作者": p.get("author_name", ""),
                    "分类": p.get("category", ""),
                    "评分": f"★{p['rating']}",
                    "使用": f"{p['usage_count']:,}",
                })
            console.print(tabulate(table_data, headers="keys", tablefmt="rounded_outline"))
        else:
            console.print("  [yellow]暂无收藏的提示词[/yellow]")
