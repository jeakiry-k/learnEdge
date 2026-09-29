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

### 一、为什么需要连接池

每次操作 Redis 都新建 TCP 连接，用完再关闭，开销巨大：

```
无连接池：
  请求 → TCP 三次握手 → AUTH 认证 → 执行命令 → TCP 四次挥手
  每次请求都重复上述流程，QPS 高时连接建立/断开成为瓶颈

有连接池：
  启动时创建 N 个连接 → 复用 → 请求直接从池中取连接 → 用完归还
  省去了反复建连的开销
```

### 二、连接池工作原理

连接池内部维护两个集合：**空闲连接集合**（idle）和**活跃连接集合**（active）。

```
应用启动
  │
  ▼
初始化 minIdle 个连接，放入空闲集合
  │
  ▼
线程 A 来请求 getResource()
  │
  ├─ 空闲集合有连接？ ──是──→ 取出，移入活跃集合，交给线程 A
  │     │
  │     否
  │     ▼
  ├─ 活跃连接数 < maxTotal？ ──是──→ 新建连接，放入活跃集合
  │     │
  │     否（池已满）
  │     ▼
  └─ 进入等待队列，等待 maxWaitMillis
        │
        ├─ 等待期间有连接归还 → 获取成功
        │
        └─ 超时仍无连接 → 抛出异常
              JedisConnectionException:
              Could not get a resource from the pool

线程 A 用完 close()/try-with-resources
  │
  ▼
连接从活跃集合移回空闲集合（不是真正关闭 TCP），等待下一个线程复用
```

#### 关键机制

| 机制 | 说明 |
|------|------|
| 借还模型 | `getResource()` 借出 → `close()` 归还，`close()` 对池化连接不是关闭 TCP，而是归还池中 |
| 按需扩容 | 空闲连接不够时才新建连接，直到 maxTotal |
| 空闲回收 | 后台线程定期销毁超过 maxIdle 的空闲连接，保持在 minIdle~maxIdle 之间 |
| 阻塞等待 | 池满后线程排队等待，超时快速失败而非无限挂起 |
| 连接保活 | `testWhileIdle` 定期检测空闲连接活性，防止取到已被 Redis 端断开的死连接 |

> 关键理解：**连接池里的 TCP 连接是长连接**，应用运行期间持续保持，避免反复三次握手/四次挥手。

#### minIdle 与 maxIdle 的处理机制

两个参数共同控制「空闲连接」的保底与上限：

| 参数 | 角色 | 处理时机 |
|------|------|---------|
| `minIdle` | 空闲保底数，池自动补足，永不低于此值 | 后台线程定时巡检 |
| `maxIdle` | 空闲上限，归还时超出的连接直接关闭 | 连接归还时刻 |

```
【扩容：保证不低于 minIdle】
Evictor 后台线程（每 timeBetweenEvictionRunsMillis 巡检一次）
  │
  ├─ 空闲连接数 < minIdle？
  │     └─ 是 → 创建新连接补足到 minIdle
  │
  └─ 缩容检查：空闲数 > minIdle
        且该连接空闲时长 > minEvictableIdleTimeMillis（默认 30 分钟）？
              └─ 是 → 销毁多余空闲连接，回落到 minIdle

【归还：不超过 maxIdle】
线程用完连接，close() 归还
  │
  ├─ 当前空闲连接数 < maxIdle → 放回空闲集合，供下次复用
  │
  └─ 当前空闲连接数 ≥ maxIdle → 不入池，直接物理关闭 TCP
```

要点：

1. **minIdle 是保底**：Evictor 线程发现空闲数不足会自动补建连接（commons-pool2 的 ensureMinIdle 机制，Jedis/Lettuce 均基于此）
2. **maxIdle 只影响归还动作**：借出时不受它限制（受 maxTotal 限制），归还时池满即关
3. **缩容不是直接砍到 minIdle**：空闲超过 minIdle 的连接，还要再满足「空闲时长超过 30 分钟」才会被回收，避免流量短暂波动导致频繁建连
4. **maxIdle 不宜远小于 maxTotal**：否则高峰期新建的连接归还时会被 maxIdle 挤掉关闭，流量回升又要重建，造成「连接抖动」。推荐 `maxIdle ≈ maxTotal`

