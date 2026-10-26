"""本地 SQLite 存储：清单条目 + 元信息（预算、提醒日期）。

金额一律以字符串形式存 Decimal，避免浮点误差。
数据库路径：环境变量 DOUBLE11_DB 优先，否则 ~/.double11-list/list.db。
"""
from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path


def default_db_path() -> Path:
    env = os.environ.get("DOUBLE11_DB")
    if env:
        return Path(env)
    return Path.home() / ".double11-list" / "list.db"


def to_decimal(value) -> Decimal | None:
    """把用户输入转成 Decimal；空值或非法值返回 None（视为未录入）。"""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None


@dataclass
class Item:
    name: str
    platform: str = ""
    daily_price: Decimal | None = None
    target_price: Decimal | None = None
    cut: Decimal = Decimal("0")
    platform_coupon: Decimal = Decimal("0")
    shop_coupon: Decimal = Decimal("0")
    id: int | None = None


_SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    platform TEXT DEFAULT '',
    daily_price TEXT,
    target_price TEXT,
    cut TEXT DEFAULT '0',
    platform_coupon TEXT DEFAULT '0',
    shop_coupon TEXT DEFAULT '0'
);
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


def _dec(text) -> Decimal | None:
    return Decimal(text) if text is not None else None


def _dec0(text) -> Decimal:
    return Decimal(text) if text is not None else Decimal("0")


def _txt(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


class Store:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path else default_db_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(_SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def add_item(self, item: Item) -> int:
        cur = self.conn.execute(
            "INSERT INTO items (name, platform, daily_price, target_price, cut, platform_coupon, shop_coupon)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                item.name,
                item.platform,
                _txt(item.daily_price),
                _txt(item.target_price),
                str(item.cut),
                str(item.platform_coupon),
                str(item.shop_coupon),
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def list_items(self) -> list[Item]:
        rows = self.conn.execute("SELECT * FROM items ORDER BY id").fetchall()
        return [self._row_to_item(r) for r in rows]

    def get_item(self, item_id: int) -> Item | None:
        row = self.conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        return self._row_to_item(row) if row else None

    def remove_item(self, item_id: int) -> bool:
        cur = self.conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def get_meta(self, key: str) -> str | None:
        row = self.conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None

    def set_meta(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        self.conn.commit()

    @staticmethod
    def _row_to_item(row: sqlite3.Row) -> Item:
        return Item(
            id=row["id"],
            name=row["name"],
            platform=row["platform"] or "",
            daily_price=_dec(row["daily_price"]),
            target_price=_dec(row["target_price"]),
            cut=_dec0(row["cut"]),
            platform_coupon=_dec0(row["platform_coupon"]),
            shop_coupon=_dec0(row["shop_coupon"]),
        )
