"""search 命令组。

提供搜索话题、筛选高赞案例等功能。
"""

import click
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from tabulate import tabulate

from ..config import ConfigManager
from ..api_client import APIClient
from .post import _format_time

console = Console()

CONTENT_TYPE_LABELS = {
    "all": "全部",
    "posts": "短帖",
    "prompts": "提示词",
    "drafts": "草稿",
}

TYPE_ICONS = {
    "post": "📝",
    "prompt": "✨",
    "draft": "📄",
}


@click.group()
def search():
    """搜索社区内容。

    搜索帖子、提示词、草稿，支持高赞筛选和话题标签。
    """
    pass


@search.command()
@click.argument("query")
@click.option("-t", "--type", "content_type",
              type=click.Choice(["all", "posts", "prompts", "drafts"]),
              default="all", show_default=True, help="内容类型")
@click.option("-l", "--min-likes", type=int, default=0, show_default=True, help="最小点赞/收藏数（高赞筛选）")
@click.option("--tag", "tag_filter", help="按话题标签筛选")
@click.option("-p", "--page", type=int, default=1, show_default=True, help="页码")
@click.option("-s", "--size", type=int, default=15, show_default=True, help="每页数量")
@click.option("--top", "top_n", type=int, help="直接显示Top N条结果（跳过分页）")
@click.pass_context
def find(ctx, query, content_type, min_likes, tag_filter, page, size, top_n):
    """搜索社区内容。

    示例:\n
        aicomm search find "AI应用"\n
        aicomm search find "Prompt" -t prompts -l 100\n
        aicomm search find "学习" --tag AI应用 --top 10
    """
    config: ConfigManager = ctx.obj["config"]
    client = APIClient(config)

    if top_n:
        page = 1
        size = top_n

    results, total = client.search(
        query=query,
        content_type=content_type,
        min_likes=min_likes,
        tag=tag_filter,
        page=page,
        page_size=size,
    )

    if not results:
        filter_desc = []
        if min_likes > 0:
            filter_desc.append(f"点赞≥{min_likes}")
        if tag_filter:
            filter_desc.append(f"标签={tag_filter}")
        extra = f" ({', '.join(filter_desc)})" if filter_desc else ""

        console.print(Panel.fit(
            f"[yellow]未找到与「{query}」相关的{CONTENT_TYPE_LABELS[content_type]}内容[/yellow]\n"
            f"[dim]尝试减少筛选条件或更换关键词{extra}[/dim]",
            title="搜索结果",
            border_style="yellow",
        ))
        return

    type_count = {}
    for r in results:
        t = r.get("_type", "unknown")
        type_count[t] = type_count.get(t, 0) + 1

    type_summary = " | ".join(f"{TYPE_ICONS.get(t, '❓')} {CONTENT_TYPE_LABELS.get(t + 's', t)} {c}" for t, c in type_count.items())

    table_data = []
    for i, r in enumerate(results, 1):
        ctype = r.get("_type", "unknown")
        icon = TYPE_ICONS.get(ctype, "❓")
        if ctype == "post":
            title = r["content"][:50] + ("..." if len(r["content"]) > 50 else "")
            author = r.get("author_name", r.get("author", ""))
            extra = f"💬{r['comments']:,}"
        elif ctype == "prompt":
            title = r.get("title", "(无标题)")
            author = r.get("author_name", r.get("author", ""))
            extra = f"★{r.get('rating', 0)}"
        else:
            title = r.get("title", "(无标题)")
            author = r.get("author", "")
            extra = f"{r.get('word_count', 0):,}字"

        table_data.append({
            "#": i,
            "类型": f"{icon} {CONTENT_TYPE_LABELS.get(ctype + 's', ctype)}",
            "标题/摘要": title,
            "作者": author,
            "❤️/收藏": f"{r.get('likes', 0):,}",
            "附加信息": extra,
            "标签": ", ".join("#" + t for t in r.get("tags", []))[:20],
            "时间": _format_time(r.get("created_at", "")),
        })

    console.print()
    console.print(Panel.fit(
        f"[bold]🔍 关键词：[/bold]「{query}」    "
        f"[bold]类型：[/bold]{CONTENT_TYPE_LABELS[content_type]}    "
        f"[bold]共找到：[/bold]{total} 条\n"
        f"[dim]类型分布：{type_summary}[/dim]\n\n" +
        tabulate(table_data, headers="keys", tablefmt="rounded_outline"),
        title=f"搜索结果（第 {page} 页）",
        border_style="blue",
    ))

    if not top_n and total > page * size:
        console.print(f"\n[dim]💡 下一页: aicomm search find \"{query}\" -p {page + 1}[/dim]")


