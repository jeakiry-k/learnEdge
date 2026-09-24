---
date: "2026-09-24"
category: "JavaScript"
title: "事件循环（Event Loop）"
---

# 事件循环（Event Loop）

## 问题

> 请解释 JavaScript 的事件循环机制，宏任务和微任务有什么区别？

## 答案

JavaScript 是单线程语言，通过**事件循环**机制实现异步非阻塞。

### 核心概念

| 概念 | 说明 |
|------|------|
| **调用栈** | 执行同步代码的栈结构 |
| **宏任务队列** | `setTimeout`、`setInterval`、`I/O`、UI 渲染等 |
| **微任务队列** | `Promise.then`、`MutationObserver`、`queueMicrotask` |

### 执行顺序

1. 执行同步代码（调用栈）
2. 清空**微任务队列**
3. 执行一个**宏任务**
4. 回到步骤 2，循环往复

### 示例

```javascript
console.log('1');                          // 同步

setTimeout(() => {
  console.log('2');                        // 宏任务
}, 0);

Promise.resolve().then(() => {
  console.log('3');                        // 微任务
});

console.log('4');                          // 同步

// 输出顺序: 1 → 4 → 3 → 2
```

### 关键点

- 每次宏任务执行后，会清空所有微任务，再执行下一个宏任务
- 微任务优先级高于宏任务
- `async/await` 本质是 Promise，`await` 后的代码相当于 `.then()`
