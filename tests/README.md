# 🧪 SurveyX 测试套件

这个文件夹包含了SurveyX项目的各种测试文件，用于验证系统各组件的正常运行。

## 📁 文件结构

```
tests/
├── README.md                    # 本文件
├── run_tests.py                 # 测试运行器主脚本
├── config_example.py            # 配置示例文件
├── test_embed_model.py         # Embed模型测试
├── test_chat_agent.py          # ChatAgent测试
├── test_data_cleaner.py        # 数据清理模块测试（待实现）
├── test_llm_config.py          # LLM配置测试
└── utils/
    └── test_helpers.py         # 测试辅助函数
```

## 🚀 快速开始

### 1. 环境准备

确保您已经安装了所有必要的依赖：

```bash
pip install -r requirements.txt
```

### 2. 配置测试环境

编辑 `src/configs/config.py` 确保LLM配置正确：

**推荐方式：使用配置示例文件**

```bash
# 复制配置示例
cp tests/config_example.py src/configs/config_test.py

# 编辑配置文件
nano src/configs/config_test.py  # 或使用您喜欢的编辑器
```

**示例配置：**
```python
# 示例配置
REMOTE_URL = "https://api.openai.com/v1/chat/completions"
TOKEN = "sk-your-actual-api-key-here"  # 🔴 替换为您的真实API密钥
DEFAULT_CHATAGENT_MODEL = "gpt-4o-mini"
DEFAULT_EMBED_ONLINE_MODEL = "./models/bge-base"  # 本地模型路径
```

**验证配置：**
```bash
# 运行配置验证
python tests/config_example.py
```

### 3. 运行测试

#### 使用测试运行器（推荐）

```bash
# 运行所有测试
python tests/run_tests.py

# 运行embed相关测试
python tests/run_tests.py -t embed

# 并行运行所有测试（显示详细信息）
python tests/run_tests.py -v -p

# 列出所有可用测试
python tests/run_tests.py -l

# 显示帮助信息
python tests/run_tests.py --help
```

#### 手动运行单个测试

```bash
# 运行embed模型测试
python tests/test_embed_model.py

# 运行ChatAgent测试
python tests/test_chat_agent.py

# 运行配置测试
python tests/test_llm_config.py
```

#### 使用pytest（如果已安装）

```bash
# 运行所有测试
python -m pytest tests/ -v

# 只运行embed测试
python -m pytest tests/test_embed_model.py -v
```

## 📄 Docling PDF→Markdown 快速试跑

本仓库提供了一个最小可用的 Docling 转换脚本，便于将本地 PDF 批量转换为 Markdown，作为 SurveyX 离线流程的参考文献输入。

### 1) 依赖与模型（推荐 8GB M1 设置）
- 安装 Docling 及工具：
  ```bash
  pip install -U docling docling-tools
  ```
- 预下载模型（离线可用）：
  ```bash
  docling-tools models download -o "$HOME/.cache/docling/models"
  ```
- （macOS 可选，推荐）Apple OCR：
  ```bash
  xcode-select --install
  pip install -U ocrmac
  ```

### 2) 运行转换脚本

```bash
bash tests/run_test_docling_to_md.sh [INPUT_PATH] [OUTPUT_DIR]
```
不带参数时，默认从 `resources/offline_refs/pdfs` 读取，输出到 `resources/offline_refs/docling_md_test`。

脚本默认设置：
- 使用 `DOCLING_ARTIFACTS_PATH="$HOME/.cache/docling/models"`
- 输出 Markdown (`--to md`)
- 图片导出模式当前为 embedded（如需减少体积，建议改为 placeholder）

建议在 8GB M1 上将图片模式切换为 `placeholder`，并在需要时启用 Apple OCR（`--ocr-engine ocrmac`）。可直接编辑脚本或手动运行 Docling：

```bash
docling <INPUT> \
  --to md \
  --image-export-mode placeholder \
  --ocr true --ocr-engine ocrmac --ocr-lang en-US \
  --device mps --num-threads 2 --page-batch-size 2 \
  --output <OUTPUT_DIR> \
  --artifacts-path "$HOME/.cache/docling/models"
```

转换完成后，将 `.md` 文件所在目录作为 `--ref_path` 传入 `tasks/offline_run.py` 即可。

### 3) 常见问题
- `ImportError: No module named 'ocrmac'`：未安装 Apple OCR。按上文安装 `ocrmac`，或移除 `--ocr-engine ocrmac`。
- `.md` 过大：使用 `--image-export-mode placeholder`，避免内嵌 base64 图像导致体积与 token 膨胀。

## 🧪 测试说明

### test_embed_model.py
- 测试本地BAAI/bge-base-en-v1.5模型的加载和运行
- 验证embeddings的维度和基本功能
- 检查模型是否能正确处理中文和英文文本

### test_chat_agent.py
- 测试ChatAgent与LLM API的连接
- 验证不同模型的调用（gpt-4o-mini, gpt-4o）
- 检查token使用统计功能

### test_data_cleaner.py
- 测试数据清理模块的功能
- 验证Markdown文件的解析
- 检查论文元数据提取

### test_llm_config.py
- 验证LLM配置的正确性
- 测试API连接性
- 检查模型可用性

## 🔧 故障排除

### 常见问题

1. **ImportError**: 模块导入失败
   ```bash
   # 确保Python路径正确
   export PYTHONPATH=/path/to/SurveyX:$PYTHONPATH
   ```

2. **模型加载失败**: 本地embed模型无法加载
   ```bash
   # 检查模型路径
   ls -la models/bge-base/

   # 重新下载模型
   huggingface-cli download BAAI/bge-base-en-v1.5 --local-dir ./models/bge-base
   ```

3. **API连接失败**: LLM API无法访问
   ```bash
   # 检查网络连接
   curl -I https://api.openai.com/v1/models

   # 检查API密钥
   # 确保TOKEN变量设置正确
   ```

## 📊 测试覆盖

### 已实现测试

- ✅ **Embed模型功能测试** (`test_embed_model.py`)
  - 本地BAAI/bge-base-en-v1.5模型加载
  - 向量维度验证
  - 批量处理性能测试
  - 相似度计算测试

- ✅ **ChatAgent API调用测试** (`test_chat_agent.py`)
  - OpenAI API连接测试
  - 多模型支持验证
  - Token监控功能测试
  - 错误处理测试

- ✅ **LLM配置验证测试** (`test_llm_config.py`)
  - 配置文件完整性检查
  - API密钥和URL验证
  - 模型路径检查
  - 网络连接测试
  - Python依赖验证

- ✅ **测试运行器** (`run_tests.py`)
  - 统一测试执行
  - 并行/串行运行支持
  - 测试结果汇总
  - 详细错误报告

### 待实现测试

- 🔄 数据清理模块测试 (`test_data_cleaner.py`)
- 🔄 LaTeX生成测试
- 🔄 端到端流程测试
- 🔄 性能基准测试

### 测试辅助工具

- 🛠️ **测试辅助函数** (`utils/test_helpers.py`)
  - 文件和目录检查
  - 执行时间测量
  - API连接测试
  - 测试结果保存
  - 配置验证工具

## 🤝 贡献

如果您想添加新的测试：

1. 在 `tests/` 目录下创建新的测试文件
2. 遵循 `test_*.py` 的命名规范
3. 在本README中添加相应的说明
4. 确保测试可以独立运行

## 📞 支持

如果遇到测试相关的问题，请：

1. 检查本README的故障排除部分
2. 查看项目的主要README文件
3. 在GitHub Issues中提交问题

---

**注意**: 这些测试需要有效的API密钥和网络连接才能完全运行。
