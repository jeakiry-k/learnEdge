---
date: "2026-10-20"
category: "Java基础"
title: "IO 模型与多路复用：从 BIO 到 Reactor"
tags: [Java, IO多路复用, NIO, Reactor]
---

# IO 模型与多路复用：从 BIO 到 Reactor

<div class="question-tags">
  <span class="question-tag">Java</span>
  <span class="question-tag">IO多路复用</span>
  <span class="question-tag">NIO</span>
  <span class="question-tag">Reactor</span>
</div>

> 什么是 IO 多路复用？同步/异步、阻塞/非阻塞到底怎么区分？三种 Reactor 形态运行时差别在哪？Netty 的 boss/worker 线程组怎么对应 Reactor？一次请求的真实数据流转是怎样的？IO 线程如何保证读写顺序？

### 一、从一个故事讲起：什么是 IO 多路复用

用「银行办业务」来理解最直观。假设你是大堂经理，要服务很多客户：

| 模型 | 做法 | 缺点 |
|------|------|------|
| **阻塞（BIO）** | 每来一个客户，配一个专职柜员全程跟着 | 客户一多，柜员（线程）就爆炸 |
| **非阻塞轮询** | 自己挨个问每个窗口「好了没」 | 大部分时间在空转，累死 |
| **IO 多路复用** | 请一个「叫号系统」，谁好了自动通知你 | 一个经理就够，高效省力 |

**IO 多路复用（IO Multiplexing）** 就是那个「叫号系统」：

```
传统方式：一个连接一个线程，线程数 = 连接数

多路复用：
  select/epoll 同时监听 N 个连接（叫号系统盯着所有窗口）
  → 哪个连接有数据了（客户办好了），才把它交给线程处理
  → 一个线程可以服务成千上万个连接
```

> 核心思想：**用一个「监视器」同时监听多条 IO 通道，把「有数据可读/可写」的事件集中通知，让少量线程处理大量连接。**

<div class="diagram-card">
  <img src="../../assets/diagrams/io-multiplexing/bio-vs-mux.svg" alt="BIO 与 IO 多路复用对比：一连接一线程 vs 一个线程管 N 个连接">
</div>

### 二、先搞清两个被混用的维度

「同步/异步」和「阻塞/非阻塞」经常被当成一回事，其实是**两个正交的维度**：

| 维度 | 问的是 | 关注点 |
|------|--------|--------|
| **同步/异步** | 结果怎么**通知**你 | 是主动等结果，还是被通知 |
| **阻塞/非阻塞** | 调用时线程**挂不挂起** | 是干等着，还是先去干别的 |

组合起来是一个 2×2 矩阵。下面逐一通俗解释四种组合。

### 三、四种 IO 组合，通俗说明

#### 1. 同步阻塞（同步 + 阻塞）—— 最传统

**通俗版**：你去柜台交材料，然后**隔着玻璃一直盯着柜员**，他办完前你哪也不去、啥也不干。

**技术版**：调用 `read()`，数据没到，线程被挂起，一直等到数据来了才返回。

```java
// 传统 BIO
ServerSocket server = new ServerSocket(8080);
Socket socket = server.accept();      // 阻塞：等连接
InputStream in = socket.getInputStream();
byte[] buf = new byte[1024];
in.read(buf);                          // 阻塞：等数据
```

- **优点**：代码最简单，好理解
- **缺点**：一个连接占一个线程，并发高时线程爆炸

#### 2. 同步非阻塞（同步 + 非阻塞）—— 反复问

**通俗版**：你交完材料回座位，但**每隔几分钟跑回去问一次**「好了没」，没好就再回来。

**技术版**：把 `read()` 设为非阻塞，没数据时**立刻返回** `null`/`0`，你需要**不停轮询**直到有数据。

```java
// 非阻塞：socket 设为 O_NONBLOCK
while (true) {
    int n = read();        // 立刻返回
    if (n > 0) { break; }  // 有数据了
    // 没数据，继续循环问（空转，烧 CPU）
}
```

- **优点**：线程不用挂起，一个线程能处理多个连接
- **缺点**：轮询空转会白耗 CPU，效率并不高

#### 3. 异步阻塞（异步 + 阻塞）—— 几乎不存在的组合

**通俗版**：你交材料时告诉银行「办好了**打电话通知我**」，结果你却**守在电话旁干等**——逻辑上很别扭。

**技术版**：发起异步操作（用回调通知），但之后又主动阻塞等待结果。**这个组合在实战中几乎没有意义**，因为异步的本意就是「不用等」，你却又等回去，等于把异步的价值浪费了。

> 结论：**「异步阻塞」通常不作为标准模型讨论**。记住常见的是另外三种即可。

