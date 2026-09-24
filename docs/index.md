---
hide:
  - navigation
  - toc
---

# 面试知识合集

<style>
.md-content__inner {
  padding: 0 !important;
  max-width: 100% !important;
}

.hero {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: #0a0a0a;
  color: #fff;
}
.hero::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
  background-size: 60px 60px;
}
.hero::after {
  content: "";
  position: absolute;
  width: 600px;
  height: 600px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(59,130,246,0.15) 0%, transparent 70%);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
.hero-content {
  position: relative;
  z-index: 1;
  text-align: center;
}
.hero-tag {
  font-size: 0.8rem;
  letter-spacing: 0.3em;
  color: rgba(255,255,255,0.4);
  text-transform: uppercase;
  margin-bottom: 2rem;
}
.hero-title {
  font-size: 3.5rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  margin: 0;
  background: linear-gradient(135deg, #fff 0%, #6b7280 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.hero-subtitle {
  font-size: 1.1rem;
  color: rgba(255,255,255,0.5);
  margin-top: 1.5rem;
  letter-spacing: 0.15em;
}
.hero-divider {
  width: 40px;
  height: 1px;
  background: rgba(255,255,255,0.2);
  margin: 2.5rem auto;
}
.hero-stats {
  display: flex;
  gap: 4rem;
  justify-content: center;
}
.hero-stat {
  text-align: center;
}
.hero-stat-num {
  font-size: 2.5rem;
  font-weight: 700;
  color: #3b82f6;
  font-variant-numeric: tabular-nums;
}
.hero-stat-label {
  font-size: 0.75rem;
  color: rgba(255,255,255,0.4);
  letter-spacing: 0.1em;
  margin-top: 0.3rem;
}
.hero-quote {
  position: absolute;
  bottom: 3rem;
  left: 0;
  right: 0;
  text-align: center;
  z-index: 1;
}
.hero-quote-text {
  font-size: 0.9rem;
  color: rgba(255,255,255,0.3);
  letter-spacing: 0.2em;
}
.hero-quote-author {
  font-size: 0.7rem;
  color: rgba(255,255,255,0.2);
  margin-top: 0.3rem;
}
.hero-enter {
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
}
.hero-enter:hover {
  border-color: #3b82f6;
  color: #3b82f6;
  background: rgba(59,130,246,0.05);
}
.update-section {
  max-width: 780px;
  margin: 0 auto;
  padding: 4rem 2rem;
}
.update-section h2 {
  font-size: 1.3rem;
  font-weight: 600;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 0.5rem;
}
.update-list {
  list-style: none;
  padding: 0;
}
.update-list li {
  padding: 0.8rem 0;
  border-bottom: 1px solid #f3f4f6;
  display: flex;
  align-items: center;
  gap: 1rem;
}
.update-date {
  font-size: 0.8rem;
  color: #9ca3af;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
  min-width: 100px;
}
.update-cat {
  font-size: 0.75rem;
  padding: 0.1rem 0.6rem;
  border-radius: 3px;
  background: #f3f4f6;
  color: #6b7280;
  white-space: nowrap;
}
.update-title a {
  color: #1f2937;
  text-decoration: none;
  font-size: 0.9rem;
}
.update-title a:hover {
  color: #3b82f6;
}
</style>

<div class="hero">
  <div class="hero-content">
    <div class="hero-tag">INTERVIEW COLLECTION</div>
    <h1 class="hero-title">面试知识合集</h1>
    <div class="hero-subtitle">朝花夕拾 · 温故而知新</div>
    <div class="hero-divider"></div>
    <div class="hero-stats">
      <div class="hero-stat">
        <div class="hero-stat-num">5</div>
        <div class="hero-stat-label">收录题目</div>
      </div>
      <div class="hero-stat">
        <div class="hero-stat-num">4</div>
        <div class="hero-stat-label">分类</div>
      </div>
      <div class="hero-stat">
        <div class="hero-stat-num">2026-09-24</div>
        <div class="hero-stat-label">最近更新</div>
      </div>
    </div>
    <a href="css/centering.md" class="hero-enter">进入合集 →</a>
  </div>
  <div class="hero-quote">
    <div class="hero-quote-text">朝花夕拾 · 温故而知新</div>
    <div class="hero-quote-author">— 持续更新中</div>
  </div>
</div>

<div class="update-section">
  <h2>更新日志</h2>
  <ul class="update-list">
    <li>
      <span class="update-date">2026-09-24</span>
      <span class="update-cat">CSS</span>
      <span class="update-title"><a href="css/centering.md">CSS 居中方案</a></span>
    </li>
    <li>
      <span class="update-date">2026-09-24</span>
      <span class="update-cat">浏览器与网络</span>
      <span class="update-title"><a href="browser-network/http-caching.md">HTTP 缓存策略</a></span>
    </li>
    <li>
      <span class="update-date">2026-09-24</span>
      <span class="update-cat">JavaScript</span>
      <span class="update-title"><a href="javascript/event-loop.md">事件循环（Event Loop）</a></span>
    </li>
    <li>
      <span class="update-date">2026-09-24</span>
      <span class="update-cat">JavaScript</span>
      <span class="update-title"><a href="javascript/closure.md">闭包（Closure）</a></span>
    </li>
    <li>
      <span class="update-date">2026-09-24</span>
      <span class="update-cat">工程化</span>
      <span class="update-title"><a href="engineering/url-shortener.md">短链服务系统设计</a></span>
    </li>
  </ul>
</div>
