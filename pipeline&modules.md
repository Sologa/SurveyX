# SurveyX完整Pipeline架构

## 核心创新点总结

1. **多层次信息提取**: 通过4种专门的AttributeTree模板处理不同类型论文
2. **智能大纲生成**: 从一级到二级大纲的完整生成和优化流程
3. **迭代内容填充**: 支持大规模文献信息的逐步整合
4. **多维度精修**: RAG重写、章节重写、图表检索三位一体
5. **自动化图表生成**: 基于文献内容的智能图表构建
6. **全面质量控制**: 从预处理到编译的完整质量保障体系

## 一、预处理阶段（Preprocessing Stage）

### 1. PaperRecaller - 文献召回模块
**核心功能**: 基于关键词的迭代式文献检索
**相关Prompts**:
- `PaperRecall_gen_key_word.md`: 基于聚类分析生成新的检索关键词
- `generate_keyword.md`: 关键词生成策略
- `generate_topic.md`: 主题生成

**详细用途**:
- 从Google Scholar和arXiv进行多轮检索
- 使用K-means聚类分析文献语义相似度
- 根据现有关键词的语义分布选择最优新关键词
- 实现文献池的动态扩充，直到达到预设规模

### 2. DataCleaner - 数据清洗模块
**用途**: 确保文献数据质量和一致性
- 过滤无效字段、空内容和重复条目
- 标准化文献格式和元数据
- 为后续处理准备干净的数据集

### 3. PaperFilter - 文献过滤模块
**相关Prompts**:
- `judge_relevance.md`: LLM进行语义相关性判断
- `paper_type_classification.md`: 论文类型自动分类

**详细用途**:
- **粗粒度过滤**: 基于嵌入相似度计算，Top-K选择
- **细粒度过滤**: LLM语义判别，生成相关性评分
- 支持多种论文类型识别（method/benchmark/survey/theory）

### 4. AttributeTree预处理模块 - 结构化信息提取
**核心功能**: 将全文转换为结构化属性树
**相关Prompts**:
- `attri_tree_for_survey.md`: 综述类论文属性提取
- `attri_tree_for_method.md`: 方法类论文属性提取
- `attri_tree_for_benchmark.md`: 基准类论文属性提取
- `attri_tree_for_theory.md`: 理论类论文属性提取

**详细用途**:
- **Survey论文提取**: background/problem/architecture/conclusion/discussion/gaps
- **Method论文提取**: background/problem/idea/method/experiments/conclusion/discussion
- **Benchmark论文提取**: background/problem/idea/dataset/metrics/experiments/conclusion/discussion
- **Theory论文提取**: background/problem/idea/theory/experiments/conclusion/discussion

## 二、大纲生成阶段（Outline Generation Stage）

### 5. OutlinesGenerator - 大纲生成模块
**相关Prompts**:
- `write_primary_outline.md`: 生成一级大纲结构
- `mout_paper_on_plain_outline.md`: 将文献挂载到一级大纲
- `write_secondary_outline.md`: 生成二级大纲详情
- `deduplicate_subsection.md`: 二级大纲去重
- `reorganize_outline.md`: 大纲重组优化
- `create_sections.md`, `generate_outlines.md`, `merge_outline.md`, `score_outlines.md`: 辅助大纲生成

**详细用途**:
- **一级大纲生成**: 基于主题和文献摘要生成主要章节结构
- **文献挂载**: 将属性树信息映射到大纲的相应章节
- **二级大纲生成**: 基于挂载信息生成详细的子章节
- **去重重组**: 消除冗余，优化章节逻辑顺序

## 三、内容生成阶段（Content Generation Stage）

### 6. ContentGenerator - 内容生成模块
**相关Prompts**:
- `fulfill_content.md`: 单次内容填充
- `fulfill_content_iteratively.md`: 迭代式内容填充
- `mount_tree_on_outlines.md`: 属性树与大纲映射
- `write_abstract.md`: 摘要生成
- `write_section_words.md`: 章节连接词生成

**详细用途**:
- **单次填充**: 一次性生成完整章节内容
- **迭代填充**: 分批处理大量文献信息，逐步完善内容
- **属性树映射**: 将结构化信息精确映射到大纲位置
- **摘要生成**: 基于完整内容生成学术摘要（<250词）
- **章节连接**: 生成章节间的过渡性文字

## 四、后处理精修阶段（Post-refinement Stage）

### 7. PostRefiner - 后处理协调模块
**用途**: 协调多个精修子模块的执行顺序

#### 7.1 RagRefiner - RAG重写精修模块
**相关Prompts**:
- `rag_rewrite_sentence.md`: 基于检索结果重写句子
- `retrieve_paper_segments.md`: 检索相关论文片段

