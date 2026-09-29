---
date: "2026-09-24"
category: "浏览器与网络"
title: "HTTP 缓存策略"
tags: [HTTP, 缓存, 性能, 304]
---

# HTTP 缓存策略

<div class="question-tags">
  <span class="question-tag">HTTP</span>
  <span class="question-tag">缓存</span>
  <span class="question-tag">性能</span>
  <span class="question-tag">304</span>
</div>


> 浏览器的 HTTP 缓存机制是怎样的？强缓存和协商缓存有什么区别？


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

### 协商缓存在后端的实现

后端处理协商缓存的核心逻辑：读取请求头 → 与资源当前状态比对 → 决定返回 304 还是 200。

#### ETag 方式（推荐）

```java
// Spring Boot 示例
@GetMapping("/api/data")
public ResponseEntity<?> getData(
        @RequestHeader(value = "If-None-Match", required = false) String ifNoneMatch) {

    String body = getDataAsJson(); // 获取数据并序列化

    // 1. 生成 ETag（内容的 MD5 哈希）
    String etag = "\"" + DigestUtils.md5Hex(body) + "\"";

    // 2. 比对：一致则返回 304，不返回 body
    if (etag.equals(ifNoneMatch)) {
        return ResponseEntity.status(HttpStatus.NOT_MODIFIED)
                .eTag(etag)
                .build();
    }

    // 3. 不一致则返回新资源 + 新 ETag
    return ResponseEntity.ok()
            .eTag(etag)
            .header("Cache-Control", "no-cache") // 每次都要协商
            .body(body);
}
```

#### Last-Modified 方式

```java
// Spring Boot 示例
@GetMapping("/static/{filename}")
public ResponseEntity<Resource> getStaticFile(
        @PathVariable String filename,
        @RequestHeader(value = "If-Modified-Since", required = false)
        String ifModifiedSince) throws IOException {

    Resource file = new FileSystemResource("./public/" + filename);
    long lastModified = file.getFile().lastModified();

    // 1. 格式化修改时间为 HTTP 日期
    String lastModifiedStr = ZonedDateTime
            .ofInstant(Instant.ofEpochMilli(lastModified), ZoneId.of("GMT"))
            .format(DateTimeFormatter.RFC_1123_DATE_TIME);

    // 2. 比对时间：未修改则返回 304
    if (ifModifiedSince != null) {
        long clientTime = ZonedDateTime
                .parse(ifModifiedSince, DateTimeFormatter.RFC_1123_DATE_TIME)
                .toInstant().toEpochMilli();
        if (clientTime >= lastModified) {
            return ResponseEntity.status(HttpStatus.NOT_MODIFIED).build();
        }
    }

    // 3. 已修改则返回新资源 + 新 Last-Modified
    return ResponseEntity.ok()
            .header("Last-Modified", lastModifiedStr)
            .header("Cache-Control", "no-cache")
            .body(file);
}
```

#### 两种方式对比

| | ETag | Last-Modified |
|--|------|---------------|
| 精度 | 内容级（哈希比对） | 秒级（时间比对） |
| 准确性 | 高，内容变则 ETag 变 | 低，1 秒内多次修改无法感知 |
| 性能 | 需计算哈希，有开销 | 读文件 mtime，开销小 |
| 优先级 | 高（同时存在时以 ETag 为准） | 低 |

> Nginx 默认开启 ETag（基于文件大小 + 修改时间生成），静态资源无需手写代码。

#### 为什么实际开发中很少手写协商缓存？

协商缓存看似优雅，但在实际业务中很少需要手动实现，原因如下：

**1. 静态资源由 Nginx / CDN 自动处理**

前端打包产物（JS、CSS、图片）通常由 Nginx 或 CDN 托管，它们默认开启了 ETag 和 Last-Modified，无需后端介入。配合文件名 hash + 长强缓存，命中率接近 100%。

**2. API 接口数据变化频繁，304 收益低**

协商缓存的前提是「资源不常变化」。但后端 API 返回的 JSON 数据（如用户列表、订单状态）几乎每次都不同，304 命中率极低，反而增加了每次请求都要计算 ETag/比对的开销。

**3. 计算成本可能抵消收益**

```java
// 要生成 ETag，必须先完整序列化数据 —— 这本身就是最耗时的操作
String body = getDataAsJson();       // ← 数据库查询 + 序列化，开销在这
String etag = md5Hex(body);          // ← 哈希本身很快，但为时已晚
```

生成 ETag 需要先拿到完整响应内容再做哈希，最耗时的数据库查询和序列化已经执行了，304 省下的只是网络传输，不是真正省掉计算。

**4. Spring 框架已提供 `ShallowEtagHeaderFilter`**

Spring 内置了开箱即用的 ETag 过滤器，自动对响应体生成 ETag，无需手写：

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Bean
    public FilterRegistrationBean<ShallowEtagHeaderFilter> etagFilter() {
        FilterRegistrationBean<ShallowEtagHeaderFilter> bean = new FilterRegistrationBean<>();
        bean.setFilter(new ShallowEtagHeaderFilter());
        bean.addUrlPatterns("/api/*");
        return bean;
    }
}
```

> 但注意它仍是「先完整执行 Controller → 再生成 ETag」，只省带宽不省计算。

**实际项目中的主流方案：** 静态资源靠 Nginx + hash 文件名 + 长强缓存；API 数据靠 Redis 缓存 + 主动失效，协商缓存更多是理论知识点。

### 五、最佳实践

- HTML 文件：`Cache-Control: no-cache`（每次协商）
- 带 hash 的静态资源：`Cache-Control: max-age=31536000`（强缓存一年）
- 入口文件配合 hash 文件名，实现更新与缓存两不误
