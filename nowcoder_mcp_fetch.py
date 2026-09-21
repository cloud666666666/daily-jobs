#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""牛客校招岗位抓取(官方 MCP 版): 通过牛客官方 MCP 服务(JSON-RPC over HTTP)查询
"最近 N 天发布"的 27 届 AI/算法岗, 输出今日新增。零依赖(仅标准库)。

需要 Token(官方技能包页面生成, 见 README):

    export NOWCODER_MCP_TOKEN='nk-...'

与旧版(Cookie 抓校招日历内部接口)相比: 官方通道、字段更全(职位描述/要求/申请链接),
不消耗登录态 Cookie。旧版保留为备用(nowcoder_fetch.py)。
"""
import json, os, sys, datetime, urllib.request

TOKEN = os.environ.get("NOWCODER_MCP_TOKEN", "").strip()
ENDPOINT = "https://www.nowcoder.com/agent/mcp"
PAGE_SIZE = 20
MAX_PAGES = 4  # 每页 20 条, 最多翻 4 页

AI_KEYWORDS = ["算法", "AI", "人工智能", "大模型", "机器学习", "深度学习", "多模态", "强化学习",
               "NLP", "CV", "计算机视觉", "自动驾驶", "具身", "机器人", "语音", "推荐", "AIGC", "数据挖掘"]


def rpc(method, params=None, rid=None):
    body = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        body["params"] = params
    if rid is not None:
        body["id"] = rid
    req = urllib.request.Request(ENDPOINT, data=json.dumps(body).encode(), headers={
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": "Bearer " + TOKEN,
    }, method="POST")
    with urllib.request.urlopen(req, timeout=40) as r:
        raw = r.read().decode("utf-8", "replace")
    if raw.lstrip().startswith("{"):
        return json.loads(raw)
    for line in raw.splitlines():          # SSE 响应格式兼容
        line = line.strip()
        if line.startswith("data:"):
            try:
                obj = json.loads(line[5:].strip())
                if "result" in obj or "error" in obj:
                    return obj
            except Exception:
                continue
    return {}


def fetch_new(days=3):
    """返回 (错误信息或None, {"new": [...], "total_matched": N})"""
    if not TOKEN:
        return {"error": "未配置 NOWCODER_MCP_TOKEN(见 README), 跳过牛客源"}, None

    # 握手(实测端点宽容, 失败也继续)
    try:
        rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                           "clientInfo": {"name": "daily-jobs", "version": "1.0"}}, rid=1)
        rpc("notifications/initialized", None, rid=None)
    except Exception:
        pass

    all_items = []
    for page in range(1, MAX_PAGES + 1):
        try:
            resp = rpc("tools/call", {
                "name": "nowclaw_job_recommend",
                "arguments": {"keywords": AI_KEYWORDS, "publishedWithinDays": days,
                              "size": PAGE_SIZE, "page": page},
            }, rid=100 + page)
        except Exception as e:
            return {"error": f"牛客 MCP 调用失败: {e}"}, None
        res = resp.get("result") or {}
        if res.get("isError"):
            texts = " ".join(c.get("text", "") for c in res.get("content", []))
            return {"error": f"牛客 MCP 返回错误: {texts[:200]}"}, None
        payload = None
        for c in res.get("content", []):
            if c.get("type") == "text":
                try:
                    payload = json.loads(c.get("text"))
                except Exception:
                    continue
        if not payload:
            break
        items = payload.get("data") or []
        if not items:
            break
        all_items.extend(items)

    today = datetime.date.today()
    matches = []
    for it in all_items:
        batch = it.get("batch") or ""
        if not ("27" in batch or "2027" in batch):     # 届别: 27届
            continue
        if "实习" in batch:
            continue
        hay = (it.get("title") or "") + " " + (it.get("category") or "") + " " + (it.get("description") or "")[:200]
        if not any(k in hay for k in AI_KEYWORDS):     # AI/算法方向
            continue
        dl = (it.get("deadline") or "")
        if dl and dl[:4].isdigit():                    # 能解析出日期且已过 -> 跳过
            try:
                d = datetime.date.fromisoformat(dl[:10].replace("/", "-"))
                if d < today:
                    continue
            except Exception:
                pass
        matches.append(it)

    state_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".state_nowcoder_mcp.json")
    seen = set()
    if os.path.exists(state_file):
        seen = set(json.load(open(state_file, encoding="utf-8")))
    new = [m for m in matches if m.get("id") not in seen]
    seen.update(m.get("id") for m in matches)
    json.dump(sorted(x for x in seen if x), open(state_file, "w", encoding="utf-8"), ensure_ascii=False)

    def hit_careers(it):
        found = [k for k in AI_KEYWORDS if k in ((it.get("title") or "") + " " + (it.get("description") or "")[:200])]
        return ", ".join(found[:4])

    new_list = [{
        "name": m.get("company", ""),
        "title": m.get("title", ""),
        "careers": hit_careers(m),
        "batch": m.get("batch", ""),
        "end": m.get("deadline") or "无截止",
        "cities": m.get("workLocation") or ", ".join(m.get("city") or []) if isinstance(m.get("city"), list) else (m.get("city") or m.get("workLocation") or ""),
        "link": m.get("url", ""),
    } for m in new]

    return None, {"new": new_list, "total_matched": len(matches)}


if __name__ == "__main__":
    err, result = fetch_new()
    if err:
        print(json.dumps(err, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=1))
