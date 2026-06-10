"""login 命令组。

提供账号登录、登出、查看状态、演示账号列表等功能。
"""

import click
from rich.console import Console
from rich.panel import Panel
from tabulate import tabulate

from ..config import ConfigManager
from ..auth import AuthManager

console = Console()


@click.group()
def login():
    """账号登录与认证管理。

    管理你的AI社区账号，包括登录、登出、查看状态等功能。
    """
    pass


@login.command()
@click.option("-u", "--username", help="用户名，也可以不填通过交互输入")
@click.option("-p", "--password", help="密码，建议通过交互方式输入更安全")
@click.pass_context
def signin(ctx, username, password):
    """登录AI社区账号。

    使用用户名和密码登录社区。如果不提供参数，将进入交互模式。

    示例:\n
        aicomm login signin -u admin -p admin123\n
        aicomm login signin
    """
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)

    if not username:
        username = click.prompt("请输入用户名", type=str)
    if not password:
        password = click.prompt("请输入密码", type=str, hide_input=True)

    auth.login(username, password)


@login.command()
@click.pass_context
def logout(ctx):
    """退出当前登录账号。"""
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    auth.logout()


@login.command()
@click.pass_context
def status(ctx):
    """查看当前登录状态和用户信息。"""
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    auth.status()


@login.command("demo-accounts")
@click.pass_context
def demo_accounts(ctx):
    """列出可用的演示账号（测试用）。"""
    config: ConfigManager = ctx.obj["config"]
    auth = AuthManager(config)
    auth.list_demo_accounts()
    console.print()
    console.print("[dim]💡 提示：使用 aicomm login signin -u <用户名> -p <密码> 登录[/dim]")
