#!/usr/bin/env python3
"""
扫描 docs/ 下所有面试题，按发布日期倒序生成首页 index.md
每个 .md 文件的 front matter 中需要有 date 和 category 字段。
用法: python3 scripts/gen_index.py
"""
import os
import re
from datetime import datetime

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")
INDEX_FILE = os.path.join(DOCS_DIR, "index.md")

CATEGORY_MAP = {
    "javascript": "JavaScript",
    "css": "CSS",
    "html": "HTML",
    "react": "React",
    "vue": "Vue",
    "browser-network": "浏览器与网络",
    "algorithm": "算法与数据结构",
    "engineering": "工程化",
    "performance": "性能优化",
}

def parse_front_matter(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    meta = {"date": None, "category": None, "title": None, "tags": []}

    fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if fm_match:
        fm = fm_match.group(1)
        for line in fm.split("\n"):
            if line.strip().startswith("date:"):
                meta["date"] = line.split(":", 1)[1].strip().strip('"').strip("'")
            elif line.strip().startswith("category:"):
                meta["category"] = line.split(":", 1)[1].strip().strip('"').strip("'")
            elif line.strip().startswith("title:"):
                meta["title"] = line.split(":", 1)[1].strip().strip('"').strip("'")
            elif line.strip().startswith("tags:"):
                tags_val = line.split(":", 1)[1].strip()
                if tags_val:
                    meta["tags"] = [t.strip() for t in tags_val.split(",")]

    rel_path = os.path.relpath(filepath, DOCS_DIR)
    dir_name = rel_path.split(os.sep)[0]
    if not meta["category"]:
        meta["category"] = CATEGORY_MAP.get(dir_name, dir_name)
    if not meta["title"]:
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        meta["title"] = title_match.group(1).strip() if title_match else os.path.splitext(os.path.basename(filepath))[0]
    if not meta["date"]:
        mtime = os.path.getmtime(filepath)
        meta["date"] = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")

    meta["path"] = rel_path.replace(os.sep, "/")
    return meta


def main():
    entries = []
    for root, dirs, files in os.walk(DOCS_DIR):
        for fname in files:
            if fname == "index.md":
                continue
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(root, fname)
            meta = parse_front_matter(fpath)
            entries.append(meta)

    entries.sort(key=lambda x: x["date"], reverse=True)

    lines = []
    lines.append("# 面试知识合集\n")
    lines.append("> 前端面试题与知识点，持续更新中。\n")
    lines.append(f"> 共 **{len(entries)}** 篇 · 最近更新: {entries[0]['date'] if entries else '-'}\n")
    lines.append("---\n")
    lines.append("## 更新日志\n")
    lines.append("| 日期 | 分类 | 题目 |")
    lines.append("|------|------|------|")

    for e in entries:
        lines.append(f"| {e['date']} | {e['category']} | [{e['title']}]({e['path']}) |")

    lines.append("")
    lines.append("---\n")
    lines.append("## 分类索引\n")

    by_cat = {}
    for e in entries:
        by_cat.setdefault(e["category"], []).append(e)

    for cat in CATEGORY_MAP.values():
        if cat not in by_cat:
            continue
        lines.append(f"### {cat}\n")
        for e in by_cat[cat]:
            lines.append(f"- [{e['title']}]({e['path']}) — {e['date']}")
        lines.append("")

    content = "\n".join(lines)
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"生成首页: {len(entries)} 篇题目")
    for e in entries:
        print(f"   {e['date']} | {e['category']:8s} | {e['title']}")


if __name__ == "__main__":
    main()
