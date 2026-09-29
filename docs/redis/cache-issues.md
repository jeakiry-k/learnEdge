---
date: "2026-09-28"
category: "Redis"
title: "缓存穿透、击穿、雪崩"
tags: [缓存, Redis, 高并发]
---

# 缓存穿透、击穿、雪崩

<div class="question-tags">
  <span class="question-tag">缓存</span>
  <span class="question-tag">Redis</span>
  <span class="question-tag">高并发</span>
</div>

> 缓存穿透、缓存击穿、缓存雪崩分别是什么？如何形象地理解并预防？

### 一、一句话类比

| 问题 | 形象类比 | 本质 |
|------|---------|------|
| 穿透 | 查了一个**根本不存在**的学号，教务系统说没有，你反复查 | 请求绕过缓存，直接打数据库，**查的 key 本身就不存在** |
| 击穿 | 某个**热门商品**的缓存刚好过期，瞬间大量请求涌入，把数据库压垮 | **单个热点 key 过期**，高并发直接打到 DB |
| 雪崩 | 大量缓存的过期时间**集中在同一时刻**，一起失效，请求全部涌向数据库 | **大面积 key 同时过期**，DB 瞬间过载 |

> 记忆口诀：穿透是「查的东西不存在」，击穿是「一个点被击穿」，雪崩是「一大片同时崩」。

---

### 二、缓存穿透

#### 场景

用户请求一个数据库中根本不存在的 key（如恶意攻击，用随机 ID 大量请求）：

```
请求 id=-1（不存在）
  → Redis 没有 → 查数据库 → 数据库也没有 → 返回空
  → 下次请求 id=-1 还是走一遍同样的流程
  → 恶意请求大量打 DB → 数据库压垮
```

#### 预防方案

**1. 缓存空值（最简单）**

```java
public User getUser(Long id) {
    String key = "user:" + id;
    Object val = redis.get(key);

    // 命中空值缓存，直接返回 null，不查 DB
    if ("NULL".equals(val)) {
        return null;
    }

    User user = userMapper.selectById(id);

    if (user == null) {
        // 缓存空值，设置短过期时间（防止数据后续被新增）
        redis.setex(key, 60, "NULL");
        return null;
    }

    redis.setex(key, 3600, JSON.toJSONString(user));
    return user;
}
```

**2. 布隆过滤器（更精确）**

在缓存之前加一层布隆过滤器，只存 key 的「是否存在」标记：

```java
public User getUser(Long id) {
    // 先过布隆过滤器：不存在则直接返回，不查 Redis 也不查 DB
    if (!bloomFilter.mightContain("user:" + id)) {
        return null;
    }

    String val = redis.get("user:" + id);
    if (val != null) {
        return JSON.parseObject(val, User.class);
    }

    User user = userMapper.selectById(id);
    if (user != null) {
        redis.setex("user:" + id, 3600, JSON.toJSONString(user));
    }
    return user;
}
```

> 布隆过滤器有极低误判率（说不存在就一定不存在，说存在可能不存在），适合防止恶意穿透。

---

### 三、缓存击穿

#### 场景

某个**热点 key**（如秒杀商品详情）缓存过期的瞬间，大量并发请求同时涌入：

```
热门商品 key 过期
  → 1000 个请求同时到达 Redis → 都没命中
  → 1000 个请求同时查数据库 → 数据库被压垮
```

#### 预防方案

**1. 互斥锁（推荐，只放一个请求去查 DB）**

```java
public String getProduct(Long id) {
    String key = "product:" + id;
    String val = redis.get(key);

    if (val != null) {
        return val;
    }

    // 获取分布式锁，只有一个线程能查数据库
    String lockKey = "lock:product:" + id;
    try {
        // setnx + 过期时间 = 简易分布式锁
        boolean locked = redis.setnx(lockKey, "1", 10);
        if (!locked) {
            // 没拿到锁，短暂等待后重试
            Thread.sleep(50);
            return getProduct(id);
        }

        // 拿到锁，查数据库
        val = redis.get(key); // double check，防止前一个线程已写回
        if (val != null) {
            return val;
        }

        Product product = productMapper.selectById(id);
        val = JSON.toJSONString(product);
        redis.setex(key, 3600, val);
        return val;
    } finally {
        redis.del(lockKey);
    }
}
```

**2. 热点 key 永不过期（适合极端热点）**

```java
// 不设 TTL，通过后台异步更新
redis.set("product:hot", val); // 无过期时间

// 后台定时任务检测数据变化，主动刷新缓存
@Scheduled(fixedDelay = 60000)
public void refreshHotKeys() {
    Product product = productMapper.selectById(HOT_ID);
    redis.set("product:hot", JSON.toJSONString(product));
}
```

---

### 四、缓存雪崩

#### 场景

大量 key 的过期时间**集中在同一时刻**，一起失效：

```
00:00:00  商品缓存过期 → 10 万请求涌向 DB
00:00:00  用户缓存过期 → 又 10 万请求
00:00:00  文章缓存过期 → 再 10 万请求
→ 数据库瞬间过载 → 雪崩
```

#### 预防方案

**1. 过期时间加随机偏移（最关键）**

```java
// 错误做法：所有 key 统一 3600 秒
redis.setex(key, 3600, val);

// 正确做法：3600 + 随机 0~300 秒，打散过期时间
int ttl = 3600 + ThreadLocalRandom.current().nextInt(300);
redis.setex(key, ttl, val);
```

**2. 多级缓存（兜底）**

```java
public String getData(String key) {
    // L1: 本地缓存（Caffeine / Guava）
    String val = localCache.getIfPresent(key);
    if (val != null) return val;

    // L2: Redis
    val = redis.get(key);
    if (val != null) return val;

    // L3: 数据库
    val = db.query(key);
    int ttl = 3600 + ThreadLocalRandom.current().nextInt(300);
    redis.setex(key, ttl, val);
    localCache.put(key, val);
    return val;
}
```

**3. 限流降级（最后一道防线）**

当数据库负载过高时，直接返回降级数据，保护 DB 不被打垮：

```java
public String getData(String key) {
    String val = redis.get(key);
    if (val != null) return val;

    // 限流：每秒最多 100 个请求查 DB
    if (!rateLimiter.tryAcquire()) {
        return getDefaultData(); // 返回降级数据或空页面
    }

    val = db.query(key);
    redis.setex(key, 3600 + random(300), val);
    return val;
}
```

---

### 五、三者对比总结

| | 缓存穿透 | 缓存击穿 | 缓存雪崩 |
|--|---------|---------|---------|
| 原因 | 查的 key **不存在** | **热点** key 过期 | **大面积** key 同时过期 |
| 规模 | 持续打 DB | 高并发打 DB | 瞬间洪峰打 DB |
| 预防 | 缓存空值 / 布隆过滤器 | 互斥锁 / 永不过期 | 随机过期 + 多级缓存 + 限流降级 |
| 关键词 | 不存在 | 单点热点 | 大面积失效 |
