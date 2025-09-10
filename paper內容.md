
# SurveyX：基于大语言模型的学术综述自动化（中文完整版）

> 说明：本文为 **SurveyX: Academic Survey Automation via Large Language Models** 的中文译本与整理，尽量保持原文结构、段落与公式。图与表无法直接嵌入，已保留其标题与说明，并在正文中以“图”“表”引用。若需把图表也转成可执行脚本或生成可视化，我可以继续补充相应的生成脚本与示例。  
> 来源：KDD 2025（Toronto, Canada），作者与单位等信息见下。fileciteturn4file0

---

## 标题
**SurveyX：通过大语言模型实现学术综述自动化**

## 作者与单位
- **Xun Liang∗**（中国人民大学，Email: xliang@ruc.edu.cn）  
- **Jiawei Yang∗**（中国人民大学，Email: j1aweiyang@ruc.edu.cn）  
- **Yezhaohui Wang∗**（东北大学，Email: yezhaohuiwang@gmail.com）  
- **Chen Tang∗**（先进算法研究院，上海，Email: tangc@iaar.ac.cn）  
- **Zifan Zheng**（悉尼大学，Email: zzhe0348@uni.sydney.edu.au）  
- **Shichao Song**（中国人民大学，Email: songshichao@ruc.edu.cn）  
- **Zehao Lin**（先进算法研究院，上海，Email: linzh@iaar.ac.cn）  
- **Yebin Yang**（先进算法研究院，上海，Email: yangyb@iaar.ac.cn）  
- **Simin Niu**（中国人民大学，Email: niusimin@ruc.edu.cn）  
- **Hanyu Wang**（中国人民大学，Email: hy.wang@ruc.edu.cn）  
- **Bo Tang**（先进算法研究院，上海，Email: tangb@iaar.ac.cn）  
- **Feiyu Xiong**（先进算法研究院，上海，Email: xiongfy@iaar.ac.cn）  
- **Keming Mao**（东北大学，Email: maokm@mail.neu.edu.cn）  
- **Zhiyu Li†**（先进算法研究院，上海，Email: lizy@iaar.ac.cn）  
\* 共同一作；† 通讯作者。

> 会议：**KDD 2025**（2025年8月，加拿大多伦多）  
> 许可与版权：遵循ACM相关许可条款（原文保留）。  
> 项目页：<http://www.surveyx.cn>

---

## 摘要
大语言模型（LLMs）展现出卓越的理解能力与庞大的知识储备，提示其可作为**自动化综述写作**的高效工具。然而，现有自动综述研究仍受限于：**上下文窗口有限**、**缺乏深入内容讨论**以及**缺少系统化评测框架**。受人类写作流程启发，本文提出 **SurveyX** ——一种将综述撰写拆分为“**准备阶段**”与“**生成阶段**”的高效有序系统。通过**引入在线参考文献检索**、**基于 AttributeTree 的预处理方法**以及**RAG驱动的重写润色**流程，SurveyX 显著提升了综述写作成效。实验表明，SurveyX 在**内容质量**（提升 0.259）与**引用质量**（提升 1.76）上均优于已有自动综述系统，并在多项评价维度上逼近人类专家水平。示例综述见项目网站。

**关键词**：自动综述生成、文献综合、LLM、NLP

---

## 1 引言
近年计算机科学诸多方向快速发展。据统计，**arXiv.org** 日均接收约一千篇新稿。**图1** 显示：近三年（2022–2024），arXiv 年发文量由 **186,339** 增至 **285,174**（增长逾50%），预计 **2025** 年将达 **约368,292**。文献**指数式增长**使研究者从零起步理解某一子领域的技术演进与发展脉络愈发困难。**综述**在梳理研究现状与历史演化方面至关重要，但**人工撰写成本**持续攀升，覆盖性与质量承压。在“**信息过载**”背景下，构建**高效的自动化综述生成系统**势在必行。

LLMs 以大规模语料训练，具备**流畅且逻辑连贯**的文本生成能力。尽管如此，将 LLM 用于自动综述仍面临两类挑战：

