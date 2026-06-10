"""draft 命令组。

提供长文草稿的创建、编辑、提交审核、本地同步和协作流转功能。
"""

import click
import json
import os
import csv
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
    "transferred": ("📨", "cyan"),
    "approved": ("✅", "green"),
    "published": ("✅", "green"),
    "rejected": ("❌", "red"),
}

CATEGORIES = ["技术深度", "个人成长", "产品分析", "行业观察", "AI应用", "教程指南", "未分类"]

PERSPECTIVE_LABELS = {
    "pending_me": "📥 待我处理",
    "my_initiated": "📤 我发起的",
    "rejected_to_me": "↩️  已退还给我",
    "rejected": "❌ 全部已退回",
    "transferred": "📨 全部流转中",
    "approved": "✅ 全部已批准",
}


@click.group()
def draft():
    """长文草稿管理。

    创建、编辑、提交、流转、审阅长文草稿，支持本地同步和版本管理。
    """
    pass


@draft.command("list")
@click.option("-s", "--status", type=click.Choice(["draft", "reviewing", "transferred", "approved", "published", "rejected"]),
              help="按状态筛选")
@click.option("-a", "--author", help="按作者用户名筛选")
@click.option("--view", "perspective",
              type=click.Choice(["pending_me", "my_initiated", "rejected_to_me", "rejected", "transferred", "approved"]),
              help="按协作视角筛选：待我处理/我发起的/已退还给我/全部已退回/全部流转中/全部已批准")
@click.option("-d", "--days", type=int, help="按最近N天筛选（按更新时间）")
@click.option("--from", "from_date", help="起始日期 YYYY-MM-DD")
@click.option("--to", "to_date", help="结束日期 YYYY-MM-DD")
@click.option("--only-local", is_flag=True, help="仅显示本地未同步的草稿")
@click.option("--export", "export_path", type=click.Path(), help="导出当前筛选结果到文件")
@click.option("-f", "--format", "export_fmt",
              type=click.Choice(["json", "csv", "markdown"]), default="json", show_default=True,
              help="导出格式")
