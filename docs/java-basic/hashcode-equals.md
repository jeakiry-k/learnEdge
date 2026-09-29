---
title: hashCode 相等，equals 必须相等么？
description: hashCode 和 equals 的关系、哈希冲突的影响，以及面试考察的核心要点。
date: 2026-09-29
category: Java基础
tags: [Java, hashCode, equals, 哈希冲突]
---

## hashCode 相等，equals 必须相等么？

> hashCode 相等，equals 必须相等么？会带来什么问题？为什么？

### 直接回答

**不必须。** hashCode 相等，equals 不一定相等，这就是**哈希冲突**。

```java
String a = "Aa";
String b = "BB";

System.out.println(a.hashCode());  // 2112
System.out.println(b.hashCode());  // 2112
System.out.println(a.equals(b));   // false
```

---

### 正确的关系

| 关系 | 是否成立 | 原因 |
|------|---------|------|
| equals 相等 → hashCode 必须相等 | ✅ 必须 | 否则 HashMap 无法正确定位 |
| hashCode 相等 → equals 必须相等 | ❌ 不一定 | 哈希冲突，不同对象可能算出相同 hashCode |

---

### 为什么 equals 相等，hashCode 必须一致？

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

---

### 为什么 hashCode 相等，equals 不一定相等？

**鸽笼原理（抽屉原理）：**
- `hashCode()` 返回 `int`，只有 2^32 ≈ 42 亿个可能值
- 字符串数量是无限的（理论上是无限长的）
- 必然存在不同字符串映射到相同 hashCode

**为什么不能强制 equals 相等？**
- 如果强制，hashCode 就必须是完美哈希（无冲突）
- 完美哈希需要为每个对象分配唯一 ID，内存和计算成本不可接受

---

### 哈希冲突会带来什么问题？

**HashMap 中的问题：**

```java
Map<String, Integer> map = new HashMap<>();
map.put("Aa", 1);
map.put("BB", 2);  // 和 "Aa" 哈希冲突，存入同一个桶

// 查找时
map.get("Aa");  // 先定位桶，再遍历链表/红黑树，用 equals 比对
```

**问题本质：**
- 哈希冲突导致**链表变长**或**红黑树退化**
- 查找从 O(1) 退化为 O(N) 或 O(logN)
- 极端情况（恶意构造冲突）导致 HashMap 性能骤降

---

### 如何写好 hashCode？

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

### 面试考察点

1. **正确理解关系**：equals 相等 → hashCode 必须相等（反之不成立）
2. **知道哈希冲突**：不同对象可能有相同 hashCode
3. **明白对 HashMap 的影响**：冲突导致链表/红黑树，性能下降
4. **知道为什么允许冲突**：鸽笼原理，完美哈希不现实
5. **知道如何避免**：重写 hashCode 时尽量分散（用 Objects.hash()）

---

> 一句话：**hashCode 是「定位」，equals 是「确认」。定位可以冲突，确认必须唯一。**
