---
date: "2026-10-11"
category: "Java基础"
title: "Java 单例模式的几种实现方式"
tags: [Java, 单例, 设计模式]
---

# Java 单例模式的几种实现方式

<div class="question-tags">
  <span class="question-tag">Java</span>
  <span class="question-tag">单例</span>
  <span class="question-tag">设计模式</span>
</div>

> 单例模式有哪些实现方式？各自的优缺点是什么？为什么推荐用枚举或静态内部类？

### 一、什么是单例模式

单例模式（Singleton）保证一个类**在整个 JVM 里只有一个实例**，并提供全局访问点。

核心有三个要点：

1. 构造方法私有化（`private`），外部无法 `new`
2. 类内部创建唯一实例
3. 对外提供静态方法返回该实例

典型使用场景：配置类、线程池、数据库连接池、日志记录器、缓存管理器等——这些对象全局只需要一份。

### 二、名字怎么来的：饿汉 vs 懒汉

这两个形象的名字，描述的是**实例创建时机的区别**：

```
饿汉式（Eager Initialization）：
  类一加载就立刻创建实例，不管你现在用不用
  → 像"饿急了的人，一上桌就迫不及待开吃"

懒汉式（Lazy Initialization）：
  等到第一次真正调用 getInstance() 时才创建
  → 像"懒人，不到万不得已绝不动手"
```

核心区分点就是：**急着先创建（饿） vs 用到才创建（懒）**。明白了这个，后面的各种实现只是在这两种基础上解决「线程安全、防破坏」等衍生问题。

### 三、饿汉式（静态常量）

```java
public class Singleton {
    // 类加载时就创建实例
    private static final Singleton INSTANCE = new Singleton();

    private Singleton() {}

    public static Singleton getInstance() {
        return INSTANCE;
    }
}
```

- **优点**：实现最简单，类加载时实例已就绪，天然线程安全。
- **缺点**：没有懒加载——即使全程没用到，类加载时也会创建实例，浪费内存。
- **适用**：实例创建开销小、且确定会被用到的情况。

### 四、懒汉式（线程不安全）

```java
public class Singleton {
    private static Singleton instance;

    private Singleton() {}

    public static Singleton getInstance() {
        if (instance == null) {       // 检查
            instance = new Singleton();
        }
        return instance;
    }
}
```

- **优点**：懒加载，第一次调用才创建。
- **缺点**：线程不安全。多个线程同时通过 `instance == null` 检查，可能创建多个实例。
- **结论**：**单线程可用，多线程禁用**。

### 五、懒汉式（同步方法）

```java
public class Singleton {
    private static Singleton instance;

    private Singleton() {}

    public static synchronized Singleton getInstance() {
        if (instance == null) {
            instance = new Singleton();
        }
        return instance;
    }
}
```

- **优点**：通过 `synchronized` 保证线程安全，且懒加载。
- **缺点**：每次调用 `getInstance()` 都要加锁，即使实例早已创建。高并发下性能差。
- **结论**：能保证单例，但效率低，一般不用。

### 六、双重检查锁（DCL）

```java
public class Singleton {
    // volatile 防止指令重排
    private static volatile Singleton instance;

    private Singleton() {}

    public static Singleton getInstance() {
        if (instance == null) {                 // 第一次检查：避免不必要的加锁
            synchronized (Singleton.class) {
                if (instance == null) {         // 第二次检查：保证只创建一次
                    instance = new Singleton();
                }
            }
        }
        return instance;
    }
}
```

- **优点**：懒加载 + 线程安全 + 性能好（实例创建后不再加锁）。
- **关键点**：`instance` 必须用 `volatile` 修饰。

**为什么必须 `volatile`？**

`new Singleton()` 不是原子操作，分三步：

```
1. 分配内存空间
2. 初始化对象（调用构造方法）
3. 将 instance 指向内存地址
```

JVM 可能进行指令重排，让步骤 2 和 3 对调。此时另一个线程在第一次检查时看到 `instance != null` 就直接返回了一个**尚未完成初始化**的对象。

`volatile` 禁止这种指令重排，保证 `instance` 的写操作对其它线程可见且有序。

### 七、静态内部类（推荐）

```java
public class Singleton {
    private Singleton() {}

    // 静态内部类，只有被引用时才加载
    private static class Holder {
        private static final Singleton INSTANCE = new Singleton();
    }

    public static Singleton getInstance() {
        return Holder.INSTANCE;
    }
}
```

- **原理**：利用 JVM 类加载机制——`Holder` 内部类在 `getInstance()` 首次调用时才被加载并初始化 `INSTANCE`，天然线程安全（类初始化由 JVM 保证）。
- **优点**：懒加载 + 线程安全 + 无锁 + 实现简洁。**兼顾了饿汉式的安全和懒汉式的延迟加载**。
- **缺点**：无法传参；单例类破坏性强反射场景下仍需处理。

### 八、枚举（最推荐）

```java
public enum Singleton {
    INSTANCE;

    public void doSomething() {
        // 业务方法
    }
}

// 使用
Singleton.INSTANCE.doSomething();
```

- **原理**：`enum` 本质是类，JVM 保证枚举常量只会被实例化一次，且构造默认私有。
- **优点**：
  1. 写法最简洁
  2. 线程安全（JVM 保证）
  3. **天然防反射**——反射调用 `newInstance` 会抛 `IllegalArgumentException`
  4. **天然防序列化破坏**——反序列化不会创建新实例
- **结论**：《Effective Java》作者 Joshua Bloch 推荐的「最佳单例实现方式」。日常开发无特殊需求时优先用枚举。

### 九、几种方式对比

| 方式 | 懒加载 | 线程安全 | 防反射/序列化 | 性能 | 推荐度 |
|------|:---:|:---:|:---:|------|:---:|
| 饿汉式 | ✗ | ✓ | ✗ | 高 | 一般 |
| 懒汉式（不安全） | ✓ | ✗ | ✗ | 高 | 禁用（多线程） |
| 懒汉式（同步方法） | ✓ | ✓ | ✗ | 低 | 不推荐 |
| 双重检查锁 DCL | ✓ | ✓ | ✗ | 高 | 较推荐 |
| 静态内部类 | ✓ | ✓ | ✗ | 高 | 推荐 |
| 枚举 | ✓ | ✓ | ✓ | 高 | **最推荐** |

### 十、序列化与反射破坏单例

除了实现方式的选择，还要注意两个「破坏单例」的场景：

```java
// 1. 反射破坏：私有构造方法拦不住反射
Constructor<Singleton> c = Singleton.class.getDeclaredConstructor();
c.setAccessible(true);
Singleton s = c.newInstance();   // 普通类会被这样突破出第二个实例

// 2. 序列化破坏：反序列化绕过构造方法
ObjectInputStream in = new ObjectInputStream(...);
Singleton s = (Singleton) in.readObject();  // 得到新实例
```

- **反射破坏** → 用枚举解决（枚举不允许反射实例化）。
- **序列化破坏** → 用枚举解决，或在普通类中增加 `readResolve()` 方法返回已有实例。

> 这也是为什么面试中回答「单例怎么实现最安全」时，枚举是最稳的答案——它同时免疫反射和序列化两种破坏。