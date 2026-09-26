---
date: "2026-09-24"
category: "工程化"
title: "短链系统设计"
tags: [系统设计, Base62, Redis, 高并发, 缓存]
---

# 短链系统设计

<div class="question-tags">
  <span class="question-tag">系统设计</span>
  <span class="question-tag">Base62</span>
  <span class="question-tag">Redis</span>
  <span class="question-tag">高并发</span>
  <span class="question-tag">缓存</span>
</div>


> 设计一个短链服务系统（URL Shortener），支持短链生成、跳转、高并发读取，请描述整体架构、核心算法和存储方案。



### 一、需求分析

#### 功能性需求

| 需求 | 说明 |
|------|------|
| 短链生成 | 给定长 URL，返回短链接 |
| 短链跳转 | 访问短链，重定向到原始长 URL |
| 自定义短码 | 用户可指定自定义短码（可选） |
| 过期机制 | 支持设置短链过期时间（可选） |
| 数据统计 | 记录点击量、来源等分析数据 |

#### 非功能性需求

- **高可用**：系统不可用会导致所有短链失效，需保证高可用（99.99%）
- **低延迟**：跳转延迟 < 100ms
- **高读低写**：读写比约 100:1
- **可扩展**：支持水平扩展
- **短码不可预测**：防止枚举攻击

### 二、容量估算

```
假设：
  - 日活用户：1 亿
  - 每用户每天生成 5 个短链 → 新增 5 亿/天
  - 每短链平均点击 100 次 → 读请求 500 亿/天

写 QPS：  5亿 / 86400 ≈ 5,800 QPS  （峰值约 15,000 QPS）
读 QPS：  500亿 / 86400 ≈ 580,000 QPS （峰值约 1,500,000 QPS）

存储（10年）：
  5亿/天 × 365 × 10 = 1.825万亿条记录
  每条约 500 bytes → 约 912 TB

短码长度：
  Base62 编码（a-z, A-Z, 0-9 = 62字符）
  7位 → 62^7 ≈ 3.5万亿 → 足够 10 年使用
```

### 三、系统 API 设计

#### 1. 生成短链

```
POST /api/v1/shorten
Content-Type: application/json

Request:
{
  "url": "https://www.example.com/very/long/path?param=value",
  "custom_alias": "mylink",
  "expire_at": "2026-12-31T23:59:59Z",
  "user_id": "u12345"
}

Response:
{
  "short_url": "https://s.co/aB3xK9p",
  "original_url": "https://www.example.com/very/long/path?param=value",
  "expire_at": "2026-12-31T23:59:59Z",
  "created_at": "2026-09-24T10:00:00Z"
}
```

#### 2. 短链跳转

```
GET /aB3xK9p

Response:
  301 / 302 → Location: https://www.example.com/very/long/path?param=value
```

#### 3. 数据统计

```
GET /api/v1/stats/aB3xK9p

Response:
{
  "short_code": "aB3xK9p",
  "total_clicks": 152340,
  "clicks_today": 2340,
  "top_referrers": [{"source": "google.com", "count": 50000}],
  "top_countries": [{"country": "CN", "count": 80000}]
}
```

### 四、整体架构

```
                         ┌──────────────────────────────────────────────┐
                         │              Global Load Balancer             │
                         │            (Geo-DNS / Anycast)               │
                         └──────────┬───────────────────┬───────────────┘
                                    │                   │
                    ┌───────────────▼──┐         ┌──────▼────────────┐
                    │   Write Service   │         │   Read Service    │
                    │   (生成短链)       │         │   (短链跳转)      │
                    │   Auto-scaling    │         │   Auto-scaling   │
                    └───────┬──────────┘         └────────┬─────────┘
                            │                              │
                     ┌──────▼──────┐            ┌─────────▼──────────┐
                     │  ID Service  │            │   Redis Cluster     │
                     │ (Snowflake/  │            │   (缓存层)          │
                     │  Range Pool) │            │   L1: 本地缓存      │
                     └──────┬──────┘            │   L2: Redis 集群    │
                            │                   └─────────┬──────────┘
                            │                             │
                    ┌───────▼─────────────────────────────▼──────┐
                    │            Database Layer                    │
                    │  ┌─────────────┐  ┌──────────────────────┐  │
                    │  │  Write DB   │  │    Read Replicas     │  │
                    │  │ (主库)       │  │    (只读副本 x N)     │  │
                    │  │  NoSQL/SQL  │  │     NoSQL/SQL        │  │
                    │  └─────────────┘  └──────────────────────┘  │
                    └─────────────────────────────────────────────┘
                            │
                    ┌───────▼──────────┐
                    │  Analytics Queue  │
                    │  (Kafka / Kinesis)│
                    └───────┬──────────┘
                            │
                    ┌───────▼──────────┐
                    │ Analytics Worker  │
                    │ (聚合/写入统计DB)   │
                    └──────────────────┘
```