#### 4. 异步非阻塞（异步 + 非阻塞）—— 真正的异步 AIO

**通俗版**：你交完材料，**留个手机号就走人**，干自己的事，办好了银行**短信通知你**。

**技术版**：发起 `aio_read()` 后**立刻返回**，内核在后台帮你把数据读好，再通过**回调/信号**通知你数据已就绪。

```java
// Java AIO（异步 IO）
AsynchronousSocketChannel ch = ...;
ch.read(buf, null, new CompletionHandler<Integer, Void>() {
    public void completed(Integer n, Void v) { /* 数据好了，回调通知 */ }
});
```

- **优点**：真正的异步，线程全程不用管，效率最高
- **缺点**：实现复杂，Linux 底层 AIO 生态不如 epoll 成熟，Java 里用得少

#### 四种组合速记表

| 组合 | 类比 | 线程状态 | 代表 |
|------|------|---------|------|
| 同步阻塞 | 排队一直盯着 | 挂起等待 | BIO、传统 Socket |
| 同步非阻塞 | 不停回去问 | 不挂起但空转 | NIO + 轮询 |
| 异步阻塞 | 该等却偏打电话干等 | 矛盾 | 几乎不存在 |
| 异步非阻塞 | 留手机号走人 | 全程不管 | AIO、真异步 |

> 关键记忆点：**IO 多路复用属于「同步」**——因为数据就绪后，还是要你**自己调用 read 去读**，只是「等」这一步被 select/epoll 高效地替代了。

### 四、IO 多路复用的实现：select / poll / epoll

多路复用本身在 Linux 上有三代实现，性能一代比一代强：

| 实现 | 机制 | 缺点 |
|------|------|------|
| **select** | 把 1024 个 fd 的位图交给内核监听 | 最多 1024 个；每次要整体拷贝；要遍历全部 fd |
| **poll** | 用链表存 fd，去掉 1024 限制 | 仍需遍历全部 fd，海量连接时慢 |
| **epoll** | 内核维护就绪链表，只返回就绪的 fd | 仅 Linux 有，但性能最优 |

**epoll 为什么快**（Redis、Nginx 都用它）：

```
select/poll：每次调用都要重新把所有连接扫描一遍 → 连接越多越慢 O(n)

epoll：内核直接记录"哪些连接就绪"
  → 调用时只返回"就绪的那几个"，不用全扫 → 连接再多也不怕 O(就绪数)
```

### 五、Reactor 模型：三种形态的运行时对比

Reactor（反应器）是**基于 IO 多路复用的编程模型**，核心是「事件驱动」：

```
Reactor = 事件分发器 + 事件处理器

  EventLoop（事件循环）：
    while (运行) {
      调用 selector.select()   // 等就绪事件
      遍历就绪事件，分发给对应 handler 处理
    }
```

三种形态容易混淆，结合「运行时谁在干什么」来看就清楚了：

#### 1. 单 Reactor 单线程

```
线程 A（唯一）：
  ├─ select() 监听所有事件
  ├─ 处理 accept（新连接）
  ├─ 处理 read / write（所有连接的 IO）
  └─ 处理业务逻辑（解码、计算、响应）

一个线程全包了。
```

- **优点**：模型最简单，无线程切换、无并发问题
- **缺点**：业务一慢，后面所有事件全部排队；且只用到一个 CPU 核
- **典型**：**Redis 6.0 之前**就是这个模型

#### 2. 单 Reactor 多线程

```
线程 A（Reactor，唯一）：
  ├─ select() 监听所有事件
  ├─ 处理 accept（新连接）
  └─ 处理 read / write（所有连接的 IO）← 还是它一个

worker 线程池：
  └─ 只处理业务逻辑（Reactor 把解出的请求丢过来）
```

**注意和主从 Reactor 的区别：这里 IO 读写仍然压在单个 Reactor 线程上**，只是把「业务计算」外包给了线程池。

瓶颈在哪？连接数爆炸时，**单个 Reactor 线程要处理所有连接的 read/write**——每个连接的 IO 都要它亲手做，CPU 单核跑满后，accept 队列和读写事件一起积压。极端场景（如秒杀瞬间百万级新建连接）下，连 accept 这个动作本身都消化不完，新连接直接在 backlog 队列里排队、超时。

看图对比瓶颈位置：

<div class="diagram-card">
  <img src="../../assets/diagrams/io-multiplexing/reactor-mt-bottleneck.svg" alt="单 Reactor 多线程的瓶颈：所有连接的 IO 仍压在单个 Reactor 线程上">
</div>

#### 3. 主从 Reactor 多线程

