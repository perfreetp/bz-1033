"""prompt 命令组。

提供提示词的上传、浏览、违规词检查、管理等功能。
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

PROMPT_CATEGORIES = ["写作辅助", "编程辅助", "营销文案", "学习教育", "创意灵感", "数据分析", "翻译润色", "其他"]
MODELS = ["GPT-4", "GPT-4 Turbo", "GPT-3.5", "Claude 3", "Gemini", "通义千问", "文心一言", "通用"]


@click.group()
def prompt():
    """提示词广场管理。

    上传、浏览、管理你的AI提示词，支持违规词检查和批量导出。
    """
    pass


@prompt.command("list")
@click.option("-p", "--page", type=int, default=1, show_default=True, help="页码")
@click.option("-s", "--size", type=int, default=10, show_default=True, help="每页数量")
@click.option("-c", "--category", type=click.Choice(PROMPT_CATEGORIES), help="按分类筛选")
@click.option("--sort", "sort_by", type=click.Choice(["rating", "usage_count", "favorites", "created_at"]),
              default="rating", show_default=True, help="排序方式")
@click.option("--mine", is_flag=True, help="只看我的提示词")
@click.pass_context
def list_prompts(ctx, page, size, category, sort_by, mine):
    """浏览提示词广场。

    示例:\n
        aicomm prompt list\n
        aicomm prompt list -c 编程辅助 --sort usage_count\n
        aicomm prompt list --mine
    """
    config: ConfigManager = ctx.obj["config"]
    client = APIClient(config)

    username = config.get("username") if mine else None

    prompts, total = client.list_prompts(page=page, page_size=size, category=category, sort_by=sort_by)

    if mine and username:
        prompts = [p for p in prompts if p["author"] == username]
        total = len(prompts)

    if not prompts:
        console.print("[yellow]暂无提示词[/yellow]")
        return

    table_data = []
    for p in prompts:
        fav = "⭐" if p.get("is_favorited") else "  "
        stars = "★" * int(p["rating"]) + "☆" * (5 - int(p["rating"]))
        table_data.append({
            "": fav,
            "ID": p["id"],
            "标题": p["title"][:25] + "..." if len(p["title"]) > 25 else p["title"],
            "分类": p.get("category", "其他"),
            "作者": p.get("author_name", p["author"]),
            "评分": f"{stars} {p['rating']}",
            "使用": f"{p['usage_count']:,}",
            "收藏": f"{p['favorites']:,}",
            "时间": _format_time(p["created_at"]),
        })

    console.print()
    console.print(Panel.fit(
        tabulate(table_data, headers="keys", tablefmt="rounded_outline"),
        title=f"提示词广场（第 {page} 页，共 {total} 个）",
        border_style="magenta",
    ))

    if total > page * size:
        console.print(f"\n[dim]💡 下一页: aicomm prompt list -p {page + 1}[/dim]")


@prompt.command()
@click.option("-t", "--title", prompt="请输入提示词标题", help="提示词标题")
@click.option("-c", "--category", type=click.Choice(PROMPT_CATEGORIES), default="其他",
              show_default=True, help="提示词分类")
@click.option("-m", "--model", type=click.Choice(MODELS), default="通用", show_default=True, help="适用模型")
@click.option("-f", "--file", "file_path", type=click.Path(exists=True), help="从文件读取提示词内容")
@click.option("--tag", "tags", multiple=True, help="添加标签，可多次使用")
@click.option("--private", is_flag=True, help="设为私有（仅自己可见）")
@click.pass_context
def upload(ctx, title, category, model, file_path, tags, private):
    """上传新提示词到广场。

    示例:\n
        aicomm prompt upload -t "代码审查专家" -c 编程辅助 -m GPT-4\n
        aicomm prompt upload -t "标题" -f ./my_prompt.txt --tag Python
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
        console.print("[yellow]请在编辑器中编写提示词（保存并关闭后继续）...[/yellow]")
        default_content = """[系统设定]
你是一位专业的助手。

[任务描述]
请完成以下任务：

[输出要求]
- 使用清晰的格式
- 分点说明
"""
        content = click.edit(text=default_content, extension=".txt") or ""
        if not content.strip():
            console.print("[yellow]内容为空，取消上传[/yellow]")
            return

    tag_list = list(tags) if tags else []

    client = APIClient(config)

    is_valid, found_keywords = client.check_violation(title + " " + content)
    if not is_valid:
        console.print(Panel.fit(
            "[red]检测到以下违规词，无法上传：[/red]\n" +
            "\n".join(f"  ⚠️  {kw}" for kw in found_keywords),
            title="违规词检测",
            border_style="red",
        ))
        return

    new_prompt = client.upload_prompt(
        title=title,
        content=content,
        category=category,
        tags=tag_list,
        model=model,
        is_public=not private,
    )

    scope = "🔒 私有" if private else "🌍 公开"
    console.print()
    console.print(Panel.fit(
        f"[green]✓ 上传成功！[/green]\n\n"
        f"[bold]✨ {new_prompt['title']}[/bold]\n"
        f"[cyan]ID:[/cyan] {new_prompt['id']}\n"
        f"[cyan]分类:[/cyan] {new_prompt['category']}  [cyan]模型:[/cyan] {new_prompt['model']}\n"
        f"[cyan]可见性:[/cyan] {scope}  [cyan]标签:[/cyan] {' '.join('#' + t for t in new_prompt['tags'])}\n"
        f"[cyan]预览:[/cyan]\n{new_prompt['content'][:150]}...",
        title="上传提示词",
        border_style="green",
    ))


