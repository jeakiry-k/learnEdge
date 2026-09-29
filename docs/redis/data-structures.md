---
title: Redis 数据结构
description: Redis 五大基础数据结构（String、Hash、List、Set、ZSet）的底层实现、适用场景与选型对比。
date: 2026-09-29
category: Redis
tags: [Redis, 数据结构, 底层实现]
---

> Redis 支持多种数据结构，每种数据结构的底层实现和适用场景是什么？如何根据业务选择合适的数据结构？

### 一、五大基础数据结构概览

| 类型 | 底层实现 | 时间复杂度 | 典型场景 |
|------|---------|-----------|---------|
| **String** | SDS（简单动态字符串） | O(1) | 缓存、计数器、分布式锁 |
| **Hash** | ziplist / hashtable | O(1) | 对象存储、购物车 |
| **List** | ziplist / quicklist | O(1) 两端 / O(N) 中间 | 消息队列、时间线、栈 |
| **Set** | intset / hashtable | O(1) | 去重、共同好友、抽奖 |
| **ZSet** | ziplist / skiplist | O(logN) | 排行榜、延迟队列 |

---

### 二、String

**底层实现：SDS（Simple Dynamic String）**

```
struct sdshdr {
    int len;        // 已使用长度（O(1) 获取字符串长度）
    int free;       // 剩余可用空间（空间预分配，减少内存重分配）
    char buf[];     // 实际存储的字节数组
}
```

**SDS vs C 字符串：**

| 特性 | C 字符串 | SDS |
|------|---------|-----|
| 获取长度 | O(N) 遍历 | O(1) 读 len |
| 防止溢出 | 容易溢出 | 自动扩容 |
| 减少重分配 | 每次修改都重分配 | 空间预分配 + 惰性释放 |
| 二进制安全 | 不能存 `\0` | 可以存任意二进制 |

**适用场景：**

```bash
# 缓存对象（JSON 序列化）
SET user:1 '{"name":"张三","age":25}'

# 计数器（原子操作）
INCR article:1001:views

# 分布式锁
SET lock:order:123 uuid NX EX 30

# 限流（令牌桶）
SET rate:limit:api 100 EX 60
```

---

### 三、Hash

**底层实现：ziplist / hashtable**

- 字段少且值小 → ziplist（压缩列表，节省内存）
- 字段多或值大 → hashtable（哈希表，O(1) 查询）

```
ziplist（紧凑存储）：
┌────────┬────────┬────────┬────────┐
│ name   │ 张三   │ age    │ 25     │
└────────┴────────┴────────┴────────┘

hashtable（标准哈希表）：
name → 张三
age  → 25
```

**转换条件（Redis 6.x）：**

```conf
hash-max-ziplist-entries 512   # 字段数超过 512 转 hashtable
hash-max-ziplist-value 64      # 值超过 64 字节转 hashtable
```

**适用场景：**

```bash
# 存储对象（比 String JSON 更灵活）
HSET user:1 name 张三 age 25 city 北京

# 购物车
HSET cart:user:1 product:1001 2
HSET cart:user:1 product:1002 1

# 统计用户属性
HINCRBY user:1 login_count 1
```

**String JSON vs Hash 对比：**

| 维度 | String JSON | Hash |
|------|-------------|------|
| 内存占用 | 序列化开销大 | 更紧凑 |
| 字段更新 | 需整体替换 | 单字段更新 |
| 序列化 | 需 JSON 解析 | 直接操作 |
| 适用场景 | 简单缓存 | 对象属性频繁更新 |

---

### 四、List

**底层实现：ziplist / quicklist**

- Redis 3.2 之前：ziplist / linkedlist
- Redis 3.2 之后：**quicklist**（ziplist + linkedlist 的混合）

```
quicklist：
┌─────────┐    ┌─────────┐    ┌─────────┐
│ ziplist │◄──►│ ziplist │◄──►│ ziplist │
│ 节点1   │    │ 节点2   │    │ 节点3   │
└─────────┘    └─────────┘    └─────────┘
     ↑ 双向链表连接多个 ziplist
```

**适用场景：**

```bash
# 消息队列（简单版）
LPUSH queue:task task1
BRPOP queue:task 5

# 时间线（Timeline）
LPUSH timeline:user:1 "发布了一条动态"
LRANGE timeline:user:1 0 9

# 栈
LPUSH stack:data item1
LPOP stack:data

# 最新消息列表
LPUSH news:latest news1
LTRIM news:latest 0 99  # 只保留最近 100 条
```

---

### 五、Set

**底层实现：intset / hashtable**

- 元素都是整数且数量少 → intset（整数集合，节省内存）
- 否则 → hashtable（value 为 NULL 的哈希表）

