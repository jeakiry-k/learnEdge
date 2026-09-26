#!/usr/bin/env python3
"""
扫描 docs/ 下所有面试题，自动生成首页 index.md。
首页设计：一屏内展示，不纵向滚动，最多展示 8 条。
用法: python3 scripts/gen_index.py
"""
import os, re
from datetime import datetime

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
INDEX_FILE = os.path.join(DOCS_DIR, "index.md")

CATEGORY_MAP = {
    "javascript": "JavaScript", "css": "CSS", "html": "HTML",
    "react": "React", "vue": "Vue", "browser-network": "浏览器与网络",
    "algorithm": "算法与数据结构", "engineering": "工程化",
    "performance": "性能优化", "other": "其他", "misc": "其他",
}
CAT_SLUG = {v: k for k, v in CATEGORY_MAP.items()}

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
                tags_val = line.split(":", 1)[1].strip().strip("[]").replace('"', '').replace("'", "")
                meta["tags"] = [t.strip() for t in tags_val.split(",") if t.strip()]
    rel_path = os.path.relpath(filepath, DOCS_DIR)
    dir_name = rel_path.split(os.sep)[0]
    if not meta["category"]:
        meta["category"] = CATEGORY_MAP.get(dir_name, "其他")
    if not meta["title"]:
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        meta["title"] = title_match.group(1).strip() if title_match else os.path.splitext(os.path.basename(filepath))[0]
    if not meta["date"]:
        mtime = os.path.getmtime(filepath)
        meta["date"] = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
    meta["path"] = rel_path.replace(os.sep, "/").removesuffix(".md")
    return meta

def main():
    entries = []
    for root, dirs, files in os.walk(DOCS_DIR):
        for fname in files:
            if fname == "index.md" or not fname.endswith(".md"):
                continue
            if "/category/" in root:
                continue
            entries.append(parse_front_matter(os.path.join(root, fname)))

    entries.sort(key=lambda x: x["date"], reverse=True)

    total = len(entries)
    cats = sorted(set(e["category"] for e in entries))
    cat_count = len(cats)
    latest = entries[0]["date"] if entries else "-"
    display = entries[:8]

    list_items = []
    for e in display:
        tags_html = ""
        if e.get("tags"):
            tags_html = "".join('<span class="li-tag">%s</span>' % t for t in e["tags"][:3])
        cat_slug = CAT_SLUG.get(e["category"], "other")
        cat_link = "../category/%s" % cat_slug
        item = '<li>'
        item += '<a href="%s" class="li-link">' % e["path"]
        item += '<span class="li-title">%s</span>' % e["title"]
        item += '<span class="li-tags">%s</span>' % tags_html
        item += '</a>'
        item += '<a href="%s" class="li-cat">%s</a>' % (cat_link, e["category"])
        item += '</li>'
        list_items.append(item)
    list_html = "\n".join(list_items)

    CSS = """
html, body {
  height: 100% !important;
  overflow: hidden !important;
}
.md-main {
  flex-grow: 1;
  overflow: hidden !important;
  height: calc(100vh - 48px) !important;
}
.md-main__inner {
  margin-top: 0 !important;
  height: 100% !important;
  overflow: hidden !important;
}
.md-content {
  max-width: 100% !important;
  height: 100% !important;
  overflow: hidden !important;
}
.md-content__inner {
  margin: 0 !important;
  padding: 0 !important;
  max-width: 100% !important;
  height: 100% !important;
  overflow: hidden !important;
}
.md-content__inner > h1 {
  display: none !important;
}
.home {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 1.5rem 2rem;
  max-width: 900px;
  margin: 0 auto;
  box-sizing: border-box;
  overflow: hidden;
}
.home-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 1rem;
  flex-shrink: 0;
}
.home-title {
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--md-default-fg-color);
  margin: 0;
}
.home-stats {
  font-size: 0.8rem;
  color: var(--md-default-fg-color--light);
  white-space: nowrap;
}
.home-stats strong {
  color: var(--md-accent-fg-color);
  font-size: 1rem;
  font-weight: 700;
}
.home-list {
  list-style: none;
  padding: 0;
  margin: 0;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: thin;
}
.home-list::-webkit-scrollbar {
  width: 4px;
}
.home-list::-webkit-scrollbar-thumb {
  background: var(--md-default-fg-color--lightest);
  border-radius: 2px;
}
.home-list li {
  border-bottom: 1px solid var(--md-default-fg-color--lightest);
  display: flex;
  align-items: center;
  gap: 0.8rem;
  padding: 0.6rem 0;
}
.li-link {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  text-decoration: none;
  flex: 1;
  min-width: 0;
  transition: padding-left 0.15s;
}
.li-link:hover {
  padding-left: 0.5rem;
}
.li-title {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--md-default-fg-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.li-link:hover .li-title {
  color: var(--md-accent-fg-color);
}
.li-tags {
  display: flex;
  gap: 0.3rem;
  flex-shrink: 0;
}
.li-tag {
  font-size: 0.65rem;
  padding: 0.05rem 0.4rem;
  border-radius: 3px;
  background: var(--md-default-fg-color--lightest);
  color: var(--md-default-fg-color--light);
  white-space: nowrap;
}
.li-cat {
  font-size: 0.7rem;
  color: var(--md-default-fg-color--lighter);
  white-space: nowrap;
  flex-shrink: 0;
  text-decoration: none;
  transition: color 0.15s;
}
.li-cat:hover {
  color: var(--md-accent-fg-color);
}
"""

    HTML = """---
hide:
  - navigation
  - toc
---

<style>
%s
</style>

<div class="home">
  <div class="home-header">
    <h1 class="home-title">更新日志</h1>
    <span class="home-stats">共 <strong>%d</strong> 篇 · %d 分类 · 最近 %s</span>
  </div>
  <ul class="home-list">
%s
  </ul>
</div>
""" % (CSS, total, cat_count, latest, list_html)

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(HTML)

    print("首页已生成: %d 篇, %d 分类, 展示 %d 条" % (total, cat_count, len(display)))
    for e in display:
        print("  %s | %8s | %s" % (e["date"], e["category"], e["title"]))

if __name__ == "__main__":
    main()