**详细用途**:
- 从属性森林中检索相关证据
- 重写句子以补充准确引用
- 剔除不相关引用，增强内容准确性
- 基于上下文进行内容润色

#### 7.2 FigRetrieveRefiner - 图表检索精修模块
**相关Prompts**:
- `describe_subsection_topic.md`: 章节主题描述
- `filter_figs.md`: 图表相关性过滤
- `generate_fig_caption.md`: 图表标题生成
- `generate_fig_title_desc.md`: 图表标题和描述生成
- `write_paragraphs_to_introduce_figs.md`: 图表介绍段落生成

**详细用途**:
- 从原始文献中检索相关图表
- 生成图表标题、描述和说明文字
- 将高质量图表引入到综述中

#### 7.3 SectionRewriter - 章节重写模块
**相关Prompts**:
- `compress_sections.md`: 章节压缩
- `introduction_compression.md`: 引言压缩
- `iterative_compression.md`: 迭代压缩
- `rewrite_conclusion.md`: 结论重写
- `rewrite_section_with_compressed_context.md`: 基于压缩上下文重写章节

**详细用途**:
- **章节压缩**: 减少冗余，提高内容密度
- **引言压缩**: 优化引言部分的简洁性
- **结论重写**: 基于引言内容重写结论，确保逻辑连贯
- **迭代重写**: 基于前序章节的压缩上下文重写后续章节

#### 7.4 LatexHandler系列 - LaTeX处理模块
**相关Prompts** (latex_table_builder/):
- `Attribute_Extract.txt`: 属性提取模板
- `Attribute_fill.txt`: 属性填充模板
- `Attribute_Summary.txt`: 属性汇总模板
- `Benchmark.txt`: 基准相关表格
- `Comparison.txt`: 比较表格
- `Content_rewrite.txt`: 内容重写
- `Extract_Prompt.txt`: 提取提示
- `find_benchmark_section.md`: 查找基准章节
- `find_method_section.md`: 查找方法章节
- `Table_description.txt`: 表格描述

**详细用途**:
- **LatexFigureBuilder**: 基于文献信息自动生成图表
- **LatexTableBuilder**: 生成汇总表、比较表、列表表等
- **LatexTextBuilder**: 处理文本格式转换

## 五、编译生成阶段（Compilation Stage）

### 8. LatexGenerator - LaTeX生成模块
**用途**:
- 将所有组件整合成完整的LaTeX文档
- 编译生成最终PDF文件
- 添加水印和格式处理

## 六、支持模块（Supporting Modules）

### 9. ChatAgent - 对话代理模块
**用途**: 封装与大语言模型的交互接口
- 支持批量对话和单次对话
- 管理token使用量和API调用

### 10. EmbedAgent - 嵌入代理模块
**用途**: 处理文本嵌入和向量量化
- 将文献内容转换为向量表示
- 支持相似度计算和检索

### 11. LlamaIndexWrapper - RAG索引模块
**用途**: 构建和维护向量索引
- 创建向量索引用于高效语义检索
- 支持Top-K检索和相似度过滤

### 12. Monitor系列 - 监控模块
**用途**:
- **TimeMonitor**: 监控各阶段执行时间
- **TokenMonitor**: 监控API调用token使用量

## 关于Gaps（研究空白）的专门处理

### Gaps处理流程
**1. 信息提取阶段**:
- 在`attri_tree_for_survey.md`中专门提取"gaps"字段：
  ```
  "Gaps": Identify the gaps in current research. What questions remain unanswered or what areas need further exploration?
  ```
- 在`attri_tree_for_method.md`、`attri_tree_for_benchmark.md`、`attri_tree_for_theory.md`中通过"limitation"和"future work"字段间接提取gaps信息

**2. 大纲生成阶段**:
- gaps信息作为hints被用于生成二级大纲
- 确保综述能够覆盖研究空白讨论

**3. 内容生成阶段**:
- gaps信息会被整合到相关章节中
- 进行批判性分析（critical analysis）
- 在Discussion部分突出显示研究空白

**4. 后处理精修阶段**:
- 通过RAG重写确保gaps讨论的准确性
- 通过章节重写优化gaps分析的表达

### Gaps在JSON结构中的存储
```json
{
  "discussion": {
    "limitation": ["局限性1", "局限性2"],
    "gaps": ["研究空白1", "研究空白2"],
    "future_work": ["未来工作方向1", "未来工作方向2"]
  }
}
```

这个架构确保了SurveyX能够生成高质量、结构完整、内容丰富的学术综述，同时保持了高度的自动化和可扩展性。
