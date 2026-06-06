# Garden Creation Patterns

本文档把 `ConardLi/garden-skills` 中适合 Article Pool 的创作方法改造成 repo-local 规则。只吸收方法，不要求安装外部仓库，也不把外部 skill 原样作为运行依赖。

## 来源与许可

- 参考仓库：`https://github.com/ConardLi/garden-skills`
- 参考 skill：`gpt-image-2`、`kb-retriever`、`web-video-presentation`、`web-design-engineer`
- 许可证：MIT。若后续复制大量原文、脚本或模板，需要在仓库中保留对应版权与许可说明。

## 本地知识检索

对应 repo-local skill：`article-research-kb`。

使用场景：

- 用户要求“结合我以前写过的文章”“从资料库找依据”“参考本地运营资料”。
- 选题需要复用历史文章、笔记、报告、截图说明或内部资料。
- 需要确认本地已经写过什么，避免重复选题或重复角度。

核心流程：

1. 先确认知识库根目录，默认 `knowledge/`，也可以使用用户指定路径。
2. 如有 `data_structure.md`，先按分层索引导航。
3. 生成 3-8 个关键词，按路径收窄后使用 `rg` 检索。
4. 对命中只读取附近片段，保存文件路径、位置、片段和支持的 claim。
5. 最多 5 轮检索；仍不足时明确记录缺口，不编造。

本地知识只能补充上下文，不替代时效性搜索和一手来源验证。

## 模式感知生图

借鉴 `gpt-image-2` 的 A/B/C 模式，但 Article Pool 默认只采用 B/C：

- **Mode B：Host-Native**。当前 Agent 有 `image_gen` 或宿主生图能力时，先渲染高质量 prompt，再调用宿主图像工具生成本地图。封面必须直接生成最终 PNG，不交给 `gen_cover.py` 后处理；正文插图可按插图流程交给 `illustration_gen.py` 上传和嵌入。
- **Mode C：Advisor**。没有生图能力时，只生成可复用 prompt 和 brief，写入运行报告，不要假装出图成功。

Article Pool 不默认启用 Garden Mode A，不读取 `ENABLE_GARDEN_IMAGEGEN`，不调用外部 Node 生图脚本。这样仓库保持自包含，且不会把 API Key、网关和付费依赖变成硬条件。

执行要求：

1. 先判断任务是封面、插图、图改、UI mockup、信息图、学术图、技术架构图还是海报。
2. 从文章主张、内容符号、品牌元素、构图、避雷词生成结构化 prompt。
3. 事实型视觉必须真实捕获；生成图只能表达概念。
4. Mode B 输出图片路径；Mode C 输出 prompt 路径与“未生成图片”的明确状态。
5. 不要把模式说明复制到读者可见正文。

## 文章转网页视频

借鉴 `web-video-presentation`，作为 `mm-video` 的可选上游，不替代现有视频解说工具。

适用场景：

- 用户想把公众号文章、口播稿或教程改造成视频号/B 站/YouTube 横屏讲解。
- 需要 16:9 网页演示，而不是静态 PPT。
- 需要先形成 `script.md` 和 `outline.md`，再决定是否制作网页演示和字幕/音频。

Article Pool 约束：

- 先从文章生成 `script.md` 和 `outline.md`，再让用户确认节奏、主题、素材和开发模式。
- `outline.md` 只规划章节、节拍、信息密度和素材，不写死动画。
- 每个 step 只承载一个口播节拍；网页录屏应避免标题页、页码、过度 UI chrome。
- 如果进入真实网页实现，再使用前端项目自己的验证；`mm-video` 只负责媒体叶子节点。

## 网页设计原则提炼

借鉴 `web-design-engineer` 的原则，只落到 Article Pool 的视觉审阅，不扩展成通用前端工作流：

- 具体品牌、产品、模型、活动必须先查证，不凭记忆写视觉事实。
- 品牌识别优先真实 logo、官方截图、产品图；不要用 CSS 轮廓或泛科技图替代。
- 视觉系统先回答叙事角色、观看距离、视觉温度、信息容量，再决定色彩与动效。
- 避免 AI 视觉俗套：紫粉蓝渐变、emoji 充图标、左边框彩卡、无意义光效、泛化科技背景。
- 缺素材时使用诚实占位或向用户确认，不伪造数据、logo、界面或截图。
