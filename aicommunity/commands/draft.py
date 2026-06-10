"""draft 命令组。

提供长文草稿的创建、编辑、提交审核、本地同步等功能。
"""

import click
import json
import os
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

STATUS_COLORS = {
    "draft": ("📝", "yellow"),
    "reviewing": ("🔍", "blue"),
    "published": ("✅", "green"),
    "rejected": ("❌", "red"),
}

CATEGORIES = ["技术深度", "个人成长", "产品分析", "行业观察", "AI应用", "教程指南", "未分类"]


@click.group()
def draft():
    """长文草稿管理。

    创建、编辑、提交长文草稿，支持本地同步和版本管理。
    """
    pass


@draft.command("list")
@click.option("-s", "--status", type=click.Choice(["draft", "reviewing", "published", "rejected"]),
              help="按状态筛选")
@click.pass_context
def list_drafts(ctx, status):
    """列出我的长文草稿。

    示例:\n
        aicomm draft list\n
        aicomm draft list -s reviewing
    """
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return

    client = APIClient(config)
    client.load_local_drafts()
    drafts = client.list_drafts(status=status)

    if not drafts:
        console.print("[yellow]暂无草稿[/yellow]")
        return

    table_data = []
    for d in drafts:
        icon, color = STATUS_COLORS.get(d["status"], ("❓", "white"))
        sync_status = "☁️" if d["is_synced"] else "💾"
        table_data.append({
            "ID": d["id"],
            "标题": d["title"][:30] + "..." if len(d["title"]) > 30 else d["title"],
            "分类": d.get("category", "未分类"),
            "字数": f"{d['word_count']:,}",
            f"{icon} 状态": click.style(d["status"], fg=color),
            "同步": sync_status,
            "更新时间": _format_time(d["updated_at"]),
        })

    console.print()
    console.print(Panel.fit(
        tabulate(table_data, headers="keys", tablefmt="rounded_outline"),
        title=f"我的草稿（共 {len(drafts)} 篇）",
        border_style="cyan",
    ))


@draft.command()
@click.option("-t", "--title", prompt="请输入文章标题", help="文章标题")
@click.option("-c", "--category", type=click.Choice(CATEGORIES), default="未分类",
              show_default=True, help="文章分类")
