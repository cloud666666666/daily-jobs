#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""牛客校招日历抓取: 27届 + AI/算法岗 筛选, 输出今日新增。

零依赖(仅标准库)。需要你自己的牛客 Cookie:

    export NOWCODER_COOKIE='你的Cookie'

Cookie 获取方式见 README。"""
import json, os, sys, datetime
import urllib.request

COOKIE = os.environ.get("NOWCODER_COOKIE", "").strip()
PAGE_SIZE = 50
MAX_PAGES = 4  # 新收录排前, 前几页覆盖近期新增

AI_KEYWORDS = ["算法", "AI", "人工智能", "大模型", "机器学习", "深度学习", "自然语言",
               "计算机视觉", "NLP", "CV", "强化学习", "LLM", "多模态", "AIGC",
               "自动驾驶", "具身", "机器人", "数据挖掘", "推荐算法", "语音", "安全"]


def fetch_page(page):
    body = json.dumps({"query": "", "tab": 0, "page": page, "pageSize": PAGE_SIZE})
    req = urllib.request.Request(
        "https://www.nowcoder.com/np-api/u/school-schedule/list-card",
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


def fetch_new():
    """返回 (错误信息或None, {"new": [...], "total_matched": N})"""
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
        batch = it.get("batchName") or ""
        if not ("27" in batch or "2027" in batch):   # 届别: 27届
            continue
        if "实习" in batch:
            continue
        careers = it.get("careerNameList") or []
        if not any(any(k in c for k in AI_KEYWORDS) for c in careers):
            continue
        end = it.get("wangshenEndDate")
        if end and datetime.date.fromtimestamp(end / 1000) < today:
            continue
        matches.append(it)

    state_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".state_nowcoder.json")
    seen = set()
    if os.path.exists(state_file):
        seen = set(json.load(open(state_file, encoding="utf-8")))
    new = [m for m in matches if m.get("companyId") not in seen]
    seen.update(m.get("companyId") for m in matches)
    json.dump(sorted(x for x in seen if x), open(state_file, "w", encoding="utf-8"), ensure_ascii=False)

    new_list = [{
        "name": m.get("name", ""),
        "careers": ",".join(m.get("careerNameList") or []),
        "batch": m.get("batchName", ""),
        "end": ts(m.get("wangshenEndDate")) or "无截止",
        "cities": ",".join(m.get("cityList") or []),
    } for m in new]

    return None, {"new": new_list, "total_matched": len(matches)}


if __name__ == "__main__":
    err, result = fetch_new()
    if err:
        print(json.dumps(err, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=1))
