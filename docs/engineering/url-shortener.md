---
date: "2026-09-24"
category: "工程化"
title: "短链服务系统设计"
---

# 短链服务系统设计

## 问题

> 设计一个短链服务系统（URL Shortener），要求：
> 1. 给定长 URL，生成短链
> 2. 访问短链时跳转到原始长 URL
> 3. 支持高并发读取
>
> 请描述整体架构、核心算法和存储方案。

---

## 答案

### 1 整体架构

```
                        用户请求短链
                             │
                             ▼
                    ┌─────────────────┐
                    │   CDN / 负载均衡  │
                    └────────┬────────┘
                             │
                    缓存命中? │
                    ┌────────┴────────┐
                   是                 否
                    │                 │
                    ▼                 ▼
              ┌──────────┐    ┌──────────────┐
              │  Redis   │    │  API 服务层   │
              │  缓存    │    └──────┬───────┘
              └────┬─────┘           │
                   │            ┌─────┴──────┐
              301 跳转          │  Bloom     │
                               │  Filter    │
                               └─────┬──────┘
                                     │
                               ┌─────┴──────┐
                               │ MySQL /    │
                               │ DynamoDB   │
                               └────────────┘
```

### 2 短码生成算法

#### 方案 A：自增 ID + Base62（推荐）

```
全局自增 ID: 10000000001
Base62 编码: "eW8nLm"
短链:       https://t.co/eW8nLm
```

| 优点 | 缺点 |
|------|------|
| 短码有序、不重复 | 可被遍历（加随机前缀缓解） |
| 生成速度快 | 依赖分布式 ID 服务 |

Base62 编码表：`0-9 a-z A-Z` 共 62 个字符。

```python
BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

def encode(num: int) -> str:
    if num == 0:
        return BASE62[0]
    chars = []
    while num > 0:
        num, rem = divmod(num, 62)
        chars.append(BASE62[rem])
    return ''.join(reversed(chars))

def decode(s: str) -> int:
    num = 0
    for c in s:
        num = num * 62 + BASE62.index(c)
    return num
```

#### 方案 B：MD5 哈希取前 N 位

```
对长 URL 做 MD5:  "a2b3c4d5e6..."
取前 6 位 Base62:  "a2b3c4"
冲突则取下一段或加盐重试
```

| 优点 | 缺点 |
|------|------|
| 无需中心化 ID | 可能哈希冲突 |
| 同一长 URL 得到相同短码 | 短码长度不固定 |

#### 方案 C：随机短码（KGS）

预生成大量随机 6 位 Base62 短码，存入队列，生成时直接取用。

### 3 存储方案

| 存储 | 用途 | 说明 |
|------|------|------|
| MySQL | 持久化映射 | `short_code` (PK), `original_url`, `expires_at` |
| Redis | 热点缓存 | 短码 → 长URL，TTL = 过期时间 |
| Bloom Filter | 防穿透 | 快速判断短码是否存在 |

表结构：

```sql
CREATE TABLE url_mapping (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    short_code   VARCHAR(10) NOT NULL UNIQUE,
    original_url TEXT NOT NULL,
    user_id      BIGINT,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at   DATETIME,
    click_count  BIGINT DEFAULT 0,
    INDEX idx_original (original_url(255))
);
```

### 4 核心流程

#### 创建短链

```
POST /api/shorten
{ "url": "https://very-long-url.com/path?query=1" }
```

```
1. 校验 URL 格式
2. 查询是否已存在（original_url 索引）
   ├─ 存在 → 返回已有短码
   └─ 不存在 → 生成新短码
3. 写入 MySQL + 写入 Redis 缓存
4. 返回短链: https://t.co/eW8nLm
```

#### 访问短链

```
GET /eW8nLm  →  301 Redirect
```

```
1. 查 Redis 缓存
   ├─ 命中 → 301 跳转 + 异步计数
   └─ 未命中 ↓
2. 查 Bloom Filter（短码是否存在）
   ├─ 不存在 → 返回 404
   └─ 可能存在 ↓
3. 查 MySQL
   ├─ 找到 → 回填 Redis + 301 跳转
   └─ 未找到 → 返回 404
```

### 5 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 跳转方式 | 301 | 浏览器缓存，减少服务压力 |
| 短码长度 | 6-7 位 | 62^6 ≈ 568 亿，足够用 |
| ID 生成 | Snowflake | 分布式自增，无单点 |
| 缓存策略 | Redis + Bloom Filter | 热数据毫秒级返回 |
| 过期策略 | TTL + 懒删除 | 短链可设有效期 |

### 6 容量估算

| 指标 | 估算 |
|------|------|
| 日活跳转 | 1 亿次 |
| 新增短链 | 10 万/天 |
| 短码空间 | 62^6 ≈ 568 亿（够用 100+ 年） |
| 存储需求 | ~1.5 GB/年（仅映射表） |
| QPS | ~1200 跳转/秒，~1 新增/秒 |

### 7 扩展优化

- **高可用**：MySQL 主从 + Redis 集群
- **防滥用**：限流（令牌桶）+ 黑名单 URL 检测
- **数据分析**：异步写入 ClickHouse 做点击统计
- **自定义短码**：预留命名空间，用户可指定易记短码
- **批量生成**：KGS 预生成短码队列，消费即可用