@click.pass_context
def list_drafts(ctx, status, author, perspective, days, from_date, to_date, only_local, export_path, export_fmt):
    """列出草稿：支持视角/状态/作者/时间/同步多维筛选 + 结果导出。

    示例:\n
        aicomm draft list --view pending_me\n
        aicomm draft list --view my_initiated -d 30\n
        aicomm draft list --view rejected_to_me\n
        aicomm draft list -s draft --export ./待处理.csv -f csv
    """
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return

    client = APIClient(config)
    client.load_local_drafts()

    drafts, total = client.list_drafts(
        status=status, author=author, perspective=perspective,
        days=days, from_date=from_date, to_date=to_date,
        only_local=only_local, mine_only=(author is None and perspective is None),
    )

    filters_desc = []
    if perspective: filters_desc.append(PERSPECTIVE_LABELS.get(perspective, perspective))
    if status: filters_desc.append(f"状态={status}")
    if author: filters_desc.append(f"作者={author}")
    if days: filters_desc.append(f"最近{days}天")
    if from_date or to_date: filters_desc.append(f"日期:{from_date or '*'}~{to_date or '*'}")
    if only_local: filters_desc.append("仅本地未同步")

    if not drafts:
        hint = f"（筛选: {' / '.join(filters_desc)}）" if filters_desc else ""
        console.print(f"[yellow]暂无草稿[/yellow] {hint}")
        return

    table_data = []
    for d in drafts:
        icon, color = STATUS_COLORS.get(d["status"], ("❓", "white"))
        sync_status = "☁️" if d.get("is_synced") else "💾"
        reviewer_info = ""
        if d.get("reviewer"):
            reviewer_info = f"→{d.get('reviewer')}"
        table_data.append({
            "ID": d["id"],
            "标题": d["title"][:30] + "..." if len(d["title"]) > 30 else d["title"],
            "作者": d.get("author", ""),
            "审阅人": reviewer_info,
            "分类": d.get("category", "未分类"),
            "字数": f"{d['word_count']:,}",
            "状态": icon + " " + click.style(d["status"], fg=color),
            "同步": sync_status,
            "更新时间": _format_time(d["updated_at"]),
        })

    title = f"草稿列表（共 {total} 篇，当前 {len(drafts)} 篇）"
    if filters_desc:
        title += f"  [dim]筛选: {' / '.join(filters_desc)}[/dim]"

    console.print()
    console.print(Panel.fit(
        tabulate(table_data, headers="keys", tablefmt="rounded_outline"),
        title=title,
        border_style="cyan",
    ))

    if export_path:
        ext = os.path.splitext(export_path)[1].lower()
        fmt = export_fmt
        if ext == ".csv": fmt = "csv"
        elif ext in (".json",): fmt = "json"
        elif ext in (".md", ".markdown"): fmt = "markdown"

        export_dir = os.path.dirname(os.path.abspath(export_path)) or "."
        os.makedirs(export_dir, exist_ok=True)
        count = len(drafts)

        try:
            if fmt == "json":
                export_list = []
                for d in drafts:
                    export_list.append({
                        "id": d["id"], "title": d["title"], "author": d.get("author"),
                        "reviewer": d.get("reviewer"), "category": d.get("category"),
                        "tags": d.get("tags", []), "status": d["status"],
                        "word_count": d["word_count"], "is_synced": d.get("is_synced", False),
                        "version_count": len(d.get("versions", [])),
                        "review_comments_count": len(d.get("review_comments", [])),
                        "created_at": d.get("created_at"), "updated_at": d.get("updated_at"),
                    })
                with open(export_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "filters": {
                            "perspective": perspective, "status": status, "author": author,
                            "days": days, "from_date": from_date, "to_date": to_date,
                            "only_local": only_local,
                        }, "count": count, "items": export_list
                    }, f, ensure_ascii=False, indent=2)

            elif fmt == "csv":
                headers = ["ID","标题","作者","审阅人","分类","状态","字数","版本数","批注数","同步","创建时间","更新时间"]
                with open(export_path, "w", encoding="utf-8-sig", newline="") as f:
                    w = csv.writer(f)
                    w.writerow(headers)
                    for d in drafts:
                        w.writerow([
                            d["id"], d["title"], d.get("author",""), d.get("reviewer",""),
                            d.get("category","未分类"), d["status"], d["word_count"],
                            len(d.get("versions",[])), len(d.get("review_comments",[])),
                            "已同步" if d.get("is_synced") else "本地",
                            d.get("created_at",""), d.get("updated_at",""),
                        ])

            elif fmt == "markdown":
                lines = [f"# 稿件清单（{count} 篇）","",
                         f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]
                if filters_desc:
                    lines.append(f"**筛选条件**: {' / '.join(filters_desc)}")
                lines.append("")
                lines.append("| ID | 标题 | 作者 | 审阅人 | 分类 | 状态 | 字数 | 版本 | 批注 | 同步 | 更新时间 |")
                lines.append("|---|---|---|---|---|---|---:|---:|---:|---|---|")
                for d in drafts:
                    sync = "☁️" if d.get("is_synced") else "💾"
                    lines.append(
                        f"| {d['id']} | {d['title'][:35]} | {d.get('author','')} | {d.get('reviewer','')} "
                        f"| {d.get('category','')} | {d['status']} | {d['word_count']:,} "
                        f"| {len(d.get('versions',[]))} | {len(d.get('review_comments',[]))} "
                        f"| {sync} | {_format_time(d['updated_at'])} |"
                    )
                lines.append("")
                lines.append("## 待处理清单")
                for i, d in enumerate(drafts, 1):
                    lines.append(f"### {i}. {d['title']}  ")
                    lines.append(f"- **ID**: `{d['id']}`  ")
                    lines.append(f"- **作者/审阅**: {d.get('author','')} / {d.get('reviewer','(无)')}  ")
                    lines.append(f"- **字数/版本/批注**: {d['word_count']:,}字 / {len(d.get('versions',[]))}版 / {len(d.get('review_comments',[]))}条  ")
                    lines.append(f"- **状态**: {STATUS_COLORS.get(d['status'],('?','white'))[0]} {d['status']}  ")
                    if d.get('review_comments'):
                        latest = d['review_comments'][-1]
                        lines.append(f"- **最新批注**: [{latest.get('reviewer','')}] {latest.get('comment','')[:80]}  ")
                    lines.append("")
                with open(export_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))

            file_size = os.path.getsize(export_path)
            size_str = f"{file_size/1024:.1f}KB" if file_size < 1024*1024 else f"{file_size/(1024*1024):.1f}MB"
            console.print(f"\n[green]✓ 已导出 {count} 篇到: {export_path}[/green] [dim]({size_str}, {fmt})[/dim]")
        except (IOError, OSError) as e:
            console.print(f"[red]错误：导出失败 ({e})[/red]")


@draft.command("transfer")
@click.argument("draft_id")
@click.option("-r", "--reviewer", required=True,
              type=click.Choice(["admin", "writer", "demo"]),
              help="审阅人用户名")
