#!/usr/bin/env python3
"""
扫描 docs/ 下所有面试题，自动生成首页 index.md。
首页包含：海报式 Hero（统计数字）+ 更新日志（按日期倒序）
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

CAT_SLUG = {v: k for k, v in CATEGORY_MAP.items()}

def parse_front_matter(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    meta = {"date": None, "category": None, "title": None}
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
            if fname == "index.md" or not fname.endswith(".md"):
                continue
            fpath = os.path.join(root, fname)
            entries.append(parse_front_matter(fpath))

    entries.sort(key=lambda x: x["date"], reverse=True)

    total = len(entries)
    cats = sorted(set(e["category"] for e in entries))
    cat_count = len(cats)
    latest = entries[0]["date"] if entries else "-"

    # 生成更新日志列表
    update_items = []
    for e in entries:
        update_items.append(f'''    <li>
      <span class="update-date">{e["date"]}</span>
      <span class="update-cat">{e["category"]}</span>
      <span class="update-title"><a href="{e["path"]}">{e["title"]}</a></span>
    </li>''')
    update_html = "\n".join(update_items)

    html = f'''---
hide:
  - navigation
  - toc
---

# 面试知识合集

<style>
.md-content__inner {{
  padding: 0 !important;
  max-width: 100% !important;
}}

.hero {{
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: #0a0a0a;
  color: #fff;
}}
.hero::before {{
  content: "";
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
  background-size: 60px 60px;
}}
.hero::after {{
  content: "";
  position: absolute;
  width: 600px;
  height: 600px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(59,130,246,0.15) 0%, transparent 70%);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}}
.hero-content {{
  position: relative;
  z-index: 1;
  text-align: center;
}}
.hero-tag {{
  font-size: 0.8rem;
  letter-spacing: 0.3em;
  color: rgba(255,255,255,0.4);
  text-transform: uppercase;
  margin-bottom: 2rem;
}}
.hero-title {{
  font-size: 3.5rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  margin: 0;
  background: linear-gradient(135deg, #fff 0%, #6b7280 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}}
.hero-subtitle {{
  font-size: 1.1rem;
  color: rgba(255,255,255,0.5);
  margin-top: 1.5rem;
  letter-spacing: 0.15em;
}}
.hero-divider {{
  width: 40px;
  height: 1px;
  background: rgba(255,255,255,0.2);
  margin: 2.5rem auto;
}}
.hero-stats {{
  display: flex;
  gap: 4rem;
  justify-content: center;
}}
.hero-stat {{
  text-align: center;
}}
.hero-stat-num {{
  font-size: 2.5rem;
  font-weight: 700;
  color: #3b82f6;
  font-variant-numeric: tabular-nums;
}}
.hero-stat-label {{
  font-size: 0.75rem;
  color: rgba(255,255,255,0.4);
  letter-spacing: 0.1em;
  margin-top: 0.3rem;
}}
.hero-quote {{
  position: absolute;
  bottom: 3rem;
  left: 0;
  right: 0;
  text-align: center;
  z-index: 1;
}}
.hero-quote-text {{
  font-size: 0.9rem;
  color: rgba(255,255,255,0.3);
  letter-spacing: 0.2em;
}}
.hero-quote-author {{
  font-size: 0.7rem;
  color: rgba(255,255,255,0.2);
  margin-top: 0.3rem;
}}
.hero-enter {{
  margin-top: 2.5rem;
  display: inline-block;
  padding: 0.7rem 2rem;
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 2px;
  color: rgba(255,255,255,0.8);
  font-size: 0.85rem;
  letter-spacing: 0.1em;
  text-decoration: none;
  transition: all 0.3s;
}}
.hero-enter:hover {{
  border-color: #3b82f6;
  color: #3b82f6;
  background: rgba(59,130,246,0.05);
}}
.update-section {{
  max-width: 780px;
  margin: 0 auto;
  padding: 4rem 2rem;
}}
.update-section h2 {{
  font-size: 1.3rem;
  font-weight: 600;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 0.5rem;
}}
.update-list {{
  list-style: none;
  padding: 0;
}}
.update-list li {{
  padding: 0.8rem 0;
  border-bottom: 1px solid #f3f4f6;
  display: flex;
  align-items: center;
  gap: 1rem;
}}
.update-date {{
  font-size: 0.8rem;
  color: #9ca3af;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
  min-width: 100px;
}}
.update-cat {{
  font-size: 0.75rem;
  padding: 0.1rem 0.6rem;
  border-radius: 3px;
  background: #f3f4f6;
  color: #6b7280;
  white-space: nowrap;
}}
.update-title a {{
  color: #1f2937;
  text-decoration: none;
  font-size: 0.9rem;
}}
.update-title a:hover {{
  color: #3b82f6;
}}
</style>

<div class="hero">
  <div class="hero-content">
    <div class="hero-tag">INTERVIEW COLLECTION</div>
    <h1 class="hero-title">面试知识合集</h1>
    <div class="hero-subtitle">朝花夕拾 · 温故而知新</div>
    <div class="hero-divider"></div>
    <div class="hero-stats">
      <div class="hero-stat">
        <div class="hero-stat-num">{total}</div>
        <div class="hero-stat-label">收录题目</div>
      </div>
      <div class="hero-stat">
        <div class="hero-stat-num">{cat_count}</div>
        <div class="hero-stat-label">分类</div>
      </div>
      <div class="hero-stat">
        <div class="hero-stat-num">{latest}</div>
        <div class="hero-stat-label">最近更新</div>
      </div>
    </div>
    <a href="{entries[0]["path"] if entries else "#"}" class="hero-enter">进入合集 →</a>
  </div>
  <div class="hero-quote">
    <div class="hero-quote-text">朝花夕拾 · 温故而知新</div>
    <div class="hero-quote-author">— 持续更新中</div>
  </div>
</div>

<div class="update-section">
  <h2>更新日志</h2>
  <ul class="update-list">
{update_html}
  </ul>
</div>
'''

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ 首页已生成: {total} 篇题目, {cat_count} 个分类")
    for e in entries:
        print(f"   {e['date']} | {e['category']:8s} | {e['title']}")

if __name__ == "__main__":
    main()