@search.command("topics")
@click.option("-l", "--min-likes", type=int, default=50, show_default=True, help="话题最小累计点赞数")
@click.option("-s", "--sort", "sort_by", type=click.Choice(["likes", "count", "trending"]),
              default="trending", show_default=True, help="排序方式")
@click.option("--top", type=int, default=15, show_default=True, help="显示前N个话题")
@click.pass_context
def hot_topics(ctx, min_likes, sort_by, top):
    """浏览热门话题标签。

    示例:\n
        aicomm search topics\n
        aicomm search topics -l 100 --sort likes --top 20
    """
    config: ConfigManager = ctx.obj["config"]
    client = APIClient(config)

    tag_stats = {}

    posts, _ = client.list_posts(page=1, page_size=100)
    for p in posts:
        for tag in p.get("tags", []):
            if tag not in tag_stats:
                tag_stats[tag] = {"count": 0, "likes": 0, "posts": 0, "prompts": 0}
            tag_stats[tag]["count"] += 1
            tag_stats[tag]["posts"] += 1
            tag_stats[tag]["likes"] += p.get("likes", 0)

    prompts, _ = client.list_prompts(page=1, page_size=100)
    for p in prompts:
        for tag in p.get("tags", []):
            if tag not in tag_stats:
                tag_stats[tag] = {"count": 0, "likes": 0, "posts": 0, "prompts": 0}
            tag_stats[tag]["count"] += 1
            tag_stats[tag]["prompts"] += 1
            tag_stats[tag]["likes"] += p.get("favorites", 0)

    filtered_tags = {k: v for k, v in tag_stats.items() if v["likes"] >= min_likes}

    if not filtered_tags:
        console.print(f"[yellow]暂无达到最小点赞数（≥{min_likes}）的话题标签[/yellow]")
        return

    if sort_by == "likes":
        sorted_tags = sorted(filtered_tags.items(), key=lambda x: x[1]["likes"], reverse=True)
    elif sort_by == "count":
        sorted_tags = sorted(filtered_tags.items(), key=lambda x: x[1]["count"], reverse=True)
    else:
        sorted_tags = sorted(filtered_tags.items(),
                             key=lambda x: x[1]["likes"] * 2 + x[1]["count"] * 5, reverse=True)

    top_tags = sorted_tags[:top]

    max_likes = max(v["likes"] for _, v in top_tags) if top_tags else 1

    table_data = []
    for i, (tag, stats) in enumerate(top_tags, 1):
        bar_len = int(stats["likes"] / max_likes * 20)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        rank_icon = ["🥇", "🥈", "🥉"][i - 1] if i <= 3 else f"  {i}."

        table_data.append({
            "排名": rank_icon,
            "话题": f"#{tag}",
            "热度": f"{bar} {stats['likes']:,}",
            "内容数": f"{stats['count']} 条",
            "短帖": f"{stats['posts']}",
            "提示词": f"{stats['prompts']}",
            "热度值": f"{stats['likes'] * 2 + stats['count'] * 5}",
        })

    console.print()
    console.print(Panel.fit(
        tabulate(table_data, headers="keys", tablefmt="rounded_outline"),
        title=f"🔥 热门话题榜 Top {len(top_tags)}（排序：{sort_by}）",
        border_style="red",
    ))


@search.command("hot")
@click.option("-t", "--type", "content_type",
              type=click.Choice(["posts", "prompts"]),
              default="posts", show_default=True, help="内容类型")