### （1）技术挑战
- **内置知识时效性不足**：LLM 主要依赖内部知识生成文本，而高质量综述需要**最新且准确**的文献支撑；模型内知识**可能过时或给出错误引用**，影响学术严谨性与可信度。  
- **上下文窗口受限**：主流 LLM（如 GPT‑4o 128K、Claude 3.5 200K）上下文有限；而完整综述通常需**数百篇**参考文献（单篇**约10K tokens**），远超窗口容量，难以直接“装下”全部资料。

### （2）应用挑战
- **缺乏高效、及时的**大规模**在线检索工具**，难以迅速获取**最新且高度相关**的参考文献；  
- **评测框架缺失**：与传统NLG不同，综述质量**缺少统一指标与标准基准**，妨碍自动生成综述的**有效质量评估**与大规模应用。

现有工作虽提出部分方案，但仍存在：  
（i）**检索仅离线，时效不足**；（ii）**预处理信息利用不充分**（仅用标题与摘要，忽视正文关键信息）；（iii）**表达形式单一**（仅文本，无图表，影响可读性）等问题。

**SurveyX** 为此给出系统性改进：将流程划分为**准备阶段**与**生成阶段**。准备阶段：基于主题进行**在线/离线混合检索**与**两步过滤**；提出**AttributeTree** 以**高密度**提取文献要点，并构建**检索材料库**（供 RAG 使用）。生成阶段：据材料**生成大纲与正文**，并通过**表格/图形**增强展现；此外还**扩展评测框架**以覆盖更多维度。

**贡献汇总**：
1. 提出**高效文献检索算法**，通过**关键词扩展**扩大召回，并以**两步过滤**保留高相关高质量文献；  
2. 设计**AttributeTree** 预处理，高效抽取文献关键信息，**提升信息密度**并**优化上下文窗口利用**；  
3. 提出**大纲优化（Outline Optimization）**方法：先生成提示（hints）再“**分而治之、重组去冗**”，得到**逻辑更严谨、结构更清晰**的大纲；  
4. 将结果表达由**纯文本**扩展到**图与表**，增强可读性；  
5. **扩展评测框架**，新增指标用于评估**生成综述质量**与**检索文献相关性**；实验表明 SurveyX 在多项指标上**优于现有方法**，与**人类专家**表现**接近**。

> **图1**（原文）：2010–2025年 arXiv 年度论文提交量（2025为预测，约为2010年的5倍）。

---

## 2 相关工作
### 长文生成
LLM 在传统NLG任务表现突出，但**长文**的**结构化**、**一致性**与**逻辑性**仍具挑战。已有研究引入**规划**策略：先产出**领域关键词**，再**多阶段细化**为段落；或通过**辅助训练任务**赋予模型**规划与组织**能力。另一方向聚焦于**特定体裁**（如百科、综述、评论）。例如 STORM 通过**发现多视角、模拟专家对话、信息组织**来生成条目。**AutoSurvey** 将综述流程拆为**检索**→**大纲**→**并行小节写作**→**整合与评测**。相较之下，SurveyX 在**检索场景、预处理、表现形式**等方面进一步优化。

### RAG（检索增强生成）
RAG 使 LLM 能访问**外部知识**，在需要**时效性/领域性**信息的任务（问答、对话、推理等）中尤为有效。长文生成同样受益于RAG。不同于直接以**原文全文**作为检索源，SurveyX 将其**转换为属性树**，显著提升**检索效率**与**上下文利用率**。

---

## 3 方法
SurveyX 包含两个阶段：**准备阶段**（3.1）与**生成阶段**（3.2）。准备阶段**收集并预处理**参考文献，构建用于 RAG 的**材料库**；生成阶段则据此**生成大纲与正文**，并进行**后期精修**。**图2** 展示了总览流程。

### 3.1 准备阶段
#### 3.1.1 参考文献获取
为缓解缺乏高效“海量高相关”文献获取工具的问题，SurveyX 自研了**参考文献获取模块**：  
- **数据源**：  
  - **离线**：来自 arXiv 的 **2,632,189** 篇可用论文（每日更新）；  
  - **在线**：基于 **Google Scholar** 的自研爬虫系统。  
  离线源**快速**、在线源**及时**，二者结合兼顾**效率**与**时效**。
