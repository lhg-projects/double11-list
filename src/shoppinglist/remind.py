"""每日提醒：每天最多提醒一次，内容只报清单状态（达标 + 预算）。"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from .calc import estimate, fmt_money
from .store import Store


def budget_status(store: Store) -> tuple[Decimal | None, Decimal, bool | None]:
    """返回 (预算, 已知实付合计, 是否超预算)。预算未设时第一项为 None。"""
    total = Decimal("0")
    for item in store.list_items():
        result = estimate(item)
        if result.payable is not None:
            total += result.payable
    raw = store.get_meta("budget")
    if raw is None:
        return None, total, None
    budget = Decimal(raw)
    return budget, total, total > budget


def daily_remind(store: Store, today: date | None = None) -> str:
    today = today or date.today()
    today_str = today.isoformat()
    if store.get_meta("last_remind") == today_str:
        return f"今天（{today_str}）已经提醒过了，每天只提醒一次。"

    items = store.list_items()
    lines = [f"双11清单每日提醒（{today_str}）：共 {len(items)} 件"]
    reached = [it for it in items if estimate(it).reached_target]
    if reached:
        lines.append("已达到目标价，可以下手：")
        for it in reached:
            lines.append(f"  - {it.name}：预估实付 {fmt_money(estimate(it).payable)}（目标 {fmt_money(it.target_price)}）")
    else:
        lines.append("还没有商品达到目标价。")
    budget, total, over = budget_status(store)
    if budget is not None:
        flag = "，已超预算！" if over else ""
        lines.append(f"预算 {fmt_money(budget)}，当前清单预估合计 {fmt_money(total)}{flag}")
    store.set_meta("last_remind", today_str)
    return "\n".join(lines)
