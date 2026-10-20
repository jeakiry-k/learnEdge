# AGENT.md — learnEdge 项目规范

JAVA 面试题与知识点题库，mkdocs-material 静态站，由 CI 构建发布。改动前先读本文件。

## 目录结构

| 路径 | 作用 |
|---|---|
| `docs/<分类>/<slug>.md` | 文章本体 |
| `docs/category/<分类>/index.md` | 分类页（**手写列表**，不会自动生成） |
| `docs/index.md` | 首页，主体是「更新日志」列表 |
| `docs/assets/diagrams/<slug>/*.svg` | 文章配图 |
| `mkdocs.yml` | 站点配置与 nav |
| `docs/overrides/main.html` | 主题覆写（`.question-tags`、`.diagram-card` 等样式） |

分类目录：`java-basic` / `redis` / `mysql` / `engineering` / `browser-network`
分类中文名：Java基础 / Redis / MySQL / 工程化 / 浏览器与网络

## 强制规范

### 1. 所有文章列表一律按时间倒序（新的在前）

适用：

- 首页 `docs/index.md` 的「更新日志」`home-list`
- 各 `docs/category/<分类>/index.md` 的 `category-list`

排序依据 = 文章 frontmatter 的 `date` 字段，新的排前面；**日期相同时保持 `mkdocs.yml` nav 中的相对顺序**。

新增或修改文章后，必须复核所在列表是否仍有序、篇数计数是否正确。

### 2. 新增一篇文章要同步四处，缺一不可

1. **文章本体** `docs/<分类>/<slug>.md`
   frontmatter（`date` / `category` / `title` / `tags`）+ `#` 标题 + `.question-tags` div + `>` 题目描述（把核心追问提炼成一段）+ `### 一、…` 分节正文。
2. **`mkdocs.yml`**：nav → 题目列表 加一行 `- 标题: <分类>/<slug>.md`
3. **`docs/category/<分类>/index.md`**：加 `<li>` 条目（href 写 `../../<分类>/<slug>`，**不带 `.md`**），并把 `共 N 篇` +1
4. **首页 `docs/index.md`**：「更新日志」加条目（含 `<span class="li-date">日期</span>`），`共 N 篇` +1，且**插到时间倒序的正确位置**

### 3. 配图用「手绘风 SVG」，不要 mermaid 占位

- 默认就画手绘 / flat illustration 风格 SVG：圆角盒、浅色填充 + 同色系描边、虚线标注瓶颈、底部一句灰色总结句。
- 存放 `docs/assets/diagrams/<slug>/*.svg`，文章里用
  `<div class="diagram-card"><img src="../../assets/diagrams/<slug>/xxx.svg"></div>`
- **路径必须是 `../../assets/...`**：Material 开了 `use_directory_urls`，`docs/<分类>/<slug>.md` 会渲染成两层目录，写 `../assets/` 会 404。
- **根元素必须带 `xmlns="http://www.w3.org/2000/svg"`**，否则 Chrome 把它当 XML 文档、不渲染成图。
- 复用的原版 SVG 要在首个 `<svg>` 后注入 `th` / `ts` 字体 `<style>`，否则字号退化成 16px。
- 详细流程见 skill：`mkdocs-article-diagram-upgrade`。

### 4. 构建与验证

- 本机**没有 mkdocs**，站点由 CI 构建，不要指望本地 `mkdocs build`。
- 验证方式：让用户跑 `mkdocs serve`；用 `curl` 探测页面与资源状态码；SVG 用 `xml.etree.ElementTree` 批量 parse 校验。
- 不要用 cairosvg 渲染验证中文 —— 本机缺中文字体，会渲成豆腐块导致误判。

### 5. 编辑注意

- 改文章前先 Read 最新内容再 Edit（曾出现段落被外部回滚、Edit 报成功但内容消失的情况）。
- 改完必须 grep 复核：mermaid 是否已清零、`img src` 条数是否正确、列表顺序与计数是否正确。