### 五、核心算法：短码生成

#### 方案对比

| 方案 | 优点 | 缺点 |
|------|------|------|
| Hash + Base62 | 简单、无状态 | 可能冲突、不可预测长度 |
| 自增 ID + Base62 | 无冲突、短 | 可枚举、暴露量级 |
| Snowflake ID + Base62 | 分布式、有序 | 稍长、可预测 |
| 随机数 + 布隆过滤器 | 不可枚举 | 需查重、有冲突概率 |
| 预生成号段池 | 高性能、分布式 | 需维护号段服务 |

#### 推荐方案：预生成号段池 + Base62

```
1. ID Service 预分配号段给各 Write Service 实例
   实例A: [1, 1,000,000]
   实例B: [1,000,001, 2,000,000]
   实例C: [2,000,001, 3,000,000]

2. 本地维护计数器，原子递增

3. ID → Base62 编码 → 短码
   ID = 123456789
   Base62 = "8m0Kx" (5位)
   补齐到7位 = "008m0Kx" → 实际用随机前缀混淆

4. 混淆处理（防止可预测）
   final_code = shuffle(base62(id), secret_key)
```

Base62 编码示例：

```python
CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

def encode(num):
    if num == 0:
        return CHARS[0]
    result = []
    while num > 0:
        result.append(CHARS[num % 62])
        num //= 62
    return ''.join(reversed(result))

def decode(s):
    num = 0
    for c in s:
        num = num * 62 + CHARS.index(c)
    return num
```

### 六、数据库设计

#### 主存储（NoSQL）

```
Table: url_mapping
┌─────────────┬──────────┬────────────────────────────┬──────────┬──────────────┐
│ short_code   │ user_id  │ original_url               │ expire_at│ created_at   │
│ (Partition) │          │                            │          │              │
├─────────────┼──────────┼────────────────────────────┼──────────┼──────────────┤
│ aB3xK9p     │ u12345   │ https://www.example.com... │ 2026-12  │ 2026-09-24   │
│ xY7mN2q     │ u67890   │ https://blog.example.com.. │ null     │ 2026-09-24   │
└─────────────┴──────────┴────────────────────────────┴──────────┴──────────────┘

Partition Key: short_code
```

#### 自定义短码索引表

```
Table: custom_alias
┌─────────────┬─────────────┐
│ alias       │ short_code  │
│ (Partition) │             │
├─────────────┼─────────────┤
│ mylink      │ aB3xK9p     │
└─────────────┴─────────────┘
```

#### 数据分片策略

```
按 short_code 首字母分片：
  shard_0: short_code[0] ∈ [0-9]
  shard_1: short_code[0] ∈ [a-f]
  shard_2: short_code[0] ∈ [g-p]
  shard_3: short_code[0] ∈ [q-z]
  shard_4: short_code[0] ∈ [A-Z]

→ 均匀分布，读写均衡
```

### 七、缓存策略

```
请求 → L1 本地缓存 (Caffeine/LRU)
       │ 命中 → 直接返回
       │ 未命中 ↓
       L2 Redis 集群 (一致性哈希)
       │ 命中 → 返回 + 回填 L1
       │ 未命中 ↓
       DB 查询 → 回填 L2 + L1

缓存策略：
  • TTL: 24小时（热门短链自动续期）
  • 容量: L1 ~10万条, L2 ~1亿条
  • 淘汰: LRU
  • 预热: 对 Top-N 热门短链批量加载
  • 防穿透: 空结果缓存 (NULL caching, TTL=60s)
  • 防雪崩: TTL 随机抖动 ±10%
  • 防击穿: 单飞模式 (singleflight) + 互斥锁
```

### 八、跳转流程详解

```
用户访问 https://s.co/aB3xK9p
         │
         ▼
    ┌─────────────┐
    │  CDN 边缘    │ ── 缓存热门短链的 301 响应
    └──────┬──────┘
           │ 未命中
           ▼
    ┌─────────────┐
    │  Load Balancer│
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │ Read Service │
    └──────┬──────┘
           │
     ┌─────▼─────┐
     │ L1 本地缓存 │ ── 命中? → 返回
     └─────┬─────┘
           │ 未命中
     ┌─────▼─────┐
     │ L2 Redis   │ ── 命中? → 返回 + 回填L1
     └─────┬─────┘
           │ 未命中
     ┌─────▼─────┐
     │  数据库    │ ── 查询 → 回填 L2 + L1
     └─────┬─────┘
           │
     ┌─────▼──────────────────┐
     │ 异步: 发送点击事件到     │
     │ Kafka (用于统计分析)    │
     └────────────────────────┘
           │
     ┌─────▼─────┐
     │ 301/302    │
     │ 重定向     │
     └───────────┘
```

