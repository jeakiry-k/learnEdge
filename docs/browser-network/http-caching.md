---
date: "2026-09-24"
category: "浏览器与网络"
title: "HTTP 缓存策略"
---

# HTTP 缓存策略

## 问题

> 浏览器的 HTTP 缓存机制是怎样的？强缓存和协商缓存有什么区别？

## 答案

浏览器缓存分为两个阶段：**强缓存** → **协商缓存**。

### 强缓存（不请求服务器）

| Header | 说明 |
|--------|------|
| `Cache-Control: max-age=31536000` | 缓存有效期（秒），优先级高 |
| `Expires: Wed, 24 Sep 2027 00:00:00 GMT` | 绝对过期时间 |

命中强缓存时，浏览器直接读本地副本，状态码 **200 (from disk/memory cache)**。

### 协商缓存（请求服务器验证）

| 方式 | 请求 Header | 响应 Header |
|------|------------|------------|
| Last-Modified | `If-Modified-Since` | `Last-Modified` |
| ETag（推荐） | `If-None-Match` | `ETag` |

命中协商缓存时，服务器返回 **304 Not Modified**，浏览器使用本地缓存。

### 完整流程

```
请求资源
  │
  ├─ 强缓存未过期？ ──是──→ 200 (from cache) ✅
  │     │
  │     否
  │     ▼
  ├─ 协商缓存验证 ──未修改──→ 304 ✅
  │     │
  │     已修改
  │     ▼
  └─ 服务器返回新资源 → 200 + 新缓存标识
```

### 最佳实践

- HTML 文件：`Cache-Control: no-cache`（每次协商）
- 带 hash 的静态资源：`Cache-Control: max-age=31536000`（强缓存一年）
- 入口文件配合 hash 文件名，实现更新与缓存两不误