**适用场景：**

```bash
# 去重
SADD user:1:tags tag1 tag2 tag3

# 共同好友
SINTER user:1:friends user:2:friends

# 抽奖
SADD lottery:pool user1 user2 user3
SRANDMEMBER lottery:pool 3  # 随机抽 3 人

# 点赞/收藏
SADD post:1001:likes user1
SISMEMBER post:1001:likes user1  # 是否已点赞
```

---

### 六、ZSet（Sorted Set）

**底层实现：ziplist / skiplist + hashtable**

- 元素少且小 → ziplist
- 否则 → **skiplist（跳表）+ hashtable**

```
skiplist（跳表）：
Level 3:  1 ──────────────────────► 100
Level 2:  1 ──────────► 50 ────────► 100
Level 1:  1 ────► 25 ──► 50 ──► 75 ──► 100
          ↑ 多层索引，O(logN) 查询

hashtable：member → score 映射，O(1) 获取分数
```

**为什么用跳表而不是红黑树？**

| 维度 | 跳表 | 红黑树 |
|------|------|--------|
| 实现复杂度 | 简单 | 复杂 |
| 范围查询 | 高效（链表遍历） | 需中序遍历 |
| 并发友好 | 容易实现无锁 | 加锁复杂 |
| 内存占用 | 额外索引层 | 更紧凑 |

**适用场景：**

```bash
# 排行榜
ZADD leaderboard 100 user1
ZADD leaderboard 95 user2
ZREVRANGE leaderboard 0 9 WITHSCORES  # TOP 10

# 延迟队列
ZADD delay:queue 1635000000 task1  # score 为执行时间戳
ZRANGEBYSCORE delay:queue 0 now    # 获取到期任务

# 热搜榜
ZINCRBY hot:search 1 "关键词"

# 滑动窗口限流
ZADD rate:limit:user:1 now uuid
ZREMRANGEBYSCORE rate:limit:user:1 0 (now-60000)  # 移除1分钟前
ZCARD rate:limit:user:1  # 统计1分钟内请求数
```

---

### 七、底层数据结构详解

#### ziplist（压缩列表）

紧凑的连续内存块，节省内存，适合小数据量。

```
┌──────┬──────┬──────┬──────┬──────┬──────┐
│zlbytes│zltail│zllen │entry1│entry2│zlend │
└──────┴──────┴──────┴──────┴──────┴──────┘
  总字节数  尾偏移  元素数  实际数据      结束符
```

**优点：** 内存紧凑，无指针开销
**缺点：** 插入/删除需内存重分配，级联更新风险

#### skiplist（跳表）

多层有序链表，空间换时间，O(logN) 查询。

```c
typedef struct zskiplistNode {
    sds ele;                          // 成员对象
    double score;                     // 分数
    struct zskiplistNode *backward;   // 后退指针
    struct zskiplistLevel {
        struct zskiplistNode *forward; // 前进指针
        unsigned long span;            // 跨度（用于排名计算）
    } level[];                         // 层级数组
} zskiplistNode;
```

---

### 八、选型建议

| 业务场景 | 推荐类型 | 原因 |
|---------|---------|------|
| 缓存对象 | String / Hash | String 简单，Hash 支持单字段更新 |
| 计数器 | String | INCR 原子操作 |
| 消息队列 | List | LPUSH + BRPOP 简单可靠 |
| 去重 | Set | 天然去重 |
| 排行榜 | ZSet | 自动排序 + 范围查询 |
| 延迟队列 | ZSet | score 存时间戳，定时扫描 |
| 共同好友 | Set | SINTER 交集运算 |
| 分布式锁 | String | SET NX EX 原子性 |

---

### 九、内存优化建议

1. **小数据量用 ziplist**：控制字段数 < 512，值 < 64 字节
2. **避免大 key**：单个 key 的 value 不超过 10KB
3. **合理设置过期时间**：避免内存无限增长
4. **使用 Hash 代替多个 String**：`user:1:name`、`user:1:age` → `HSET user:1 name xxx age 25`

---

### 十、面试常见陷阱

#### 1. String 的 SDS 和普通字符串混淆

**陷阱问题：** Redis 的 String 和 Java 的 String 有什么区别？

**错误回答：** 都是字符串，没什么区别。

**正确回答：**
- Redis String 底层是 **SDS**（简单动态字符串），不是 C 字符串
- SDS 有 len 字段，获取长度是 O(1)；C 字符串要遍历，O(N)
- SDS 有空间预分配和惰性释放，减少内存重分配
- SDS 是二进制安全的，可以存 `\0`、图片、序列化对象；C 字符串遇 `\0` 就截断

#### 2. Hash 和 String JSON 混用

