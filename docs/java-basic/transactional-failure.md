---
date: "2026-10-26"
category: "Java基础"
title: "@Transactional 失效的原因有哪些"
tags: [Spring, 事务, AOP]
---

# @Transactional 失效的原因有哪些

<div class="question-tags">
  <span class="question-tag">Spring</span>
  <span class="question-tag">事务</span>
  <span class="question-tag">AOP</span>
</div>

> 为什么 @Transactional 有时候不起作用？它依赖什么机制生效？方法不是 public、类内部自调用、catch 吞掉异常、rollbackFor 配置不对、传播行为设错……这些分别为什么会导致事务失效？数据库层面、多线程、跨库又有什么坑？

### 一、先搞懂：@Transactional 靠什么生效

@Transactional 本身不干任何事，真正起作用的是 **Spring AOP 代理**。

Spring 会给打了注解的类生成一个**代理对象**，外部调用方法时，先经过代理里的 `TransactionInterceptor`（事务拦截器），由它负责**开启事务 → 调用目标方法 → 提交或回滚**。

```
Client ──调用──▶ 代理对象(proxy) ──▶ TransactionInterceptor(开事务)
                                          │
                                          ▼
                                    目标方法(业务逻辑)
                                          │
                                          ▼
                              提交 / 回滚（异常时）
```

> 记住这条地基：**事务是「代理」这个中间层提供的。只要调用没有经过代理，事务就不生效。** 下面几乎所有失效原因，本质都是「调用没走代理」或「代理没开成事务」。

### 二、失效原因总览

<div class="diagram-card">
  <img src="../../assets/diagrams/transactional-failure/failure-overview.svg" alt="@Transactional 失效原因总览：代理层面、异常层面、传播行为、管理层面、数据库层面、并发与分布六类">
</div>

| 类别 | 具体原因 |
|------|---------|
| 代理层面 | 方法非 public、类内部自调用 |
| 异常层面 | catch 吞掉异常、rollbackFor 不对 |
| 传播行为 | NOT_SUPPORTED / NEVER / SUPPORTS 不开事务 |
| 管理层面 | 类没被 Spring 管理、手动 new 对象 |
| 数据库层面 | 存储引擎不支持事务（MyISAM） |
| 并发与分布 | 多线程拿不到事务、跨库需分布式事务 |

### 三、原因一：方法不是 public

Spring AOP（JDK 动态代理 / CGLIB）只能拦截 public 方法。注解加在 `private` / `protected` / 默认包可见的方法上，事务不生效。

```java
@Service
public class OrderService {
    @Transactional
    private void save(Order o) {   // ❌ private，事务失效
        orderMapper.insert(o);
    }
}
```

> Spring 官方文档明确建议 @Transactional 用在 public 方法上；从 Spring 5.2 起，遇到非 public 方法上的 @Transactional 还会打警告日志。

### 四、原因二：自调用（self-invocation）—— 最常见

类内部一个方法调用另一个 @Transactional 方法时，走的是 `this.method()`，**绕过了代理**，事务不生效。

```java
@Service
public class OrderService {
    public void createOrder(Order o) {
        save(o);    // ❌ 相当于 this.save()，没走代理，事务失效
    }

    @Transactional
    public void save(Order o) {
        orderMapper.insert(o);
    }
}
```

<div class="diagram-card">
  <img src="../../assets/diagrams/transactional-failure/self-invocation.svg" alt="自调用失效对比：this.method 绕过代理事务不生效，外部调用经过代理事务生效">
</div>

**解决方式**：

1. 把 @Transactional 方法拆到另一个 Bean，通过注入调用
2. 注入自身（`@Autowired` 注入自己，或 `@Lazy` 延迟注入避免循环依赖）
3. `AopContext.currentProxy()` 拿到代理再调用（需 `@EnableAspectJAutoProxy(exposeProxy = true)`）

### 五、原因三：异常被 catch 吞掉

Spring 只在方法**抛出异常**时才回滚。catch 住异常又不往外抛，事务感知不到，就会正常提交。

```java
@Transactional
public void save(Order o) {
    try {
        orderMapper.insert(o);
        int x = 1 / 0;             // 抛异常
    } catch (Exception e) {
        log.error("出错", e);        // ❌ 吞掉异常，事务照样提交
    }
}
```

### 六、原因四：rollbackFor 配置不对（受检异常不回滚）

默认只对 `RuntimeException` 和 `Error` 回滚，**受检异常（Checked Exception）默认不回滚**。

```java
@Transactional                       // 默认 rollbackFor = RuntimeException
public void save() throws IOException {
    orderMapper.insert(order);
    throw new IOException();          // ❌ 受检异常，默认不回滚
}
```

解决：`@Transactional(rollbackFor = Exception.class)`，或更彻底 `rollbackFor = Throwable.class`。

> 两个「异常」坑要分清：**「吞异常」是异常没抛出去，「rollbackFor 不对」是异常抛了但不属于回滚范围**。结果一样——事务没回滚，但原因不同。