- **检索算法**：分两步  
  1) **召回（recall）**：尽可能不漏掉相关文献；  
  2) **过滤（filter）**：尽可能去除不相关文献。  

为实现（1），提出**关键词扩展算法**（Algorithm 1）。从初始关键词集合 \(K_0\) 出发，基于新增关键词检索得到文献集合 \(Doc\)，对其摘要进行**语义聚类**并为各聚类**提取关键词** \(K_c\)，再与已有关键词池 \(K_{pool}\) 与主题 \(T\) 做**语义距离**比较，选取最优关键词 \(k^\*\) 加入池中；循环直至 \(Doc\) 数量达阈值 \(\theta=1000\)。

> **Algorithm 1：关键词扩展算法（伪代码）**  
> 输入：初始关键词集合 \(K_0\)，主题 \(T\)  
> 输出：检索到的文献 \(Doc\)  
> 1. \(K_{pool}\leftarrow K_0\)  
> 2. **While** \(|Doc|<\theta\)**:**  
>  a) 用新加入的关键词检索并累加到 \(Doc\)；  
>  b) 以 \(n+1\) 个类对 \(Doc\) 摘要聚类并提取关键词 \(K_c\)；  
>  c) 计算 \(K_c\) 与 \(K_{pool}, T\) 的语义距离；  
>  d) 选择最优 \(k^\*\) 并加入 \(K_{pool}\)；  
> 3. 返回 \(Doc\)。

> **最优候选词选择**  
> 令排序函数为 \(\mathrm{rank}(\cdot)\)，向量表示器为 \(E(\cdot)\)。  
> 目标：
> \[
> k^\*=\arg\min_{k_c\in K_C}\left(R_1(k_c)+R_2(k_c)\right)
> \]
> 其中  
> \[
> R_1(k_c)=\mathrm{rank}_{K_c}\left(\frac{1}{|K_{pool}|}\sum_{k_e\in K_{pool}}\cos\_sim(E(k_c),E(k_e))\right)
> \]
> \[
> R_2(k_c)=\mathrm{rank}_{K_c}\left(-\max\_{k_e\in K_{pool}}\cos\_sim(E(k_c),E(k_e))\right)
> \]

为实现（2），提出**两步过滤**：  
- **粗粒度**：用**嵌入模型**计算**主题与文献摘要**的语义相关度，取**Top‑K**；  
- **细粒度**：用 **LLM** 进行**更精细**的语义判别，进一步剔除不相关文献。

#### 3.1.2 参考文献预处理：AttributeTree
直接把**全文**喂给 LLM **低效**且**窗口利用率差**。受人类作者在写综述前**整理材料**的做法启发，SurveyX 设计 **AttributeTree**：  
- 为不同**文献类型**预先设计不同的**属性树模板**；  
- 以模板**高效抽取关键信息**；  
- 汇总所有文献的属性树形成**属性森林（Attribute Forest）**，作为后续**RAG检索材料库**。  
该方法显著提升**信息密度**与**上下文窗口利用效率**，为**高质量写作**奠定基础。  
> 附录B给出了属性树模板示例。

### 3.2 生成阶段
该阶段分为三步：**大纲生成**、**正文生成**与**后期精修**。

#### 3.2.1 大纲生成：Outline Optimization
**大纲质量**决定综述的**结构与逻辑**。初步实验显示：  
- **一级大纲**：仅用 LLM **内部知识**即可达“人类水平”；  
- **二级大纲**：难度更高，需结合**属性树**提供的**提示（hints）**。  

**两步法**（见**图3**）：  
1. **基于属性树生成 hints**，引导二级大纲生成；  
2. **“分离再重组”去冗**：将所有二级大纲从一级大纲中**抽离**（只保留标题），由 LLM **去重、重排**，再**回填**到一级大纲，得到**结构更清晰**的最终大纲。

#### 3.2.2 正文生成
延续大纲阶段的**hint 驱动**思路：由**二级大纲**产出**写作提示**，LLM 按**小节（subsection）**逐段生成正文，书写当前小节时可**查看已写内容**以保证**一致性**。

#### 3.2.3 后期精修
目标：  
1) **质量提升**：改进**引用准确性**、**文本流畅性**与**表述一致性**；  
2) **多模态增强**：加入**图表**提升表达力。  

