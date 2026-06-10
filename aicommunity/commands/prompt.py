"""prompt 命令组。

提供提示词的上传、浏览、违规词检查、管理和发布审核功能。
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

APPROVAL_STATUS_LABELS = {
    "none": ("⚪", "默认私有", "white"),
    "pending_review": ("⏳", "待审核(公开申请中)", "yellow"),
    "approved": ("✅", "已公开(审核通过)", "green"),
    "rejected": ("❌", "已拒绝(退回私有)", "red"),
}


@click.group()
def prompt():
    """提示词广场管理+发布审核。

    上传、浏览、管理提示词；私有改公开需审核，管理员批准后才进广场。
    """
    pass


@prompt.command("list")
@click.option("-p", "--page", type=int, default=1, show_default=True)
@click.option("-s", "--size", type=int, default=10, show_default=True)
@click.option("-c", "--category", type=click.Choice(PROMPT_CATEGORIES))
@click.option("-a", "--author", help="按作者用户名筛选")
@click.option("--sort", "sort_by", type=click.Choice(["rating", "usage_count", "favorites", "created_at"]),
              default="rating", show_default=True)
@click.option("--mine", is_flag=True, help="只看我的提示词")
@click.option("--favorites", "only_favorites", is_flag=True, help="只看收藏的")
@click.option("--public-only", is_flag=True, help="只看已公开的")
@click.option("--status", "status_filter",
              type=click.Choice(["pending_review", "approved", "rejected"]),
              help="按审核状态筛选：pending待审核/approved已通过/rejected已拒绝（需--mine或admin）")
@click.pass_context
def list_prompts(ctx, page, size, category, author, sort_by, mine, only_favorites, public_only, status_filter):
    """浏览提示词广场。

    示例:\n
        aicomm prompt list --mine --status pending_review\n
        aicomm prompt list --status pending_review            # 管理员看全部待审\n
        aicomm prompt list --mine --status rejected            # 查看被拒的
    """
    config: ConfigManager = ctx.obj["config"]
    client = APIClient(config)

    prompts, total = client.list_prompts(
        page=page, page_size=size, category=category, author=author, sort_by=sort_by,
        mine_only=mine, only_favorites=only_favorites, only_public=public_only,
        status_filter=status_filter,
    )

    if not prompts:
        desc = []
        if status_filter: desc.append(f"状态={status_filter}")
        if mine: desc.append("我的")
        hint = f"（{'/'.join(desc)}）" if desc else ""
        console.print(f"[yellow]暂无提示词[/yellow] {hint}")
        return

    table_data = []
    for p in prompts:
        fav = "⭐" if p.get("is_favorited") else "  "
        stars = "★" * int(p["rating"]) + "☆" * (5 - int(p["rating"]))
        approval = p.get("approval_status", "approved")
        ap_icon, ap_label, ap_color = APPROVAL_STATUS_LABELS.get(approval, ("❓", approval, "white"))
        scope = "🔒" if not p.get("is_public", True) else "🌍"
        table_data.append({
            "": fav,
            "ID": p["id"],
            "标题": p["title"][:22] + "..." if len(p["title"]) > 22 else p["title"],
            "分类": p.get("category", "其他"),
            "作者": p.get("author_name", p["author"]),
            "审核": click.style(f"{ap_icon}", fg=ap_color),
            "可见性": scope,
            "评分": f"{stars} {p['rating']}",
            "使用": f"{p['usage_count']:,}",
            "时间": _format_time(p["created_at"]),
        })

    title_parts = []
    if status_filter: title_parts.append(f"[status={status_filter}]")
    if mine: title_parts.append("我的")
    suffix = f" {'·'.join(title_parts)}" if title_parts else ""

    console.print()
    console.print(Panel.fit(
        tabulate(table_data, headers="keys", tablefmt="rounded_outline"),
        title=f"提示词广场（第 {page} 页，共 {total} 个）{suffix}",
        border_style="magenta",
    ))

    if total > page * size:
        console.print(f"\n[dim]💡 下一页: aicomm prompt list -p {page + 1}[/dim]")


@prompt.command()
@click.option("-t", "--title", prompt="请输入提示词标题")
@click.option("-c", "--category", type=click.Choice(PROMPT_CATEGORIES), default="其他", show_default=True)
@click.option("-m", "--model", type=click.Choice(MODELS), default="通用", show_default=True)
@click.option("-f", "--file", "file_path", type=click.Path(exists=True))
@click.option("--tag", "tags", multiple=True)
@click.option("--private/--public", default=True, show_default=True,
              help="--private(默认)创建为私有 / --public创建为公开（非admin需先进入待审核）")
@click.pass_context
def upload(ctx, title, category, model, file_path, tags, private):
    """上传新提示词。

    --private：默认创建为私有提示词，之后可 submit 申请公开\n
    --public：直接申请公开（非admin会进入pending_review待审核）
    """
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return
    username = config.get("username", "")

    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        default_content = """[系统设定]\n你是一位专业的助手。\n\n[任务描述]\n请完成任务。\n"""
        content = click.edit(text=default_content, extension=".txt") or ""
        if not content.strip():
            console.print("[yellow]内容为空，取消上传[/yellow]")
            return

    tag_list = list(tags) if tags else []

    client = APIClient(config)
    is_valid, found_keywords = client.check_violation(title + " " + content)
    if not is_valid:
        console.print(Panel.fit(
            "[red]检测到违规词，无法上传：[/red]\n" +
            "\n".join(f"  ⚠️  {kw}" for kw in found_keywords),
            title="违规词检测", border_style="red",
        ))
        return

    # 创建时先创建为指定状态，然后如果选了公开且非admin → 自动提审pending
    new_prompt = client.upload_prompt(
        title=title, content=content, category=category,
        tags=tag_list, model=model, is_public=(not private),
    )

    # 如果选了public且不是admin，自动提交审核
    if not private and username != "admin":
        client.submit_prompt_for_approval(new_prompt["id"])
        console.print(Panel.fit(
            f"[green]✓ 上传成功！已提交公开审核[/green]\n\n"
            f"[bold]✨ {new_prompt['title']}[/bold]\n"
            f"[cyan]ID:[/cyan] {new_prompt['id']}\n"
            f"[yellow]⏳ 状态: 待管理员审核，批准后进入公共广场[/yellow]",
            title="上传 + 提交审核", border_style="yellow",
        ))
        return

    scope = "🔒 私有" if private else ("🌍 公开（管理员直接通过）" if username == "admin" else "🌍 公开")
    console.print()
    console.print(Panel.fit(
        f"[green]✓ 上传成功！[/green]\n\n"
        f"[bold]✨ {new_prompt['title']}[/bold]\n"
        f"[cyan]ID:[/cyan] {new_prompt['id']}\n"
        f"[cyan]分类:[/cyan] {new_prompt['category']}  [cyan]模型:[/cyan] {new_prompt['model']}\n"
        f"[cyan]可见性:[/cyan] {scope}\n"
        f"[dim]💡 私有→公开：aicomm prompt submit {new_prompt['id']}[/dim]",
        title="上传提示词", border_style="green",
    ))


@prompt.command("submit")
@click.argument("prompt_id")
@click.pass_context
def submit_prompt(ctx, prompt_id):
    """私有提示词申请公开（进入待审核）。

    示例:\n
        aicomm prompt submit prompt_001
    """
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return
    client = APIClient(config)
    ok, msg, _ = client.submit_prompt_for_approval(prompt_id)
    if ok:
        console.print(Panel.fit(f"[green]✓ {msg}[/green]", title="提交审核", border_style="green"))
    else:
        console.print(f"[red]✗ {msg}[/red]")


@prompt.command("approve")
@click.argument("prompt_id")
@click.option("-c", "--comment", help="审核意见")
@click.pass_context
def approve_prompt(ctx, prompt_id, comment):
    """[管理员]批准提示词公开申请。"""
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return
    client = APIClient(config)
    ok, msg, _ = client.approve_prompt_public(prompt_id, comment or "")
    if ok:
        console.print(Panel.fit(f"[green]✓ {msg}[/green]", title="审核通过", border_style="green"))
    else:
        console.print(f"[red]✗ {msg}[/red]")


@prompt.command("reject")
@click.argument("prompt_id")
@click.option("-r", "--reason", required=True, help="拒绝原因（必填）")
@click.pass_context
def reject_prompt(ctx, prompt_id, reason):
    """[管理员]拒绝提示词公开申请（附原因，退回给作者）。"""
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return
    client = APIClient(config)
    ok, msg, _ = client.reject_prompt_public(prompt_id, reason)
    if ok:
        console.print(Panel.fit(f"[red]✓ {msg}[/red]", title="已拒绝", border_style="red"))
    else:
        console.print(f"[red]✗ {msg}[/red]")


@prompt.command()
@click.argument("prompt_id")
@click.option("-c", "--copy", "do_copy", is_flag=True, help="复制内容到剪贴板")
@click.pass_context
def show(ctx, prompt_id, do_copy):
    """查看提示词详情。"""
    config: ConfigManager = ctx.obj["config"]
    client = APIClient(config)
    p = client.get_prompt(prompt_id)
    if not p:
        console.print(f"[red]未找到提示词 {prompt_id}[/red]")
        return

    stars = "★" * int(p["rating"]) + "☆" * (5 - int(p["rating"]))
    fav = "⭐ 已收藏" if p.get("is_favorited") else "未收藏"
    scope = "🔒 私有" if not p.get("is_public", True) else "🌍 公开"
    approval = p.get("approval_status", "approved")
    ap_icon, ap_label, ap_color = APPROVAL_STATUS_LABELS.get(approval, ("❓", approval, "white"))

    extra = ""
    if approval == "rejected" and p.get("rejection_reason"):
        extra = f"\n[red]❌ 拒绝原因:[/red] {p['rejection_reason']}\n"

    history = p.get("approval_history", [])
    history_md = ""
    if history:
        history_md = "\n[bold]📋 审核历史:[/bold]\n"
        for h in history[-5:]:
            history_md += f"  [{h.get('time','')[:16]}] {h.get('actor','')} · {h.get('action','')} — {h.get('detail','')[:50]}\n"

    console.print()
    console.print(Panel(
        f"[bold magenta]✨ {p['title']}[/bold magenta]\n\n"
        f"[cyan]ID:[/cyan] {p['id']}\n"
        f"[cyan]作者:[/cyan] {p.get('author_name', p['author'])}  [cyan]模型:[/cyan] {p.get('model', '通用')}\n"
        f"[cyan]分类:[/cyan] {p.get('category', '其他')}  [cyan]可见性:[/cyan] {scope}\n"
        f"[{ap_color}]{ap_icon} 审核状态:[/] {ap_label}\n"
        f"{extra}"
        f"[cyan]标签:[/cyan] {' '.join('#' + t for t in p.get('tags', []))}\n\n"
        f"📊 [cyan]评分:[/cyan] {stars} {p['rating']}    "
        f"[cyan]使用:[/cyan] {p['usage_count']:,}    "
        f"[cyan]收藏:[/cyan] {p['favorites']:,}\n"
        f"{fav}\n"
        f"[dim]{_format_time(p['created_at'])} 创建 | {_format_time(p['updated_at'])} 更新[/dim]\n"
        f"{history_md}\n"
        + ("═" * 60) + "\n\n" + p["content"],
        title=f"提示词详情 - {prompt_id}", border_style="magenta",
    ))

    if do_copy:
        try:
            import pyperclip
            pyperclip.copy(p['content'])
            console.print("[green]✓ 已复制到剪贴板[/green]")
        except ImportError:
            console.print(p['content'])


@prompt.command("check-violation")
@click.option("-c", "--content")
@click.option("-f", "--file", "file_path", type=click.Path(exists=True))
@click.option("-a", "--add-keyword")
@click.option("-l", "--list-keywords", "list_kw", is_flag=True)
@click.option("-r", "--remove-keyword")
@click.pass_context
def check_violation(ctx, content, file_path, add_keyword, list_kw, remove_keyword):
    """检查内容中的违规词。"""
    config: ConfigManager = ctx.obj["config"]
    client = APIClient(config)
    if list_kw:
        keywords = config.get_violation_keywords()
        console.print(Panel.fit(
            "\n".join(f"  {i+1:2d}. {kw}" for i, kw in enumerate(keywords)),
            title=f"违规词词库（共 {len(keywords)} 个）", border_style="yellow",
        ))
        return
    if add_keyword:
        config.add_violation_keyword(add_keyword)
        console.print(f"[green]✓ 已添加违规词: {add_keyword}[/green]")
        return
    if remove_keyword:
        if config.remove_violation_keyword(remove_keyword):
            console.print(f"[green]✓ 已移除违规词: {remove_keyword}[/green]")
        else:
            console.print(f"[yellow]未找到: {remove_keyword}[/yellow]")
        return
    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    if not content:
        content = click.edit(text="在此输入要检查的内容...", extension=".txt") or ""
        if not content.strip():
            console.print("[yellow]未输入内容[/yellow]")
            return
    ok, found = client.check_violation(content)
    if ok:
        console.print(Panel.fit(f"[green]✓ 内容合规[/green]（{len(content)} 字符）",
                                title="检查结果", border_style="green"))
    else:
        console.print(Panel.fit(
            f"[red]✗ 检测到 {len(found)} 个违规词：[/red]\n" +
            "\n".join(f"  ⚠️  {kw}" for kw in found),
            title="检查结果", border_style="red",
        ))


@prompt.command()
@click.argument("prompt_id")
@click.pass_context
def favorite(ctx, prompt_id):
    """收藏/取消收藏提示词。"""
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return
    client = APIClient(config)
    p = client.get_prompt(prompt_id)
    if not p:
        console.print(f"[red]未找到提示词 {prompt_id}[/red]")
        return
    ok, is_fav, msg = client.toggle_favorite("prompts", prompt_id)
    if not ok:
        console.print(f"[red]✗ {msg}[/red]")
        return
    if is_fav:
        console.print(f"[green]⭐ 已收藏《{p['title']}》[/green]")
    else:
        console.print(f"[yellow]已取消收藏《{p['title']}》[/yellow]")


@prompt.command("favorites")
@click.pass_context
def list_favorites(ctx):
    """列出我收藏的提示词。"""
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return
    client = APIClient(config)
    prompts = client.list_favorites(content_type="prompts").get("prompts", [])
    if not prompts:
        console.print("[yellow]暂无收藏的提示词[/yellow]")
        return
    data = []
    for p in prompts:
        data.append({"ID": p["id"], "标题": p["title"][:30], "作者": p.get("author_name", p["author"]),
                     "分类": p.get("category", ""), "评分": f"★{p['rating']}"})
    console.print(Panel.fit(
        tabulate(data, headers="keys", tablefmt="rounded_outline"),
        title=f"我收藏的提示词（共 {len(prompts)} 个）", border_style="yellow",
    ))


@prompt.command()
@click.argument("prompt_id")
@click.option("-t", "--title")
@click.option("-c", "--category", type=click.Choice(PROMPT_CATEGORIES))
@click.option("-m", "--model", type=click.Choice(MODELS))
@click.option("--tag", "tags", multiple=True)
@click.option("-f", "--file", "file_path", type=click.Path(exists=True))
@click.option("--public/--private", "is_public", default=None,
              help="改为公开（非admin=进入pending_review）/ 改为私有")
@click.pass_context
def edit(ctx, prompt_id, title, category, model, tags, file_path, is_public):
    """编辑提示词。--public会自动提交审核。"""
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return
    username = config.get("username", "")
    client = APIClient(config)
    p = client.get_prompt(prompt_id)
    if not p:
        console.print(f"[red]未找到提示词 {prompt_id}[/red]")
        return

    kwargs = {}
    if title: kwargs["title"] = title
    if category: kwargs["category"] = category
    if model: kwargs["model"] = model
    if tags: kwargs["tags"] = list(tags)
    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            kwargs["content"] = f.read()

    need_submit = False
    if is_public is not None:
        kwargs["is_public"] = is_public
        if is_public and username != "admin":
            need_submit = True

    if not kwargs and not click.confirm("未传入修改项，打开编辑器修改正文？", default=True):
        return
    if not kwargs:
        new_content = click.edit(text=p.get("content", ""), extension=".txt") or ""
        if new_content != p.get("content", ""):
            kwargs["content"] = new_content
        else:
            console.print("[yellow]未做任何修改[/yellow]")
            return

    ok, msg, updated = client.edit_prompt(prompt_id, **kwargs)
    if not ok:
        console.print(f"[red]✗ {msg}[/red]")
        return

    # 自动提审
    if need_submit and updated:
        client.submit_prompt_for_approval(updated["id"])
        approval = "⏳ 已提交审核（等待管理员批准）"
        color = "yellow"
    else:
        visibility = "🌐 公开" if updated.get("is_public") else "🔒 私有"
        approval = visibility
        color = "green"

    changed = ", ".join(kwargs.keys())
    console.print(Panel.fit(
        f"[green]✓ {msg}！[/green]\n\n"
        f"📄 {updated['title']}\n"
        f"[cyan]修改字段:[/cyan] {changed}\n"
        f"[cyan]分类:[/cyan] {updated.get('category', '')}\n"
        f"[{color}]状态:[/] {approval}",
        title="编辑提示词", border_style="green",
    ))


@prompt.command()
@click.argument("prompt_id")
@click.option("-y", "--yes", is_flag=True)
@click.pass_context
def delete(ctx, prompt_id, yes):
    """删除自己上传的提示词。"""
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return
    client = APIClient(config)
    p = client.get_prompt(prompt_id)
    if not p:
        console.print(f"[red]未找到提示词 {prompt_id}[/red]")
        return
    if not yes and not click.confirm(f"删除《{p['title']}》？不可恢复"):
        return
    ok, msg = client.delete_prompt(prompt_id)
    if ok:
        console.print(f"[green]✓ {msg}[/green]")
    else:
        console.print(f"[red]✗ {msg}[/red]")