**陷阱问题：** 存储用户信息，用 String JSON 还是 Hash？

**错误回答：** 都可以，随便用。

**正确回答：**

| 场景 | 推荐 | 原因 |
|------|------|------|
| 读多写少，整体读取 | String JSON | 一次 GET，序列化简单 |
| 字段频繁更新 | Hash | HSET 单字段更新，无需整体替换 |
| 字段数多（>10） | Hash | 内存更紧凑 |
| 需要部分字段 | Hash | HGET/HMGET 按需获取 |

**反例：** 用 String JSON 存用户信息，每次改个字段都要 GET → 反序列化 → 修改 → 序列化 → SET，性能差且并发不安全。

#### 3. List 当消息队列的坑

**陷阱问题：** 用 List 做消息队列有什么问题？

**错误回答：** LPUSH + BRPOP 很简单，没问题。

**正确回答：**

- **没有 ACK 机制**：消费者处理失败，消息已出队，丢失
- **没有重复消费**：一条消息只能被一个消费者拿到，无法实现广播
- **没有消息回溯**：消费完就删除，无法重新消费历史消息

**解决方案：**
- 简单场景：List + 应用层重试/补偿
- 复杂场景：用 Redis Stream（Redis 5.0+）或专业 MQ（Kafka/RabbitMQ）

#### 4. Set 和 ZSet 的混淆

**陷阱问题：** 排行榜为什么用 ZSet 不用 Set？

**错误回答：** Set 也能存用户 ID，用 Set 就行。

**正确回答：**
- Set 是无序的，无法按分数排序
- ZSet 有 score 字段，自动排序，支持 `ZREVRANGE 0 9` 取 TOP N
- ZSet 支持 `ZRANGEBYSCORE` 范围查询，Set 不支持

#### 5. ZSet 底层结构的陷阱

**陷阱问题：** ZSet 为什么用跳表不用红黑树？

**错误回答：** 跳表更快。

**正确回答：**

| 维度 | 跳表 | 红黑树 |
|------|------|--------|
| 实现复杂度 | 简单（100 行代码） | 复杂（旋转、变色） |
| 范围查询 | O(logN) + O(M)，链表遍历 | O(logN) + O(M)，中序遍历 |
| 并发实现 | 容易实现无锁 | 加锁复杂 |
| 内存占用 | 额外索引层（约 1.33 倍） | 更紧凑 |

**关键点：** 跳表的范围查询是链表顺序遍历，红黑树需要中序遍历，跳表更直观高效。

#### 6. 大 key 问题

**陷阱问题：** 什么是大 key？有什么危害？

**错误回答：** key 的名字太长。

**正确回答：**

**大 key 定义：**
- String：value > 10KB
- Hash/List/Set/ZSet：元素数 > 5000 或总大小 > 10MB

**危害：**
- 单次操作耗时高（O(N)），阻塞 Redis 主线程
- 网络传输慢，客户端超时
- 内存分配不均匀，集群节点倾斜
- 删除大 key 时阻塞（Redis 4.0+ 用 `UNLINK` 异步删除）

**排查：**
```bash
# 扫描大 key
redis-cli --bigkeys

# 检查 key 大小
MEMORY USAGE user:1:large:hash
```

#### 7. ziplist 级联更新

**陷阱问题：** ziplist 有什么缺点？

**错误回答：** 查询慢。

**正确回答：**

ziplist 的 entry 记录了前一个 entry 的长度（prevlen），如果前一个 entry 从 < 254 字节变成 ≥ 254 字节，prevlen 从 1 字节扩展到 5 字节，可能导致后续所有 entry 连锁更新。

**极端场景：** 连续多个 entry 都在 250-253 字节之间，插入一个 254 字节的 entry，触发级联更新，性能骤降。

**Redis 3.2+ 的解决：** quicklist 将大 ziplist 拆分成多个小 ziplist，控制单个 ziplist 大小，减少级联更新影响。

---

### 十一、面试要点

1. **五大类型**：String、Hash、List、Set、ZSet，各自的底层实现和适用场景
2. **底层结构**：SDS、ziplist、quicklist、intset、skiplist 的特点
3. **ZSet 为什么用跳表**：实现简单、范围查询高效、并发友好
4. **选型原则**：根据业务操作（读多写少、是否需要排序、是否需要范围查询）选择
5. **内存优化**：小数据用 ziplist、避免大 key、Hash 代替多个 String
6. **常见陷阱**：SDS vs C 字符串、Hash vs String JSON、List 消息队列的坑、大 key 危害

> 总结：Redis 不只是 KV 数据库，丰富的数据结构让它能应对缓存、队列、排行榜、计数器等多种场景。选型的核心是理解每种类型的底层实现和时间复杂度。