对应两个模块：  
- **RAG重写模块**：以初稿**段落**为查询，从**属性森林**检索材料，构造提示让 LLM **重写段落**：**剔除不相关引用、补充高相关引用**，并基于上下文**润色**。  
- **图表生成模块**：受 **Napkin** 启发，设计**信息抽取模板** ↔ **图表生成脚本模板**；用 LLM 从属性树抽取生成图表所需信息，再由脚本**自动构建图/表**。此外，按**子章**粒度结合 **MLLM + 上下文**从参考文献**检索原图**，若能有效支撑该小节则**引入**。

> **图2**（原文）：SurveyX 流水线（Part 1：检索与材料预处理；Part 2：写作与润色）。  
> **图3**（原文）：二级大纲生成示例：先基于属性树生成 hints，再综合 hints 确定**切分策略**与**条目**。

---

## 4 实验

### 4.1 评价指标
**自动评价（内容质量）**：在 [38] 的维度基础上，新增  
- **综合度（Synthesis）**：能否联结不同研究、识别共性/矛盾，构建超越逐篇摘要的**整体框架**；  
- **批判性分析（Critical Analysis）**：能否指出**方法局限**、**理论不一致**与**研究空白**。

**自动评价（引用质量）**：采用 [38] 的  
- **引用召回（Citation Recall）**：文本中每一陈述是否**被引用充分支持**；  
- **引用精度（Citation Precision）**：是否存在**不相关引用**。  
并新增 **F1** 综合衡量引用质量。

**参考文献相关性评价**：以往研究未充分覆盖，本文提出三项新指标：  
1. **IoU（Insertion over Union）**：衡量**机器检索**与**人类检索**结果的**交并比**：  
\[
IoU=\frac{Doc_{human}\cap Doc_{machine}}{Doc_{human}\cup Doc_{machine}}
\]
2. **Relevance\_{semantic}（基于嵌入的相关性）**：文献与主题的**平均余弦相似度**：  
\[
\mathrm{Rel}_{sem}=\frac{1}{|Doc|}\sum_{d\in Doc}\cos\_sim(E(d),E(topic))
\]
3. **Relevance\_{LLM}（基于LLM的相关性）**：通过构造提示，令 LLM 对各文献与主题的相关性进行**直接判定**：  
\[
\mathrm{Rel}_{LLM}=\frac{1}{|Doc|}\sum_{d\in Doc}\mathbf{1}_{\text{relevant}}(LLM(Prompt(d,topic)))
\]  
> 相关提示见**附录A.3**；人工评价标准见**附录A.2**。

### 4.2 实验设置
- **实现**：检索与评测阶段均采用 **bge-base-en-v1.5** 作为嵌入模型；全流程的 LLM 为 **GPT‑4o（2024‑08‑06）**。  
- **基线**：  
  - **Human**：人类撰写的 arXiv 综述（详见项目页）；  
  - **Naive RAG**：用与 SurveyX 相同的参考文献，仅提供**摘要**给 LLM 生成综述（提示见**附录A.4**）；  
  - **AutoSurvey**：[38] 提出的自动综述系统（我们使用其 **64k** 版本）。  
- **测试用题目**：采用 [38] 的 **20 个主题**（详见**表4**）。  
- **消融**：依次去除（或替换）  
  1) **关键词扩展**（仅用初始关键词检索）；  
  2) **AttributeTree**（改为直接使用全文）；  
  3) **大纲优化**（改为“一步出全纲”的提示）；  
  4) **RAG重写模块**（完全移除）。

### 4.3 结果与分析
**表1** 给出内容质量与引用质量（以及**表3**的参考文献相关性）结果。**要点**如下（节选）：
- **内容质量**：SurveyX 在 **Coverage / Structure / Relevance / Synthesis / Critical Analysis** 上整体表现最好，平均分 **4.590**；接近 **Human** 的 **4.754**。  
- **引用质量**：SurveyX 的 **Recall / Precision / F1** 分别为 **85.23 / 78.12 / 81.52**，优于 AutoSurvey（**82.25 / 77.41 / 79.76**）。  
- **参考相关性**：**IoU**（与人类检索交并比）**0.55**；\(\mathrm{Rel}_{sem}=0.4226\)、\(\mathrm{Rel}_{LLM}=0.7689\)，总体接近人工选择但仍有提升空间。

