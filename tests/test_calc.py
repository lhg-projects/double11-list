from decimal import Decimal

from shoppinglist.calc import estimate
from shoppinglist.store import Item


def test_full_price_math():
    item = Item(
        id=None, name="耳机", daily_price=Decimal("1000"), target_price=Decimal("800"),
        cut=Decimal("150"), platform_coupon=Decimal("50"), shop_coupon=Decimal("30"),
    )
    r = estimate(item)
    assert r.payable == Decimal("770")
    assert r.reached_target is True


def test_missing_daily_is_unknown():
    item = Item(id=None, name="神秘商品")
    r = estimate(item)
    assert r.payable is None
    assert "日常价" in r.missing


def test_payable_floor_zero():
    item = Item(id=None, name="羊毛", daily_price=Decimal("10"), cut=Decimal("50"))
    assert estimate(item).payable == Decimal("0")


def test_no_target_means_no_reached_flag():
    item = Item(id=None, name="x", daily_price=Decimal("100"))
    assert estimate(item).reached_target is None