@click.option("-l", "--min-likes", type=int, default=100, show_default=True, help="最小点赞/收藏数（高赞案例）")
@click.option("--top", type=int, default=10, show_default=True, help="显示前N条")
@click.pass_context
def hot_content(ctx, content_type, min_likes, top):
    """查看高赞案例排行榜。

    示例:\n
        aicomm search hot -t posts -l 500 --top 10\n
        aicomm search hot -t prompts
    """
    config: ConfigManager = ctx.obj["config"]
    client = APIClient(config)

    if content_type == "posts":
        items, _ = client.list_posts(page=1, page_size=100)
        items = [item for item in items if item.get("likes", 0) >= min_likes]
        items.sort(key=lambda x: x.get("likes", 0), reverse=True)
        items = items[:top]
        unit_label = "点赞"
    else:
        items, _ = client.list_prompts(page=1, page_size=100, sort_by="favorites")
        items = [item for item in items if item.get("favorites", 0) >= min_likes]
        items.sort(key=lambda x: x.get("favorites", 0), reverse=True)
        items = items[:top]
        unit_label = "收藏"

    if not items:
        console.print(f"[yellow]暂无{min_likes}{unit_label}以上的高赞{CONTENT_TYPE_LABELS[content_type]}[/yellow]")
        return

    max_value = max(item.get("likes" if content_type == "posts" else "favorites", 0) for item in items)

    table_data = []
    for i, item in enumerate(items, 1):
        value = item.get("likes" if content_type == "posts" else "favorites", 0)
        bar_len = int(value / max_value * 15)
        bar = "█" * bar_len + "░" * (15 - bar_len)
        rank_icon = ["🥇", "🥈", "🥉"][i - 1] if i <= 3 else f"  {i}."

        if content_type == "posts":
            title = item["content"][:40] + ("..." if len(item["content"]) > 40 else "")
            author = item.get("author_name", item.get("author", ""))
            extra_info = f"💬{item.get('comments', 0)} 👁️{item.get('views', 0):,}"
        else:
            title = item.get("title", "(无标题)")
            author = item.get("author_name", item.get("author", ""))
            extra_info = f"★{item.get('rating', 0)} 使用{item.get('usage_count', 0):,}"

        table_data.append({
            "排名": rank_icon,
            "ID": item["id"],
            "标题/摘要": title,
            "作者": author,
            f"{unit_label}": f"{bar} {value:,}",
            "附加": extra_info,
        })

    type_name = "短帖" if content_type == "posts" else "提示词"
    console.print()
    console.print(Panel.fit(
        tabulate(table_data, headers="keys", tablefmt="rounded_outline"),
        title=f"🏆 高赞{type_name}榜 Top {len(items)}（{unit_label}≥{min_likes}）",
        border_style="yellow",
    ))


@search.command("author")
@click.argument("author_name")
@click.option("-l", "--min-likes", type=int, default=0, help="最小点赞数")
@click.option("-p", "--page", type=int, default=1, show_default=True, help="页码")
@click.pass_context
def by_author(ctx, author_name, min_likes, page):
    """按作者搜索内容。

    示例:\n
        aicomm search author admin\n
        aicomm search author writer -l 500
    """
    config: ConfigManager = ctx.obj["config"]
    client = APIClient(config)

    posts, p_total = client.list_posts(page=page, page_size=10, author=author_name)
    posts = [p for p in posts if p.get("likes", 0) >= min_likes]

    prompts, _ = client.list_prompts(page=1, page_size=100)
    prompts = [p for p in prompts if p.get("author") == author_name and p.get("favorites", 0) >= min_likes]

    if not posts and not prompts:
        console.print(f"[yellow]未找到作者「{author_name}」的内容[/yellow]")
        return

    from .auth import get_user_info
    user = get_user_info(author_name)
    if user:
        console.print()
        console.print(Panel.fit(
            f"{user.get('avatar', '👤')} [bold]{user.get('display_name', author_name)}[/bold] (@{author_name})\n"
            f"[dim]{user.get('bio', '')}[/dim]\n"
            f"等级: Lv.{user.get('level', 0)} | 积分: {user.get('points', 0):,} | "
            f"关注者: {user.get('followers', 0):,} | 关注: {user.get('following', 0)}",
            title="👤 作者信息",
            border_style="cyan",
        ))

    if posts:
        table_data = []
        for p in posts:
            table_data.append({
                "ID": p["id"],
                "内容": p["content"][:40] + ("..." if len(p["content"]) > 40 else ""),
                "标签": ", ".join("#" + t for t in p.get("tags", []))[:20],
                "❤️": f"{p['likes']:,}",
                "💬": f"{p['comments']:,}",
                "时间": _format_time(p["created_at"]),
            })
        console.print(Panel.fit(
            tabulate(table_data, headers="keys", tablefmt="rounded_outline"),
            title=f"📝 {author_name} 的短帖（{len(posts)} 条）",
            border_style="green",
        ))

    if prompts:
        table_data = []
        for p in prompts:
            table_data.append({
                "ID": p["id"],
                "标题": p["title"][:30],
                "分类": p.get("category", ""),
                "评分": f"★{p.get('rating', 0)}",
                "收藏": f"{p.get('favorites', 0):,}",
                "使用": f"{p.get('usage_count', 0):,}",
            })
        console.print(Panel.fit(
            tabulate(table_data, headers="keys", tablefmt="rounded_outline"),
            title=f"✨ {author_name} 的提示词（{len(prompts)} 个）",
            border_style="magenta",
        ))
