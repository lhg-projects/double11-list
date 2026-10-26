"""实付计算：实付 = 日常价 - 立减 - 平台券 - 店铺券。

算不出的项标【待核实】，绝不硬算：没有日常价就无法估算实付。
实付只是预估，最终以平台结算页为准。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from .store import Item


@dataclass
class PriceResult:
    payable: Decimal | None
    missing: list[str] = field(default_factory=list)
    reached_target: bool | None = None


def estimate(item: Item) -> PriceResult:
    missing: list[str] = []
    if item.daily_price is None:
        missing.append("日常价")
    if missing:
        return PriceResult(payable=None, missing=missing, reached_target=None)

    payable = item.daily_price - item.cut - item.platform_coupon - item.shop_coupon
    if payable < 0:
        payable = Decimal("0")

    reached: bool | None = None
    if item.target_price is not None:
        reached = payable <= item.target_price
    return PriceResult(payable=payable, missing=[], reached_target=reached)


def fmt_money(value: Decimal | None) -> str:
    if value is None:
        return "【待核实】"
    return f"¥{value:.2f}"