@click.option("-s", "--summary", help="文章摘要")
@click.option("-f", "--file", "file_path", type=click.Path(exists=True), help="从Markdown文件读取正文")
@click.option("--tag", "tags", multiple=True, help="添加标签，可多次使用")
@click.pass_context
def create(ctx, title, category, summary, file_path, tags):
    """创建新的长文草稿。

    示例:\n
        aicomm draft create -t "我的AI学习之路" -c 个人成长\n
        aicomm draft create -t "标题" -f ./article.md --tag AI --tag 教程
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
    else:
        console.print("[yellow]请在编辑器中撰写正文（保存并关闭编辑器后继续）...[/yellow]")
        content = click.edit(text="# 在这里开始写作...\n\n", extension=".md") or ""
        if not content.strip():
            console.print("[yellow]内容为空，取消创建[/yellow]")
            return

    if not summary:
        summary = content[:150].replace("\n", " ") + "..." if len(content) > 150 else content

    tag_list = list(tags) if tags else []

    client = APIClient(config)
    is_valid, found_keywords = client.check_violation(title + " " + content)
    if not is_valid:
        console.print(Panel.fit(
            "[red]草稿中检测到以下违规词：[/red]\n" +
            "\n".join(f"  ⚠️  {kw}" for kw in found_keywords) +
            "\n\n[yellow]草稿仍会保存到本地，但提交审核前需要修改[/yellow]",
            title="违规词检测",
            border_style="yellow",
        ))

    new_draft = client.create_draft(title, content, tags=tag_list, category=category, summary=summary)

    console.print()
    console.print(Panel.fit(
        f"[green]✓ 草稿创建成功！[/green]\n\n"
        f"[bold]📄 {new_draft['title']}[/bold]\n"
        f"[cyan]ID:[/cyan] {new_draft['id']}\n"
        f"[cyan]分类:[/cyan] {new_draft['category']}\n"
        f"[cyan]字数:[/cyan] {new_draft['word_count']:,} 字\n"
        f"[cyan]标签:[/cyan] {' '.join('#' + t for t in new_draft['tags'])}\n"
        f"[cyan]本地路径:[/cyan] {os.path.join(config.drafts_dir, new_draft['id'] + '.json')}\n\n"
        f"[dim]💡 使用 aicomm draft edit {new_draft['id']} 继续编辑[/dim]\n"
        f"[dim]💡 使用 aicomm draft submit {new_draft['id']} 提交审核[/dim]",
        title="创建草稿",
        border_style="green",
    ))


@draft.command()
@click.argument("draft_id")
@click.option("-t", "--title", help="修改标题")
@click.option("-c", "--category", type=click.Choice(CATEGORIES), help="修改分类")
@click.option("-s", "--summary", help="修改摘要")
@click.option("-f", "--file", "file_path", type=click.Path(exists=True), help="从文件替换正文")
@click.option("--tag", "tags", multiple=True, help="替换全部标签")
@click.pass_context
def edit(ctx, draft_id, title, category, summary, file_path, tags):
    """编辑现有草稿。

    不带内容选项时会打开编辑器修改正文。

    示例:\n
        aicomm draft edit draft_001\n
        aicomm draft edit draft_001 -t "新标题" -f ./new_content.md
    """
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return

    client = APIClient(config)
    draft = client.get_draft(draft_id)
    if not draft:
        console.print(f"[red]未找到草稿 {draft_id}[/red]")
        return

    update_kwargs = {}
    if title:
        update_kwargs["title"] = title
    if category:
        update_kwargs["category"] = category
    if summary:
        update_kwargs["summary"] = summary
    if tags:
        update_kwargs["tags"] = list(tags)

    content_changed = False
    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                update_kwargs["content"] = f.read()
                content_changed = True
        except IOError as e:
            console.print(f"[red]错误：无法读取文件 ({e})[/red]")
            return
    elif not any([title, category, summary, tags]):
        console.print("[yellow]正在打开编辑器...[/yellow]")
        new_content = click.edit(text=draft["content"], extension=".md")
        if new_content is not None and new_content != draft["content"]:
            update_kwargs["content"] = new_content
            content_changed = True

    if not update_kwargs:
        console.print("[yellow]未做任何修改[/yellow]")
        return

    updated = client.update_draft(draft_id, **update_kwargs)
    if updated:
        console.print()
        changed_fields = ", ".join(update_kwargs.keys())
        console.print(Panel.fit(
            f"[green]✓ 草稿已更新！[/green]\n\n"
            f"[cyan]修改字段:[/cyan] {changed_fields}\n"
            f"[cyan]当前字数:[/cyan] {updated['word_count']:,} 字\n"
            f"[cyan]更新时间:[/cyan] {_format_time(updated['updated_at'])}\n"
            f"[yellow]⚠️  本地有修改，使用 aicomm draft sync 同步到云端[/yellow]",
            title="更新草稿",
            border_style="green",
        ))


@draft.command()
@click.argument("draft_id")
@click.pass_context
def submit(ctx, draft_id):
    """提交草稿审核。

    示例:\n
        aicomm draft submit draft_001
    """
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return

    client = APIClient(config)
    draft = client.get_draft(draft_id)
    if not draft:
        console.print(f"[red]未找到草稿 {draft_id}[/red]")
        return

    if draft["word_count"] < 500:
        if not click.confirm(f"草稿字数较少（{draft['word_count']}字），确认提交审核吗？"):
            return

    is_valid, found_keywords = client.check_violation(draft["title"] + " " + draft["content"])
    if not is_valid:
        console.print(Panel.fit(
            "[red]草稿中检测到违规词，无法提交：[/red]\n" +
            "\n".join(f"  ⚠️  {kw}" for kw in found_keywords),
            title="提交失败",
            border_style="red",
        ))
        return

    result = client.submit_draft(draft_id)
    if result:
        console.print()
        console.print(Panel.fit(
            f"[green]✓ 提交审核成功！[/green]\n\n"
            f"📄 {result['title']}\n"
            f"[cyan]提交时间:[/cyan] {_format_time(result['updated_at'])}\n\n"
            f"[dim]💡 审核通常需要 24-48 小时，请耐心等待[/dim]",
            title="提交审核",
            border_style="green",
        ))
    else:
        console.print(f"[yellow]草稿当前状态为 [{draft['status']}]，无法重复提交[/yellow]")


@draft.command()
@click.argument("draft_id")
@click.pass_context
def show(ctx, draft_id):
    """查看草稿详情。

    示例:\n
        aicomm draft show draft_001
    """
    config: ConfigManager = ctx.obj["config"]
    client = APIClient(config)

    draft = client.get_draft(draft_id)
    if not draft:
        console.print(f"[red]未找到草稿 {draft_id}[/red]")
        return

    icon, color = STATUS_COLORS.get(draft["status"], ("❓", "white"))
    sync_icon = "☁️ 已同步" if draft["is_synced"] else "💾 仅本地"
    synced_at = draft["synced_at"] or "从未同步"

    console.print()
    console.print(Panel(
        f"[bold]📄 {draft['title']}[/bold]\n\n"
        f"[cyan]ID:[/cyan] {draft['id']}\n"
        f"[cyan]分类:[/cyan] {draft.get('category', '未分类')}\n"
        f"[cyan]标签:[/cyan] {' '.join('#' + t for t in draft.get('tags', []))}\n"
        f"[cyan]字数:[/cyan] {draft['word_count']:,} 字\n"
        f"[{color}]{icon} 状态:[/] {draft['status']}\n"
        f"[cyan]同步状态:[/cyan] {sync_icon} ({synced_at})\n"
        f"[cyan]创建时间:[/cyan] {_format_time(draft['created_at'])}\n"
        f"[cyan]更新时间:[/cyan] {_format_time(draft['updated_at'])}\n\n"
        f"[bold]📝 摘要:[/bold]\n{draft.get('summary', '（无摘要）')}\n\n"
        f"[bold]📖 正文预览:[/bold]\n" +
        ("—" * 50) + "\n" +
        draft["content"][:500] + ("..." if len(draft["content"]) > 500 else ""),
        title=f"草稿详情 - {draft_id}",
        border_style="cyan",
    ))


@draft.command()
@click.option("--all", "sync_all", is_flag=True, help="同步所有草稿")
@click.pass_context
def sync(ctx, sync_all):
    """同步本地草稿到云端。

    示例:\n
        aicomm draft sync\n
        aicomm draft sync --all
    """
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return

    client = APIClient(config)

    if sync_all:
        client.load_local_drafts()

    synced, total = client.sync_drafts()

    console.print()
    console.print(Panel.fit(
        f"[green]✓ 同步完成！[/green]\n\n"
        f"[cyan]本次同步:[/cyan] {synced} 篇\n"
        f"[cyan]总草稿数:[/cyan] {total} 篇\n"
        f"[cyan]同步目录:[/cyan] {config.drafts_dir}",
        title="草稿同步",
        border_style="green",
    ))


@draft.command()
@click.argument("draft_id")
@click.option("-o", "--output", type=click.Path(), help="输出文件路径")
@click.option("--format", "fmt", type=click.Choice(["md", "json"]), default="md",
              show_default=True, help="导出格式")
@click.pass_context
def export(ctx, draft_id, output, fmt):
    """导出草稿到本地文件。

    示例:\n
        aicomm draft export draft_001 -o ./my_article.md\n
        aicomm draft export draft_001 --format json
    """
    config: ConfigManager = ctx.obj["config"]
    client = APIClient(config)

    draft = client.get_draft(draft_id)
    if not draft:
        console.print(f"[red]未找到草稿 {draft_id}[/red]")
        return

    if not output:
        safe_title = "".join(c for c in draft["title"] if c.isalnum() or c in "-_ ")[:50]
        output = os.path.join(config.export_dir, f"{safe_title}.{fmt}")

    os.makedirs(os.path.dirname(output) if os.path.dirname(output) else ".", exist_ok=True)

    try:
        if fmt == "md":
            with open(output, "w", encoding="utf-8") as f:
                f.write(f"# {draft['title']}\n\n")
                f.write(f"> 分类：{draft.get('category', '未分类')}  \n")
                f.write(f"> 标签：{', '.join(draft.get('tags', []))}  \n")
                f.write(f"> 字数：{draft['word_count']:,} 字  \n\n")
                if draft.get("summary"):
                    f.write(f"## 摘要\n\n{draft['summary']}\n\n---\n\n")
                f.write(draft["content"])
        else:
            with open(output, "w", encoding="utf-8") as f:
                json.dump(draft, f, ensure_ascii=False, indent=2)

        console.print(f"[green]✓ 已导出到: {output}[/green]")
    except IOError as e:
        console.print(f"[red]错误：导出失败 ({e})[/red]")