> **表1：内容与引用质量（节选）**  
> | 模型 | Coverage | Structure | Relevance | Synthesis | Critical Analysis | Avg | Recall | Precision | F1 |  
> |---|---:|---:|---:|---:|---:|---:|---:|---:|---:|  
> | naive RAG | 4.40 | 3.66 | 4.66 | 3.82 | 2.82 | 3.872 | 68.79 | 61.97 | 65.20 |  
> | AutoSurvey | 4.73 | 4.33 | 4.86 | 4.00 | 3.73 | 4.331 | 82.25 | 77.41 | 79.76 |  
> | **SurveyX** | **4.95** | **4.91** | **4.94** | **4.10** | **4.05** | **4.590** | **85.23** | **78.12** | **81.52** |  
> | **Human** | **5.00** | **4.95** | **5.00** | **4.44** | **4.38** | **4.754** | **86.33** | **77.78** | **81.83** |

> **图2、图3** 等更多实验可视化及**附录**内容：原文给出更详尽的流程细节、提示模板与属性树模板示例（见 A.2、A.3、A.4、附录B 等）。

---

## 5 小结与展望
SurveyX 以**人类写作流程**为蓝本，将自动综述写作拆分为**准备**与**生成**两大阶段，并在**检索、预处理、大纲–正文–润色**的每一环节引入针对性的**算法与模块**（关键词扩展、两步过滤、AttributeTree、Outline Optimization、RAG重写、图表生成）。实验显示，其在**内容质量**与**引用质量**方面**显著优于**已有系统，并在多个指标上**逼近人类专家**。

**未来方向**包括：  
- 更强的**在线检索**与**多源融合**；  
- 更鲁棒的**引用核验**与**事实一致性**；  
- 更丰富的**多模态表达**与**可复现图表模板库**；  
- 系统化、可泛化的**评测框架**与**公开基准**。

---

### 译注
1. 本文中文稿据公开论文文本整理翻译，**保留了原始结构、公式与主要实验数据**；图片未内嵌，仅保留标题与说明。  
2. 原文在实验分析后及附录处仍有**部分细节与模板**（例如：人评标准 A.2、相关性评测提示 A.3、Naive RAG 提示 A.4、属性树模板附录B、方法‑LLM模板附录C 等）。若你需要，我可以继续**逐段补齐**或将**附录模板**整理为**可直接使用的 Markdown/JSON**。


---
# 附录 A：评测与提示（Prompts）模板

> 说明：以下内容为基于正文方法学所做的“可执行化”补充模板，便于直接复用到你的 SurveyX 流水线中。若与原论文细节存在出入，请以实际实现为准。

## A.1 术语与符号
- **Topic / 主题**：本次综述的研究主题或问题域。
- **Doc / 文献**：候选参考文献；含 `title / authors / venue / year / abstract / pdf_url / sections` 等字段。
- **AttributeTree / 属性树**：对单篇文献按固定 schema 抽取的高密度结构化信息。
- **Hints / 提示要点**：从属性森林中提炼的“要写什么/如何写”的纲要粒度线索。
- **Section / Subsection**：综述的章节与二级小节。

## A.2 人工评测标准（可直接打分）
采用五维度 1–5 分 Likert 量表（1=很差，5=卓越），每维度打分锚点如下：

### A.2.1 Coverage（覆盖度）
- **1**：大量关键工作缺失；年代或子方向覆盖极不均衡。
- **3**：主干工作覆盖基本完整，但较新或小众分支遗漏明显。
- **5**：主干+新近+边缘方向均有覆盖，并清楚标明边界与未覆盖原因。

### A.2.2 Structure（结构性）
- **1**：纲目混乱，章节层级不清；跳跃严重。
- **3**：总体结构可读但存在冗余/重复；过渡略生硬。
- **5**：自顶向下结构清晰；过渡自然；段落内主题统一、层次分明。

### A.2.3 Relevance（相关性）
- **1**：大段与主题无关或泛泛而谈。
- **3**：大多数内容相关，但个别段落跑题。
- **5**：内容高度围绕主题；例证与论点紧密对应。