@prompt.command()
@click.argument("prompt_id")
@click.option("-c", "--copy", "do_copy", is_flag=True, help="复制内容到剪贴板")
@click.pass_context
def show(ctx, prompt_id, do_copy):
    """查看提示词详情。

    示例:\n
        aicomm prompt show prompt_001\n
        aicomm prompt show prompt_002 -c
    """
    config: ConfigManager = ctx.obj["config"]
    client = APIClient(config)

    prompt = client.get_prompt(prompt_id)
    if not prompt:
        console.print(f"[red]未找到提示词 {prompt_id}[/red]")
        return

    stars = "★" * int(prompt["rating"]) + "☆" * (5 - int(prompt["rating"]))
    fav = "⭐ 已收藏" if prompt.get("is_favorited") else "未收藏"
    scope = "🔒 私有" if not prompt.get("is_public", True) else "🌍 公开"
    vstatus = {"passed": "✅ 合规", "pending": "⏳ 审核中", "failed": "❌ 违规"}.get(
        prompt.get("violation_check", "pending"), prompt.get("violation_check", "⏳ 审核中"))

    console.print()
    console.print(Panel(
        f"[bold magenta]✨ {prompt['title']}[/bold magenta]\n\n"
        f"[cyan]ID:[/cyan] {prompt['id']}\n"
        f"[cyan]作者:[/cyan] {prompt.get('author_name', prompt['author'])}  [cyan]模型:[/cyan] {prompt.get('model', '通用')}\n"
        f"[cyan]分类:[/cyan] {prompt.get('category', '其他')}  [cyan]可见性:[/cyan] {scope}\n"
        f"[cyan]标签:[/cyan] {' '.join('#' + t for t in prompt.get('tags', []))}\n\n"
        f"📊 [cyan]评分:[/cyan] {stars} {prompt['rating']}    "
        f"[cyan]使用:[/cyan] {prompt['usage_count']:,}    "
        f"[cyan]收藏:[/cyan] {prompt['favorites']:,}\n"
        f"[{vstatus[:2]}]{vstatus}[/]    {fav}\n\n"
        f"[dim]{_format_time(prompt['created_at'])} 创建  |  {_format_time(prompt['updated_at'])} 更新[/dim]\n\n"
        + ("═" * 60) + "\n\n"
        f"{prompt['content']}",
        title=f"提示词详情 - {prompt_id}",
        border_style="magenta",
    ))

    if do_copy:
        try:
            import pyperclip
            pyperclip.copy(prompt['content'])
            console.print("[green]✓ 已复制到剪贴板[/green]")
        except ImportError:
            console.print("[yellow]提示：安装 pyperclip 可启用剪贴板功能[/yellow]")
            console.print(prompt['content'])


