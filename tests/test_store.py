from decimal import Decimal

from shoppinglist.store import Item, Store


def test_add_list_remove(tmp_path):
    store = Store(tmp_path / "t.db")
    item_id = store.add_item(Item(name="洗衣机", platform="京东", daily_price=Decimal("2999")))
    items = store.list_items()
    assert len(items) == 1 and items[0].name == "洗衣机" and items[0].daily_price == Decimal("2999")
    assert store.get_item(item_id).platform == "京东"
    assert store.remove_item(item_id) is True
    assert store.list_items() == []
    store.close()


def test_meta_roundtrip(tmp_path):
    store = Store(tmp_path / "t.db")
    assert store.get_meta("budget") is None
    store.set_meta("budget", "5000")
    assert store.get_meta("budget") == "5000"
    store.close()