@click.option("-n", "--note", help="转让附言（给审阅人）")
@click.pass_context
def transfer(ctx, draft_id, reviewer, note):
    """将草稿转给某人审阅（协作流转）。

    示例:\n
        aicomm draft transfer draft_001 -r admin -n "麻烦帮忙看一下架构章节"
    """
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return

    client = APIClient(config)
    ok, msg, _ = client.transfer_draft(draft_id, reviewer, note or "")
    if ok:
        console.print(Panel.fit(f"[green]✓ {msg}[/green]", title="转让成功", border_style="green"))
    else:
        console.print(f"[red]✗ {msg}[/red]")


@draft.command("review")
@click.argument("draft_id")
@click.option("-a", "--action", "action", required=True,
              type=click.Choice(["approve", "reject", "comment"]),
              help="approve批准发布 / reject退回 / comment仅批注")
@click.option("-c", "--comment", "comment", help="审阅意见（approve/comment时）")
@click.option("-r", "--reason", "reason", help="退回原因（reject时必填）")
@click.pass_context
def review(ctx, draft_id, action, comment, reason):
    """审阅人处理草稿：批准/退回/批注。

    示例:\n
        aicomm draft review draft_001 -a comment -c "建议补充案例"\n
        aicomm draft review draft_001 -a approve -c "写得很好"\n
        aicomm draft review draft_001 -a reject -r "章节结构需要重组"
    """
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return

    if action == "reject" and not reason and not comment:
        console.print("[yellow]警告：reject 建议使用 --reason 说明退回原因[/yellow]")

    client = APIClient(config)
    ok, msg, updated = client.review_draft(draft_id, action, comment or "", reason or "")
    if ok:
        border = "green" if action == "approve" else ("red" if action == "reject" else "blue")
        console.print(Panel.fit(f"[{'green' if action == 'approve' else ('red' if action == 'reject' else 'cyan')}]✓ {msg}[/]",
                                title=f"审阅完成 - {action}", border_style=border))
    else:
        console.print(f"[red]✗ {msg}[/red]")


@draft.command()
@click.option("-t", "--title", prompt="请输入文章标题", help="文章标题")
@click.option("-c", "--category", type=click.Choice(CATEGORIES), default="未分类",
              show_default=True, help="文章分类")
