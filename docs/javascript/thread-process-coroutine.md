---
date: "2026-09-25"
category: "JavaScript"
title: "线程、进程、协程的区别"
tags: [进程, 线程, 协程, 并发, 并行]
---

# 线程、进程、协程的区别

<div class="question-tags">
  <span class="question-tag">进程</span>
  <span class="question-tag">线程</span>
  <span class="question-tag">协程</span>
  <span class="question-tag">并发</span>
  <span class="question-tag">并行</span>
</div>

> 请解释进程（Process）、线程（Thread）和协程（Coroutine）的区别，以及它们各自的适用场景。

### 一、定义与层级

| 概念 | 定义 | 资源归属 |
|------|------|---------|
| **进程** | 操作系统分配资源的最小单位 | 拥有独立的地址空间、文件描述符、堆栈 |
| **线程** | CPU 调度的最小单位 | 共享所属进程的地址空间，拥有独立栈和寄存器 |
| **协程** | 用户态的轻量级调度单元 | 共享线程资源，由程序自身（而非内核）调度 |

```
┌──────────────────────────┐
│       进程 A              │
│  ┌────────────────────┐  │
│  │  线程 A1  ┌──────┐ │  │
│  │          │协程1 │ │  │
│  │          │协程2 │ │  │
│  │          └──────┘ │  │
│  ├────────────────────┤  │
│  │  线程 A2           │  │
│  └────────────────────┘  │
└──────────────────────────┘
```

### 二、核心区别对比

| 维度 | 进程 | 线程 | 协程 |
|------|------|------|------|
| 调度者 | 内核（操作系统） | 内核 | 用户态（程序自身） |
| 切换代价 | 高（上下文切换 + 内存映射切换） | 中（上下文切换） | 极低（仅寄存器保存/恢复） |
| 并发单位 | 多进程 | 多线程 | 协程间协作 |
| 内存隔离 | 完全隔离 | 共享进程内存 | 共享线程内存 |
| 创建/销毁代价 | 重 | 中 | 极轻 |
| 通信方式 | IPC（管道、Socket、消息队列） | 共享内存 + 锁 | 通道、回调 |
| 可调度数 | 几百 | 几千 | 几十万~百万 |
| 是否存在竞态 | 低 | 高（需加锁） | 低（协作式） |

### 三、调度方式

**进程调度（抢占式）**：

```
CPU 时间片到 → 保存进程 A 上下文 → 加载进程 B 上下文 → 执行进程 B
                       ↓ 内核态切换，开销 ~1-10μs
```

**线程调度（抢占式）**：

```
CPU 时间片到 → 保存线程 A 寄存器 → 加载线程 B 寄存器 → 执行线程 B
                       ↓ 内核态切换，开销 ~0.1-1μs
```

**协程调度（协作式）**：

```
协程 A 异步等待 I/O
  ↓ yield / await    ← 用户态主动让出
协程 B 继续执行
  ↓ resume
协程 A I/O 完成后恢复
                       ↓ 用户态切换，开销 ~0.01μs（纳秒级）
```

### 四、JavaScript 中的协程

JavaScript 通过 **`async/await`** 实现协程机制：

```javascript
// 协程：async 函数本质是一个协程
async function fetchUserData(userId) {
  const user = await fetch(`/api/user/${userId}`);  // 让出控制权
  const posts = await fetch(`/api/posts/${userId}`); // 再次让出
  return { user, posts };
}
```

执行流程：

```
fetchUserData() 开始执行
  │
  ├─ await fetch(...) → 协程挂起，事件循环执行其他任务
  │                        ↓ I/O 完成
  ├─ 协程恢复，继续执行
  │
  ├─ await fetch(...) → 再次挂起
  │                        ↓ I/O 完成
  ├─ 协程恢复，返回结果
  ▼
```

### 五、语言实现对比

| 语言/平台 | 进程 | 线程 | 协程 |
|-----------|------|------|------|
| Node.js | `child_process` | 单线程 + Worker Threads | `async/await`, Promise |
| Python | `multiprocessing` | `threading` | `async/await`, `gevent` |
| Go | `os/exec` | goroutine 本质是协程 | goroutine + channel |
| Java | `ProcessBuilder` | `Thread`, `ExecutorService` | `virtual threads` (Loom) |
| Rust | `std::process` | `std::thread` | `async/await`, tokio |

### 六、适用场景

| 场景 | 推荐 | 理由 |
|------|------|------|
| CPU 密集计算 | 多进程 或 多线程 | 充分利用多核 CPU |
| I/O 密集（网络请求、文件读写） | 协程 | 极低成本等待 I/O，支持高并发 |
| 需要严格隔离 | 多进程 | 进程间完全隔离，崩溃不影响其他 |
| 共享数据频繁 | 多线程 | 共享内存通信快（注意加锁） |
| 高并发（数万连接以上） | 协程 | 内存开销极小，可调度百万级 |
| 稳定性要求极高 | 多进程 | 进程级隔离，一个挂掉不影响整体 |

### 七、典型例子

**Node.js 处理 HTTP 请求（协程 + 单线程）**：

```javascript
const http = require('http');

http.createServer(async (req, res) => {
  const data = await queryDatabase();   // 协程挂起，不阻塞线程
  const result = await processData(data); // 再次挂起
  res.end(result);
}).listen(3000);

// 虽然是单线程，但能同时处理数万请求
// 因为 await 让出执行权，事件循环处理其他请求
```

**Go 的 goroutine（协程 + channel）**：

```go
func main() {
    ch := make(chan string)
    go func() {            // 启动一个 goroutine（协程）
        ch <- "hello"      // 发送
    }()
    msg := <-ch            // 接收
    fmt.Println(msg)
}
```

### 八、总结

```
进程 ← 资源隔离，重量级
  │
  ├─ 线程 ← CPU 调度，共享内存
  │     │
  │     └─ 协程 ← 用户态调度，极轻量
  │
  └─ 协程可以直接运行在线程上

选型口诀：
  CPU 密集 → 多进程
  I/O 密集 → 协程
  需要隔离 → 多进程
  需要共享 → 多线程
  高并发   → 协程
```