301 vs 302 选择：

| 方式 | 说明 |
|------|------|
| 301（永久重定向） | 浏览器缓存，减少服务器压力，但无法统计后续点击 |
| 302（临时重定向） | 每次都经过服务器，可统计点击，但延迟略高 |

推荐 302：短链场景需要统计数据，且 CDN 可弥补性能。

### 九、数据分析系统

```
跳转请求 → 异步写入 → Kafka Topic
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
     ┌──────────────┐ ┌────────────┐ ┌──────────────┐
     │ 实时统计      │ │ 批处理聚合  │ │ 数据仓库     │
     │ (Redis       │ │ (Spark     │ │ (ClickHouse  │
     │  HyperLogLog)│ │  Streaming)│ │  / BigQuery) │
     └──────────────┘ └────────────┘ └──────────────┘
         │                  │               │
         ▼                  ▼               ▼
     实时看板            小时/日报表      历史趋势分析
```

每条点击事件包含：

```json
{
  "short_code": "aB3xK9p",
  "timestamp": 1695542400,
  "ip": "1.2.3.4",
  "user_agent": "Mozilla/5.0...",
  "referer": "https://google.com/...",
  "country": "CN",
  "device": "mobile"
}
```

### 十、高可用与容错

| 层面 | 措施 |
|------|------|
| 多机房部署 | 主备 + 多活，DNS 级别自动切换（< 30s） |
| 数据库高可用 | 主从复制 + 自动故障转移 + 多 AZ + 定期快照 |
| 缓存高可用 | Redis Cluster 3主3从 + Sentinel，降级直查 DB |
| 限流与保护 | 令牌桶限流 + 熔断器 + 降级策略 |

### 十一、安全设计

| 威胁 | 防御措施 |
|------|---------|
| 短码枚举 | 混淆算法 + 速率限制 |
| 恶意 URL | 接入 Google Safe Browsing API + 黑名单 |
| DDoS | CDN 防护 + WAF + 速率限制 |
| 短链劫持 | HTTPS + HSTS + 签名校验 |
| 隐私泄露 | IP 脱敏存储 + 数据匿名化 |
| 自定义短码抢注 | 原子性写入 + 唯一约束 |

### 十二、技术选型总结

| 组件 | 技术选型 | 理由 |
|------|---------|------|
| 负载均衡 | Nginx + Cloud LB | 成熟稳定 |
| 写服务 | Go / Java | 高并发、低延迟 |
| 读服务 | Go | 极致性能 |
| 主数据库 | Cassandra / DynamoDB | 海量写入、水平扩展 |
| 缓存 | Redis Cluster | 低延迟、高吞吐 |
| 消息队列 | Kafka | 高吞吐、持久化 |
| 分析数据库 | ClickHouse | 列存、聚合查询快 |
| ID 服务 | Snowflake 变体 | 分布式、有序 |
| CDN | Cloudflare / AWS CloudFront | 边缘缓存、DDoS 防护 |

### 十三、核心代码示例

```go
// 短码生成服务
type ShortCodeService struct {
    idGenerator  IDGenerator
    encoder     Base62Encoder
    obfuscator  Obfuscator
}

func (s *ShortCodeService) Generate() (string, error) {
    id, err := s.idGenerator.NextID()
    if err != nil {
        return "", err
    }
    encoded := s.encoder.Encode(id)
    code := s.obfuscator.Shuffle(encoded)
    return code, nil
}

// 跳转处理
func HandleRedirect(w http.ResponseWriter, r *http.Request) {
    code := r.URL.Path[1:]

    if url, ok := localCache.Get(code); ok {
        analytics.Send(code, r)
        http.Redirect(w, r, url, 302)
        return
    }

    url, err := redisClient.Get(code)
    if err == nil {
        localCache.Set(code, url)
        analytics.Send(code, r)
        http.Redirect(w, r, url, 302)
        return
    }

    url, err = db.QueryOriginalURL(code)
    if err != nil {
        http.Error(w, "Not Found", 404)
        return
    }

    redisClient.Set(code, url, 24*time.Hour)
    localCache.Set(code, url)
    analytics.Send(code, r)
    http.Redirect(w, r, url, 302)
}
```
