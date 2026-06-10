"""export 命令组。

提供批量导出提示词、生成个人月报等功能。
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

console = Console()


@click.group()
def export():
    """数据导出与报告。

    批量导出提示词，生成个人月报，导出社区数据。
    """
    pass


@export.command("prompts")
@click.option("-o", "--output", type=click.Path(), help="输出目录（默认: ~/.aicommunity/exports）")
@click.option("-f", "--format", "fmt",
              type=click.Choice(["json", "yaml", "markdown"]),
              default="markdown", show_default=True, help="导出格式")
@click.option("--public-only", is_flag=True, help="只导出公开的提示词")
@click.option("--favorites", "only_favorites", is_flag=True, help="只导出已收藏的提示词")
@click.option("-c", "--category", help="按分类筛选导出")
@click.option("-t", "--tag", "tag_filter", help="按标签筛选导出")
@click.pass_context
def export_prompts(ctx, output, fmt, public_only, only_favorites, category, tag_filter):
    """批量导出我的提示词。

    示例:\n
        aicomm export prompts -f markdown\n
        aicomm export prompts -o ./exports -f json -c 编程辅助\n
        aicomm export prompts --public-only --favorites -t Python
    """
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return

    output_dir = output or config.export_dir
    client = APIClient(config)

    count, filepath = client.export_prompts(
        output_dir=output_dir,
        format_type=fmt,
        only_public=public_only,
        only_favorites=only_favorites,
        category=category,
        tag=tag_filter,
    )

    if count == 0 and not filepath:
        console.print("[red]错误：不支持的导出格式[/red]")
        return

    if count == 0:
        console.print("[yellow]没有符合条件的提示词可导出[/yellow]")
        return

    file_size = os.path.getsize(filepath)
    size_str = f"{file_size / 1024:.1f} KB" if file_size < 1024 * 1024 else f"{file_size / (1024 * 1024):.1f} MB"

    filters = []
    if public_only:
        filters.append("仅公开")
    if only_favorites:
        filters.append("仅收藏")
    if category:
        filters.append(f"分类={category}")
    if tag_filter:
        filters.append(f"标签={tag_filter}")
    filter_str = f"（筛选条件：{', '.join(filters)}）" if filters else ""

    console.print()
    console.print(Panel.fit(
        f"[green]✓ 导出成功！[/green]\n\n"
        f"[cyan]导出数量:[/cyan] {count} 个提示词\n"
        f"[cyan]文件格式:[/cyan] {fmt.upper()}\n"
        f"[cyan]文件大小:[/cyan] {size_str}\n"
        f"[cyan]保存路径:[/cyan] {filepath}\n"
        f"{filter_str}",
        title="导出提示词",
        border_style="green",
    ))


@export.command("report")
@click.option("-m", "--months", type=int, default=1, show_default=True, help="统计几个月的数据")
@click.option("-o", "--output", type=click.Path(), help="输出目录（默认: ~/.aicommunity/exports）")
@click.option("-f", "--format", "fmt",
              type=click.Choice(["markdown"]),
              default="markdown", show_default=True, help="报告格式")
@click.option("--show", "show_in_console", is_flag=True, help="同时在终端中显示报告")
@click.pass_context
def monthly_report(ctx, months, output, fmt, show_in_console):
    """生成个人月报。

    统计你的发帖、提示词、互动数据，生成月度报告。

    示例:\n
        aicomm export report\n
        aicomm export report -m 3 -o ./reports --show
    """
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return

    output_dir = output or config.export_dir
    client = APIClient(config)

    filepath = client.generate_monthly_report(
        output_dir=output_dir,
        months=months,
        format_type=fmt,
    )

    if not filepath:
        console.print("[red]错误：生成报告失败[/red]")
        return

    stats = client.get_user_stats(months=months)

    total_score = (
        stats['posts']['count'] * 10 +
        stats['posts']['total_likes'] * 1 +
        stats['prompts']['count'] * 20 +
        stats['drafts']['total_words'] // 100
    )

    if total_score >= 1000:
        comment = "🎉 太棒了！你是社区的核心贡献者"
    elif total_score >= 500:
        comment = "💪 做得不错！本月表现很活跃"
    elif total_score >= 100:
        comment = "👍 稳步前进"
    else:
        comment = "🌱 下个月加油"

    console.print()
    console.print(Panel.fit(
        f"[green]✓ 月报生成成功！[/green]\n\n"
        f"[bold]📊 {stats['user']['display_name']} 的{stats['period']}报告[/bold]\n"
        f"[dim]统计周期：{stats['start_date']} ~ {stats['end_date']}[/dim]\n\n"
        f"📝 帖子发布: [cyan]{stats['posts']['count']}[/cyan] 篇 | "
        f"❤️ 点赞总计: [cyan]{stats['posts']['total_likes']:,}[/cyan]\n"
        f"✨ 提示词上传: [cyan]{stats['prompts']['count']}[/cyan] 个 | "
        f"🔧 使用次数: [cyan]{stats['prompts']['total_usage']:,}[/cyan]\n"
        f"📄 草稿活跃: [cyan]{stats['drafts']['count']}[/cyan] 篇 | "
        f"📖 写作字数: [cyan]{stats['drafts']['total_words']:,}[/cyan] 字\n"
        f"📬 收到通知: [cyan]{stats['notifications_received']}[/cyan] 条\n\n"
        f"🏆 [bold]综合活跃度得分:[/bold] [yellow]{total_score}[/yellow]\n"
        f"   {comment}\n\n"
        f"[cyan]报告已保存到:[/cyan] {filepath}",
        title="个人月报生成",
        border_style="cyan",
    ))

    if show_in_console:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            console.print()
            console.print(Panel(content, title="月报内容预览", border_style="magenta"))
        except IOError:
            pass


@export.command("stats")
@click.option("-m", "--months", type=int, default=1, show_default=True, help="统计最近几个月")
@click.pass_context
def show_stats(ctx, months):
    """在终端中显示个人统计数据。

    示例:\n
        aicomm export stats\n
        aicomm export stats -m 6
    """
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return

    client = APIClient(config)
    stats = client.get_user_stats(months=months)

    total_post_score = stats['posts']['count'] * 10 + stats['posts']['total_likes']
    total_prompt_score = stats['prompts']['count'] * 20 + stats['prompts']['total_usage'] // 100
    total_draft_score = stats['drafts']['total_words'] // 100
    total_score = total_post_score + total_prompt_score + total_draft_score

    max_val = max(
        stats['posts']['total_likes'],
        stats['prompts']['total_usage'],
        stats['drafts']['total_words'] // 10,
        1,
    )

    def make_bar(value, max_v, width=15):
        ratio = min(value / max_v, 1.0)
        filled = int(ratio * width)
        return "█" * filled + "░" * (width - filled)

    console.print()
    console.print(f"[bold]📊 个人数据统计 - 最近{months}个月[/bold]")
    console.print("═" * 60)

    overview_table = [
        ["用户", f"{stats['user']['display_name']} (@{stats['user']['username']})"],
        ["等级", f"Lv.{stats['user']['level']} | 积分: {stats['user']['points']:,}"],
        ["社交", f"关注者: {stats['followers']:,} | 正在关注: {stats['following']}"],
        ["统计周期", f"{stats['start_date']} ~ {stats['end_date']}"],
    ]
    console.print(tabulate(overview_table, tablefmt="rounded_outline"))

    console.print()
    console.print("[bold]📝 帖子数据[/bold]")
    post_table = [
        ["发布数量", stats['posts']['count'], make_bar(stats['posts']['count'] * 5, max_val)],
        ["总点赞数", f"{stats['posts']['total_likes']:,}", make_bar(stats['posts']['total_likes'], max_val)],
        ["总评论数", f"{stats['posts']['total_comments']:,}", make_bar(stats['posts']['total_comments'], max_val)],
        ["总浏览量", f"{stats['posts']['total_views']:,}", make_bar(stats['posts']['total_views'] // 10, max_val)],
        ["平均点赞", f"{stats['posts']['avg_likes']}", make_bar(int(stats['posts']['avg_likes'] * 3), max_val)],
        ["得分贡献", f"{total_post_score} 分", make_bar(total_post_score, total_score or 1, 20)],
    ]
    console.print(tabulate(post_table, headers=["指标", "数值", "分布"], tablefmt="rounded_outline"))

    console.print()
    console.print("[bold]✨ 提示词数据[/bold]")
    prompt_table = [
        ["上传数量", stats['prompts']['count'], make_bar(stats['prompts']['count'] * 10, max_val)],
        ["总使用次数", f"{stats['prompts']['total_usage']:,}", make_bar(stats['prompts']['total_usage'], max_val)],
        ["总收藏数", f"{stats['prompts']['total_favorites']:,}", make_bar(stats['prompts']['total_favorites'], max_val)],
        ["得分贡献", f"{total_prompt_score} 分", make_bar(total_prompt_score, total_score or 1, 20)],
    ]
    console.print(tabulate(prompt_table, headers=["指标", "数值", "分布"], tablefmt="rounded_outline"))

    console.print()
    console.print("[bold]📄 长文草稿数据[/bold]")
    draft_table = [
        ["活跃草稿", stats['drafts']['count'], make_bar(stats['drafts']['count'] * 5, max_val)],
        ["总字数", f"{stats['drafts']['total_words']:,} 字", make_bar(stats['drafts']['total_words'] // 10, max_val)],
        ["得分贡献", f"{total_draft_score} 分", make_bar(total_draft_score, total_score or 1, 20)],
    ]
    console.print(tabulate(draft_table, headers=["指标", "数值", "分布"], tablefmt="rounded_outline"))

    console.print()
    console.print(f"[bold yellow]🏆 综合活跃度总分: {total_score} 分[/bold yellow]")

    if total_score >= 1000:
        console.print("[green]🎉 核心贡献者级别 - 继续保持！[/green]")
    elif total_score >= 500:
        console.print("[green]💪 活跃创作者级别 - 再接再厉！[/green]")
    elif total_score >= 100:
        console.print("[blue]👍 稳步成长级别 - 继续加油！[/blue]")
    else:
        console.print("[yellow]🌱 新手起步级别 - 期待你更多内容！[/yellow]")


@export.command("activity-csv")
@click.option("-o", "--output", type=click.Path(), help="输出CSV文件路径")
@click.option("-m", "--months", type=int, default=1, help="最近几个月的数据")
@click.pass_context
def export_activity_csv(ctx, output, months):
    """导出活动数据为CSV格式（便于数据分析）。

    示例:\n
        aicomm export activity-csv -o ./my_activity.csv -m 3
    """
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    if not auth.require_login():
        return

    client = APIClient(config)
    stats = client.get_user_stats(months=months)

    if not output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = os.path.join(config.export_dir, f"activity_{timestamp}.csv")

    os.makedirs(os.path.dirname(output) if os.path.dirname(output) else ".", exist_ok=True)

    try:
        with open(output, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["指标类别", "指标名称", "数值", "统计周期", "生成时间"])

            writer.writerow(["概览", "统计周期(月)", months, stats['period'], datetime.now().isoformat()])
            writer.writerow(["概览", "起始日期", stats['start_date'], stats['period'], datetime.now().isoformat()])
            writer.writerow(["概览", "结束日期", stats['end_date'], stats['period'], datetime.now().isoformat()])
            writer.writerow(["概览", "用户等级", stats['user']['level'], stats['period'], datetime.now().isoformat()])
            writer.writerow(["概览", "用户积分", stats['user']['points'], stats['period'], datetime.now().isoformat()])
            writer.writerow(["概览", "关注者数", stats['followers'], stats['period'], datetime.now().isoformat()])
            writer.writerow(["概览", "关注数", stats['following'], stats['period'], datetime.now().isoformat()])

            writer.writerow(["帖子", "发布数量", stats['posts']['count'], stats['period'], datetime.now().isoformat()])
            writer.writerow(["帖子", "总点赞数", stats['posts']['total_likes'], stats['period'], datetime.now().isoformat()])
            writer.writerow(["帖子", "总评论数", stats['posts']['total_comments'], stats['period'], datetime.now().isoformat()])
            writer.writerow(["帖子", "总浏览量", stats['posts']['total_views'], stats['period'], datetime.now().isoformat()])
            writer.writerow(["帖子", "平均点赞", stats['posts']['avg_likes'], stats['period'], datetime.now().isoformat()])

            writer.writerow(["提示词", "上传数量", stats['prompts']['count'], stats['period'], datetime.now().isoformat()])
            writer.writerow(["提示词", "总使用次数", stats['prompts']['total_usage'], stats['period'], datetime.now().isoformat()])
            writer.writerow(["提示词", "总收藏数", stats['prompts']['total_favorites'], stats['period'], datetime.now().isoformat()])

            writer.writerow(["草稿", "活跃草稿数", stats['drafts']['count'], stats['period'], datetime.now().isoformat()])
            writer.writerow(["草稿", "总写作字数", stats['drafts']['total_words'], stats['period'], datetime.now().isoformat()])

            writer.writerow(["互动", "收到通知数", stats['notifications_received'], stats['period'], datetime.now().isoformat()])

        file_size = os.path.getsize(output)
        console.print(f"[green]✓ CSV数据已导出到: {output}[/green]")
        console.print(f"[dim]文件大小: {file_size / 1024:.1f} KB[/dim]")
    except IOError as e:
        console.print(f"[red]错误：导出失败 ({e})[/red]")
