---
name: article-research-kb
description: Use when Article Pool needs to retrieve evidence from a local knowledge base, historical articles, notes, reports, docs, PDFs, or spreadsheets before drafting or reviewing content.
---

# article-research-kb

Article Pool 的本地知识检索子 skill。它只服务文章创作：把本地资料变成可溯源的 `evidence_artifacts`，不替代外部时效性搜索。

## 使用边界

- 优先用于：历史文章复用、运营资料、私有笔记、产品资料、选题库、报告、截图说明、长文档。
- 默认知识库根目录是 `knowledge/`；若不存在，先检查 `文章/`、`docs/`、`reports/` 是否与任务相关，再向用户确认路径。
- 不使用网络搜索；网络资料由 `mm-article` 的 `research.sources` 和 `research.timeliness` 处理。
- 不整文件吞读大文件；先索引、关键词、局部读取，再综合。

## 工作流

1. 提取用户问题中的主题、时间、平台、文章类型和需要回答的问题。
2. 找知识库入口：优先用户指定路径，其次 `knowledge/`，再按任务检查 `文章/`、`docs/`、`reports/`。
3. 如果存在 `data_structure.md`，先读它；逐层沿最相关目录钻取。
4. 从问题中生成 3-8 个关键词，包含中文、英文缩写、同义词和上下位词。
5. 最多做 5 轮检索：每轮只搜最相关路径，读取命中附近片段，记录文件、位置和支持的说法。
6. PDF、Excel、长 HTML 等文件先转换或局部抽取，再检索；不要直接整文件读入。
7. 输出 `local_kb_evidence_artifacts`，每条至少包含 `path_or_url`、`position`、`claim_supported`、`confidence`、`notes`。

## 输出格式

```json
{
  "local_kb_evidence_artifacts": [
    {
      "path_or_url": "docs/example.md",
      "position": "heading or line nearby",
      "claim_supported": "这条资料能支持的具体说法",
      "confidence": "high|medium|low",
      "notes": "限制、上下文或需要外部验证的地方"
    }
  ],
  "missing_information": ["没有在本地资料中找到的关键问题"],
  "searched_paths": ["knowledge", "文章/2026年05月"]
}
```

## 质量门禁

- 每个进入正文的本地事实都要有路径和位置。
- 本地资料只能证明“历史记录/内部材料这样写过”，不能替代官方来源和最新事实。
- 如果 5 轮后仍没有足够证据，明确写 `missing_information`，不要编造。
- 读者可见正文里不能出现“知识库检索”“data_structure.md”“检索轮次”等生产痕迹。
