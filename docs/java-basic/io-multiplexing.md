---
date: "2026-10-14"
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

> 什么是 IO 多路复用？同步/异步、阻塞/非阻塞到底怎么区分？Reactor 模型是怎么运作的？Nginx、Netty、Redis 凭什么一个线程扛住海量连接？

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

> 关键记忆点：**IO 多路复用属于「同步」**——因为数据就绪后，还是要你**自己调用 read 去读**，只是「等」这一步被 selec/epoll 高效地替代了。

### 四、POSIX 标准的五种 IO 模型

上面是「两个维度」的视角，Linux 官方（POSIX）则给出五种模型：

| 模型 | 说明 |
|------|------|
| 1. 阻塞 IO | 一直等到数据就绪并读完才返回 |
| 2. 非阻塞 IO | 数据没就绪立即返回，需轮询 |
| 3. **IO 多路复用** | select/poll/epoll 统一监听多个连接 |
| 4. 信号驱动 IO | 数据就绪时发信号通知（用得少） |
| 5. 异步 IO | 内核读完数据再通知（真异步） |

前四种都是「同步」（读数据这一步要自己来），只有第 5 种异步是「内核帮你读完」。

### 五、IO 多路复用的实现：select / poll / epoll

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

### 六、Reactor 模型

Reactor（反应器）是**基于 IO 多路复用的编程模型**，核心是「事件驱动」：

```
Reactor = 事件分发器 + 事件处理器

  EventLoop（事件循环）：
    while (运行) {
      调用 selector.select()   // 等就绪事件
      遍历就绪事件，分发给对应 handler 处理
    }
```

按线程数量分为三种演进形态：

| 形态 | 结构 | 适用 |
|------|------|------|
| **单 Reactor 单线程** | 一个线程既监听又处理 | 简单，处理慢会阻塞后续事件（Redis 早期） |
| **单 Reactor 多线程** | 一个线程监听，多个 work 线程处理 | 处理耗时任务，但监听仍是单点 |
| **主从 Reactor 多线程** | 主 Reactor 只负责 accept，从 Reactor 负责读写 | Netty 的标准做法，生产主流 |

**主从 Reactor 多线程（Netty 就是这么干的）：**

```
主 Reactor（boss 线程组）：
  只负责接收新连接 accept
  → 把连接注册到从 Reactor

从 Reactor（worker 线程组）：
  负责已建立连接的读写事件
  → 每个 worker 管理一批连接，并行处理
```

> 类比：老板（主 Reactor）只负责「迎宾拉客」，进店后分给服务员（从 Reactor）各自服务，老板不亲自端盘子。

### 七、Java NIO 怎么操作：Selector 示例

Java 的 `Selector` 就是对 epoll 的封装，NIO 写多路复用服务的骨架如下：

```java
// 1. 创建选择器和通道
Selector selector = Selector.open();
ServerSocketChannel server = ServerSocketChannel.open();
server.bind(new InetSocketAddress(8080));
server.configureBlocking(false);              // 必须非阻塞
server.register(selector, SelectionKey.OP_ACCEPT);  // 注册"接受连接"事件

while (true) {
    selector.select();                        // 阻塞等待就绪事件（多路复用的核心）
    for (SelectionKey key : selector.selectedKeys()) {
        if (key.isAcceptable()) {
            SocketChannel client = server.accept();
            client.configureBlocking(false);
            client.register(selector, SelectionKey.OP_READ);  // 新连接注册读事件
        } else if (key.isReadable()) {
            SocketChannel client = (SocketChannel) key.channel();
            // 读数据、处理...
        }
    }
    selector.selectedKeys().clear();
}
```

关键三步：**注册事件 → select 等待 → 分发处理**。

### 八、总结

| 问题 | 答案 |
|------|------|
| IO 多路复用是什么 | 一个监视器同时监听多个连接，哪个就绪处理哪个 |
| 同步 vs 异步 | 结果怎么通知：主动等（同步）/ 被通知（异步） |
| 阻塞 vs 非阻塞 | 调用时线程挂不挂起 |
| 四种组合 | 同步阻塞(BIO)、同步非阻塞、异步非阻塞(AIO)、异步阻塞基本不存在 |
| 多路复用是同步还是异步 | 同步（数据就绪后仍需自己 read） |
| 三代实现 | select → poll → epoll（性能递增） |
| Reactor 是什么 | 基于多路复用的事件驱动编程模型 |
| 生产主流 | 主从 Reactor 多线程（Netty） |