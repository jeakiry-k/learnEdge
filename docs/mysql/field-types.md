---
date: "2026-09-28"
category: "MySQL"
title: "MySQL 字段类型与存储空间估算"
tags: [MySQL, 存储, 数据类型]
---

# MySQL 字段类型与存储空间估算

<div class="question-tags">
  <span class="question-tag">MySQL</span>
  <span class="question-tag">存储</span>
  <span class="question-tag">数据类型</span>
</div>

> MySQL 各字段类型占多少存储空间？如何估算一张表的大小？选错类型会浪费多少空间？

### 数值类型

| 类型 | 存储空间（字节） | 范围（有符号） | 范围（无符号） |
|------|:---:|------|------|
| `TINYINT` | 1 | -128 ~ 127 | 0 ~ 255 |
| `SMALLINT` | 2 | -32768 ~ 32767 | 0 ~ 65535 |
| `MEDIUMINT` | 3 | ±838万 | 0 ~ 1677万 |
| `INT` | 4 | ±21亿 | 0 ~ 42亿 |
| `BIGINT` | 8 | ±922亿亿 | 0 ~ 1844亿亿 |
| `DECIMAL(M,D)` | ≈M+2 | 任意精度 | — |
| `FLOAT` | 4 | 单精度浮点 | — |
| `DOUBLE` | 8 | 双精度浮点 | — |

> `INT(11)` 中的 11 只是显示宽度，不改变存储空间，`INT` 永远占 4 字节。

### 字符串类型

| 类型 | 存储空间 | 说明 |
|------|---------|------|
| `CHAR(N)` | N × 字符集字节 | 定长，不足补空格。UTF-8 下 `CHAR(10)` = 30~40 字节 |
| `VARCHAR(N)` | 实际长度 + 1~2 字节 | 变长，额外 1 字节（N≤255）或 2 字节（N>255）记录长度 |
| `TEXT` | 实际长度 + 2 字节 | 最大 64KB，不计入行 |
| `MEDIUMTEXT` | 实际长度 + 3 字节 | 最大 16MB |
| `LONGTEXT` | 实际长度 + 4 字节 | 最大 4GB |
| `BLOB` 系列 | 同 TEXT 对应 | 二进制版本 |

#### VARCHAR 和 CHAR 怎么选？

```sql
-- 存储 'hello'（5 字节）
CHAR(10)    → 固定占 10 字符 × 3(UTF8) = 30 字节，浪费 25 字节
VARCHAR(10) → 占 5 + 1 = 6 字节，几乎不浪费

-- 存储 13 位手机号 '13800138000'
CHAR(11)    → 11 × 3 = 33 字节（定长，适合等长数据）
VARCHAR(11) → 11 + 1 = 12 字节（更省空间）
```

> 经验法则：长度基本一致用 `CHAR`（如手机号、MD5），长度变化大用 `VARCHAR`。

#### VARCHAR 的存储公式

`VARCHAR(N)` 实际占用的存储空间 = **字符的实际字节数 + 长度前缀字节**

关键在于字符的实际字节数取决于字符集和字符内容：

| 字符类型 | UTF-8（utf8mb4）每字符字节 | 举例 |
|---------|:---:|------|
| ASCII（a-z, 0-9, @, .） | 1 | `a`、`@`、`1` |
| 中文等 BMP 字符 | 3 | `你`、`好` |
| Emoji 等 4 字节字符 | 4 | 😀、🎉 |

长度前缀：N ≤ 255 用 1 字节，N > 255 用 2 字节。

```sql
-- VARCHAR(100)，存储 'admin@qq.com'（12 个 ASCII 字符）
-- 实际占用 = 12 × 1(ASCII) + 2(N>100) = 14 字节

-- VARCHAR(100)，存储 '用户反馈内容说明书详细描述'（14 个中文字符）
-- 实际占用 = 14 × 3(中文) + 2 = 44 字节

-- CHAR(11)，存储手机号 '13800138000'（11 个 ASCII 数字）
-- 实际占用 = 11 × 1(ASCII) = 11 字节（CHAR 是定长的）
```

> 注意：估算存储空间时务必区分字符类型。例如 email 是纯 ASCII，30 个字符只占 `30 × 1 + 2 = 32 字节`；若是中文内容，30 个字符则占 `30 × 3 + 2 = 92 字节`。

