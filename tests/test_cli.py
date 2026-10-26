from typer.testing import CliRunner

from shoppinglist.cli import app

runner = CliRunner()


def _run(*args):
    return runner.invoke(app, list(args))


def test_full_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("DOUBLE11_DB", str(tmp_path / "cli.db"))
    r = _run("add", "耳机", "--platform", "抖音商城", "--daily", "1000", "--target", "800",
             "--cut", "150", "--platform-coupon", "50", "--shop-coupon", "30")
    assert r.exit_code == 0 and "¥770.00" in r.output
    r = _run("list")
    assert "耳机" in r.output and "已达目标价" in r.output
    r = _run("price", "1")
    assert r.exit_code == 0 and "预估实付" in r.output
    r = _run("budget", "500")
    assert "已超预算" in r.output
    r = _run("remind")
    assert "已达到目标价" in r.output
    r = _run("remind")
    assert "已经提醒过了" in r.output
    r = _run("remove", "1")
    assert r.exit_code == 0
    r = _run("list")
    assert "清单是空的" in r.output


def test_export_md(tmp_path, monkeypatch):
    monkeypatch.setenv("DOUBLE11_DB", str(tmp_path / "cli.db"))
    _run("add", "大米", "--daily", "60")
    out = tmp_path / "list.md"
    r = _run("export", "--out", str(out))
    assert r.exit_code == 0
    text = out.read_text(encoding="utf-8")
    assert "大米" in text and "双11购物清单" in text
