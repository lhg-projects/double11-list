# double11-list 双11比价清单

双 11 购物清单本地小工具：手动录入想买的东西、目标价和券，算出叠券后实付、超预算提醒；11 月 11 日前每天只提醒一次，不骚扰。双 11 结束后可复用为日常 / 618 比价清单。

**合规底线（先说清）**：价格全部手动录入。本工具不接任何电商 API、不登录任何平台账号、不爬取价格页。数据只存在你自己电脑上（SQLite 单文件）。实付只是预估，最终以平台结算页为准。

## 安装

```bash
pip install double11-list   # 或从源码：pip install .
```

## 用法

```bash
# 加一件商品（日常价是实付计算的基准；立减/平台券/店铺券按活动页写的填）
double11 add 降噪耳机 --platform 抖音商城 --daily 1000 --target 800 --cut 150 --platform-coupon 50 --shop-coupon 30

double11 list          # 看清单、每件预估实付、合计与预算状态
double11 price 1       # 看 1 号商品的计算明细
double11 budget 2000   # 设总预算（不带金额只查看）
double11 export --out 清单.md   # 导出 Markdown / CSV，对着手机逐项下单核对
double11 remind        # 每日提醒：达标商品 + 预算状态（每天最多一次）
double11 remove 1      # 删除
```

实付公式：**预估实付 = 日常价 − 立减 − 平台券 − 店铺券**。没填日常价的商品算不出实付，标【待核实】，不硬算。

## 开发

```bash
pip install -e ".[dev]"
pytest
```

数据库默认在 `~/.double11-list/list.db`，可用环境变量 `DOUBLE11_DB` 改路径。

## License

MIT
