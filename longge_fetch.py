#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""龙哥27届秋招汇总表抓取(腾讯文档 smartsheet)。

无需任何凭据, 纯公开 API。零依赖(仅标准库)。

原理: 网页前端是 canvas 渲染, DOM 里没有数据; 但页面实际通过
    GET https://docs.qq.com/dop-api/get/sheet?padId=...&subId=...&startrow=...&endrow=...
拉取数据, 返回 JSON 里 initialAttributedText.text[0].smartsheet
是 base64+zlib 压缩的 JSON。解包后:
    blob[0][0] = 列定义(t:3005), blob[0][1:] = 行数据块(t:3028)
    c.k2.k1 = {rowId: {k1: {colId: cell}}}, 文本在 cell.k1[0].k2
"""
import json, base64, zlib, datetime
import urllib.request, urllib.parse

PAD = "300000000$NrvcQyadGvDp"   # 文档 padId
SUB = "toi7BY"                    # "新开企业-每日更新" sheet
REFERER = "https://docs.qq.com/smartsheet/DTnJ2Y1F5YWRHdkRw"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/150.0.0.0"

# 届别过滤: 阿里系要求 2026.11 后毕业才算 27 届(2026.9 毕业者不符)
ALI_KW = ["阿里", "菜鸟", "灵犀", "瓴羊", "蚂蚁", "淘宝", "天猫"]
# 分组标签行
NOISE_KW = ["27届", "中大厂", "以下为", "以下阿里", "内推汇总", "提前批", "秋招"]


def fetch(startrow, endrow):
    qs = {
        "padId": PAD, "subId": SUB, "startrow": startrow, "endrow": endrow,
        "outformat": 1, "normal": 1, "needSheetState": 2, "optimizedVer": 2, "nowb": 1,
    }
    url = "https://docs.qq.com/dop-api/get/sheet?" + urllib.parse.urlencode(qs)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": REFERER})
    with urllib.request.urlopen(req, timeout=40) as resp:
        return json.loads(resp.read())


def cell_text(cell):
    if not isinstance(cell, dict):
        return ""
    v = cell.get("k1")
    if isinstance(v, list):
        return " ".join(str(s.get("k2", "")) for s in v if isinstance(s, dict))
    return v if isinstance(v, str) else ""


def parse_chunk(enc):
    raw = base64.b64decode(enc + "=" * (-len(enc) % 4))
    return json.loads(zlib.decompress(raw).decode("utf-8"))


def fetch_all():
    """返回龙哥表全部有效公司行 [{"name","job","deadline","code"}]"""
    d = fetch(0, 60)
    data = d.get("data") or {}
    maxrow = data.get("maxrow", 0)
    rows = {}
    start = 0
    while start < maxrow:
        d = fetch(start, min(start + 60, maxrow - 1))
        text = ((d.get("data") or {}).get("initialAttributedText") or {}).get("text") or []
        for chunk in text:
            enc = chunk.get("smartsheet", "")
            if not enc:
                continue
            try:
                blob = parse_chunk(enc)
            except Exception:
                continue
            for item in blob:
                for piece in (item if isinstance(item, list) else [item]):
                    if isinstance(piece, dict) and piece.get("t") == 3028:
                        rowmap = (piece.get("c", {}).get("k2", {}) or {}).get("k1", {})
                        for rid, wrap in rowmap.items():
                            cells = (wrap or {}).get("k1", {}) if isinstance(wrap, dict) else {}
                            row = rows.setdefault(rid, {})
                            for col, cell in cells.items():
                                row[col] = cell_text(cell)
        start += 60

    companies = []
    for r in rows.values():
        name = str(r.get("fq2BBI", "")).strip()
        if not name:
            continue
        if any(k in name for k in NOISE_KW):
            continue
        if any(k in name for k in ALI_KW):
            continue
        companies.append({
            "name": name,
            "job": str(r.get("f1emzF", "")).strip(),
            "deadline": str(r.get("fSqe11", "")).strip(),
            "code": str(r.get("feDcBm", "")).strip(),
        })
    return companies


def fetch_new(companies=None):
    """对比 .state_longge.json 返回新增"""
    companies = companies if companies is not None else fetch_all()
    state_file = __import__("os").path.join(
        __import__("os").path.dirname(__import__("os").path.abspath(__file__)),
        ".state_longge.json")
    import os
    seen = set()
    if os.path.exists(state_file):
        seen = set(json.load(open(state_file, encoding="utf-8")))
    new = [c for c in companies if c["name"] not in seen]
    seen.update(c["name"] for c in companies)
    json.dump(sorted(seen), open(state_file, "w", encoding="utf-8"), ensure_ascii=False)
    return new


if __name__ == "__main__":
    companies = fetch_all()
    new = fetch_new(companies)
    print(json.dumps({
        "total": len(companies),
        "new_count": len(new),
        "new": new[:30],
    }, ensure_ascii=False, indent=1))
