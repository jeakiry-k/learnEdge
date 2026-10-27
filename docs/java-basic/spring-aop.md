---
date: "2026-10-27"
category: "Java基础"
title: "Spring AOP 方式和原理，开发中注意事项"
tags: [Spring, AOP, 代理, 切面]
---

# Spring AOP 方式和原理，开发中注意事项

<div class="question-tags">
  <span class="question-tag">Spring</span>
  <span class="question-tag">AOP</span>
  <span class="question-tag">代理</span>
  <span class="question-tag">切面</span>
</div>

> Spring AOP 是怎么实现的？JDK 动态代理和 CGLIB 有什么区别、Spring 分别怎么选？切点、通知、切面、织入这些概念各是什么？五种通知类型（@Before / @After / @Around…）的执行顺序是怎样的？为什么有些方法切面拦截不到（自调用、非 public、final、static）？开发中拿它做事务、日志、权限、缓存时有哪些坑要注意？

### 一、AOP 是什么：解决横切关注点

AOP（Aspect-Oriented Programming，面向切面编程）解决的是**横切关注点**（cross-cutting concern）的问题。

日志、事务、权限校验、缓存这些逻辑，几乎每个业务方法里都要写一点，但它们和「下单」「扣库存」这些核心业务本身没关系。如果每个方法里都硬塞，代码就变成：

```java
public void createOrder(Order o) {
    log.info("开始创建订单");          // 日志（横切）
    SecurityUtils.check();             // 权限（横切）
    tx.begin();                        // 事务（横切）
    orderMapper.insert(o);             // 核心业务
    tx.commit();
    log.info("订单创建完成");
}
```

AOP 的思路是把这些横切逻辑**抽出来集中管理**，再「织入」到需要的地方。业务方法里只剩一行核心逻辑，横切逻辑全部挪进切面。

<div class="diagram-card">
  <img src="../../assets/diagrams/spring-aop/crosscutting.svg" alt="横切关注点：日志/事务/权限散落在各方法 vs AOP 集中到切面统一织入">
</div>

> 一句话：AOP 让你在不改业务代码的前提下，给一批方法统一「加料」。Spring 里 @Transactional 就是最典型的一个 AOP 应用——它由 `TransactionInterceptor` 这个 Advice 实现。

### 二、AOP 的核心概念

这几个词面试常被混着问，先一次性厘清：

| 概念 | 英文 | 含义 |
|------|------|------|
| 连接点 | JoinPoint | 所有「可以被拦截」的点，Spring 里就是方法执行 |
| 切入点 | Pointcut | 用表达式筛选出**真正要拦截**的那些连接点 |
| 通知 | Advice | 拦截到之后**具体做什么**（before / around…） |
| 切面 | Aspect | **切入点 + 通知**的组合，一个类就是一个切面 |
| 目标对象 | Target | 被代理的原始对象 |
| 代理对象 | Proxy | 织入切面后生成的、对外暴露的新对象 |
| 织入 | Weaving | 把切面应用到目标对象、生成代理的**过程** |

用一句话串起来：**在连接点里，用切入点挑出一批点，用通知定义拦截逻辑，两者合起来是切面，把切面应用到目标对象生成代理的过程叫织入。**

### 三、两种实现方式：JDK 动态代理 vs CGLIB

Spring AOP 的底层只有两种「造代理」的手段，这是理解一切行为（包括失效）的钥匙。

| 维度 | JDK 动态代理 | CGLIB |
|------|------------|-------|
| 原理 | 基于**接口**：`Proxy` + `InvocationHandler`，用反射调用 | 基于**继承**：字节码生成目标类的**子类** |
| 前提 | 目标类必须实现接口 | 不要求接口，但类/方法不能是 `final` |
| 拦截范围 | 只能拦截接口里定义的方法 | 可拦截所有非 final 方法 |
| 调用方式 | 反射（`Method.invoke`） | 直接调用子类方法（`FastClass` 索引） |
| 性能 | 生成快，调用略慢 | 生成稍慢，调用更快 |

Spring 怎么选：

- **传统 XML 时代**：目标类实现了接口 → 默认用 JDK 代理；没实现接口 → CGLIB。
- **Spring Boot 2.0+**：默认 `spring.aop.proxy-target-class=true`，**统一用 CGLIB**，即使实现了接口也走 CGLIB。目的是行为一致，避免「JDK 代理只能强转成接口、转具体类报错」这类坑。
- 手动指定：`@EnableAspectJAutoProxy(proxyTargetClass = true)` 强制 CGLIB，`false` 则「有接口就 JDK」。

<div class="diagram-card">
  <img src="../../assets/diagrams/spring-aop/jdk-vs-cglib.svg" alt="JDK 动态代理基于接口、CGLIB 基于继承生成子类的对比">
</div>

### 四、五种通知类型与执行顺序

切面里能写五种通知（Advice），注解分别是：

| 注解 | 时机 |
|------|------|
| `@Before` | 目标方法执行**前** |
| `@AfterReturning` | 目标方法**正常返回后** |
| `@AfterThrowing` | 目标方法**抛异常后** |
| `@After` | **无论如何**都执行（相当于 finally） |
| `@Around` | 包在最外层，可控制是否执行目标方法 |

