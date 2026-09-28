---
hide:
  - navigation
  - toc
---

<style>

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

/* 移动端适配 */
@media screen and (max-width: 768px) {
  .home { padding: 1rem; }
  .li-tags { display: none; }
}
@media screen and (max-width: 480px) {
  .home { padding: 0.85rem; }
  .home-title { font-size: 1.1rem; }
  .li-cat { display: none; }
  .li-link:hover { padding-left: 0; }
}

</style>

<div class="home">
  <div class="home-header">
    <h1 class="home-title">更新日志</h1>
    <span class="home-stats">共 <strong>6</strong> 篇 · 4 分类 · 最近 2026-09-28</span>
  </div>
  <ul class="home-list">
<li><a href="browser-network/tcp-handshake-farewell" class="li-link"><span class="li-title">TCP 三次握手与四次挥手</span><span class="li-tags"><span class="li-tag">TCP</span><span class="li-tag">网络</span><span class="li-tag">协议</span></span></a><a href="../category/browser-network" class="li-cat">浏览器与网络</a></li>
<li><a href="redis/connection-pool" class="li-link"><span class="li-title">Redis 连接池</span><span class="li-tags"><span class="li-tag">Redis</span><span class="li-tag">连接池</span><span class="li-tag">性能优化</span></span></a><a href="../category/redis" class="li-cat">Redis</a></li>
<li><a href="mysql/field-types" class="li-link"><span class="li-title">MySQL 字段类型与存储空间估算</span><span class="li-tags"><span class="li-tag">MySQL</span><span class="li-tag">存储</span><span class="li-tag">数据类型</span></span></a><a href="../category/mysql" class="li-cat">MySQL</a></li>
<li><a href="redis/cache-issues" class="li-link"><span class="li-title">缓存穿透、击穿、雪崩</span><span class="li-tags"><span class="li-tag">缓存</span><span class="li-tag">Redis</span><span class="li-tag">高并发</span></span></a><a href="../category/redis" class="li-cat">Redis</a></li>
<li><a href="browser-network/http-caching" class="li-link"><span class="li-title">HTTP 缓存策略</span><span class="li-tags"><span class="li-tag">HTTP</span><span class="li-tag">缓存</span><span class="li-tag">性能</span></span></a><a href="../category/browser-network" class="li-cat">浏览器与网络</a></li>
<li><a href="engineering/url-shortener" class="li-link"><span class="li-title">短链系统设计</span><span class="li-tags"><span class="li-tag">系统设计</span><span class="li-tag">Base62</span><span class="li-tag">Redis</span></span></a><a href="../category/engineering" class="li-cat">工程化</a></li>
  </ul>
</div>
