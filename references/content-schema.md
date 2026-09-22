# 读书卡内容模型

渲染器读取一个 UTF-8 JSON 文件。卡片数量动态变化，不设置固定页数。

## 顶层结构

```json
{
  "book": {
    "title": "必填，书名",
    "author": "可选，作者",
    "category": "可选，类型或主题",
    "subtitle": "可选，一句话定位",
    "cover_kicker": "可选，封面顶部短句",
    "cover_note": "可选，封面说明",
    "cover_english": "可选，英文名",
    "cover_color": "可选，十六进制颜色",
    "cover_image": "可选，本地图片路径或 data URI",
    "overview": "必填，第一页的总述",
    "cover_points": ["必填，阅读收获一", "必填，阅读收获二", "必填，阅读收获三"]
  },
  "pages": []
}
```

渲染器自动生成第 1 页封面总览。`pages` 只放第 2 页以后的内容，不得再出现书名、封面或作者。

`book.overview` 应是一句能吸引读者继续阅读的核心主张，而不是普通图书简介。`book.cover_points` 必须恰好包含 3 个短语，每项建议 6–12 个汉字，分别概括理解、方法或行动层面的阅读收获。

## 通用字段

每个内容页至少包含：

```json
{
  "type": "statement",
  "section": "核心观点",
  "title": "这一页只讲一个意思"
}
```

数据中不要添加 `evidence`、`sources` 或 `boundary`。成品不显示证据标签、章节出处、网址或来源页。

## 页面类型

### statement：观点或逻辑页

```json
{
  "type": "statement",
  "section": "逻辑剖析",
  "title": "懂了却做不到，通常不是因为不够努力",
  "body": ["第一段解释。", "第二段解释。"],
  "highlight": "需要记住的一句话"
}
```

### list：场景、误区、反常识或凝结页

```json
{
  "type": "list",
  "section": "现实问题",
  "title": "这套方法适合什么时候用",
  "items": [
    {"title": "场景一", "body": "具体说明"}
  ]
}
```

每页建议 2–4 项。超过时拆页。

### steps：模型、行动或复盘页

```json
{
  "type": "steps",
  "section": "行动转化",
  "title": "今天开始的三个动作",
  "items": [
    {"title": "10 分钟完成什么", "body": "动作和完成标志"}
  ]
}
```

每页建议 2–3 步。动作必须包含时间、具体内容和可验证完成标志。

### quote：短引文或概念页

```json
{
  "type": "quote",
  "section": "短引文",
  "title": "概念主题",
  "quote": "已核实的短句",
  "interpretation": "一句通俗解读",
  "scene": "适用场景"
}
```

逐字引文只有在实际核对过时才使用 `quote`。没有可靠原句时，改用 `statement.highlight` 写成不带引号的核心表达。

## 内容到页面的映射

- 书籍定位：1–2 个 `statement` 或 `list` 页。
- 现实问题：多个 `list` 页。
- 每个核心知识单元：至少一个 `statement`，必要时追加误区或场景 `list`。
- 逻辑剖析：`statement`。
- 模型工具：`steps`。
- 场景迁移与行动：`list` 或 `steps`。
- 反常识：每页 1–2 条，避免把正文压得太小。
- 短引文：`quote`，仅在确有可靠原句时使用。
- 终极凝结：接近结尾的 `statement` 或 `list`。
- 最后一页：内容回顾、行动计划或方法边界，不生成来源页。

## 单屏容量

- 标题尽量不超过 22 个汉字。
- `statement.body` 最多 3 段，每段建议不超过 70 个汉字。
- `list` 最多 4 项，`steps` 最多 3 项。
- 内容略超首屏时可以向下滚动；主题过多或滚动明显过长时拆页，不缩小到难以阅读。