@prompt.command("check-violation")
@click.option("-c", "--content", help="直接输入要检查的内容")
@click.option("-f", "--file", "file_path", type=click.Path(exists=True), help="从文件读取内容检查")
@click.option("-a", "--add-keyword", help="检查并添加新违规词到词库")
@click.option("-l", "--list-keywords", "list_kw", is_flag=True, help="列出所有违规词")
@click.option("-r", "--remove-keyword", help="从词库移除违规词")
@click.pass_context
def check_violation(ctx, content, file_path, add_keyword, list_kw, remove_keyword):
    """检查内容中的违规词。

    示例:\n
        aicomm prompt check-violation -c "这里是要检查的内容"\n
        aicomm prompt check-violation -f ./article.txt\n
        aicomm prompt check-violation -l
    """
    config: ConfigManager = ctx.obj["config"]
    client = APIClient(config)

    if list_kw:
        keywords = config.get_violation_keywords()
        console.print()
        console.print(Panel.fit(
            "\n".join(f"  {i + 1:2d}. {kw}" for i, kw in enumerate(keywords)),
            title=f"违规词词库（共 {len(keywords)} 个）",
            border_style="yellow",
        ))
        return

    if add_keyword:
        config.add_violation_keyword(add_keyword)
        console.print(f"[green]✓ 已添加违规词: {add_keyword}[/green]")
        return

    if remove_keyword:
        removed = config.remove_violation_keyword(remove_keyword)
        if removed:
            console.print(f"[green]✓ 已移除违规词: {remove_keyword}[/green]")
        else:
            console.print(f"[yellow]未找到违规词: {remove_keyword}[/yellow]")
        return

    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except IOError as e:
            console.print(f"[red]错误：无法读取文件 ({e})[/red]")
            return

    if not content:
        content = click.edit(text="在此输入要检查的内容...", extension=".txt") or ""
        if not content.strip():
            console.print("[yellow]未输入内容[/yellow]")
            return

    is_valid, found_keywords = client.check_violation(content)

    if is_valid:
        console.print(Panel.fit(
            f"[green]✓ 内容合规，未检测到违规词[/green]\n\n"
            f"[dim]已检查 {len(content)} 个字符[/dim]",
            title="违规词检查结果",
            border_style="green",
        ))
    else:
        highlighted = content
        for kw in found_keywords:
            highlighted = highlighted.replace(kw, f"[{kw}]")

        console.print(Panel(
            f"[red]✗ 检测到 {len(found_keywords)} 个违规词[/red]\n\n"
            f"[bold]违规词列表:[/bold]\n" +
            "\n".join(f"  ⚠️  {kw}" for kw in found_keywords) +
            "\n\n[bold]高亮显示:[/bold]\n" + ("─" * 50) + "\n" +
            highlighted[:500] + ("..." if len(highlighted) > 500 else ""),
            title="违规词检查结果",
            border_style="red",
        ))


@prompt.command()
@click.argument("prompt_id")
@click.pass_context
def favorite(ctx, prompt_id):
    """收藏/取消收藏提示词。

    示例:\n
        aicomm prompt favorite prompt_001
    """
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return

    client = APIClient(config)
    prompt = client.get_prompt(prompt_id)
    if not prompt:
        console.print(f"[red]未找到提示词 {prompt_id}[/red]")
        return

    ok, is_fav = client.toggle_favorite("prompts", prompt_id)
    if ok:
        if is_fav:
            console.print(f"[green]⭐ 已收藏《{prompt['title']}》[/green]")
        else:
            console.print(f"[yellow]已取消收藏《{prompt['title']}》[/yellow]")


@prompt.command("favorites")
@click.pass_context
def list_favorites(ctx):
    """列出我收藏的提示词。

    示例:\n
        aicomm prompt favorites
    """
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return

    client = APIClient(config)
    favs = client.list_favorites(content_type="prompts")
    prompts = favs.get("prompts", [])

    if not prompts:
        console.print("[yellow]暂无收藏的提示词[/yellow]")
        return

    table_data = []
    for p in prompts:
        table_data.append({
            "ID": p["id"],
            "标题": p["title"][:30] + "..." if len(p["title"]) > 30 else p["title"],
            "作者": p.get("author_name", p["author"]),
            "分类": p.get("category", "其他"),
            "评分": f"★ {p['rating']}",
            "收藏": f"{p['favorites']:,}",
            "收藏时间": _format_time(p["created_at"]),
        })

    console.print()
    console.print(Panel.fit(
        tabulate(table_data, headers="keys", tablefmt="rounded_outline"),
        title=f"我收藏的提示词（共 {len(prompts)} 个）",
        border_style="yellow",
    ))