```
主 Reactor（1 个线程）：
  └─ 只干一件事：accept 新连接 → 注册给从 Reactor

从 Reactor（N 个线程，通常 = CPU 核数）：
  ├─ 各自 select() 监听分到自己名下的连接
  ├─ 各自处理这些连接的 read / write
  └─ 业务逻辑再丢给 worker 线程池（或直接在 IO 线程跑轻量逻辑）
```

主从 Reactor 分流后，运行时是这样：

<div class="diagram-card">
  <img src="../../assets/diagrams/io-multiplexing/reactor-main-sub.svg" alt="主从 Reactor：Main 只 accept，多个 Sub Reactor 分摊各自名下连接的读写">
</div>

对比就清晰了：

| | 单 Reactor 多线程 | 主从 Reactor 多线程 |
|---|---|---|
| accept 谁做 | 唯一的 Reactor 线程 | 主 Reactor |
| **read/write 谁做** | **唯一的 Reactor 线程（瓶颈）** | **多个从 Reactor 分摊** |
| 瓶颈点 | 所有连接的 IO 压一个线程 | accept 单点（但 accept 很轻，够快） |

> 一句话区分：**多线程 Reactor 是「一个人收发所有信件，雇人拆信」；主从 Reactor 是「一个人负责开门迎客，多个收发员分管各自的信箱」。** 连接爆炸时卡的是「收发信件」这个环节，所以后者才能横向扩展。

<div class="diagram-card">
  <img src="../../assets/diagrams/io-multiplexing/reactor-evolution.svg" alt="Reactor 模型三阶段演进：单线程 → 多线程 → 主从多线程">
</div>

### 六、Netty 的 bossGroup 与 workerGroup

Netty 就是主从 Reactor 的标准实现，两个线程组直接对应：

```
EventLoopGroup bossGroup   = new NioEventLoopGroup(1);   // 主 Reactor
EventLoopGroup workerGroup = new NioEventLoopGroup();    // 从 Reactor（默认 2×CPU 核）

ServerBootstrap b = new ServerBootstrap();
b.group(bossGroup, workerGroup)     // ← 主从关系在这里确立
 .channel(NioServerSocketChannel.class)
 .childHandler(...);                // 每个连接的业务 pipeline
```

| Netty 概念 | Reactor 角色 | 干什么 |
|-----------|-------------|--------|
| `bossGroup` | 主 Reactor | 只 accept 新连接，注册给 worker |
| `workerGroup` | 从 Reactor | 处理已建立连接的 read/write 事件 |
| `EventLoop` | Reactor 线程本体 | 一个线程一个 Selector，跑事件循环 |
| `Channel` | 一条连接 | 注册到**某一个固定**的 EventLoop 上 |

底层就是多路复用：每个 `EventLoop` 持有一个 `Selector`（Linux 下即 epoll），循环 `select()` → 处理就绪事件 → 跑任务队列。

<div class="diagram-card">
  <img src="../../assets/diagrams/io-multiplexing/netty-boss-worker.svg" alt="Netty 线程组结构：BossGroup 只 accept，WorkerGroup 处理读写，Channel 终身绑定 EventLoop">
</div>

> 三者关系一句话：**多路复用是底层机制（epoll），Reactor 是基于它的编程模型（事件循环），Netty 的 boss/worker 是主从 Reactor 的具体落地。**

### 七、一次完整的数据流转：从连接到响应

以 Netty 为例，把一个请求的真实旅程完整跑一遍：

```
1. 建连
   客户端 connect → 内核 TCP 三次握手完成 → 连接进入服务端 backlog 队列

2. accept（boss 线程）
   boss EventLoop 的 select() 返回 OP_ACCEPT
   → accept() 拿到 SocketChannel
   → 轮询挑一个 worker EventLoop，把 channel 注册上去（监听 OP_READ）

3. 数据到达（内核侧）
   客户端发数据 → 网卡收包 → 内核协议栈处理
   → 数据进入该 socket 的接收缓冲区 → epoll 把这个 fd 标记为可读

4. 读取（worker 线程）
   worker EventLoop 的 select() 返回 OP_READ
   → channel.read() 把数据从内核缓冲区拷到 ByteBuf
   → 沿 pipeline 流动：decoder（拆包/解码）→ 业务 handler

5. 处理 + 回写
   业务处理完 ctx.writeAndFlush(response)
   → 出站方向过 encoder → 写入 socket 发送缓冲区
   → 内核协议栈负责真正把数据发回客户端
```

关键点：**第 2 步在 boss 线程，第 4、5 步在 worker 线程**，一条连接从注册那一刻起，后续所有 IO 都由**同一个** worker EventLoop 负责——这正是下一节顺序保证的基础。

<div class="diagram-card">
  <img src="../../assets/diagrams/io-multiplexing/netty-data-flow.svg" alt="Netty 一次请求的数据流转：客户端、内核、boss 线程、worker 线程四列泳道上的八个步骤">