`@Around` 是最强大的，用 `ProceedingJoinPoint.proceed()` 手动触发目标方法，可以改参数、改返回值、甚至不调用目标方法。

执行顺序是「洋葱模型」——`@Around` 包在最外层，往里依次是 `@Before` → 目标方法 → `@AfterReturning`/`@AfterThrowing` → `@After`：

<div class="diagram-card">
  <img src="../../assets/diagrams/spring-aop/advice-order.svg" alt="五种通知执行顺序：Around 包最外层，Before 前、AfterReturning/AfterThrowing 后、After 兜底">
</div>

```java
@Around("pointcut()")
public Object around(ProceedingJoinPoint pjp) throws Throwable {
    // 1. 环绕前
    Object result = pjp.proceed();  // 触发 @Before → 目标方法 → @After*
    // 4. 环绕后
    return result;
}
```

> 多个切面叠加时，顺序由 `@Order`（值小优先）或切面类加载顺序决定。这一点在「日志切面 + 事务切面」同时存在时很重要，顺序错了可能日志记录不到事务回滚之后的状态。

### 五、切点表达式怎么写

切点表达式（Pointcut Expression）决定「哪些方法被拦截」。最常用的是 `execution`：

```
execution(修饰符? 返回类型 类路径.方法名(参数) 异常?)
```

几个高频例子：

| 表达式 | 含义 |
|--------|------|
| `execution(* com.xx.service.*.*(..))` | service 包下所有类的所有方法 |
| `execution(public * *(..))` | 所有 public 方法 |
| `execution(* com.xx..*Service.*(..))` | 任意层级下 `*Service` 类的方法 |
| `@annotation(com.xx.MyAnno)` | 所有打了 `@MyAnno` 的方法 |
| `within(com.xx.service.*)` | service 包下所有类（不含子包） |

`*` 匹配任意字符，`..` 匹配任意层级的包或任意参数。配合 `&&`、`||`、`!` 组合。

### 六、为什么切面有时不生效

这部分和 @Transactional 失效是**同一套根因**——Spring AOP 靠代理，只要调用没走代理，切面就不生效：

1. **自调用**：同类里 `this.method()`，绕过了代理，切面拦截不到。最常见。
2. **方法非 public**：JDK 代理只能拦接口的 public 方法，CGLIB 也拦不了 private。
3. **final / static 方法**：CGLIB 靠继承，`final` 方法无法覆写；`static` 方法不属于实例、代理不了。
4. **切面类没交给 Spring 管理**：`@Aspect` 类忘了加 `@Component`，或目标类不在扫描路径。
5. **切入点表达式写错**：匹配不到任何方法（比如包路径拼错），静默失效。
6. **目标对象是 `new` 出来的**：不是容器里的代理 Bean，注解自然无效。

解决自调用的老办法和事务篇一致：把被代理方法拆到另一个 Bean，或 `AopContext.currentProxy()` 拿代理调用，或注入自身（`@Lazy`）。

### 七、开发中的注意事项

1. **类型判断别用具体类**。拿到的是代理对象，`bean instanceof ImplClass` 在 JDK 代理下会 `false`（代理实现的是接口）。判断类型要用接口，注入也要用接口类型。

2. **事务就是 AOP，理解了 AOP 才懂事务失效**。@Transactional 底层是 `TransactionInterceptor`，事务篇所有失效原因（自调用、非 public、catch 吞异常）本质都是「没走代理」。

3. **性能开销**。代理有反射开销，但现代 JVM 下可忽略；真正的开销是你自己在切面里干重活——比如在 `@Around` 里同步查库、加锁，那才是性能杀手。

4. **循环依赖**。构造器注入 + AOP 代理容易触发循环依赖。Spring 用三级缓存解决 setter 循环依赖，但**构造器循环依赖无解**，会直接报错。

5. **切面顺序要显式控制**。多个切面同时命中一个方法时，用 `@Order(n)` 指定顺序，别依赖类名字典序这种隐式规则。

6. **不要用 `this` 调自己的代理方法**。同上，自调用绕过代理，切面失效。

### 八、总结

| 问题 | 答案 |
|------|------|
| AOP 解决什么 | 横切关注点：日志/事务/权限/缓存等与业务无关的重复逻辑 |
| 核心组成 | 切入点（选谁）+ 通知（干什么）= 切面，应用到目标对象叫织入 |
| 两种实现 | JDK 动态代理（基于接口）、CGLIB（基于继承生成子类） |
| Spring 怎么选 | 有接口用 JDK，无接口用 CGLIB；Boot 2.0+ 默认统一 CGLIB |
| 五种通知 | Before / AfterReturning / AfterThrowing / After / Around |
| 通知顺序 | Around 最外层 → Before → 目标方法 → AfterReturning/Throwing → After |
| 切面为什么失效 | 自调用、非 public、final/static、切面未托管、表达式写错、new 对象 |
| 开发注意 | 类型判断用接口、理解事务即 AOP、控制切面顺序、规避循环依赖 |
