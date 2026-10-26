"""double11-list CLI：add / list / price / budget / export / remove / remind。

价格全部手动录入：本工具不登录任何平台、不爬取价格页。
"""
from __future__ import annotations

import csv
import io
from decimal import Decimal
from pathlib import Path

import typer

from .calc import estimate, fmt_money
from .remind import budget_status, daily_remind
from .store import Item, Store, to_decimal

app = typer.Typer(help="双11比价清单：手动录价、叠券实付计算、预算提醒（数据全在本地）")


def _store() -> Store:
    return Store()


@app.command()
def add(
    name: str = typer.Argument(..., help="商品名"),
    platform: str = typer.Option("", "--platform", help="平台，如 抖音商城/京东/天猫"),
    daily: str = typer.Option("", "--daily", help="日常价（实付计算基准）"),
    target: str = typer.Option("", "--target", help="目标价（到了标绿）"),
    cut: str = typer.Option("0", "--cut", help="立减金额"),
    platform_coupon: str = typer.Option("0", "--platform-coupon", help="平台券金额"),
    shop_coupon: str = typer.Option("0", "--shop-coupon", help="店铺券金额"),
) -> None:
    """往清单里加一件商品。"""
    store = _store()
    item = Item(
        name=name,
        platform=platform,
        daily_price=to_decimal(daily),
        target_price=to_decimal(target),
        cut=to_decimal(cut) or Decimal("0"),
        platform_coupon=to_decimal(platform_coupon) or Decimal("0"),
        shop_coupon=to_decimal(shop_coupon) or Decimal("0"),
    )
    item_id = store.add_item(item)
    result = estimate(item)
    typer.echo(f"已添加 #{item_id} {name}，预估实付 {fmt_money(result.payable)}")
    store.close()


@app.command("list")
def list_items() -> None:
    """列出清单和每件的预估实付。"""
    store = _store()
    items = store.list_items()
    if not items:
        typer.echo("清单是空的，先用 add 加商品。")
        store.close()
        return
    for it in items:
        result = estimate(it)
        mark = "【已达目标价】" if result.reached_target else ""
        typer.echo(
            f"#{it.id} {it.name}（{it.platform or '未填平台'}）"
            f" 日常价 {fmt_money(it.daily_price)} → 预估实付 {fmt_money(result.payable)}{mark}"
        )
    budget, total, over = budget_status(store)
    typer.echo(f"合计（可计算部分）：{fmt_money(total)}")
    if budget is not None:
        typer.echo(f"预算：{fmt_money(budget)}" + ("【已超预算】" if over else ""))
    store.close()


@app.command()
def price(item_id: int = typer.Argument(..., help="商品编号（list 里 # 后面的数字）")) -> None:
    """看一件商品的实付计算明细。"""
    store = _store()
    item = store.get_item(item_id)
    if item is None:
        typer.echo(f"没有 #{item_id} 这件商品。")
        raise typer.Exit(code=1)
    result = estimate(item)
    typer.echo(f"{item.name}（{item.platform or '未填平台'}）")
    typer.echo(f"  日常价：{fmt_money(item.daily_price)}")
    typer.echo(f"  立减：-{fmt_money(item.cut)}　平台券：-{fmt_money(item.platform_coupon)}　店铺券：-{fmt_money(item.shop_coupon)}")
    if result.payable is None:
        typer.echo(f"  预估实付：【待核实】（缺 {'、'.join(result.missing)}）")
    else:
        typer.echo(f"  预估实付：{fmt_money(result.payable)}（预估值，最终以结算页为准）")
    if item.target_price is not None:
        typer.echo(f"  目标价：{fmt_money(item.target_price)}　{'已达到' if result.reached_target else '还没到'}")
    store.close()


@app.command()
def budget(amount: str = typer.Argument("", help="总预算金额；不填只查看")) -> None:
    """设置或查看总预算。"""
    store = _store()
    if amount:
        value = to_decimal(amount)
        if value is None:
            typer.echo("预算金额不对，请输入数字。")
            raise typer.Exit(code=1)
        store.set_meta("budget", str(value))
        typer.echo(f"总预算已设为 {fmt_money(value)}")
    current, total, over = budget_status(store)
    if current is None:
        typer.echo("还没设总预算。")
    else:
        typer.echo(f"当前清单预估合计 {fmt_money(total)} / 预算 {fmt_money(current)}" + ("【已超预算】" if over else ""))
    store.close()


@app.command()
def export(
    fmt: str = typer.Option("md", "--format", help="md 或 csv"),
    out: str = typer.Option("", "--out", help="输出文件路径；不填直接打印"),
) -> None:
    """把清单导出为 Markdown 或 CSV，对着手机逐项下单核对。"""
    store = _store()
    items = store.list_items()
    if fmt == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["编号", "商品", "平台", "日常价", "立减", "平台券", "店铺券", "预估实付", "目标价", "状态"])
        for it in items:
            r = estimate(it)
            status = "已达目标价" if r.reached_target else ("待核实" if r.payable is None else "")
            writer.writerow([it.id, it.name, it.platform, it.daily_price or "", it.cut, it.platform_coupon, it.shop_coupon, r.payable if r.payable is not None else "待核实", it.target_price or "", status])
        content = buf.getvalue()
    else:
        lines = ["# 双11购物清单", "", "| 编号 | 商品 | 平台 | 日常价 | 预估实付 | 目标价 | 状态 |", "|---|---|---|---|---|---|---|"]
        for it in items:
            r = estimate(it)
            status = "已达目标价" if r.reached_target else ("【待核实】" if r.payable is None else "")
            lines.append(f"| {it.id} | {it.name} | {it.platform or '-'} | {fmt_money(it.daily_price)} | {fmt_money(r.payable)} | {fmt_money(it.target_price)} | {status} |")
        lines.append("")
        lines.append("预估实付 = 日常价 − 立减 − 平台券 − 店铺券，只是预估，最终以结算页为准。")
        content = "\n".join(lines) + "\n"
    if out:
        Path(out).write_text(content, encoding="utf-8")
        typer.echo(f"已导出到 {out}")
    else:
        typer.echo(content)
    store.close()


@app.command()
def remove(item_id: int = typer.Argument(..., help="要删除的商品编号")) -> None:
    """从清单删除一件商品。"""
    store = _store()
    if store.remove_item(item_id):
        typer.echo(f"已删除 #{item_id}")
    else:
        typer.echo(f"没有 #{item_id} 这件商品。")
        raise typer.Exit(code=1)
    store.close()


@app.command()
def remind() -> None:
    """每日提醒（每天最多一次）：达标商品 + 预算状态。"""
    store = _store()
    typer.echo(daily_remind(store))
    store.close()


if __name__ == "__main__":
    app()
