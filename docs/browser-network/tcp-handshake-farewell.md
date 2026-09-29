---
date: "2026-09-28"
category: "浏览器与网络"
title: "TCP 三次握手与四次挥手"
tags: [TCP, 网络, 协议]
---

# TCP 三次握手与四次挥手

<div class="question-tags">
  <span class="question-tag">TCP</span>
  <span class="question-tag">网络</span>
  <span class="question-tag">协议</span>
</div>

> TCP 为什么建立连接要三次握手，断开连接要四次挥手？开发中有哪些实践与此相关？

### 一、三次握手（建立连接）

```
客户端                    服务端
  │                          │
  │ ── SYN, seq=x ────────→  │   第 1 次：客户端发起连接请求
  │                          │   （我要连了，我的序号是 x）
  │                          │
  │ ←── SYN+ACK, seq=y,ack=x+1 ─  第 2 次：服务端确认并发起自己的 SYN
  │                          │   （收到，我也准备好了，我的序号是 y）
  │                          │
  │ ── ACK, ack=y+1 ──────→ │   第 3 次：客户端确认服务端的 SYN
  │                          │   （收到，开始传数据吧）
  │                          │
  │ ←──── 数据双向传输 ────→ │
```

#### 为什么是三次，不是两次？

**两次握手的致命问题：** 服务端无法确认客户端的 SYN 是「当前请求」还是「历史迟到的报文」。

```
场景：两次握手下，迟到的旧 SYN 导致服务端误开连接

1. 客户端发 SYN(seq=100)，网络拥塞，报文滞留
2. 客户端超时，发新 SYN(seq=200)，正常建立连接、传数据、关闭
3. 旧的 SYN(seq=100) 终于到达服务端
4. 两次握手 → 服务端直接返回 ACK，连接建立 → 浪费资源等待永不来的数据
   三次握手 → 服务端返回 SYN+ACK，客户端发现 seq 不对，不回 ACK → 连接不会建立
```

> 一句话：三次握手保证**双方都确认了对方的接收能力**——第三次 ACK 证明客户端确实收到了服务端的 SYN。

#### 为什么不是四次？

三次已经足够确认双方收发能力，第四次是多余的：

```
三次握手已确认：
  第 1 次：服务端确认客户端有发送能力
  第 2 次：客户端确认服务端有发送+接收能力
  第 3 次：服务端确认客户端有接收能力
  → 双方收发能力全部确认，无需第 4 次
```

---

### 二、四次挥手（断开连接）

```
客户端                    服务端
  │                          │
  │ ── FIN, seq=u ────────→  │   第 1 次：客户端说"我没有数据了"
  │                          │   （客户端进入 FIN_WAIT_1）
  │                          │
  │ ←── ACK, ack=u+1 ──────  │   第 2 次：服务端说"收到"
  │                          │   （服务端进入 CLOSE_WAIT，客户端进入 FIN_WAIT_2）
  │                          │   ← 服务端可能还有未发完的数据
  │ ←── 数据传输 ───────────  │
  │                          │
  │ ←── FIN, seq=v ─────────  │   第 3 次：服务端说"我也没数据了"
  │                          │   （服务端进入 LAST_ACK）
  │                          │
  │ ── ACK, ack=v+1 ──────→  │   第 4 次：客户端说"收到，再见"
  │                          │   （客户端进入 TIME_WAIT，等待 2MSL 后关闭）
```

#### 为什么挥手是四次，不是三次？

**核心原因：TCP 是全双工的，两个方向的关闭独立。**

```
建立连接时：
  服务端的 SYN 和 ACK 可以合并成一次发送（SYN+ACK）→ 省一次 → 三次

断开连接时：
  服务端收到客户端的 FIN 后，可能还有数据没发完
  → 必须先回 ACK 确认收到 FIN（第 2 次）
  → 继续发剩余数据
  → 数据发完后才能发自己的 FIN（第 3 次）
  → ACK 和 FIN 不能合并，因为中间有数据要传 → 四次
```

#### TIME_WAIT 为什么要等 2MSL？

