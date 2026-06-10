"""backup 命令组。

离线数据备份管理：手动备份、列表、详情、回滚。
"""

import click
import os
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from tabulate import tabulate

from ..config import ConfigManager
from ..auth import AuthManager
from ..api_client import APIClient

console = Console()


@click.group()
def backup():
    """离线数据备份与恢复。

    创建手动备份、列出备份、查看备份概要、回滚到指定备份。
    每次升级前会自动备份，恢复前也会自动生成即时备份，可回退。
    """
    pass


@backup.command("create")
@click.option("-r", "--reason", help="备份原因/备注", default="手动备份")
@click.pass_context
def create_backup(ctx, reason):
    """手动创建离线数据备份。

    示例:\n
        aicomm backup create\n
        aicomm backup create -r "升级前备份"
    """
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return

    client = APIClient(config)
    ok, key, msg = client.create_backup(reason)
    if ok:
        console.print()
        console.print(Panel.fit(
            f"[green]✓ {msg}[/green]\n\n"
            f"[cyan]备份Key:[/cyan] {key}\n"
            f"[cyan]原因:[/cyan] {reason}\n"
            f"[cyan]时间:[/cyan] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"[dim]💡 查看备份: aicomm backup show {key}[/dim]\n"
            f"[dim]💡 回滚到备份: aicomm backup restore {key}[/dim]",
            title="创建备份", border_style="green",
        ))
    else:
        console.print(f"[red]✗ 创建失败[/red]")


@backup.command("list")
@click.pass_context
def list_backups(ctx):
    """列出所有备份条目。

    包括：用户手动备份、升级v1→v2迁移备份、恢复前自动备份。
    """
    config: ConfigManager = ctx.obj["config"]
    client = APIClient(config)
    backups = client.list_backups()

    if not backups:
        console.print("[yellow]暂无备份，执行 aicomm backup create 手动创建[/yellow]")
        return

    table_data = []
    for i, b in enumerate(backups, 1):
        created = b["created_at"][:16].replace("T", " ") if b["created_at"] != "N/A" else "N/A"
        backup_type = "手动" if b["key"].startswith("backup_") and "pre_restore" not in b["key"] else (
            "恢复前" if "pre_restore" in b["key"] else "迁移"
        )
        type_icon = {"手动": "🖐️", "恢复前": "🛡️", "迁移": "🔄"}.get(backup_type, "❓")
        table_data.append({
            "#": i,
            "备份Key": b["key"][:32] + ("..." if len(b["key"]) > 32 else ""),
            "类型": type_icon + " " + backup_type,
            "创建人": b.get("created_by", "system"),
            "帖子/草稿/提示词": f"{b['posts_count']}/{b['drafts_count']}/{b['prompts_count']}",
            "原因": (b.get("reason", "")[:30]),
            "Schema": b.get("schema", "?"),
            "创建时间": created,
        })

    console.print()
    console.print(Panel.fit(
        tabulate(table_data, headers="keys", tablefmt="rounded_outline"),
        title=f"备份列表（共 {len(backups)} 个）",
        border_style="cyan",
    ))


@backup.command("show")
@click.argument("backup_key")
@click.pass_context
def show_backup(ctx, backup_key):
    """查看指定备份的详细信息。

    示例:\n
        aicomm backup show backup_20260610_xxx_writer
    """
    config: ConfigManager = ctx.obj["config"]
    client = APIClient(config)
    info = client.get_backup_info(backup_key)
    if info is None:
        console.print(f"[red]未找到备份: {backup_key}[/red]")
        return

    meta = info["meta"]
    backup_type = "手动备份" if backup_key.startswith("backup_") and "pre_restore" not in backup_key else (
        "恢复前自动备份" if "pre_restore" in backup_key else "v1→v2迁移备份"
    )
    t = Table(title=f"备份详情 - {backup_key}", header_style="bold cyan",
              show_lines=False, border_style="cyan")
    t.add_column("项目", style="bold", width=20)
    t.add_column("内容", overflow="fold")
    t.add_row("备份类型", backup_type)
    t.add_row("创建人", meta.get("created_by", "system"))
    t.add_row("创建时间", meta.get("created_at", "N/A"))
    t.add_row("Schema版本", meta.get("schema_version", "?"))
    t.add_row("原因/备注", meta.get("reason", "无"))
    t.add_row("帖子数", str(info["posts_count"]))
    t.add_row("草稿数", str(info["drafts_count"]))
    t.add_row("提示词数", str(info["prompts_count"]))
    t.add_row("通知数", str(info.get("notifications_count", 0)))
    t.add_row("审计日志数", str(info.get("audit_logs_count", 0)))
    t.add_row("Profile用户", ", ".join(info.get("user_profiles", [])) or "(无)")
    console.print()
    console.print(t)


@backup.command("restore")
@click.argument("backup_key")
@click.option("-y", "--yes", is_flag=True, help="跳过确认")
@click.pass_context
def restore_backup(ctx, backup_key, yes):
    """回滚到指定备份（恢复前自动备份当前状态，可回退）。

    ⚠️  会覆盖当前所有离线数据，但执行前会自动生成一个 pre_restore 备份，可回滚。

    示例:\n
        aicomm backup restore backup_20260610_xxx_writer
    """
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return

    client = APIClient(config)
    info = client.get_backup_info(backup_key)
    if info is None:
        console.print(f"[red]未找到备份: {backup_key}[/red]")
        return

    if not yes:
        console.print()
        console.print(Panel.fit(
            f"[yellow]⚠️  即将恢复备份：[/yellow]\n\n"
            f"[cyan]备份Key:[/cyan] {backup_key}\n"
            f"[cyan]创建时间:[/cyan] {info['meta'].get('created_at','N/A')}\n"
            f"[cyan]帖子/草稿/提示词:[/cyan] {info['posts_count']}/{info['drafts_count']}/{info['prompts_count']}\n"
            f"[cyan]Profile用户:[/cyan] {', '.join(info.get('user_profiles', [])) or '(无)'}\n\n"
            f"[dim]💡 执行前会自动备份当前状态[/dim]\n"
            f"[dim]💡 恢复后立即重启终端保证内存状态刷新[/dim]\n\n"
            "[red]⚠️  当前所有离线数据将被覆盖！[/red]",
            title="恢复确认", border_style="yellow",
        ))
        if not click.confirm("确认恢复？输入 y 继续"):
            return

    ok, msg = client.restore_backup(backup_key)
    if ok:
        console.print()
        console.print(Panel.fit(
            f"[green]✓ {msg}[/green]\n\n"
            f"[cyan]备份Key:[/cyan] {backup_key}\n\n"
            f"[dim]💡 建议重启终端，重新登录确保内存状态与磁盘一致[/dim]\n"
            f"[dim]💡 如需撤销此次恢复：restore <恢复前备份key>[/dim]",
            title="恢复成功", border_style="green",
        ))
    else:
        console.print(f"[red]✗ {msg}[/red]")
