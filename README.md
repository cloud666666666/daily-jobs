# 🎯 daily-jobs · 27届秋招 AI/算法岗每日雷达

开源、零依赖(纯 Python3 标准库)的校招职位每日监控工具。

双数据源:
- **牛客校招日历** — 每天抓取最新收录的 AI/算法岗(需要你自己的 Cookie)
- **龙哥27届秋招信息汇总表**(腾讯文档 smartsheet)— 无需凭据,公开 API

每天生成 `data/YYYY-MM-DD.json` 快照 + `latest.json` 最新数据。

## 🚀 快速开始

```bash
git clone https://github.com/cloud666666666/daily-jobs.git
cd daily-jobs

# 只用龙哥表(无需任何配置)
python3 run.py

# 加上牛客源: 先获取你的 Cookie(见下), 然后
export NOWCODER_COOKIE='你的Cookie'
python3 run.py
```

无任何第三方依赖,Python 3.8+ 即可。

## 🍪 获取牛客 Cookie

1. 浏览器登录 nowcoder.com
2. F12 打开开发者工具 → Network 面板
3. 刷新校招日历页(https://www.nowcoder.com/jobs/school/schedule)
4. 找 `calendar/search` 请求 → Request Headers 里复制完整 `Cookie` 值
5. `export NOWCODER_COOKIE='粘贴这里'`

> Cookie 含登录态,请勿提交进 git。仓库已忽略 `.state_*.json`(增量去重状态,首次运行会自动生成)。

## ⏰ 定时运行

```bash
# crontab 示例: 每天 9:45 抓取并推送
45 9 * * * cd /path/to/daily-jobs && NOWCODER_COOKIE='xxx' python3 run.py --push
```

`--push` 需要先把仓库 fork/clone 到自己的账号并配好 remote。

## 📂 数据格式

`latest.json`:

```json
{
  "date": "2026-09-08",
  "nowcoder_new": [{"name": "...", "job": "...", "end": "...", "cities": "...", "link": "..."}],
  "longge_new":   [{"name": "...", "job": "...", "deadline": "...", "code": "内推码"}],
  "longge_total": 272
}
```

## 🔧 技术点

- 龙哥表前端是 canvas 渲染,DOM 抓不到数据 → 从网络请求里挖出公开 JSON 接口(`/dop-api/get/sheet`),数据是 base64+zlib 压缩,解包即完整表格
- 已过滤:阿里系(届别要求 2026.11 后毕业)、非 AI/算法方向、分组标签行

## 📜 License

MIT

---

本项目由 [Joker.Yun](https://github.com/cloud666666666) 维护,Hermes cron 每日自动更新数据快照。
