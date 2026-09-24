# CSS 居中方案

## 问题

> 请列举你知道的 CSS 水平垂直居中方案，并说明各自的适用场景。

## 答案

### 方案一：Flex（推荐）

```css
.parent {
  display: flex;
  justify-content: center;
  align-items: center;
}
```

**适用**：现代浏览器，最简洁。

---

### 方案二：Grid

```css
.parent {
  display: grid;
  place-items: center;
}
```

**适用**：一行搞定，浏览器支持 Grid 即可。

---

### 方案三：绝对定位 + transform

```css
.child {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
```

**适用**：需要绝对定位的场景，兼容性好。

---

### 方案四：绝对定位 + margin auto

```css
.child {
  position: absolute;
  top: 0; right: 0; bottom: 0; left: 0;
  margin: auto;
  width: 100px;   /* 需有固定宽高 */
  height: 100px;
}
```

**适用**：已知宽高的元素。

---

### 对比总结

| 方案 | 代码量 | 需固定宽高 | 兼容性 |
|------|--------|-----------|--------|
| Flex | 少 | 否 | IE10+ |
| Grid | 最少 | 否 | 现代浏览器 |
| transform | 中 | 否 | IE9+ |
| margin auto | 中 | 是 | IE6+ |
