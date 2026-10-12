---
date: "2026-10-12"
category: "Java基础"
title: "Java 线程的六种状态与状态流转"
tags: [Java, 线程, 状态, 并发]
---

# Java 线程的六种状态与状态流转

<div class="question-tags">
  <span class="question-tag">Java</span>
  <span class="question-tag">线程</span>
  <span class="question-tag">状态</span>
  <span class="question-tag">并发</span>
</div>

> Java 线程有哪几种状态？每种状态是如何触发、如何退出的？开发中判断线程状态时有哪些常见误区？

### 一、六种状态概览

Java 线程状态由 `Thread.State` 枚举定义，共 **6 种**：

| 状态 | 枚举 | 含义 | 本质 |
|------|------|------|------|
| 新建 | `NEW` | 线程对象已创建，尚未调用 `start()` | 还没开始运行 |
| 运行 | `RUNNABLE` | 可运行，包括「正在运行」和「就绪等待 CPU」 | 拿到或等待 CPU |
| 阻塞 | `BLOCKED` | 等待进入 `synchronized` 锁 | 在等锁 |
| 等待 | `WAITING` | 无限期等待，需被显式唤醒 | 在等别人叫醒 |
| 限时等待 | `TIMED_WAITING` | 限时等待，超时自动唤醒 | 在等一段时间 |
| 终止 | `TERMINATED` | 线程已完成执行 | 已结束 |

> 注意：`RUNNABLE` 对应操作系统的「就绪 + 运行」两个底层状态，JVM 把它们合并成了一个。所以 `RUNNABLE` 不一定是「正在跑」，可能只是在排队等 CPU。

### 二、各状态如何触发

#### 1. NEW → RUNNABLE

```java
Thread t = new Thread(task);  // NEW，还没开始
t.start();                    // 调用 start() 后进入 RUNNABLE
// 注意：start() 只能调用一次，重复调用抛 IllegalThreadStateException
```

#### 2. RUNNABLE → BLOCKED

线程尝试获取一个**被其他线程持有**的 `synchronized` 锁时，进入 BLOCKED：

```java
synchronized (lock) {
    // 拿到锁的线程在这里运行（RUNNABLE）
    // 没拿到锁、在等待进入的线程是 BLOCKED
}
```

锁一旦可用，BLOCKED 线程自动变为 RUNNABLE 继续抢锁。

#### 3. RUNNABLE → WAITING

调用「无限期等待」的方法会进入 WAITING，**必须被其他线程显式唤醒**：

```java
Object.wait();          // 需要 notify()/notifyAll() 唤醒
Thread.join();          // 等价于在目标线程上 wait，目标线程结束时唤醒
LockSupport.park();     // 需要 unpark() 唤醒
```

#### 4. RUNNABLE → TIMED_WAITING

调用「限时等待」的方法，**超时自动唤醒**：

```java
Thread.sleep(1000);        // 睡眠 1 秒
Object.wait(1000);         // 最多等 1 秒
Thread.join(1000);         // 最多等 1 秒
LockSupport.parkNanos(...); // 限时 park
```

#### 5. RUNNABLE → TERMINATED

`run()` 方法执行完毕（或抛出未捕获异常）后，线程进入 TERMINATED，**不可再启动**：

```java
// 线程结束后，isAlive() 返回 false
thread.isAlive();  // false
```

### 三、状态流转总图

```
NEW ──start()──► RUNNABLE ◄────┐
                   │  │  │      │
        synchronized  │  │      │
        抢锁失败     │  │      │
                   ▼  │  │      │
                BLOCKED │      │
                   │    │      │
       锁可用自动回  │    │      │
                   └────┘      │
          wait()/join()/park() │ notify()/unpark()
                   ▼    │      │
                 WAITING ──────┘
          sleep()/wait(t)/join(t)
                   ▼    │
              TIMED_WAITING ──超时──┘
                   │
              run() 结束
                   ▼
              TERMINATED
```

### 四、关键误区

#### sleep 与 wait 的区别