```
MSL = Maximum Segment Lifetime，报文最大生存时间（Linux 默认 30s）

等待 2MSL 的原因：
  1. 保证最后一个 ACK 能到达对端
     → 如果 ACK 丢失，服务端会重发 FIN，客户端还能收到并重发 ACK
  2. 让本次连接的所有报文都从网络中消失
     → 防止迟到的报文影响下一个相同四元组的新连接
```

---

### 三、状态机速记

| 阶段 | 客户端状态 | 服务端状态 |
|------|-----------|-----------|
| 握手 | SYN_SENT → ESTABLISHED | SYN_RCVD → ESTABLISHED |
| 挥手 | FIN_WAIT_1 → FIN_WAIT_2 → TIME_WAIT → CLOSED | CLOSE_WAIT → LAST_ACK → CLOSED |

> 面试高频考点：**CLOSE_WAIT** 大量出现 = 服务端代码忘了 close 连接；**TIME_WAIT** 大量出现 = 客户端频繁建断连接（短连接模式下常见）。

---

### 四、开发中的相关实践

#### 1. 连接复用：为什么 HTTP 1.1 默认 Keep-Alive

```
HTTP/1.0：每个请求 = 三次握手 + 请求 + 四次挥手
  → 请求 100 个图片 = 100 次建连断连 → 开销大

HTTP/1.1 Keep-Alive：复用 TCP 连接
  → 三次握手一次，后续请求复用 → 省去反复建连开销
```

#### 2. 为什么高并发推荐连接池

```java
// 数据库连接池 / Redis 连接池
// 核心目的之一：避免每次请求都经历三次握手 + 四次挥手
// 复用已建立的 TCP 连接，减少延迟和系统开销
```

#### 3. TIME_WAIT 过多怎么处理

```bash
# 大量短连接 → 客户端堆积 TIME_WAIT
# 查看当前 TIME_WAIT 数量
netstat -n | grep TIME_WAIT | wc -l

# 解决方案 1：开启 TCP 复用（推荐）
sysctl -w net.ipv4.tcp_tw_reuse=1
# 允许将 TIME_WAIT 的连接重新用于新的 TCP 连接

# 解决方案 2：缩短 TIME_WAIT 时间（不推荐，可能导致旧报文干扰）
sysctl -w net.ipv4.tcp_fin_timeout=15

# 解决方案 3：改用长连接 / 连接池（从根源解决）
```

#### 4. CLOSE_WAIT 过多怎么排查

```bash
# 大量 CLOSE_WAIT = 服务端代码漏了 close
netstat -n | grep CLOSE_WAIT

# 排查思路：
# 1. 检查代码是否在异常分支漏了 close()
# 2. 检查是否有 finally 块确保资源释放
```

```java
// 错误：异常时漏 close
Connection conn = dataSource.getConnection();
Statement stmt = conn.createStatement();
stmt.execute("SELECT ...");
// 如果上面抛异常，conn 永远不会 close → CLOSE_WAIT 堆积

// 正确：try-with-resources 确保关闭
try (Connection conn = dataSource.getConnection();
     Statement stmt = conn.createStatement()) {
    stmt.execute("SELECT ...");
}
```

#### 5. SYN Flood 攻击与防御

```bash
# 攻击者伪造大量 SYN 请求，不回第三次 ACK
# → 服务端半连接队列被塞满 → 正常用户无法连接

# 防御：开启 SYN Cookies
sysctl -w net.ipv4.tcp_syncookies=1
# 原理：不分配资源给半连接，用加密 Cookie 验证合法性
#       第三次 ACK 带回 Cookie 验证通过才分配资源
```

### 五、总结

| 问题 | 答案 |
|------|------|
| 为什么三次握手 | 确认双方收发能力，防止历史 SYN 误建连接 |
| 为什么不是两次 | 服务端无法区分当前 SYN 和迟到的旧 SYN |
| 为什么四次挥手 | 全双工，两个方向独立关闭，ACK 和 FIN 中间可能还有数据 |
| 为什么 TIME_WAIT 等 2MSL | 保证 ACK 到达 + 让旧报文消失 |
| 开发实践 | Keep-Alive 复用连接、连接池、排查 TIME_WAIT/CLOSE_WAIT 堆积、SYN Flood 防御 |
