#!/usr/bin/env python3
"""
为每个有题目的分类生成列表页。
输出到 docs/category/{slug}/index.md
用法: python3 scripts/gen_category_pages.py
"""
import os, re
from datetime import datetime

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
CATEGORY_DIR = os.path.join(DOCS_DIR, "category")

CATEGORY_SLUG = {
    "JavaScript": "javascript", "CSS": "css", "HTML": "html",
    "React": "react", "Vue": "vue", "浏览器与网络": "browser-network",
    "算法与数据结构": "algorithm", "工程化": "engineering",
    "性能优化": "performance", "其他": "other",
}

CSS = """
.category-page {
  padding: 2.5rem 2rem;
}
.category-header {
  margin-bottom: 2rem;
}
.category-header h1 {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 0.3rem;
}
.category-header .count {
  font-size: 0.85rem;
  color: var(--md-default-fg-color--light);
}
.category-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.category-list li {
  border-bottom: 1px solid var(--md-default-fg-color--lightest);
  display: flex;
  align-items: center;
  gap: 0.8rem;
  padding: 0.7rem 0;
}
.category-list a {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  text-decoration: none;
  color: inherit;
  flex: 1;
  transition: padding-left 0.15s;
}
.category-list a:hover {
  padding-left: 0.5rem;
}
.item-title {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--md-default-fg-color);
  flex: 1;
}
.category-list a:hover .item-title {
  color: var(--md-accent-fg-color);
}
.item-tags {
  display: flex;
  gap: 0.3rem;
  flex-shrink: 0;
}
.item-tags .tag {
  font-size: 0.65rem;
  padding: 0.05rem 0.4rem;
  border-radius: 3px;
  background: var(--md-default-fg-color--lightest);
  color: var(--md-default-fg-color--light);
  white-space: nowrap;
}
.item-date {
  font-size: 0.75rem;
  color: var(--md-default-fg-color--lighter);
  white-space: nowrap;
  min-width: 90px;
  text-align: right;
}
"""

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
    if not meta["category"]:
        meta["category"] = "其他"
    if not meta["title"]:
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        meta["title"] = title_match.group(1).strip() if title_match else os.path.splitext(os.path.basename(filepath))[0]
    if not meta["date"]:
        mtime = os.path.getmtime(filepath)
        meta["date"] = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
    rel_path = os.path.relpath(filepath, DOCS_DIR).replace(os.sep, "/").removesuffix(".md")
    meta["path"] = rel_path
    return meta

def main():
    entries = []
    for root, dirs, files in os.walk(DOCS_DIR):
        if "/category/" in root:
            continue
        for fname in files:
            if fname == "index.md" or not fname.endswith(".md"):
                continue
            entries.append(parse_front_matter(os.path.join(root, fname)))

    entries.sort(key=lambda x: x["date"], reverse=True)
    by_cat = {}
    for e in entries:
        by_cat.setdefault(e["category"], []).append(e)

    os.makedirs(CATEGORY_DIR, exist_ok=True)

    for cat_name, items in sorted(by_cat.items()):
        slug = CATEGORY_SLUG.get(cat_name, cat_name.lower().replace(" ", "-"))
        dirpath = os.path.join(CATEGORY_DIR, slug)
        os.makedirs(dirpath, exist_ok=True)
        filepath = os.path.join(dirpath, "index.md")

        total = len(items)
        list_items = []
        for e in items:
            tag_html = ""
            if e["tags"]:
                tag_html = "".join('<span class="tag">%s</span>' % t for t in e["tags"][:3])
            item = '<li><a href="../../%s"><span class="item-title">%s</span><span class="item-tags">%s</span><span class="item-date">%s</span></a></li>' % (e["path"], e["title"], tag_html, e["date"])
            list_items.append(item)

        md = "---\nhide:\n  - navigation\n  - toc\n---\n\n<style>\n%s\n</style>\n\n<div class=\"category-page\">\n  <div class=\"category-header\">\n    <h1>%s</h1>\n    <span class=\"count\">共 %d 篇</span>\n  </div>\n  <ul class=\"category-list\">\n%s\n  </ul>\n</div>\n" % (CSS, cat_name, total, "\n".join(list_items))

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md)
        print("  %s → category/%s/ (%d篇)" % (cat_name, slug, total))

    print("分类页已生成")

if __name__ == "__main__":
    main()