### A.2.4 Synthesis（综合度）
- **1**：只是逐篇摘要罗列，无纵横比较与抽象归纳。
- **3**：有少量比较与归纳，但未形成稳定维度或框架。
- **5**：系统比较（维度齐全、可复用）；能总结共识、冲突与演化趋势。

### A.2.5 Critical Analysis（批判性）
- **1**：无批判性；未指出局限与风险。
- **3**：能点出局限但分析浅尝辄止。
- **5**：指出方法/数据/评测的系统性局限，并提出可检验的改进方向。

> 评分输出建议：为每一小节给出五维得分与 2–3 句证据性理由，最后汇总均值与标准差。

## A.3 LLM 判定“文献↔主题”相关性的 Prompt 模板
**用途**：为候选文献做细粒度过滤（与粗粒度嵌入 Top‑K 配合）。

```text
System:
你是学术助手。请严格判断“候选文献是否与目标主题密切相关”，并只输出JSON。

User:
[主题]
{{TOPIC}}

[候选文献]
Title: {{TITLE}}
Venue: {{VENUE}} ({{YEAR}})
Abstract: {{ABSTRACT}}

[判定标准]
1) 与主题的核心问题、方法、数据或应用存在直接联系；
2) 若仅为泛化类比或边缘性提及，视为“不相关”。

[输出JSON字段]
{
  "relevant": true|false,
  "rationale": "<=120字给出判断要点",
  "evidence_spans": ["摘录或要点1","要点2"]
}
```

## A.4 “Naive RAG” 综述生成 Prompt（基线）
**用途**：与 SurveyX 对比；只给摘要而不做属性树/重写。

```text
System:
你是资深学术写作者，请基于给定文献的“摘要片段”撰写一篇主题综述。禁止虚构引用。

User:
[主题]
{{TOPIC}}

[可用资料=多个摘要片段]
{{ABSTRACT_SNIPPETS}}

[写作要求]
- 输出结构：引言→方法类比对→数据与评测→挑战与展望→结论。
- 每条论断后给出“支持该论断的文献ID列表”，格式如 [CIT: id1; id7].
- 严禁捏造文献；若资料不足，请显式写明“资料不足”。

[输出]
用中文撰写完整综述。
```

## A.5 关键词扩展 Prompt（配合 Algorithm 1）
```text
System:
你是检索策略专家。基于已有关键词与主题，提出“候选扩展关键词”，并标注其语义动机。

User:
[主题] {{TOPIC}}
[已用关键词] {{K_POOL}}
[新增摘要集合采样] {{ABSTRACT_SAMPLES}}

[输出JSON数组]
[
  {"candidate": "xxxx", "why": "与主题子方向A的术语同义/近邻", "risk": "歧义→需配合过滤词B"},
  ...
]
```

---

# 附录 B：AttributeTree（属性树）模板（可直接复用）

> 说明：以下 schema 为通用版本，适配主流论文类型。可按领域自定义增删字段。建议用 JSON 存储，每篇文献一棵树，后续作为 RAG 检索语料。

## B.1 方法类论文（Method）
```json
{
  "paper_id": "{{ID}}",
  "meta": {
    "title": "{{TITLE}}",
    "authors": ["{{A1}}","{{A2}}"],
    "venue": "{{VENUE}}",
    "year": {{YEAR}},
    "area": "{{AREA}}",
    "keywords": ["{{KW1}}","{{KW2}}"]
  },
  "problem": {
    "task": "{{TASK}}",
    "assumptions": ["{{ASSUMP1}}"],
    "pain_points": ["{{PAIN1}}","{{PAIN2}}"]
  },
  "method": {
    "name": "{{METHOD_NAME}}",
    "idea": "{{ONE_SENTENCE}}",
    "components": [
      {"name": "ModuleA", "role": "xxx", "details": "xxx"},
      {"name": "ModuleB", "role": "xxx", "details": "xxx"}
    ],
    "algorithms": ["{{ALG1}}","{{ALG2}}"],
    "complexity": {"time": "{{O()}}", "space": "{{O()}}"}
  },
  "data_eval": {
    "datasets": [{"name":"{{DS1}}","domain":"{{DOM}}"}],
    "metrics": ["{{M1}}","{{M2}}"],
    "baselines": ["{{B1}}","{{B2}}"],
    "results": [{"dataset":"{{DS1}}","metric":"{{M1}}","score":{{NUM}}}],
    "ablation": ["{{ABL1}}","{{ABL2}}"],
    "limitations": ["{{LIM1}}","{{LIM2}}"]
  },
  "citations": {
    "most_related": ["{{PID_A}}","{{PID_B}}"],
    "type": "method"
  }
}
```