### 时间类型

| 类型 | 存储空间 | 范围 | 说明 |
|------|:---:|------|------|
| `YEAR` | 1 | 1901 ~ 2155 | 年份 |
| `DATE` | 3 | 1000-01-01 ~ 9999-12-31 | 仅日期 |
| `TIME` | 3 | -838h ~ 838h | 时间 |
| `DATETIME` | 8 | 1000 ~ 9999 年 | 日期+时间，与时区无关 |
| `TIMESTAMP` | 4 | 1970 ~ 2038 年 | UTC 时间戳，自动时区转换 |

> `TIMESTAMP` 只占 4 字节但有 2038 问题；`DATETIME` 占 8 字节但范围更大。

### 存储空间估算实战

#### 估算一张用户表 1000 万行的大小

```sql
CREATE TABLE `user` (
  `id`          BIGINT       NOT NULL AUTO_INCREMENT,  -- 8 字节
  `username`    VARCHAR(50)  NOT NULL,                 -- 平均 20 字符 = 60 + 2 = 62 字节
  `phone`       CHAR(11)     NOT NULL,                 -- 11 × 3 = 33 字节
  `email`       VARCHAR(100) DEFAULT NULL,             -- 平均 30 个 ASCII 字符 = 30 × 1 + 2 = 32 字节
  `status`      TINYINT      NOT NULL DEFAULT 1,      -- 1 字节
  `created_at`  DATETIME     NOT NULL,                -- 8 字节
  PRIMARY KEY (`id`)
);
```

**单行数据大小估算：**

```
8 + 62 + 33 + 32 + 1 + 8 = 144 字节/行
```

**加上 InnoDB 行开销：**

- 行头信息：约 20~30 字节
- 记录偏移目录：约 2 字节
- 空值位图：1 字节（email 可空）
- 预估单行总大小：≈ 170 字节

**1000 万行总数据量：**

```
170 字节 × 1000 万 = 1.7 GB（纯数据）
```

**加上索引和页填充率：**

```
InnoDB 页默认 16KB，填充率约 15/16（15/16 聚簇索引数据页）
1.7 GB ÷ (15/16) ≈ 1.8 GB
+ 二级索引（假设 3 个，总大小约为数据的 30%）
≈ 1.8 × 1.3 ≈ 2.3 GB
```

#### 估算的意义

```
选错类型的空间浪费对比（1000 万行）：

状态字段：
  TINYINT(1 字节)  →  10 MB
  INT(4 字节)      →  40 MB    ← 浪费 4 倍

性别字段：
  TINYINT(1 字节)  →  10 MB
  VARCHAR(2)(6 字节)→  60 MB   ← 浪费 6 倍

时间字段：
  TIMESTAMP(4 字节)→  40 MB
  DATETIME(8 字节)  →  80 MB   ← 视场景选择
```

### 字段类型适合的场景与示例

#### 数值类型

| 类型 | 适合场景 | 示例 |
|------|---------|------|
| `TINYINT` | 状态、枚举、布尔 | `status TINYINT` — 0=禁用 1=启用 2=锁定 |
| `SMALLINT` | 中等范围整数 | `port SMALLINT` — 端口号 0~65535 |
| `INT` | 自增 ID（中小型表） | `order_id INT AUTO_INCREMENT` |
| `BIGINT` | 自增 ID（大型表）、雪花算法 ID | `user_id BIGINT` — 分布式系统唯一 ID |
| `DECIMAL(M,D)` | 金额、精度要求高 | `price DECIMAL(10,2)` — 99999999.99 元 |
| `FLOAT` | 近似值、可接受精度丢失 | `temperature FLOAT` — 气温数据 |
| `DOUBLE` | 科学计算、大范围浮点 | `longitude DOUBLE` — 经纬度坐标 |

```sql
-- 金额必须用 DECIMAL，不能用 FLOAT
price DECIMAL(10,2)       -- 精确到分，无精度丢失
-- 对比 FLOAT：
-- 0.1 + 0.2 = 0.30000000000000004（精度丢失）

-- 雪花算法生成的 ID 超过 INT 范围，必须 BIGINT
snowflake_id BIGINT        -- 雪花 ID 约 19 位数字，INT 最大约 21 亿不够用
```

