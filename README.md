# 📚 JAVA题库

JAVA 面试题与知识点合集，基于 MkDocs Material 构建，自动部署于 GitHub Pages。

## 🌐 在线访问

**👉 [https://jeakiry-k.github.io/learnEdge/](https://jeakiry-k.github.io/learnEdge/)**

> 点击上方链接直接访问已部署的文档站点，支持全文搜索、亮/暗模式切换。

## ✨ 特性

- 📄 文档式简约页面
- 🔍 全文搜索（Ctrl/⌘ + K）
- 📁 分类清晰，快速索引
- 🌗 亮/暗双模式
- 🚀 推送 `main` 分支自动部署到 GitHub Pages

## ⚙️ 为什么推送代码后网页就能访问？

本项目通过 **GitHub Pages + GitHub Actions** 实现自动部署：

1. **代码推送到 `main` 分支** 时，触发 `.github/workflows/deploy.yml` 工作流
2. GitHub Actions 虚拟机会自动安装 `mkdocs-material`，执行 `mkdocs build` 将 Markdown 编译为静态 HTML（输出到 `site/` 目录）
3. 构建产物通过 `actions/upload-pages-artifact` 上传为 Pages 构件
4. `actions/deploy-pages` 将构件发布到 GitHub Pages 服务器
5. 最终通过 `https://<用户名>.github.io/<仓库名>/` 访问

整个过程无需手动操作，每次推送都会自动重新构建和部署。

## 🧭 从仓库页面跳转到站点

在 GitHub 仓库页面有两种方式找到站点入口：

- **方式一（About 区域）**：仓库首页右侧 **About** 栏 → 点击 ⚙️ 齿轮图标 → 在 **Website** 栏填入 `https://jeakiry-k.github.io/learnEdge/` 并保存，之后 About 区域会显示该链接
- **方式二（Settings）**：点击顶部 **Settings** → 左侧 **Pages**，可看到部署状态和站点 URL
- **方式三（Actions）**：点击顶部 **Actions**，可查看每次部署的构建日志和进度

## 📂 分类

| 分类 | 内容 |
|------|------|
| JavaScript | 事件循环、闭包、原型链、ES6+、异步编程 |
| CSS | 布局、动画、BFC、居中方案 |
| HTML | 语义化、可访问性 |
| React | Hooks、状态管理、渲染优化 |
| Vue | 响应式原理、组件设计 |
| 浏览器与网络 | 事件循环、HTTP、缓存策略 |
| 算法与数据结构 | 排序、树、动态规划 |
| 工程化 | Webpack/Vite、CI/CD、测试 |
| 性能优化 | 加载性能、运行时性能 |

## 📝 新增题目

1. 在 `docs/<分类>/` 下创建 `.md` 文件
2. 在 `mkdocs.yml` 的 `nav` 中添加条目
3. 提交并推送到 `main` 分支，GitHub Actions 自动部署

```bash
git add .
git commit -m "docs: 新增 xxx 题目"
git push
```

## 🚀 本地预览

```bash
pip install mkdocs-material
mkdocs serve
# 访问 http://127.0.0.1:8000
```

## 📄 License

MIT
