---
date: "2026-10-08"
category: "Java基础"
title: "线程池工作原理"
tags: [Java, 线程池, 并发]
---

# 线程池工作原理

<div class="question-tags">
  <span class="question-tag">Java</span>
  <span class="question-tag">线程池</span>
  <span class="question-tag">并发</span>
</div>

> 为什么要用线程池？它的核心参数有哪些？一个任务提交进来后，线程池是如何一步步决定谁来执行的？

### 一、为什么需要线程池

直接 `new Thread()` 执行任务，有两个致命问题：

1. **频繁创建销毁开销大**：线程的创建和销毁都是重量级操作，涉及内核态用户态切换、栈内存分配。高并发下每秒创建几百个线程，大量 CPU 消耗在"开线程/关线程"上，而不是业务逻辑。
2. **线程数量不可控**：每来一个任务就 `new Thread`，线程数无上限，最终会耗尽内存（每个线程默认栈 1MB）导致 OOM，或 CPU 频繁上下文切换性能骤降。

线程池解决的就是这两点：**复用线程** + **限制并发数量**。

### 二、核心参数（ThreadPoolExecutor 构造器）

```java
public ThreadPoolExecutor(
    int corePoolSize,              // 核心线程数
    int maximumPoolSize,           // 最大线程数
    long keepAliveTime,            // 空闲线程存活时间
    TimeUnit unit,                 // 存活时间单位
    BlockingQueue<Runnable> workQueue,  // 任务队列
    ThreadFactory threadFactory,   // 线程工厂
    RejectedExecutionHandler handler    // 拒绝策略
)
```

| 参数 | 作用 |
|------|------|
| `corePoolSize` | 核心线程数，线程池常驻线程，空闲也不会被回收 |
| `maximumPoolSize` | 最大线程数 = 核心线程 + 非核心线程 |
| `keepAliveTime` | 非核心线程空闲超过该时间后回收（`allowCoreThreadTimeOut(true)` 时核心线程也回收） |
| `workQueue` | 存放等待执行的任务队列 |
| `threadFactory` | 创建线程的工厂，用于自定义线程名、是否为守护线程等 |
| `handler` | 队列满且线程数达到上限时的拒绝策略 |

### 三、任务执行流程（面试高频）

提交任务后，线程池按以下顺序决策：

```
提交任务
   │
   ├─ ① 当前线程数 < corePoolSize？
   │      └─ 是 → 新开「核心线程」直接执行
   │
   ├─ ② 核心线程已满，队列未满？
   │      └─ 是 → 任务放入 workQueue 排队等待
   │
   ├─ ③ 队列已满，线程数 < maximumPoolSize？
   │      └─ 是 → 新开「非核心线程」执行
   │
   └─ ④ 队列满 + 线程数已达上限？
          └─ 执行拒绝策略 handler
```

> 关键记忆点：**先核心线程 → 再队列 → 再非核心线程 → 最后拒绝**。很多人记反，误以为队列满之前就会开非核心线程。

这个顺序的合理之处在于：排队比盲目扩容更划算——创建一个新线程是有代价的，先用队列缓冲，把资源留给真正需要的时候。

### 四、常见线程池（Executors 工厂方法）

| 方法 | 核心 | 最大 | 队列 | 特点 |
|------|:---:|:---:|------|------|
| `newFixedThreadPool(n)` | n | n | `LinkedBlockingQueue`（无界） | 固定线程数，队列无限增长有 OOM 风险 |
| `newCachedThreadPool()` | 0 | `Integer.MAX_VALUE` | `SynchronousQueue` | 来一个任务开一个线程，空闲 60s 回收，线程数无上限 |
| `newSingleThreadExecutor()` | 1 | 1 | `LinkedBlockingQueue`（无界） | 单线程串行执行，保证任务顺序 |
| `newScheduledThreadPool(n)` | n | `Integer.MAX_VALUE` | `DelayedWorkQueue` | 支持定时/周期任务 |

> `newFixedThreadPool` 和 `newSingleThreadExecutor` 允许队列无限增长，`newCachedThreadPool` 允许线程数无限增长——都可能 OOM。这就是《阿里巴巴 Java 开发手册》禁止用 `Executors` 直接创建、要求手动 `new ThreadPoolExecutor` 的原因。

### 五、拒绝策略（4 种）

| 策略 | 行为 |
|------|------|
| `AbortPolicy`（默认） | 直接抛 `RejectedExecutionException` |
| `CallerRunsPolicy` | 由提交任务的线程（调用者）自己执行，起到限流降速作用 |
| `DiscardPolicy` | 直接丢弃，不抛异常 |
| `DiscardOldestPolicy` | 丢弃队列中最旧的任务，再尝试提交当前任务 |

### 六、线程池参数怎么定

没有放之四海皆准的公式，但可以这样估算：

- **CPU 密集型**：线程数 ≈ CPU 核数 + 1，让每个核心尽量忙碌，避免过多切换。
- **IO 密集型**：线程数 ≈ CPU 核数 × 2 或 `CPU 核数 / (1 - 阻塞系数)`，因为线程大部分时间在等 IO，可以多开一些。

> 判断 CPU 核数：`Runtime.getRuntime().availableProcessors()`。

### 七、线程池的关闭

- `shutdown()`：不再接收新任务，等待已提交任务执行完后关闭（**平缓关闭**）。
- `shutdownNow()`：尝试中断正在执行的任务，返回队列中未执行的任务列表，不再接收新任务（**强制关闭**）。

```java
executor.shutdown();
try {
    if (!executor.awaitTermination(60, TimeUnit.SECONDS)) {
        executor.shutdownNow();
    }
} catch (InterruptedException e) {
    executor.shutdownNow();
    Thread.currentThread().interrupt();
}
```

> 优雅停机正确姿势：先 `shutdown()` 停止接收新任务，再 `awaitTermination()` 给一个超时时间等待存量任务跑完，超时仍未结束才 `shutdownNow()` 强制中断。