"""post 命令组。

提供发布短帖、浏览帖子、查看版本记录等功能。
"""

import click
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from tabulate import tabulate

from ..config import ConfigManager
from ..auth import AuthManager
from ..api_client import APIClient

console = Console()

NOTIF_TYPE_ICONS = {
    "like": "❤️",
    "comment": "💬",
    "follow": "👥",
    "favorite": "⭐",
    "mention": "@",
    "system": "🔔",
}


def _format_time(iso_str: str) -> str:
    """格式化时间显示。"""
    try:
        dt = datetime.fromisoformat(iso_str)
        now = datetime.now()
        delta = now - dt
        if delta.total_seconds() < 60:
            return f"{int(delta.total_seconds())}秒前"
        elif delta.total_seconds() < 3600:
            return f"{int(delta.total_seconds() // 60)}分钟前"
        elif delta.total_seconds() < 86400:
            return f"{int(delta.total_seconds() // 3600)}小时前"
        elif delta.total_seconds() < 86400 * 7:
            return f"{int(delta.total_seconds() // 86400)}天前"
        else:
            return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return iso_str


@click.group()
def post():
    """短帖发布与管理。

    发布和浏览社区短帖，管理你的动态内容。
    """
    pass


@post.command()
@click.argument("content", required=False)
@click.option("-t", "--tag", "tags", multiple=True, help="添加话题标签，可多次使用")
@click.option("-f", "--file", "file_path", type=click.Path(exists=True), help="从文件读取内容")
@click.pass_context
def create(ctx, content, tags, file_path):
    """发布新短帖。

    直接输入内容或从文件读取内容发布短帖。

    示例:\n
        aicomm post create "今天用AI做了个超棒的项目！#AI #分享"\n
        aicomm post create -t AI -t 分享 "内容内容"\n
        aicomm post create -f ./my_post.txt
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
        content = click.edit() or ""
        if not content:
            console.print("[yellow]内容为空，取消发布[/yellow]")
            return

    if len(content) > 500:
        if not click.confirm(f"内容较长 ({len(content)}字符)，是否截断到500字符？"):
            console.print("[yellow]已取消发布[/yellow]")
            return
        content = content[:500]

    client = APIClient(config)
    tag_list = list(tags) if tags else []

    for tag in tag_list:
        if f"#{tag}" not in content:
            content += f" #{tag}"

    is_valid, found_keywords = client.check_violation(content)
    if not is_valid:
        console.print(Panel.fit(
            "[red]检测到以下违规词，无法发布：[/red]\n" +
            "\n".join(f"  ⚠️  {kw}" for kw in found_keywords),
            title="违规词检测",
            border_style="red",
        ))
        return

    new_post = client.create_post(content, tag_list)

    console.print()
    console.print(Panel.fit(
        f"[green]✓ 发布成功！[/green]\n\n"
        f"[bold]{new_post['author_avatar']} {new_post['author_name']}[/bold]\n"
        f"[dim]{_format_time(new_post['created_at'])}[/dim]\n\n"
        f"{new_post['content']}\n\n"
        f"[cyan]帖子ID:[/cyan] {new_post['id']}",
        title="发布短帖",
        border_style="green",
    ))


@post.command("list")
@click.option("-p", "--page", type=int, default=1, show_default=True, help="页码")
@click.option("-s", "--size", type=int, default=10, show_default=True, help="每页数量")
@click.option("-a", "--author", help="按作者用户名筛选")
@click.option("-t", "--tag", "tag_filter", help="按话题标签筛选")
@click.pass_context
def list_posts(ctx, page, size, author, tag_filter):
    """浏览社区短帖列表。

    示例:\n
        aicomm post list\n
        aicomm post list -a admin -t 官方公告\n
        aicomm post list -p 2 -s 5
    """
    config: ConfigManager = ctx.obj["config"]
    client = APIClient(config)

    posts, total = client.list_posts(page=page, page_size=size, author=author, tag=tag_filter)

    if not posts:
        console.print("[yellow]暂无帖子[/yellow]")
        return

    table = Table(title=f"社区动态（第 {page} 页，共 {total} 条）", show_lines=True)
    table.add_column("ID", style="dim", width=14)
    table.add_column("作者", style="cyan", width=12)
    table.add_column("内容", width=60, no_wrap=False)
    table.add_column("标签", style="magenta", width=20)
    table.add_column("❤️", justify="right", width=6)
    table.add_column("💬", justify="right", width=6)
    table.add_column("时间", style="dim", width=10)

    for p in posts:
        tags_str = " ".join(f"#{t}" for t in p.get("tags", []))
        content_preview = p["content"][:80] + "..." if len(p["content"]) > 80 else p["content"]
        table.add_row(
            p["id"],
            f"{p['author_avatar']} {p['author_name']}",
            content_preview,
            tags_str,
            str(p["likes"]),
            str(p["comments"]),
            _format_time(p["created_at"]),
        )

    console.print()
    console.print(table)

    if total > page * size:
        console.print(f"\n[dim]💡 下一页: aicomm post list -p {page + 1}[/dim]")


@post.command()
@click.argument("post_id")
@click.pass_context
def show(ctx, post_id):
    """查看帖子详情及评论。

    示例:\n
        aicomm post show post_004
    """
    config: ConfigManager = ctx.obj["config"]
    client = APIClient(config)

    post = client.get_post(post_id)
    if not post:
        console.print(f"[red]未找到ID为 {post_id} 的帖子[/red]")
        return

    tags_str = " ".join(f"[magenta]#{t}[/magenta]" for t in post.get("tags", []))
    liked = "[green]✓ 已赞[/green]" if post["is_liked"] else "未赞"
    fav = "[yellow]⭐ 已收藏[/yellow]" if post["is_favorited"] else "未收藏"

    console.print()
    console.print(Panel(
        f"[bold cyan]{post['author_avatar']} {post['author_name']}[/bold cyan]    [dim]{_format_time(post['created_at'])}[/dim]\n\n"
        f"{post['content']}\n\n"
        f"{tags_str}\n\n"
        f"❤️ {post['likes']}    💬 {post['comments']}    🔄 {post['shares']}    👁️ {post['views']:,}\n"
        f"{liked}    {fav}",
        title=f"帖子详情 - {post['id']}",
        border_style="cyan",
    ))

    comments = client.list_comments(post_id)
    if comments:
        console.print()
        console.print("[bold]💬 评论区[/bold]")
        for i, comment in enumerate(comments, 1):
            console.print(Panel(
                f"[bold cyan]{comment['author_avatar']} {comment['author_name']}[/bold cyan]    "
                f"[dim]{_format_time(comment['created_at'])}[/dim]    ❤️ {comment['likes']}\n\n"
                f"{comment['content']}",
                title=f"评论 #{i} - {comment['id']}",
                border_style="blue",
            ))
            for reply in comment.get("replies", []):
                console.print(f"  ↳ [cyan]{reply['author_avatar']} {reply['author_name']}[/cyan] "
                              f"[dim]({_format_time(reply['created_at'])})[/dim]: {reply['content']}")


@post.command("versions")
@click.argument("post_id")
@click.pass_context
def versions(ctx, post_id):
    """查看帖子编辑版本记录。

    示例:\n
        aicomm post versions post_001
    """
    config: ConfigManager = ctx.obj["config"]
    client = APIClient(config)

    post = client.get_post(post_id)
    if not post:
        console.print(f"[red]未找到ID为 {post_id} 的帖子[/red]")
        return

    versions = client.get_post_versions(post_id)

    if not versions:
        console.print("[yellow]该帖子暂无编辑历史[/yellow]")
        return

    console.print()
    for v in versions:
        content_preview = v["content"][:100] + "..." if len(v["content"]) > 100 else v["content"]
        console.print(Panel(
            f"[bold]版本 v{v['version']}[/bold]    [dim]{_format_time(v['created_at'])}[/dim]\n\n"
            f"{content_preview}",
            title=f"帖子 {post_id} - 版本历史",
            border_style="magenta",
        ))


@post.command()
@click.argument("post_id")
@click.pass_context
def like(ctx, post_id):
    """点赞/取消点赞帖子。

    示例:\n
        aicomm post like post_001
    """
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return

    client = APIClient(config)
    post = client.get_post(post_id)
    if not post:
        console.print(f"[red]未找到帖子 {post_id}[/red]")
        return

    was_liked = post["is_liked"]
    client.like_post(post_id)
    post = client.get_post(post_id)

    if was_liked:
        console.print(f"[yellow]已取消点赞，当前点赞数: {post['likes']}[/yellow]")
    else:
        console.print(f"[green]❤️ 点赞成功！当前点赞数: {post['likes']}[/green]")
