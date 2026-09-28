---
date: "2026-09-28"
category: "Redis"
title: "Redis 常见异常"
tags: [Redis, 异常, 排查]
---

# Redis 常见异常

<div class="question-tags">
  <span class="question-tag">Redis</span>
  <span class="question-tag">异常</span>
  <span class="question-tag">排查</span>
</div>

> Redis 使用中常见的异常有哪些？什么原因导致？如何排查和解决？

### 异常总览

| 异常 | 原因 | 影响 |
|------|------|------|
| 连接超时 | 网络不通、防火墙、连接数耗尽 | 无法操作 Redis |
| 命令超时 | 大 key、慢查询、阻塞操作 | 部分命令无响应 |
| OOM | 内存超限，被 maxmemory 淘汰或拒绝写入 | 数据丢失或写入失败 |
| 主从切换 | 主节点宕机，哨兵/集群自动切换 | 短暂不可用 |
| 脑裂 | 网络分区导致多个主节点 | 数据不一致 |
| 客户端缓冲区溢出 | 输出缓冲区超限 | 连接被强制断开 |

---

### 1. 连接超时 `RedisConnectionException`

```
redis.clients.jedis.exceptions.JedisConnectionException:
  Could not get a resource from the pool
```

#### 常见原因

| 原因 | 排查方式 |
|------|---------|
| Redis 服务未启动或端口不对 | `redis-cli ping` 测试连通性 |
| 防火墙/安全组未放行 | `telnet <ip> 6379` 测试端口 |
| 连接池耗尽（maxTotal 太小或连接泄漏） | 检查是否有未归还的连接 |
| 密码错误 | 看日志 `WRONGPASS` |
| 客户端超过 `maxclients` | `INFO clients` 查看连接数 |

#### 解决

```bash
# 排查 Redis 端连接数
redis-cli INFO clients
# connected_clients:15

# 查看最大连接数配置
redis-cli CONFIG GET maxclients
# maxclients 10000

# 如果连接数异常高，查看连接来源
redis-cli CLIENT LIST
```

```java
// 排查连接泄漏：确保所有 getResource 都有对应 close
try (Jedis jedis = pool.getResource()) {  // try-with-resources 自动归还
    jedis.set("k", "v");
}

// 连接池参数调优：增大 maxTotal 或缩短 maxWaitMillis
config.setMaxTotal(200);
config.setMaxWaitMillis(1000); // 超时快速失败而非无限等待
```

---

### 2. 命令超时 `JedisDataException`

```
redis.clients.jedis.exceptions.JedisDataException:
  ERR Command timed out
```

#### 常见原因

| 原因 | 说明 |
|------|------|
| 大 key 操作 | 对一个 10MB 的 Hash 执行 HGETALL |
| KEYS 命令 | 阻塞 Redis 单线程，百万 key 时卡数秒 |
| FLUSHALL / DEL 大 key | 同步删除大量数据阻塞主线程 |
| 慢查询 | SORT、SUNION 等复杂度高的命令 |

#### 排查

```bash
# 查看慢查询
redis-cli SLOWLOG GET 10

# 查看大 key
redis-cli --bigkeys

# 查看阻塞命令
redis-cli INFO stats  # latest_fork_usec 看是否有大的 fork 操作
```

#### 解决

```bash
# 禁用 KEYS，改用 SCAN（非阻塞遍历）
redis-cli SCAN 0 COUNT 100

# 大 key 删除用 UNLINK（异步删除，Redis 4.0+）
UNLINK huge_key   # 替代 DEL huge_key
```

---

### 3. OOM / 内存超限

```
OOM command not allowed when used memory > 'maxmemory'.
```

#### 原因

Redis 内存达到 `maxmemory` 限制，且淘汰策略为 `noeviction`（不淘汰）。

#### 解决

```bash
# 查看内存使用
redis-cli INFO memory
# used_memory_human:2.5GB
# maxmemory_human:4GB

# 查看淘汰策略
redis-cli CONFIG GET maxmemory-policy
# maxmemory-policy noeviction  ← 不淘汰，满了直接报错

# 改为 LRU 淘汰
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

| 淘汰策略 | 说明 |
|---------|------|
| `noeviction` | 不淘汰，写入直接报错（默认） |
| `allkeys-lru` | 所有 key 中淘汰最近最少使用的（推荐） |
| `volatile-lru` | 仅淘汰设了过期的 key |
| `allkeys-random` | 随机淘汰 |
| `volatile-ttl` | 淘汰即将过期的 key |

---

### 4. 主从切换 / 哨兵故障转移

```
redis.clients.jedis.exceptions.JedisConnectionException:
  Failed to get a resource from the pool or server is down
```

#### 原因

主节点宕机，哨兵自动将某个从节点提升为主节点，客户端需要感知切换。

#### 解决

```java
// Jedis 哨兵模式：自动感知主节点切换
Set<String> sentinels = new HashSet<>();
sentinels.add("127.0.0.1:26379");
sentinels.add("127.0.0.1:26380");

JedisSentinelPool pool = new JedisSentinelPool("mymaster", sentinels, config);
// 哨兵会自动将请求路由到新的主节点
```

```yaml
# Spring Boot Lettuce 哨兵配置
spring:
  redis:
    sentinel:
      master: mymaster
      nodes: 127.0.0.1:26379,127.0.0.1:26380
```

---

### 5. 脑裂

#### 原因

网络分区导致哨兵认为主节点下线，提升了一个从节点为新主。但原主节点网络恢复后仍在接受写入，产生两个主节点。

#### 危害

原主节点的写入数据会丢失（切换后被降级为从，数据被覆盖）。

#### 预防

```bash
# 配置 min-slaves-to-write：主节点至少有 N 个从节点在线才接受写入
CONFIG SET min-slaves-to-write 1
# 网络分区时，原主节点没有从节点在线 → 拒绝写入 → 避免脑裂
```

---

### 6. 客户端输出缓冲区溢出

```
Client closed the connection or subscription disconnected
```

#### 原因

客户端读取速度跟不上 Redis 推送速度（如 SUBSCRIBE/SUB、MONITOR），输出缓冲区超过 `client-output-buffer-limit` 被强制断开。

#### 排查

```bash
# 查看客户端输出缓冲区大小
redis-cli CLIENT LIST
# omem=2097152  ← 输出缓冲区占用 2MB

# 查看缓冲区限制
redis-cli CONFIG GET client-output-buffer-limit
```

#### 解决

```bash
# 调大 pubsub 客户端缓冲区限制
CONFIG SET client-output-buffer-limit "pubsub 64mb 16mb 60"
# 格式：<类别> <硬限制> <软限制> <软限制时长>
# 硬限制达到立即断开，软限制持续指定时长也断开
```

### 异常排查通用思路

```
1. 先看网络：telnet / ping 确认连通性
2. 再看 Redis：INFO 命令看连接数、内存、延迟
3. 看慢日志：SLOWLOG GET 看是否有阻塞命令
4. 看大 key：--bigkeys 扫描
5. 看客户端：连接池配置是否合理，是否有连接泄漏
```