## B.2 数据集论文（Dataset）
```json
{
  "paper_id": "{{ID}}",
  "meta": {...},
  "dataset": {
    "scope": {"lang":"en/zh", "domain":"{{DOM}}", "size":"{{N}}"},
    "collection": {"source":"{{SRC}}","time_range":"{{T}}","license":"{{LIC}}"},
    "schema": {"fields":["{{F1}}","{{F2}}"], "labels":["{{L1}}"]},
    "quality_control": ["dedup","LLM-filter","human-spot-check"],
    "splits": {"train":{{N1}},"valid":{{N2}},"test":{{N3}}}
  },
  "benchmark": {"tasks":["{{T1}}","{{T2}}"], "metrics":["{{M1}}"]},
  "risks": ["privacy","toxicity","bias"]
}
```

## B.3 基准/评测（Benchmark/Eval）
```json
{
  "paper_id": "{{ID}}",
  "meta": {...},
  "eval_design": {
    "dimensions": ["faithfulness","reasoning","safety","length"],
    "protocol": "open/closed-book; zero/few-shot",
    "judge": "human|LLM-as-judge|hybrid",
    "aggregation": "avg|max|EM|MALD"
  },
  "findings": [
    {"model":"{{M}}","split":"{{S}}","metric":"{{MET}}","score":{{NUM}}}
  ],
  "caveats": ["{{C1}}","{{C2}}"]
}
```

## B.4 综述/观点（Survey/Position）
```json
{
  "paper_id": "{{ID}}",
  "meta": {...},
  "taxonomy": [{"axis":"{{A}}","bins":["b1","b2"]}],
  "claims": [
    {"claim":"{{C}}","evidence":["{{PID1}}","{{PID2}}"], "risk":"{{R}}"}
  ],
  "gaps": ["{{G1}}","{{G2}}"],
  "future": ["{{F1}}","{{F2}}"]
}
```

## B.5 系统/框架（System）
```json
{
  "paper_id": "{{ID}}",
  "meta": {...},
  "architecture": {
    "modules": [{"name":"ingest","io":"raw→chunks"}, {"name":"retriever","algo":"BM25+E"}],
    "dependencies": ["{{LIB1}}","{{LIB2}}"],
    "latency": {"P50_ms": {{N}}, "P95_ms": {{N}}}
  },
  "deployment": {"cloud":"{{C}}","gpu":"{{GPU}}","cost":"{{$}}/1k tok"}
}
```

---

# 附录 C：写作与重写提示（可直接复制）

## C.1 从属性森林生成二级小节 Hints
```text
System:
你是研究综述的结构规划者。请基于属性森林抽取“二级小节候选与要点”。

User:
[主题] {{TOPIC}}
[属性森林-采样] {{ATTR_FOREST_SNIPPETS}}

[输出JSON]
[
  {"subsection":"问题定义与范围", "bullets":["xxx","yyy"], "support":["PID_12","PID_47"]},
  {"subsection":"方法分类：A/B/C", "bullets":["判据1","判据2"], "support":["PID_5","PID_9"]}
]
```

## C.2 “分离再重组”去冗与排序
```text
System:
你是学术编辑。请对下面的二级小节列表去重、合并同类项并排序，给出合并理由。

User:
[一级大纲] {{LEVEL1_TITLES}}
[二级候选] {{RAW_SUBSECTIONS_JSON}}

[输出JSON]
{
  "ordered_subsections": [
    {"title":"…", "merge_from":["…","…"], "why":"…"}
  ],
  "dropped": [{"title":"…","why":"与X重复/跑题"}]
}
```