### 七、原因五：传播行为配置错误

`propagation` 默认 `REQUIRED`。Spring 一共定义了 **7 种传播行为**，控制的是一件事：**当前方法运行时，是加入已有事务、新建事务，还是干脆不开事务**。

| 传播行为 | 有事务时 | 无事务时 |
|---------|---------|---------|
| `REQUIRED`（默认） | 加入 | 新建 ✅ |
| `REQUIRES_NEW` | 挂起旧事务，新建独立事务 | 新建 ✅ |
| `NESTED` | 嵌套事务（savepoint） | 新建 ✅ |
| `SUPPORTS` | 加入 | 非事务运行 ⚠️ |
| `NOT_SUPPORTED` | 挂起，非事务运行 | 非事务运行 ❌ |
| `MANDATORY` | 加入 | 抛异常 ⚠️ |
| `NEVER` | 抛异常 | 非事务运行 ❌ |

<div class="diagram-card">
  <img src="../../assets/diagrams/transactional-failure/propagation-behaviors.svg" alt="Spring 七种传播行为一览：默认 REQUIRED 覆盖绝大多数，其余六种很少用">
</div>

其中「不开事务」的三种——`NOT_SUPPORTED` / `NEVER`，以及 `SUPPORTS` 且当前无事务时——方法就是**裸奔**的，不产生事务，这就是传播行为导致的失效。

#### 为什么开发中基本只用 REQUIRED？

传播行为看着像道「选择题」，但真实项目里 95% 都是默认的 `REQUIRED`，其余 6 种很少有人主动用。原因有三：

**1. `REQUIRED` 已经覆盖绝大多数场景。** 大多数业务就是一个 Service 方法、一次数据库操作、一个原子单元，「有事务就加入，没有就新建」这个语义最自然，几乎不用思考。

**2. 看似需要传播行为的场景，往往有更简单、更可靠的替代。** `REQUIRES_NEW` 的典型用途是「日志、发消息不能受主事务回滚影响」，但很多人直接用 `@Async` 异步或发 MQ 消息来解耦，而不是在同一段数据库事务链里嵌套独立事务。而且 `REQUIRES_NEW` 自带两个隐患：① 每个独立事务要多占一个数据库连接，主事务还被挂起不能释放，高并发下容易打满连接池；② 外层回滚了、内层却已提交，造成「部分提交」的数据不一致。

**3. 其余几种是防御性 / 极特殊语义，收益小、认知成本高。** `SUPPORTS`（有事务就用，没有就不用）语义模糊，同一个方法在不同调用路径下行为不一致，难推理、容易埋雷；`NOT_SUPPORTED` / `NEVER`（强制无事务）在真实业务里「必须无事务」的场景极少，通常直接写一个不加注解的方法就行；`MANDATORY`（强制要有事务）只是防御性检查；`NESTED` 依赖数据库 savepoint，配合 JPA/Hibernate 时支持有限、行为不完全可控。

所以结论是：传播行为这个参数「看着全能，实际默认值就够用」。团队规范通常也直接约定「默认 `REQUIRED`，禁止乱配」——一旦用了 `REQUIRES_NEW` / `NESTED`，事务的嵌套拓扑会变复杂，回滚范围、锁持有时间、连接占用都变得难以推理，排查成本远高于收益。

### 八、原因六：类没有被 Spring 管理

- 类忘了加 `@Service` / `@Component`，或不在组件扫描路径下
- 用 `new OrderService()` 手动 new 出来的对象调用（不是从容器拿的，没有代理，注解自然不生效）

```java
OrderService service = new OrderService();  // ❌ 手动 new，没有代理
service.save(order);
```

### 九、其他容易忽略的原因

- **数据库引擎不支持事务**：MySQL 的 **MyISAM** 不支持事务，@Transactional 对它无效，必须用 InnoDB
- **多线程**：事务信息绑定在 ThreadLocal 上，`@Async` 或手动 `new Thread` 里调用 @Transactional 方法，子线程拿不到父线程的事务，等于各自为政
- **注解写在接口 / 抽象类上**：用 CGLIB 代理时，接口上的 @Transactional 不生效，应加到实现类上
- **跨库 / 分布式**：本地事务无法跨多个数据源，需要分布式事务方案（Seata、XA 等）

### 十、总结

| 问题 | 答案 |
|------|------|
| @Transactional 靠什么生效 | Spring AOP 代理，调用必须经过代理 |
| 最常见的失效原因 | 自调用（this.method 绕过代理） |
| 为什么受检异常默认不回滚 | rollbackFor 默认只回滚 RuntimeException / Error |
| catch 吞异常会怎样 | 事务感知不到异常，正常提交 |
| 传播行为哪些不开事务 | NOT_SUPPORTED / NEVER，SUPPORTS 视情况 |
| 数据库层面 | MyISAM 不支持事务 |
| 跨库怎么办 | 需要分布式事务（Seata / XA） |
