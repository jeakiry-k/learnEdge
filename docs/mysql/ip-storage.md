---
date: "2026-10-08"
category: "MySQL"
title: "MySQL 中 IP 地址的存储与转换"
tags: [MySQL, 存储, IP 地址]
---

# MySQL 中 IP 地址的存储与转换

<div class="question-tags">
  <span class="question-tag">MySQL</span>
  <span class="question-tag">存储</span>
  <span class="question-tag">IP 地址</span>
</div>

> IP 地址在 MySQL 里怎么存最合理？直接用 `VARCHAR` 有什么问题？`INT UNSIGNED` + `INET_ATON` 为什么是经典方案？

### 一、直接用 VARCHAR 存 IP 的问题

很多新手会这样建表：

```sql
CREATE TABLE `visit_log` (
  `id`           BIGINT       NOT NULL AUTO_INCREMENT,
  `ip`           VARCHAR(15)  NOT NULL,   -- 存 '192.168.1.1'
  `created_at`   DATETIME     NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_ip` (`ip`)
);
```

这种写法能跑，但有三个明显问题：

**1. 浪费存储空间**

IPv4 最多是 `255.255.255.255`（15 个 ASCII 字符）。用 `VARCHAR(15)` 存：

```
'192.168.1.1'     → 11 × 1(ASCII) + 1 = 12 字节
'255.255.255.255' → 15 × 1(ASCII) + 1 = 16 字节
```

> 前缀是 1 字节：`VARCHAR(15)` 最大字节容量 15 × 4 = 60 ≤ 255。

而 IP 的本质是一个 32 位整数，最多 4 字节就能存下。`VARCHAR` 最多要多花 4 倍空间。

**2. 字符串比较慢**

`WHERE ip BETWEEN '192.168.1.0' AND '192.168.1.255'` 是按字符串字典序比较，逐字符比对，效率远低于整数比较。

**3. 无法直接做数值范围查询**

判断一个 IP 是否属于某个网段（如 `192.168.0.0/16`），用字符串几乎没法写 SQL，必须先转成数字。

### 二、经典方案：INT UNSIGNED + INET_ATON

MySQL 提供了 IP 与整数互转的内置函数：

| 函数 | 作用 | 示例 |
|------|------|------|
| `INET_ATON(str)` | IPv4 字符串 → 整数 | `INET_ATON('192.168.1.1')` → `3232235777` |
| `INET_NTOA(num)` | 整数 → IPv4 字符串 | `INET_NTOA(3232235777)` → `'192.168.1.1'` |
| `INET6_ATON(str)` | IPv4/IPv6 → 二进制 | `INET6_ATON('::1')` → `\0...\x01` |
| `INET6_NTOA(bin)` | 二进制 → IPv4/IPv6 字符串 | `INET6_NTOA(...)` → `'::1'` |

> `INET6_ATON` 从 MySQL 5.6 开始支持，返回 `VARBINARY(16)`，需要配合 `VARBINARY(16)` 字段存储。

建表改成：

```sql
CREATE TABLE `visit_log` (
  `id`           BIGINT        NOT NULL AUTO_INCREMENT,
  `ip`           INT UNSIGNED  NOT NULL,   -- 存 INET_ATON 转换后的整数
  `created_at`   DATETIME      NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_ip` (`ip`)
);

-- 写入时转换
INSERT INTO `visit_log` (`ip`, `created_at`)
VALUES (INET_ATON('192.168.1.1'), NOW());

-- 查询时还原
SELECT INET_NTOA(`ip`) AS ip, `created_at`
FROM `visit_log`
WHERE `ip` = INET_ATON('192.168.1.1');
```

**为什么必须是 `INT UNSIGNED`？**

IPv4 最大值 `255.255.255.255` 转换后是 `4294967295`，刚好等于 `INT UNSIGNED` 的上限（0 ~ 4294967295）。

如果误用有符号 `INT`（上限约 21.4 亿），存 `255.255.255.255`（42.9 亿）会溢出报错。

### 三、存储空间对比

| 方案 | 字段类型 | 固定占用 | 说明 |
|------|---------|:---:|------|
| 字符串 | `VARCHAR(15)` | 12~16 字节 | 取决于 IP 实际长度，还占索引更大 |
| 整数 | `INT UNSIGNED` | 4 字节 | 固定 4 字节，省 3~4 倍空间 |
| 通用（含 IPv6） | `VARBINARY(16)` | 16 字节 | 配合 `INET6_ATON`，同时兼容 IPv4/IPv6 |

> 单看一行省几字节似乎无所谓，但乘以千万级日志行数，`INT UNSIGNED` 比 `VARCHAR` 能省出上百 MB，且索引体积更小、缓存命中率更高。

### 四、数值范围查询的优势

转成整数后，网段判断就变成了简单的数值区间：

```sql
-- 判断是否属于 192.168.0.0/16 网段
-- 192.168.0.0   = 3232235520
-- 192.168.255.255 = 3232301055
SELECT COUNT(*)
FROM `visit_log`
WHERE `ip` BETWEEN 3232235520 AND 3232301055;
```

字符串方案只能靠 `LIKE '192.168.%'` 这类模糊匹配，走不了索引、逻辑也僵硬。

### 五、注意事项

**1. 一定要用 `UNSIGNED`**

前面说过，`INT` 存不下 `255.255.255.255`。这是最容易踩的坑。

**2. IPv6 用 `INET6_ATON` + `VARBINARY(16)`**

`INET_ATON` 只支持 IPv4。如果系统要兼容 IPv6：

```sql
CREATE TABLE `visit_log` (
  `id`   BIGINT        NOT NULL AUTO_INCREMENT,
  `ip`   VARBINARY(16) NOT NULL,   -- 兼容 IPv4 + IPv6
  `created_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`)
);

INSERT INTO `visit_log` (`ip`, `created_at`)
VALUES (INET6_ATON('2001:db8::1'), NOW());
```

**3. 应用层转换，避免到处写函数**

读写分离场景下，建议在**应用层**完成 IP 与整数的转换（Java/Go 都有现成的 ipv4→long 工具），SQL 里更干净：

- 写入：应用把 IP 转成 `long` 存进 `INT UNSIGNED`
- 查询：应用把查询条件转成 `long`，结果再转回字符串展示

**4. 日志分析场景优先用整数**

如果 IP 后续要做统计、聚合、范围分析（如 PV/UV、地域归属），整数方案优势更大。