@click.option("-s", "--summary", help="文章摘要")
@click.option("-f", "--file", "file_path", type=click.Path(exists=True), help="从Markdown文件读取正文")
@click.option("--tag", "tags", multiple=True, help="添加标签，可多次使用")
@click.pass_context
def create(ctx, title, category, summary, file_path, tags):
    """创建新的长文草稿。"""
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
        console.print("[yellow]请在编辑器中撰写正文...[/yellow]")
        content = click.edit(text="# 在这里开始写作...\n\n", extension=".md") or ""
        if not content.strip():
            console.print("[yellow]内容为空，取消创建[/yellow]")
            return

    if not summary:
        summary = content[:150].replace("\n", " ") + "..." if len(content) > 150 else content

    client = APIClient(config)
    is_valid, found_keywords = client.check_violation(title + " " + content)
    if not is_valid:
        console.print(Panel.fit(
            "[red]草稿中检测到以下违规词：[/red]\n" +
            "\n".join(f"  ⚠️  {kw}" for kw in found_keywords) +
            "\n\n[yellow]草稿仍会保存到本地，但提交审核前需要修改[/yellow]",
            title="违规词检测", border_style="yellow",
        ))

    new_draft = client.create_draft(title, content, tags=list(tags) if tags else [], category=category, summary=summary)

    console.print()
    console.print(Panel.fit(
        f"[green]✓ 草稿创建成功！[/green]\n\n"
        f"[bold]📄 {new_draft['title']}[/bold]\n"
        f"[cyan]ID:[/cyan] {new_draft['id']}\n"
        f"[cyan]分类:[/cyan] {new_draft['category']}\n"
        f"[cyan]字数:[/cyan] {new_draft['word_count']:,} 字\n"
        f"[cyan]标签:[/cyan] {' '.join('#' + t for t in new_draft['tags'])}\n\n"
        f"[dim]💡 edit / submit / transfer draft_001 继续操作[/dim]",
        title="创建草稿", border_style="green",
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
    """编辑现有草稿。"""
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return

    client = APIClient(config)
    d = client.get_draft(draft_id)
    if not d:
        console.print(f"[red]未找到草稿 {draft_id}[/red]")
        return

    update_kwargs = {}
    if title: update_kwargs["title"] = title
    if category: update_kwargs["category"] = category
    if summary: update_kwargs["summary"] = summary
    if tags: update_kwargs["tags"] = list(tags)

    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            update_kwargs["content"] = f.read()
    elif not any([title, category, summary, tags]):
        new_content = click.edit(text=d["content"], extension=".md")
        if new_content is not None and new_content != d["content"]:
            update_kwargs["content"] = new_content

    if not update_kwargs:
        console.print("[yellow]未做任何修改[/yellow]")
        return

    updated = client.update_draft(draft_id, **update_kwargs)
    if updated:
        console.print(Panel.fit(
            f"[green]✓ 草稿已更新！[/green]\n\n"
            f"[cyan]修改字段:[/cyan] {', '.join(update_kwargs.keys())}\n"
            f"[cyan]当前字数:[/cyan] {updated['word_count']:,} 字",
            title="更新草稿", border_style="green",
        ))


@draft.command()
@click.argument("draft_id")
@click.pass_context
def submit(ctx, draft_id):
    """提交草稿审核（等同于转让给admin）。"""
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return
    client = APIClient(config)
    d = client.get_draft(draft_id)
    if not d:
        console.print(f"[red]未找到草稿 {draft_id}[/red]")
        return
    if d["word_count"] < 500 and not click.confirm(f"草稿字数较少（{d['word_count']}字），确认提交吗？"):
        return
    ok, msg, _ = client.transfer_draft(draft_id, "admin", "提交审核")
    if ok:
        console.print(Panel.fit(f"[green]✓ {msg}[/green]", title="提交审核", border_style="green"))
    else:
        console.print(f"[red]✗ {msg}[/red]")


@draft.command()
@click.argument("draft_id")
@click.pass_context
def show(ctx, draft_id):
    """查看草稿详情（含版本记录、审阅批注、流转历史）。"""
    config: ConfigManager = ctx.obj["config"]
    client = APIClient(config)
    d = client.get_draft(draft_id)
    if not d:
        console.print(f"[red]未找到草稿 {draft_id}[/red]")
        return

    icon, color = STATUS_COLORS.get(d["status"], ("❓", "white"))
    sync_icon = "☁️ 已同步" if d.get("is_synced") else "💾 仅本地"

    reviewer_info = d.get("reviewer") or "（无审阅人）"

    console.print()
    console.print(Panel(
        f"[bold]📄 {d['title']}[/bold]\n\n"
        f"[cyan]ID:[/cyan] {d['id']}\n"
        f"[cyan]作者:[/cyan] {d.get('author','')} → [cyan]审阅人:[/cyan] {reviewer_info}\n"
        f"[cyan]分类:[/cyan] {d.get('category', '未分类')}\n"
        f"[cyan]标签:[/cyan] {' '.join('#' + t for t in d.get('tags', []))}\n"
        f"[cyan]字数:[/cyan] {d['word_count']:,} 字 / [cyan]版本:[/cyan] {len(d.get('versions',[]))}版\n"
        f"[{color}]{icon} 状态:[/] {d['status']}   [cyan]同步:[/cyan] {sync_icon}\n"
        f"[cyan]创建/更新:[/cyan] {_format_time(d['created_at'])} / {_format_time(d['updated_at'])}\n\n"
        f"[bold]📝 摘要:[/bold]\n{d.get('summary', '（无摘要）')}\n\n"
        f"[bold]📖 正文预览:[/bold]\n" + ("—" * 50) + "\n" +
        d["content"][:500] + ("..." if len(d["content"]) > 500 else ""),
        title=f"草稿详情 - {draft_id}", border_style="cyan",
    ))

    # 审阅批注
    comments = d.get("review_comments", [])
    if comments:
        t = Table(title="💬 审阅批注", header_style="bold magenta", show_lines=True, border_style="dim")
        t.add_column("#", justify="center", width=5)
        t.add_column("审阅人", style="yellow", width=12)
        t.add_column("批注内容", overflow="fold")
        t.add_column("时间", style="dim", width=20)
        for i, c in enumerate(comments, 1):
            t.add_row(str(i), c.get("reviewer",""), c.get("comment",""), _format_time(c.get("created_at","")))
        console.print(t)

    # 流转历史
    history = d.get("audit_history", [])
    if history:
        t = Table(title="🔄 协作流转历史", header_style="bold blue", show_lines=False, border_style="dim")
        t.add_column("动作", style="cyan", width=16)
        t.add_column("操作人", style="yellow", width=12)
        t.add_column("详情", overflow="fold")
        t.add_column("时间", style="dim", width=20)
        for h in history:
            t.add_row(h.get("action",""), h.get("actor",""), h.get("detail",""), _format_time(h.get("time","")))
        console.print(t)

    # 版本
    versions = client.get_draft_versions(draft_id)
    if versions:
        t = Table(title="📜 版本记录", header_style="bold magenta", show_lines=False, border_style="dim")
        t.add_column("版本", justify="center", width=8)
        t.add_column("标题", style="cyan")
        t.add_column("字数", justify="right", style="yellow")
        t.add_column("时间", style="dim")
        for v in versions:
            t.add_row(f"v{v['version']}", (v.get("title") or "")[:35],
                      f"{len(v.get('content','')):,} 字", _format_time(v.get("created_at","")))
        console.print(t)


@draft.command()
@click.option("--all", "sync_all", is_flag=True, help="同步所有草稿")
@click.pass_context
def sync(ctx, sync_all):
    """同步本地草稿到云端。"""
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return
    client = APIClient(config)
    if sync_all:
        client.load_local_drafts()
    synced, total = client.sync_drafts()
    console.print(Panel.fit(
        f"[green]✓ 同步完成！[/green]\n\n本次同步: {synced} 篇\n总草稿数: {total} 篇",
        title="草稿同步", border_style="green",
    ))


@draft.command()
@click.argument("draft_id")
@click.option("-o", "--output", type=click.Path(), help="输出文件路径")
@click.option("--format", "fmt", type=click.Choice(["md", "json"]), default="md", show_default=True)
@click.pass_context
def export(ctx, draft_id, output, fmt):
    """导出草稿到本地文件。"""
    config: ConfigManager = ctx.obj["config"]
    client = APIClient(config)
    d = client.get_draft(draft_id)
    if not d:
        console.print(f"[red]未找到草稿 {draft_id}[/red]")
        return
    if not output:
        safe_title = "".join(c for c in d["title"] if c.isalnum() or c in "-_ ")[:50]
        output = os.path.join(config.export_dir, f"{safe_title}.{fmt}")
    os.makedirs(os.path.dirname(output) if os.path.dirname(output) else ".", exist_ok=True)
    try:
        if fmt == "md":
            with open(output, "w", encoding="utf-8") as f:
                f.write(f"# {d['title']}\n\n")
                f.write(f"> 分类：{d.get('category','未分类')}  \n")
                f.write(f"> 标签：{', '.join(d.get('tags',[]))}  \n")
                f.write(f"> 字数：{d['word_count']:,} 字  \n")
                if d.get("reviewer"):
                    f.write(f"> 审阅人：{d.get('reviewer')}  \n")
                f.write("\n")
                if d.get("review_comments"):
                    f.write("## 审阅批注\n\n")
                    for c in d["review_comments"]:
                        f.write(f"- **[{c.get('reviewer','')}]** {c.get('comment','')}  \n")
                    f.write("\n---\n\n")
                if d.get("summary"):
                    f.write(f"## 摘要\n\n{d['summary']}\n\n---\n\n")
                f.write(d["content"])
        else:
            with open(output, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
        console.print(f"[green]✓ 已导出到: {output}[/green]")
    except IOError as e:
        console.print(f"[red]错误：导出失败 ({e})[/red]")


@draft.command()
@click.argument("draft_id")
@click.option("-v", "--version", type=int, required=True, help="回滚到哪个版本号")
@click.pass_context
def rollback(ctx, draft_id, version):
    """回滚草稿到指定历史版本。"""
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return
    client = APIClient(config)
    d = client.get_draft(draft_id)
    if not d:
        console.print(f"[red]未找到草稿 {draft_id}[/red]")
        return
    versions = client.get_draft_versions(draft_id)
    vmap = {v["version"]: v for v in versions}
    if version not in vmap:
        available = ", ".join(str(v["version"]) for v in versions) or "无"
        console.print(f"[red]错误：版本号 v{version} 不存在，可用：{available}[/red]")
        return
    target = vmap[version]
    if not click.confirm(
        f"即将回滚到 v{version}\n  当前: {d['title'][:40]}\n  目标: {target.get('title','')[:40]}\n"
        f"  ⚠️  当前内容会保存为新版本，确认？"
    ):
        return
    result = client.rollback_draft(draft_id, version)
    if result:
        console.print(Panel.fit(
            f"[green]✓ 已回滚到 v{version}！[/green]\n\n当前标题: {result['title']}\n当前字数: {result['word_count']:,} 字",
            title="草稿回滚", border_style="green",
        ))
