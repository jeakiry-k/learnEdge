---
date: "2026-09-28"
category: "Redis"
title: "Redis 连接池"
tags: [Redis, 连接池, 性能优化]
---

# Redis 连接池

<div class="question-tags">
  <span class="question-tag">Redis</span>
  <span class="question-tag">连接池</span>
  <span class="question-tag">性能优化</span>
</div>

> 为什么需要 Redis 连接池？连接池的核心参数有哪些？如何调优？

### 为什么需要连接池

每次操作 Redis 都新建 TCP 连接，用完再关闭，开销巨大：

```
无连接池：
  请求 → TCP 三次握手 → AUTH 认证 → 执行命令 → TCP 四次挥手
  每次请求都重复上述流程，QPS 高时连接建立/断开成为瓶颈

有连接池：
  启动时创建 N 个连接 → 复用 → 请求直接从池中取连接 → 用完归还
  省去了反复建连的开销
```

### 连接池核心参数

以 Java 主流的 **Lettuce** 和 **Jedis** 为例：

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `maxTotal` / `maxActive` | 最大连接数 | 根据并发量定，通常 50~200 |
| `maxIdle` | 最大空闲连接数 | 与 maxTotal 一致或略小 |
| `minIdle` | 最小空闲连接数 | 5~10，保证预热连接 |
| `maxWaitMillis` | 获取连接最大等待时间 | 1000~3000ms，超时抛异常 |
| `testOnBorrow` | 获取连接时检测连通性 | false（开启有性能损耗） |
| `testWhileIdle` | 空闲时定期检测 | true（推荐） |
| `timeBetweenEvictionRunsMillis` | 空闲检测间隔 | 30000ms |

#### Jedis 配置示例

```java
JedisPoolConfig config = new JedisPoolConfig();
config.setMaxTotal(100);           // 最大连接数
config.setMaxIdle(100);            // 最大空闲连接
config.setMinIdle(10);             // 最小空闲连接
config.setMaxWaitMillis(2000);     // 获取连接超时时间
config.setTestWhileIdle(true);     // 空闲时检测
config.setTimeBetweenEvictionRunsMillis(30000); // 检测间隔

JedisPool pool = new JedisPool(config, "127.0.0.1", 6379, 2000, "password");

// 使用
try (Jedis jedis = pool.getResource()) {
    jedis.set("key", "value");
}
```

#### Spring Boot Lettuce 配置

```yaml
spring:
  redis:
    host: 127.0.0.1
    port: 6379
    lettuce:
      pool:
        max-active: 100      # 最大连接数
        max-idle: 50         # 最大空闲连接
        min-idle: 10         # 最小空闲连接
        max-wait: 2000ms     # 获取连接超时
      shutdown-timeout: 100ms
```

> Lettuce 基于 Netty 的异步非阻塞模型，单连接可被多线程共享，连接数需求通常比 Jedis 少。

### 连接泄漏的常见原因

```java
// 错误：忘记归还连接（Jedis 未 try-with-resources）
Jedis jedis = pool.getResource();
jedis.set("key", "value");
// 漏了 jedis.close()，连接被占用不归还 → 池中连接逐渐耗尽

// 正确：try-with-resources 自动归还
try (Jedis jedis = pool.getResource()) {
    jedis.set("key", "value");
}
```

### 连接数怎么估算

```
单个 Redis 实例最大连接数通常 10000（redis.conf maxclients）

单应用连接池大小估算：
  maxTotal = (单次请求耗时 ms × 目标 QPS) / 1000 + 缓冲

  例：单次 Redis 操作 2ms，目标 QPS 5000
  maxTotal ≈ (2 × 5000) / 1000 + 20 = 30

多应用共享同一个 Redis 时：
  各应用 maxTotal 之和 < maxclients × 0.7（留 30% 余量给监控和运维）
```

### 连接池监控

```java
// Jedis 连接池监控
JedisPool pool = ...;
JedisPoolStats stats = pool.getPool().getStatistics();
// 可获取：活跃连接数、空闲连接数、等待线程数

// 或通过 Redis 命令查看当前连接数
// > INFO clients
// connected_clients:15
```

### 选型对比

| | Jedis | Lettuce |
|--|-------|---------|
| 线程模型 | 一连接一线程（阻塞） | 单连接多线程共享（异步非阻塞） |
| 连接池 | 需要配置 JedisPool | 内置共享连接，通常不需要额外池 |
| 性能 | 中等 | 更高（Netty 底层） |
| Spring Boot 默认 | 2.x 前默认 | 2.x 后默认 |

> Spring Boot 2.x 起默认使用 Lettuce，大部分场景无需手动配置连接池。
