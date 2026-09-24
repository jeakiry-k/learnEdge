# 闭包（Closure）

## 问题

> 什么是闭包？请举例说明闭包的应用场景和潜在问题。

## 答案

**闭包**是指一个函数能够访问其外部函数作用域中的变量，即使外部函数已经执行完毕。

### 基本示例

```javascript
function createCounter() {
  let count = 0;                    // 外部变量
  return function () {
    return ++count;                 // 内部函数引用外部变量 → 闭包
  };
}

const counter = createCounter();
counter(); // 1
counter(); // 2
counter(); // 3
```

### 应用场景

| 场景 | 说明 |
|------|------|
| **数据私有化** | 模拟私有变量，外部无法直接访问 |
| **函数柯里化** | 固定部分参数，延迟执行 |
| **防抖/节流** | 保存定时器引用 |
| **模块模式** | IIFE 封装模块 |

### 潜在问题

- **内存泄漏**：闭包引用的变量不会被 GC 回收，需注意及时释放
- **变量共享**：循环中使用 `var` + 闭包会共享同一个变量

```javascript
// 经典问题：循环中的闭包
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 0);  // 输出 3, 3, 3
}

// 解决方案：使用 let
for (let i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 0);  // 输出 0, 1, 2
}
```