```java
JedisPoolConfig config = new JedisPoolConfig();
config.setMinIdle(10);    // 保底 10 个空闲连接，掉下去自动补
config.setMaxIdle(100);   // 归还时空闲已满 100 个 → 直接关闭，不入池
```

### 三、连接池核心参数

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

### 四、连接泄漏的常见原因

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

### 五、连接池耗尽时如何排查

报错特征：

```
redis.clients.jedis.exceptions.JedisConnectionException:
  Could not get a resource from the pool
Caused by: java.util.NoSuchElementException: Timeout waiting for idle object
```

含义：池中的 maxTotal 个连接全部处于活跃状态，新线程在 maxWaitMillis 内没等到任何连接归还。

#### 第一步：看连接池监控指标，确认是哪种耗尽

```java
GenericObjectPoolConfig<?> config = ...;
GenericObjectPool<Jedis> internalPool = ((JedisPool) pool).getResourcePoolInternal();

// 实时打印连接池状态
System.out.println("活跃连接 active: " + internalPool.getNumActive());
System.out.println("空闲连接 idle:   " + internalPool.getNumIdle());
System.out.println("等待线程 waiters: " + internalPool.getNumWaiters());
```

| 现象 | 判断 |
|------|------|
| `active = maxTotal` 且持续不降 | 连接被借走后不归还（泄漏或慢操作） |
| `waiters` 持续增长 | 并发量超过池容量或处理变慢 |
| Redis 端 `connected_clients` 很高 | 多应用连接数之和超限或有连接泄漏 |

#### 第二步：Redis 端查看连接情况

```bash
# 当前连接总数
redis-cli INFO clients | grep connected_clients

# 查看所有连接的详情
redis-cli CLIENT LIST
# addr=10.0.0.1:52340 age=3600 idle=3600 cmd=get   ← age/idle 很大：长期空闲或泄漏
# addr=10.0.0.2:52341 age=10 idle=0 cmd=blpop       ← 阻塞命令占着连接

# 找出空闲时间最长的连接（可能是泄漏连接）
redis-cli CLIENT LIST | sort -t= -k5 -n | tail -20
```

关键字段含义（单位均为秒）：

| 字段 | 含义 |
|------|------|
| `age` | 连接从建立至今的**总存活时长** |
| `idle` | 距离**最后一次执行命令**的空闲时长 |

```
age - idle = 该连接实际在干活的总时长

age=3600, idle=3600 → idle == age：建立后几乎没干过活 → 空闲连接/泄漏
age=3600, idle=0    → 刚执行完命令，正在持续工作 → 正常活跃连接
age=3600, idle=3000 → 建立很久但最近 50 分钟没动 → 疑似池中闲置
```

> `idle` 很大不一定就是泄漏——连接池里的空闲连接本来就常驻，需结合应用侧 `active` 指标判断；但 `idle == age` 且数量超过池的 minIdle，大概率是泄漏。

#### 第三步：按常见原因逐一排查

**原因 1：连接泄漏（最常见）**

```java
// 排查代码中所有 getResource()，确认每个都有配对 close
// 高危写法：异常分支漏归还
Jedis jedis = pool.getResource();
try {
    jedis.set("k", "v");
    // ❌ 这里 return 或抛异常，下面的 close() 不执行
} finally {
    jedis.close();   // 必须放在 finally
}
```

特征：`active` 数只增不减，重启应用后暂时恢复，一段时间后再次耗尽。

**原因 2：慢命令占用连接过久**

```bash
# 慢查询会让连接长时间处于活跃状态
redis-cli SLOWLOG GET 10
redis-cli --bigkeys
```

典型场景：执行 `KEYS *`、大 key 的 `HGETALL`、`SMEMBERS`，连接被占用数秒。

**原因 3：阻塞式命令不返回**

```bash
# BLPOP、BRPOP、SUBSCRIBE 会长期占用连接
# 连接池连接数会被这些命令慢慢吃光
```

**原因 4：池容量配置过小**

```java
// 临时应急：调大连接池
config.setMaxTotal(200);
config.setMaxIdle(100);
config.setMaxWaitMillis(3000);
```

注意：单纯调大不是根本方案，连接数过大也会增加 Redis 端压力，需结合 QPS 估算。

**原因 5：Redis 端响应变慢或网络问题**

