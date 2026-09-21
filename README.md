# 🎯 daily-jobs · 27届秋招 AI/算法岗每日雷达

开源、零依赖(纯 Python3 标准库)的校招职位每日监控工具。

双数据源:
- **牛客校招岗位(官方 MCP 通道)** — 通过牛客官方 MCP 服务查询"最近 3 天发布"的 AI/算法岗, 只用官方 Token
- **龙哥27届秋招信息汇总表**(腾讯文档 smartsheet)— 无需凭据,公开 API

每天生成 `data/YYYY-MM-DD.json` 快照 + `latest.json` 最新数据。

## 🚀 快速开始

```bash
git clone https://github.com/cloud666666666/daily-jobs.git
cd daily-jobs

# 只用龙哥表(无需任何配置)
python3 run.py

# 加上牛客源: 先获取你的 MCP Token(见下), 然后
export NOWCODER_MCP_TOKEN='nk-你的Token'
python3 run.py
```

无任何第三方依赖,Python 3.8+ 即可。

## 🔑 获取牛客 MCP Token

1. 浏览器登录 nowcoder.com
2. 打开牛客技能包页面:**https://www.nowcoder.com/my/resume-plugin-intro?tab=skills**
3. 在页面里生成并复制你的 Token(`nk-` 开头)
4. `export NOWCODER_MCP_TOKEN='nk-...'`

> 本仓库通过**牛客官方 MCP 服务**(标准 JSON-RPC over HTTP)获取数据, 零第三方 SDK——单文件 `nowcoder_mcp_fetch.py` 用标准库直调官方通道。
> 旧版 Cookie 通道保留于 `nowcoder_fetch.py` 作为备用(如需: F12 → Network → 复制 `Cookie` 头)。
> Token 含授权,请勿提交进 git。仓库已忽略 `.state_*.json`(增量去重状态,首次运行会自动生成)。

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

- 牛客源走**官方 MCP 服务**: JSON-RPC over HTTP, 用 urllib 手写最小 MCP 客户端(`initialize` → `tools/call`), 保持零依赖
- 龙哥表前端是 canvas 渲染,DOM 抓不到数据 → 从网络请求里挖出公开 JSON 接口(`/dop-api/get/sheet`),数据是 base64+zlib 压缩,解包即完整表格
- 已过滤:阿里系(届别要求 2026.11 后毕业)、非 AI/算法方向、分组标签行

## 📜 License

MIT

---

本项目由 [Joker.Yun](https://github.com/cloud666666666) 维护,Hermes cron 每日自动更新数据快照。