## C.3 段落级 RAG 重写（引文校正+润色）
```text
System:
你是严谨的综述写作者。请仅使用“检索到的证据”重写段落并校正引用；禁止使用外部常识。

User:
[原段落] {{PARA_DRAFT}}
[检索证据-属性树片段] {{EVIDENCE_SNIPS}}
[要求]
- 只保留由证据支持的论断；对每句给出 [CIT: PIDx; PIDy]。
- 若证据不足，直接写“资料不足”并结束该句。

[输出] 重写后的段落（中文）
```

## C.4 引用核验 / 幻觉清理（后处理）
```text
System:
你是学术审校。逐句审查文本与所引证据是否匹配，输出问题清单。

User:
[段落] {{PARA}}
[证据列表] {{CITED_EVIDENCE}}

[输出JSON]
[
  {"sentence":"…","issue":"引文不支撑/年份不符/方法归因错误","suggestion":"替换为PID_23; 或删除"},
  {"sentence":"…","issue":"资料不足","suggestion":"补充实验或降格为猜想"}
]
```

## C.5 图表生成：信息抽取模板 + 脚本模板

**信息抽取 Prompt（示例：方法×指标对比表）**
```text
System:
提取“方法-数据集-指标-得分”四元组，输出JSON表格。

User:
[证据片段] {{EVIDENCE}}
[输出JSON]
[
  {"method":"X","dataset":"D1","metric":"F1","score":88.2},
  {"method":"Y","dataset":"D1","metric":"F1","score":86.5}
]
```

**表格到可视化脚本（Python，pandas+matplotlib）**
```python
import json, pandas as pd, matplotlib.pyplot as plt
data = json.loads(open("table.json","r").read())
df = pd.DataFrame(data)
pivot = df.pivot_table(index="method", columns="dataset", values="score", aggfunc="mean")
ax = pivot.plot(kind="bar", rot=30)
ax.set_ylabel("Score")
ax.set_title("Method vs Dataset")
plt.tight_layout(); plt.savefig("figure_method_dataset.png", dpi=200)
```

---

# 附录 D：参考相关性与 IoU 计算脚本（Python）

```python
from collections import Counter
import numpy as np

def iou(human_ids, machine_ids):
    A, B = set(human_ids), set(machine_ids)
    inter = len(A & B); union = len(A | B)
    return inter / union if union else 0.0

def rel_sem(emb_doc, emb_topic):
    # emb_doc: list[np.array], emb_topic: np.array
    sims = [ (v @ emb_topic) / (np.linalg.norm(v)*np.linalg.norm(emb_topic)+1e-8) for v in emb_doc ]
    return float(np.mean(sims)) if sims else 0.0

def rel_llm(judgements):
    # judgements: list[{"relevant": bool}]
    return sum(1 for j in judgements if j.get("relevant")) / max(1,len(judgements))
```

---

# 附录 E：实现与参数推荐（可作为起始配置）
- **嵌入模型**：`bge-base-en-v1.5`；向量维度 768；归一化相似度阈值建议 `0.32–0.38`（按主题调参）。
- **召回 Top‑K**：初筛 `K1=1000`；细筛后保留 `K2=150–300`。
- **段落切块**：每块 800–1200 tokens；重叠 150–200 tokens。
- **RAG 检索**：Top‑N 证据 `N=6–10`；证据窗口总量 ≤ 3k tokens。
- **写作温度**：`0.3–0.5`（保持客观与一致性）；引文核验阶段用 `0.0–0.2`。
- **图表生成**：优先表格→图；所有图表保存 `PNG+CSV` 双份以便审计复现。
- **引用格式**：统一 `[CIT: PID1; PID2]`；最终与参考文献表做 ID→Bib 的一一映射。

---

# 附录 F：属性树填充示例（节选）
```json
{
  "paper_id": "PID_47",
  "meta": {"title":"Efficient RAG for Long Surveys","venue":"NeurIPS","year":2024},
  "problem": {"task":"survey-writing","pain_points":["窗口限制","引用核验"]},
  "method": {"name":"AttrTree-Reranker","idea":"结构化抽取→高密度检索→段落重写"},
  "data_eval": {"datasets":[{"name":"20-topics"}], "metrics":["Coverage","F1-citation"]},
  "citations":{"most_related":["PID_3","PID_12"], "type":"method"}
}
```