</div>

### 八、IO 线程的顺序保证：read/write 为什么不乱

#### 单连接内：绑定 + 串行 = 天然有序

Netty 里每个 `Channel` 从注册起就**绑定到唯一一个 EventLoop**，终身不变。于是：

```
Channel X ──绑定──→ EventLoop-3（单线程）

该连接的所有事件：
  read → read → write → read → write ...
  全部在 EventLoop-3 这一个线程上，按事件循环一轮一轮串行执行
```

- **read 有序**：TCP 本身是字节流，内核按序交付，单线程按序读，天然不乱
- **write 有序**：write 先进 channel 的 outbound buffer 队列，单线程按序刷出，天然不乱
- **跨连接无需有序**：不同 Channel 绑在不同 EventLoop 上并行跑，连接之间本来就没有顺序语义

#### 跨线程写怎么办：任务队列做「栅栏」

如果业务线程池处理完想直接 `channel.write()`，会和 IO 线程的写并发，顺序就乱了。Netty 的做法：

```
业务线程调用 write()
  → Netty 判断：当前线程不是该 channel 的 EventLoop？
  → 是 → 把 write 封装成一个 task，丢进该 EventLoop 的任务队列
  → EventLoop 下一轮循环时取出执行
```

EventLoop 每轮循环的结构，就是天然的「栅栏」：

```
while (运行) {
  1. select()                    // 等 IO 事件
  2. 处理就绪的 IO 事件           // 本轮 read/write
  3. 跑任务队列（task queue）     // 其他线程塞进来的 write、定时任务等
  ← 一轮结束，进入下一轮 —— 轮次之间天然有序
}
```

所以「轮次间的栅栏」不需要额外机制：**单线程的事件循环本身就是栅栏**——同一轮内的事件处理完才进下一轮；外部线程的操作一律转成 task 排队，由这个唯一的线程按序执行。把 Channel 绑定到固定 IO 线程，再加一个任务队列串行化外部写入，顺序问题就闭环了。

<div class="diagram-card">
  <img src="../../assets/diagrams/io-multiplexing/netty-ordering.svg" alt="Netty 顺序保证：Channel 绑定固定 EventLoop，外部写入封装成 task 排队">
</div>

### 九、Redis 用的是哪种

**Redis 6.0 之前：标准的单 Reactor 单线程。**

```
Redis 主线程（唯一）：
  ├─ epoll_wait 监听所有客户端连接
  ├─ accept 新连接
  ├─ read 请求 → 执行命令 → write 响应
  └─ 全部在这一个线程里串行完成
```

这正是 Redis 不怕并发问题、不需要锁的原因。它能撑住是因为命令全是内存操作，极快，单线程不会被业务逻辑拖住（对应 Redis 为什么快那篇的分析）。

**Redis 6.0 之后：引入 IO 多线程，但命令执行仍是单线程。**

```
主线程：accept + 命令执行（还是单线程，无锁）
IO 线程组：只帮忙做 read 解析 / write 回写（瓶颈环节外包）
```

相当于从「单 Reactor 单线程」向「单 Reactor 多线程」迈了半步——把最耗 CPU 的读写编解码分摊出去，命令执行依然保持单线程的简单性。

<div class="diagram-card">
  <img src="../../assets/diagrams/io-multiplexing/redis-threading.svg" alt="Redis 6.0+ 线程模型：主线程独占命令执行，IO 线程组只做读写解析，后台线程处理惰性删除">
</div>

### 十、总结

| 问题 | 答案 |
|------|------|
| IO 多路复用是什么 | 一个监视器同时监听多个连接，哪个就绪处理哪个 |
| 同步 vs 异步 | 结果怎么通知：主动等（同步）/ 被通知（异步） |
| 阻塞 vs 非阻塞 | 调用时线程挂不挂起 |
| 四种组合 | 同步阻塞(BIO)、同步非阻塞、异步非阻塞(AIO)、异步阻塞基本不存在 |
| 多路复用是同步还是异步 | 同步（数据就绪后仍需自己 read） |
| 三代实现 | select → poll → epoll（性能递增） |
| 三种 Reactor 区别 | 看 read/write 谁做：单线程全包 → 多线程业务外包 → 主从 IO 分摊 |
| 多线程 vs 主从的关键差异 | 前者读写仍压单个 Reactor；后者多个 SubReactor 分摊读写 |
| Netty boss/worker | boss=主 Reactor 只 accept，worker=从 Reactor 管读写 |
| 单连接顺序怎么保证 | Channel 绑定固定 EventLoop + 外部写入转 task 排队，天然串行 |
| Redis 用的哪种 | 6.0 前单 Reactor 单线程；6.0 后 IO 读写多线程、执行仍单线程 |