```bash
# 查看 Redis 延迟
redis-cli --latency-history -i 1

# 检查是否开启了持久化导致卡顿
redis-cli INFO persistence   # rdb_bgsave_in_progress
```

#### 第四步：临时止血与根治

```
临时止血：
  1. 重启应用实例（清空泄漏连接）
  2. 临时调大 maxTotal / maxWaitMillis
  3. Redis 端用 CLIENT KILL 杀掉异常空闲连接：
     redis-cli CLIENT KILL ADDR 10.0.0.1:52340

根治：
  1. 修复连接泄漏：统一 try-with-resources
  2. 禁用 KEYS、大 key 全量读取等慢操作
  3. 阻塞命令（BLPOP/SUB）使用独立连接，不进通用池
  4. 接入监控：持续采集 active/idle/waiters 指标并告警
```

### 六、连接数怎么估算

```
单个 Redis 实例最大连接数通常 10000（redis.conf maxclients）

单应用连接池大小估算：
  maxTotal = (单次请求耗时 ms × 目标 QPS) / 1000 + 缓冲

  例：单次 Redis 操作 2ms，目标 QPS 5000
  maxTotal ≈ (2 × 5000) / 1000 + 20 = 30

多应用共享同一个 Redis 时：
  各应用 maxTotal 之和 < maxclients × 0.7（留 30% 余量给监控和运维）
```

#### 多应用共享 Redis：连接总数超限会怎样

连接数按**应用实例数 × maxTotal** 累加，很容易超预估：

```
应用 A：5 个实例 × maxTotal 200 = 1000 连接
应用 B：10 个实例 × maxTotal 100 = 1000 连接
监控/运维连接：约 50
─────────────────────────────────
合计 2050，而 maxclients 默认 10000
→ 应用继续扩容实例、或调大 maxTotal，就可能撞上限

Redis Cluster 下更严重：maxclients 是单节点维度，
客户端与每个节点都建连，实际连接 = 实例数 × maxTotal × 节点数
```

超限后的行为：

1. **新连接被拒绝**：Redis 达到 maxclients 后对新连接返回错误并立即关闭：
   `ERR max number of clients reached`
2. **存量连接不受影响**：已建立的连接继续正常工作——所以故障表现是「间歇性、新请求报错、老连接正常」，容易误判为偶发网络抖动
3. **客户端表现**：连接池获取/新建连接时抛异常（Connection reset、max number of clients reached），并连带触发获取连接超时

排查哪个应用占用最多：

```bash
# 确认上限与当前连接数
redis-cli CONFIG GET maxclients
redis-cli INFO clients | grep -E "connected_clients|maxclients"

# 按来源 IP 统计连接数，找出占用大户
redis-cli CLIENT LIST | grep -o 'addr=[^ ]*' \
  | cut -d= -f2 | cut -d: -f1 | sort | uniq -c | sort -rn | head
```

解决方案：

| 方案 | 说明 |
|------|------|
| 事前估算 | Σ(实例数 × maxTotal) < maxclients × 0.7，纳入发布检查 |
| 临时扩容 | `CONFIG SET maxclients 20000`（注意连接本身占内存，需留余量） |
| 治本：减少连接数 | 调小各应用 maxTotal；或统一改用 Lettuce（单连接多线程共享，连接数骤减） |
| 治本：代理收敛 | 多应用直连改为经代理层访问，由代理维护与 Redis 的少量长连接 |
| 治理闲置 | `CONFIG SET timeout 300` 自动断开长期空闲连接（对阻塞命令无效） |

### 七、连接池监控

```java
// Jedis 连接池监控
JedisPool pool = ...;
JedisPoolStats stats = pool.getPool().getStatistics();
// 可获取：活跃连接数、空闲连接数、等待线程数

// 或通过 Redis 命令查看当前连接数
// > INFO clients
// connected_clients:15
```

### 八、选型对比

| | Jedis | Lettuce |
|--|-------|---------|
| 线程模型 | 一连接一线程（阻塞） | 单连接多线程共享（异步非阻塞） |
| 连接池 | 需要配置 JedisPool | 内置共享连接，通常不需要额外池 |
| 性能 | 中等 | 更高（Netty 底层） |
| Spring Boot 默认 | 2.x 前默认 | 2.x 后默认 |

> Spring Boot 2.x 起默认使用 Lettuce，大部分场景无需手动配置连接池。
