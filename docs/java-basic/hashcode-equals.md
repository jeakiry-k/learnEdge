---
title: == 和 equals 的区别
description: == 与 equals 的本质区别、各自的适用场景，以及 equals 与 hashCode 的关系（衍生问题）。
date: 2026-09-29
category: Java基础
tags: [Java, ==, equals, hashCode]
---

# == 和 equals 的区别

<div class="question-tags">
  <span class="question-tag">Java</span>
  <span class="question-tag">==</span>
  <span class="question-tag">equals</span>
  <span class="question-tag">hashCode</span>
</div>

> `==` 和 `equals` 有什么区别？分别什么时候用？为什么重写 `equals` 时必须重写 `hashCode`？

### 一、直接回答

`==` 和 `equals` 的本质区别在于**比较的内容不同**：

| 对比项 | `==` | `equals()` |
|--------|------|-----------|
| 基本类型 | 比较**值**是否相等 | 不能使用 |
| 引用类型 | 比较**内存地址**是否相同（是不是同一个对象） | 默认比较地址，但可被重写为比较**内容** |

一句话：`==` 是「是不是同一个东西」，`equals` 是「内容是否相等」——前提是类正确重写了 `equals`。

```java
String a = new String("hello");
String b = new String("hello");

System.out.println(a == b);        // false，两个不同对象，地址不同
System.out.println(a.equals(b));   // true，String 重写了 equals，比较内容
```

### 二、== 的语义

`==` 是**运算符**，行为固定，不可重写：

```java
// 1. 基本类型：比较值
int x = 10, y = 10;
System.out.println(x == y);       // true

// 2. 引用类型：比较地址（是否同一个对象）
String s1 = new String("a");
String s2 = new String("a");
System.out.println(s1 == s2);     // false，两个不同对象

String s3 = "a";
String s4 = "a";
System.out.println(s3 == s4);     // true，字符串常量池复用同一个对象
```

> 陷阱：`String` 的常量池会让 `==` 偶尔「看起来」比较了内容，实质仍是地址比较，只是恰好指向同一对象。

### 三、equals 的语义

`equals()` 是 **Object 的方法**，默认行为和 `==` 一样（比较地址），需要时由子类重写：

```java
// Object 默认实现（未重写时）
public boolean equals(Object obj) {
    return (this == obj);   // 就是地址比较
}
```

**String 重写了 equals，改为比较内容：**

```java
// String.equals 的核心逻辑（简化）
public boolean equals(Object anObject) {
    // 先比地址，相同直接 true；再逐字符比较内容
}
```

所以「`equals` 比较内容」这句话有前提：**该类重写了 `equals`**。自定义类若不重写，退化为地址比较。

### 四、什么时候用哪个

| 场景 | 选择 | 原因 |
|------|------|------|
| 基本类型（int、char、boolean...） | `==` | equals 不能用 |
| 比较对象是否同一个（引用相等） | `==` | 语义就是地址 |
| 比较对象内容（值相等） | `equals` | 需类已重写 |
| 字符串内容比较 | `equals` | 不用 `==` |

> 高频错误：比较两个 `String` 的内容却用了 `==`，在非常量池场景会得到 `false`。

### 五、重写 equals 的规范

```java
public class Person {
    private String name;
    private int age;

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;           // 同一对象，快速通过
        if (o == null || getClass() != o.getClass()) return false;
        Person person = (Person) o;
        return age == person.age
            && Objects.equals(name, person.name);
    }
    // 重写了 equals，就必须重写 hashCode，见下一节
}
```

重写 `equals` 要遵守的约定（自反、对称、传递、一致、非空），此处不展开，重点记住一条：**重写 equals 必须同时重写 hashCode**。

---

### 六、衍生问题：hashCode 相等，equals 必须相等么？

**不必须。** hashCode 相等，equals 不一定相等，这就是**哈希冲突**。

```java
String a = "Aa";
String b = "BB";

System.out.println(a.hashCode());  // 2112
System.out.println(b.hashCode());  // 2112
System.out.println(a.equals(b));   // false
```

#### 正确的关系

| 关系 | 是否成立 | 原因 |
|------|---------|------|
| equals 相等 → hashCode 必须相等 | ✅ 必须 | 否则 HashMap 无法正确定位 |
| hashCode 相等 → equals 必须相等 | ❌ 不一定 | 哈希冲突，不同对象可能算出相同 hashCode |

#### 为什么 equals 相等，hashCode 必须一致？

**HashMap 的定位机制：**

```java
// HashMap.get() 的简化逻辑
public V get(Object key) {
    int hash = key.hashCode();        // 1. 用 hashCode 定位桶
    Node node = table[hash & (n-1)];  // 2. 找到桶位置

    while (node != null) {
        if (node.hash == hash &&      // 3. 先比对 hashCode
            key.equals(node.key)) {   // 4. 再用 equals 确认
            return node.value;
        }
        node = node.next;
    }
    return null;
}
```

