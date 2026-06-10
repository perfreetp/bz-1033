"""AI交流社区命令行工具 - 主入口。

提供 login、post、draft、prompt、search、follow、notify、export 8个命令组，
支持账号登录、发布短帖、提交长文草稿、上传提示词、查看版本记录、
搜索话题、筛选高赞案例、关注作者、列出通知、回复评论、收藏内容、
批量导出提示词、生成个人月报、检查违规词、同步本地草稿和查看社区活动。

使用方法:
    aicomm --help              查看所有命令
    aicomm login demo-accounts  查看演示账号
    aicomm <命令> --help        查看具体命令帮助
"""

import sys
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .config import ConfigManager

from .commands.login import login as login_group
from .commands.post import post as post_group
from .commands.draft import draft as draft_group
from .commands.prompt import prompt as prompt_group
from .commands.search import search as search_group
from .commands.follow import follow as follow_group
from .commands.notify import notify as notify_group
from .commands.export import export as export_group
from .commands.backup import backup as backup_group

console = Console()


class AicommCli(click.Group):
    """自定义命令组，美化帮助信息。"""

    def format_help(self, ctx, formatter):
        self.format_usage(ctx, formatter)
        self.format_help_text(ctx, formatter)
        self.format_options(ctx, formatter)

        commands_info = [
            ("login", "账号登录与认证管理", "登录、登出、状态查看、演示账号"),
            ("post", "短帖发布与管理", "发布短帖、浏览列表、查看详情与版本、点赞"),
            ("draft", "长文草稿管理", "创建/编辑草稿、提交审核、本地同步与导出"),
            ("prompt", "提示词广场管理", "上传/浏览提示词、违规词检查、收藏管理"),
            ("search", "搜索与发现", "内容搜索、热门话题、高赞案例、作者搜索"),
            ("follow", "关注与社区动态", "关注作者、时间线、用户活动、推荐作者"),
            ("notify", "通知与互动", "消息通知、回复评论、收藏内容管理"),
            ("export", "数据导出与报告", "批量导出提示词、个人月报、统计分析、操作审计"),
            ("backup", "离线备份与恢复", "手动备份、列表查看、备份概要、回滚恢复"),
        ]

        console.print()
        console.print(Panel.fit(
            f"[bold]欢迎使用 AI Community CLI v{__version__}[/bold]\n\n"
            f"[dim]重度AI社区用户的终端内容管理工具[/dim]\n\n"
            f"[cyan]快速开始:[/cyan]\n"
            f"  1. [green]aicomm login demo-accounts[/green]   查看演示账号\n"
            f"  2. [green]aicomm login signin[/green]          登录账号\n"
            f"  3. [green]aicomm post list[/green]             浏览社区动态\n"
            f"  4. [green]aicomm <命令> --help[/green]         查看命令详情",
            title="🤖 AI Community CLI",
            border_style="cyan",
        ))

        table = Table(title="可用命令", show_lines=True, border_style="green")
        table.add_column("命令", style="bold magenta", width=10)
        table.add_column("功能描述", style="bold", width=24)
        table.add_column("子命令示例", style="dim", width=40)

        for cmd, desc, examples in commands_info:
            table.add_row(cmd, desc, examples)

        console.print()
        console.print(table)

        console.print()
        console.print(Panel.fit(
            f"[cyan]配置目录:[/cyan] {ctx.obj['config'].config_dir if ctx.obj else '~/.aicommunity'}\n"
            f"[cyan]本地草稿:[/cyan] {ctx.obj['config'].drafts_dir if ctx.obj else '~/.aicommunity/drafts'}\n"
            f"[cyan]导出目录:[/cyan] {ctx.obj['config'].export_dir if ctx.obj else '~/.aicommunity/exports'}\n\n"
            f"[dim]💡 所有数据均支持本地持久化存储[/dim]",
            title="📁 数据存储位置",
            border_style="blue",
        ))

    def invoke(self, ctx):
        ctx.ensure_object(dict)
        if "config" not in ctx.obj:
            try:
                ctx.obj["config"] = ConfigManager()
            except Exception as e:
                console.print(f"[red]错误：初始化配置失败 ({e})[/red]")
                sys.exit(1)
        return super().invoke(ctx)


@click.group(cls=AicommCli, invoke_without_command=True)
@click.version_option(version=__version__, prog_name="aicomm", message="%(prog)s v%(version)s")
@click.option("--config-dir", type=click.Path(), help="自定义配置目录路径")
@click.option("-v", "--verbose", is_flag=True, help="启用详细输出模式")
@click.pass_context
def cli(ctx, config_dir, verbose):
    """AI交流社区命令行工具 (aicomm)。

    重度AI社区用户的终端内容管理助手，提供8大功能模块。

    使用 [cyan]aicomm <命令> --help[/cyan] 查看每个命令的详细用法。
    """
    ctx.ensure_object(dict)
    if config_dir:
        ctx.obj["config"] = ConfigManager(config_dir=config_dir)
    elif "config" not in ctx.obj:
        ctx.obj["config"] = ConfigManager()

    ctx.obj["verbose"] = verbose

    if verbose:
        config: ConfigManager = ctx.obj["config"]
        console.print(f"[dim]📌 配置目录: {config.config_dir}[/dim]")
        console.print(f"[dim]📌 登录状态: {'已登录' if config.is_logged_in() else '未登录'}[/dim]")

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


cli.add_command(login_group)
cli.add_command(post_group)
cli.add_command(draft_group)
cli.add_command(prompt_group)
cli.add_command(search_group)
cli.add_command(follow_group)
cli.add_command(notify_group)
cli.add_command(export_group)
cli.add_command(backup_group)


def main():
    """程序入口函数。"""
    try:
        cli(obj={})
    except KeyboardInterrupt:
        console.print("\n[yellow]操作已取消[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print("\n[red]发生错误: [/red]", end="")
        console.print(str(e), markup=False)
        console.print("[dim]使用 --verbose 查看详细错误信息[/dim]")
        import traceback
        if "--verbose" in sys.argv or "-v" in sys.argv:
            console.print(traceback.format_exc(), markup=False)
        sys.exit(1)


if __name__ == "__main__":
    main()
