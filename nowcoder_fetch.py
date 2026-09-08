#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""牛客校招日历抓取: 27届 + AI/算法岗 筛选, 输出今日新增。

零依赖(仅标准库)。需要你自己的牛客 Cookie:

    export NOWCODER_COOKIE='你的Cookie'

Cookie 获取方式见 README。"""
import json, os, sys, datetime
import urllib.request

COOKIE = os.environ.get("NOWCODER_COOKIE", "").strip()
PAGE_SIZE = 20
MAX_PAGES = 5  # 新收录排前, 一般前几页就是最新的

AI_KW = ["算法", "AI", "人工智能", "大模型", "机器学习", "深度学习", "自然语言",
         "计算机视觉", "NLP", "CV", "强化学习", "LLM", "多模态", "AIGC",
         "自动驾驶", "具身", "机器人算法", "数据挖掘", "推荐算法", "语音"]


def fetch_page(page):
    body = json.dumps({"query": "", "tab": 0, "page": page, "pageSize": PAGE_SIZE})
    req = urllib.request.Request(
        "https://gw-c.nowcoder.com/api/sparta/campus/school/job/calendar/search",
        data=body.encode(),
        headers={
            "Content-Type": "application/json",
            "Cookie": COOKIE,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/150.0.0.0",
            "Referer": "https://www.nowcoder.com/jobs/school/schedule",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def ts(ms):
    return datetime.datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d") if ms else None


def get_link(it):
    ad = it.get("adInfo") or {}
    return ad.get("rawUrl") or it.get("customWangshenLink") or ""


def fetch_new():
    """返回今日新增(相对 state 文件)的 AI/算法岗列表。"""
    if not COOKIE:
        return {"error": "未配置 NOWCODER_COOKIE 环境变量, 跳过牛客源(见 README)"}, None

    all_items = []
    for page in range(1, MAX_PAGES + 1):
        try:
            data = fetch_page(page)
            items = (data.get("data") or {}).get("datas") or []
            if not items:
                break
            all_items.extend(items)
        except Exception as e:
            return {"error": f"牛客抓取失败: {e}"}, None

    today = datetime.date.today()
    matches = []
    for it in all_items:
        name = it.get("name", "")
        job = it.get("jobName") or it.get("positionName") or ""
        end = it.get("wangshenEndDate") or 0
        if not name:
            continue
        if not any(k in job for k in AI_KW):
            continue
        if end and end / 1000 < datetime.datetime.combine(today, datetime.time()).timestamp():
            continue
        # 届别: 校招日历默认应届, 过滤明显含"实习"的
        if "实习" in job and "校招" not in job:
            continue
        matches.append({
            "name": name,
            "job": job[:60],
            "end": ts(end) or "无截止",
            "cities": ",".join(it.get("cityList") or []),
            "link": get_link(it),
        })

    state_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".state_nowcoder.json")
    seen = set()
    if os.path.exists(state_file):
        seen = set(json.load(open(state_file, encoding="utf-8")))
    new = [m for m in matches if m["name"] not in seen]
    seen.update(m["name"] for m in matches)
    json.dump(sorted(seen), open(state_file, "w", encoding="utf-8"), ensure_ascii=False)
    return None, {"new": new, "total_matched": len(matches)}


if __name__ == "__main__":
    err, result = fetch_new()
    if err:
        print(json.dumps(err, ensure_ascii=False))
        sys.exit(0)
    print(json.dumps(result, ensure_ascii=False, indent=1))
