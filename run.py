#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每日职位雷达主入口: 汇总牛客+龙哥表, 生成 data/ 快照与 latest.json。

用法:
    python3 run.py           # 抓取并生成数据文件
    python3 run.py --push    # 额外 git commit + push(需先配置好 remote)

依赖: 仅 Python3 标准库。
牛客源(两种任选其一):
  - 官方 MCP 通道: export NOWCODER_MCP_TOKEN='nk-...' (推荐, 见 README)
  - 旧 Cookie 通道: export NOWCODER_COOKIE='...' (备用)
"""
import json, os, sys, datetime
import nowcoder_fetch, nowcoder_mcp_fetch, longge_fetch

REPO = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(REPO, "data")


def main():
    today = datetime.date.today().strftime("%Y-%m-%d")

    # 牛客: 优先官方 MCP 通道(配置了 Token 时), 否则退回 Cookie 版
    if os.environ.get("NOWCODER_MCP_TOKEN"):
        nc_err, nc = nowcoder_mcp_fetch.fetch_new()
    else:
        nc_err, nc = nowcoder_fetch.fetch_new()
    if nc_err:
        print("⚠️", nc_err.get("error") if isinstance(nc_err, dict) else nc_err)
        nc_new = []
    else:
        nc_new = nc.get("new", [])

    # 龙哥表
    try:
        companies = longge_fetch.fetch_all()
        lg_new = longge_fetch.fetch_new(companies)
    except Exception as e:
        print(f"⚠️ 龙哥表抓取失败: {e}")
        companies, lg_new = [], []

    payload = {
        "date": today,
        "nowcoder_new": nc_new,
        "longge_new": lg_new[:30],
        "longge_total": len(companies),
    }

    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, f"{today}.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    with open(os.path.join(REPO, "latest.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)

    print(f"✅ {today} | 牛客新增 {len(nc_new)} | 龙哥新增 {len(lg_new)}(全量 {len(companies)})")

    if "--push" in sys.argv:
        import subprocess
        ident = ["-c", "user.name=cloud666666666", "-c", "user.email=2353493891@qq.com"]
        subprocess.run(["git"] + ident + ["add", "-A"], cwd=REPO, check=True)
        r = subprocess.run(["git"] + ident + ["commit", "-m", f"📅 {today} 每日职位更新"],
                           cwd=REPO, capture_output=True, text=True)
        if "nothing to commit" not in r.stdout + r.stderr:
            p = subprocess.run(["git", "push", "origin", "main"], cwd=REPO,
                               capture_output=True, text=True, timeout=180)
            print("push:", "✅" if p.returncode == 0 else "❌ " + p.stderr[-200:])


if __name__ == "__main__":
    main()