#### 字符串类型

| 类型 | 适合场景 | 示例 |
|------|---------|------|
| `CHAR(N)` | 定长、等长数据 | 手机号 `CHAR(11)`、MD5 `CHAR(32)`、UUID `CHAR(36)` |
| `VARCHAR(N)` | 变长、短文本 | 用户名 `VARCHAR(50)`、邮箱 `VARCHAR(100)` |
| `TEXT` | 长文本（≤64KB） | 文章正文 `TEXT`、评论 `TEXT` |
| `MEDIUMTEXT` | 中等长文本（≤16MB） | 带格式的内容 `MEDIUMTEXT` |
| `LONGTEXT` | 超长文本（≤4GB） | 日志原文 `LONGTEXT` |
| `BLOB` | 二进制数据 | 图片缩略图 `BLOB`、加密数据 `BLOB` |

```sql
-- 定长数据用 CHAR：比较时不需要比对长度，性能略优
phone      CHAR(11)        -- 11 位手机号，每个都是 11
md5_hash   CHAR(32)        -- MD5 固定 32 位
uuid       CHAR(36)        -- UUID 固定 36 位

-- 变长数据用 VARCHAR
username   VARCHAR(50)    -- 3~20 个字符
email      VARCHAR(100)   -- 长度不定

-- 大文本用 TEXT 系列
content    TEXT            -- 文章正文，不超过 64KB
-- 注意：TEXT 不能设默认值，不参与行内排序计算
```

#### 时间类型

| 类型 | 适合场景 | 示例 |
|------|---------|------|
| `DATE` | 仅需日期 | 生日 `birthday DATE` — '1990-01-15' |
| `TIME` | 仅需时间 | 营业时间 `open_time TIME` — '09:00:00' |
| `DATETIME` | 日期+时间，范围大、与时区无关 | 创建时间 `created_at DATETIME` — '2026-09-28 14:30:00' |
| `TIMESTAMP` | 自动时区转换、记录时间 | 更新时间 `updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP` |
| `YEAR` | 仅需年份 | 毕业年份 `grad_year YEAR` — 2026 |

```sql
-- TIMESTAMP：自动记录和更新时间，4 字节省空间
created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP                   -- 插入时自动填充
updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP  -- 更新时自动刷新

-- DATETIME：不受 2038 限制，适合出生日期等历史数据
birthday  DATETIME  -- 1900-01-01 到 9999-12-31，8 字节

-- DATE：只需要日期不需要时间
order_date  DATE  -- '2026-09-28'
```

#### 一个完整建表示例

```sql
CREATE TABLE `order` (
  `id`           BIGINT        NOT NULL AUTO_INCREMENT,   -- 大型表主键
  `order_no`     CHAR(20)      NOT NULL,                   -- 订单号定长
  `user_id`      BIGINT        NOT NULL,                   -- 关联用户
  `amount`       DECIMAL(10,2) NOT NULL,                   -- 金额精确到分
  `status`       TINYINT       NOT NULL DEFAULT 0,          -- 0待支付 1已支付 2已取消
  `remark`       VARCHAR(500)  DEFAULT NULL,                -- 变长备注
  `address`      VARCHAR(200)  NOT NULL,                    -- 收货地址
  `created_at`   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
  `updated_at`   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_order_no` (`order_no`),
  KEY `idx_user_id` (`user_id`)
);
```

### 选型原则

| 原则 | 说明 |
|------|------|
| 能小不大 | 状态用 `TINYINT` 不用 `INT`，能 `SMALLINT` 不用 `INT` |
| 能定长不变长 | 手机号、MD5 用 `CHAR`，提高比较效率 |
| 能整数不用字符串 | IP 用 `INT UNSIGNED`（`INET_ATON`），不用 `VARCHAR(15)` |
| 金额用 `DECIMAL` | 避免 `FLOAT/DOUBLE` 精度丢失 |
| 时间选型看场景 | 需要 2038 年后或大范围用 `DATETIME`，需要自动时区用 `TIMESTAMP` |
| 大字段单独存 | `TEXT/BLOB` 不计行内，过多会触发溢出页，影响性能 |