**如果 equals 相等但 hashCode 不同：**

```java
class Person {
    String name;

    @Override
    public boolean equals(Object o) {
        return name.equals(((Person) o).name);  // 只比对 name
    }
    // 没重写 hashCode，默认用 Object 的（基于内存地址）
}

Person p1 = new Person("张三");
Person p2 = new Person("张三");

map.put(p1, 1);
map.get(p2);  // null！虽然 equals 相等，但 hashCode 不同，定位不到同一个桶
```

**结论：** equals 相等但 hashCode 不同，HashMap 会认为是两个不同的 key，导致**数据丢失**。

#### 为什么 hashCode 相等，equals 不一定相等？

**鸽笼原理（抽屉原理）：**
- `hashCode()` 返回 `int`，只有 2^32 ≈ 42 亿个可能值
- 字符串数量是无限的（理论上是无限长的）
- 必然存在不同字符串映射到相同 hashCode

**为什么不能强制 equals 相等？**
- 如果强制，hashCode 就必须是完美哈希（无冲突）
- 完美哈希需要为每个对象分配唯一 ID，内存和计算成本不可接受

#### 如何写好 hashCode？

```java
@Override
public int hashCode() {
    return Objects.hash(name, age);  // 自动分散，避免冲突
}

// 等价于
@Override
public int hashCode() {
    int result = name != null ? name.hashCode() : 0;
    result = 31 * result + age;
    return result;
}
```

**为什么用 31？**
- 31 是奇素数，减少冲突
- `31 * i = (i << 5) - i`，JVM 可优化为位移运算
- 31 不大不小，避免溢出太频繁

---

### 七、衍生问题：三元表达式与拆装箱的空指针陷阱

`==` 一旦和包装类型、拆装箱混在一起，容易踩三个坑。

#### 1. 包装类型的缓存区间

```java
Integer a = 100, b = 100;
System.out.println(a == b);   // true —— 落在缓存区间 [-128, 127]

Integer c = 200, d = 200;
System.out.println(c == d);   // false —— 超出缓存区间，各自 new 了新对象

Integer e = 200, f = 200;
System.out.println(e.equals(f));  // true —— 内容比较才是正确姿势
```

> 原因：`Integer`/`Long` 等对 `-128 ~ 127` 做了缓存（`IntegerCache`），范围内自动装箱返回同一对象。

#### 2. == 触发的自动拆箱与空指针

```java
Integer x = null;

// ① 拆箱给基本类型，直接 NPE
int n = x;                    // NullPointerException

// ② == 比较时，只要一边是基本类型，包装类型就会被拆箱
System.out.println(x == 1);   // NullPointerException！等价于 x.intValue() == 1
```

> `==` 两边一个是基本类型、一个是包装类型时，包装类型会**自动拆箱**。若包装类型为 `null`，拆箱即抛 NPE——这是日常最容易忽现的空指针。

#### 3. 三元表达式的类型统一陷阱

三元表达式 `?:` 会做**类型统一**：当两个分支一个是基本类型、一个是包装类型时，会自动拆箱到基本类型，进而引发 NPE：

```java
Integer x = null;
boolean flag = false;

// 两个分支分别是 int 和 Integer，结果为 int，Integer 分支会拆箱
int r = flag ? 1 : x;         // 运行时 NullPointerException（x 拆箱失败）

// 规避：让两个分支都保持包装类型
Integer safe = flag ? Integer.valueOf(1) : x;   // 安全
```

#### 常见空指针清单

| 写法 | 是否 NPE | 原因 |
|------|:---:|------|
| `Integer x = null; x == 1` | ✅ | 拆箱 `x.intValue()` |
| `int n = (Integer) null` | ✅ | 拆箱 |
| `flag ? 1 : nullInteger` | ✅ | 三元表达式类型统一到 int |
| `nullInteger.equals(1)` | ✅ | 对 null 调用方法 |
| `Integer a=100,b=100; a==b` | ❌ | 缓存区间，同一对象 |

---

### 八、面试考察点

1. **== 与 equals 的区别**：`==` 比地址（基本类型比值），`equals` 默认比地址、重写后比内容
2. **正确理解 hashCode 关系**：equals 相等 → hashCode 必须相等（反之不成立）
3. **知道哈希冲突**：不同对象可能有相同 hashCode（鸽笼原理）
4. **明白对 HashMap 的影响**：冲突导致链表/红黑树，性能下降
5. **知道重写规范**：重写 equals 必须同时重写 hashCode，用 `Objects.hash()` 分散
6. **拆装箱陷阱**：包装类型缓存区间 `[-128,127]`，`==` 一侧为基本类型会触发拆箱
7. **三元表达式陷阱**：`?:` 类型统一可能导致拆箱，进而空指针

---

> 一句话：**`==` 是「地址/值相等」，`equals` 是「内容相等」；hashCode 是「定位」，equals 是「确认」。定位可以冲突，确认必须唯一。**