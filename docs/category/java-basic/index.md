---
hide:
  - navigation
  - toc
---

<style>

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

/* 移动端适配 */
@media screen and (max-width: 768px) {
  .category-page { padding: 1.5rem 1rem; }
  .item-tags { display: none; }
}
@media screen and (max-width: 480px) {
  .category-page { padding: 1.25rem 0.85rem; }
  .category-header h1 { font-size: 1.25rem; }
  .item-date { display: none; }
  .category-list a:hover { padding-left: 0; }
}

</style>

<div class="category-page">
  <div class="category-header">
    <h1>Java 基础</h1>
    <span class="count">共 2 篇</span>
  </div>
  <ul class="category-list">
<li><a href="../../java-basic/thread-pool"><span class="item-title">线程池工作原理</span><span class="item-tags"><span class="tag">Java</span><span class="tag">线程池</span><span class="tag">并发</span></span><span class="item-date">2026-10-08</span></a></li>
<li><a href="../../java-basic/hashcode-equals"><span class="item-title">hashCode 相等，equals 必须相等么？</span><span class="item-tags"><span class="tag">Java</span><span class="tag">hashCode</span><span class="tag">equals</span></span><span class="item-date">2026-09-29</span></a></li>
  </ul>
</div>