这是最高频的面试辨析，也是最容易踩的坑：

| 维度 | `Thread.sleep()` | `Object.wait()` |
|------|------------------|-----------------|
| 所属类 | `Thread` 静态方法 | `Object` 实例方法 |
| 释放锁 | ❌ **不释放**已持有的锁 | ✅ **释放**锁 |
| 唤醒 | 超时自动醒 | 需 `notify()`/`notifyAll()` |
| 使用前提 | 任意处可用 | 必须在 `synchronized` 块内，否则 `IllegalMonitorStateException` |
| 状态 | `TIMED_WAITING` | `WAITING` 或 `TIMED_WAITING` |

```java
// 典型错误：在 synchronized 里 sleep，导致其他线程拿不到锁
synchronized (lock) {
    Thread.sleep(5000);  // 持有锁睡了 5 秒，注意这里的锁没有释放！
}

// 正确做法（若想释放锁等待）：
synchronized (lock) {
    lock.wait(5000);     // 释放锁并等待，超时或被唤醒后重新竞争锁
}
```

#### BLOCKED 与 WAITING 的区别

| 状态 | 等什么 | 谁来唤醒 |
|------|--------|---------|
| `BLOCKED` | 等 `synchronized` 锁 | 锁被释放后**自动**恢复 |
| `WAITING` | 等条件满足（wait/join/park） | 需要**显式** `notify`/`unpark` |

> 一句话：`BLOCKED` 是「被动等锁」，`WAITING` 是「主动等条件」。

#### 状态是「瞬时」的

`RUNNABLE`、`BLOCKED` 可能会在极短时间内来回切换。用 jstack 观察到的状态只是**某一瞬间的快照**，多次采样才能判断线程真实卡在哪。

### 五、开发实践注意事项

1. **用 wait/notify 时必须在锁内**：`wait()` 必须在 `synchronized` 块中调用，否则抛 `IllegalMonitorStateException`。

2. **wait 要用 while 而非 if**：`wait()` 醒来后条件可能已被其他线程改变（虚假唤醒），必须循环检查：

   ```java
   synchronized (lock) {
       while (queue.isEmpty()) {   // 用 while，不是 if！
           lock.wait();
       }
       queue.remove();
   }
   ```

3. **优先用并发工具类**：生产代码尽量用 `CountDownLatch`、`CyclicBarrier`、`Semaphore`、`BlockingQueue` 替代手写 `wait/notify`，避免复杂的锁状态管理。

4. **join 用于等待线程结束**：`t.join()` 让当前线程进入 WAITING 等待 `t` 结束，常用于依赖多个线程结果的场景。

5. **sleep 不释放锁，慎用**：在持有锁的临界区内 `sleep` 会阻塞其他线程，性能问题之源。

6. **排查死锁看状态**：两个线程分别 `BLOCKED` 在对方持有的锁上，即发生死锁，可用 `jstack` 或 `ThreadMXBean.findDeadlockedThreads()` 检测。

```java
// join 典型用法：主线程等待两个子线程执行完
Thread t1 = new Thread(() -> System.out.println("任务1"));
Thread t2 = new Thread(() -> System.out.println("任务2"));
t1.start();
t2.start();
t1.join();  // 当前线程 WAITING，直到 t1 结束
t2.join();
System.out.println("两个任务都完成了");
```

### 六、总结

| 问题 | 答案 |
|------|------|
| 有哪几种状态 | NEW / RUNNABLE / BLOCKED / WAITING / TIMED_WAITING / TERMINATED |
| RUNNABLE 是什么 | 就绪 + 运行，不一定正在跑 |
| 何时 BLOCKED | 等 synchronized 锁时 |
| 何时 WAITING | wait/join/park 无限期等待 |
| 何时 TIMED_WAITING | sleep/限时 wait/限时 join |
| sleep vs wait | sleep 不释放锁、超时醒来；wait 释放锁、需 notify 唤醒 |
| 实践注意 | wait 在锁内用 while、优先用并发工具类、sleep 慎用 |