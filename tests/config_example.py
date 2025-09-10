# 🧪 SurveyX 测试配置示例
"""
这个文件展示了如何为测试配置SurveyX环境
请复制相关配置到您的 src/configs/config.py 文件中
"""

# =============================================================================
# 基本配置
# =============================================================================

# OpenAI API配置
REMOTE_URL = "https://api.openai.com/v1/chat/completions"
TOKEN = "sk-your-actual-openai-api-key-here"  # 🔴 请替换为您的真实API密钥

# 模型配置
DEFAULT_CHATAGENT_MODEL = "gpt-4o-mini"
ADVANCED_CHATAGENT_MODEL = "gpt-4o"

# =============================================================================
# Embed模型配置
# =============================================================================

# 方式1：使用本地下载的BAAI/bge-base-en-v1.5模型
DEFAULT_EMBED_ONLINE_MODEL = "./models/bge-base"

# 方式2：使用HuggingFace在线模型（如果本地模型有问题）
# DEFAULT_EMBED_ONLINE_MODEL = "BAAI/bge-base-en-v1.5"

# 方式3：使用其他embed API（可选）
EMBED_REMOTE_URL = "https://api.siliconflow.cn/v1/embeddings"
EMBED_TOKEN = "your-embed-api-token-here"

# =============================================================================
# 其他配置
# =============================================================================

# 本地LLM配置（如果需要）
LOCAL_URL = "http://localhost:8000/v1/chat/completions"  # 本地LLM服务器地址
LOCAL_LLM = "local-model-name"

# 备用embed模型
DEFAULT_EMBED_LOCAL_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# 其他参数
SPLITTER_WINDOW_SIZE = 6
SPLITTER_CHUNK_SIZE = 2048

# =============================================================================
# 使用说明
# =============================================================================

"""
配置步骤：

1. 复制此文件的配置到您的 src/configs/config.py
2. 设置您的OpenAI API密钥
3. 如果使用本地embed模型，确保已下载：
   huggingface-cli download BAAI/bge-base-en-v1.5 --local-dir ./models/bge-base
4. 运行测试验证配置：
   python tests/test_llm_config.py

环境变量支持：
您也可以使用环境变量来设置敏感信息：
export OPENAI_API_KEY="sk-your-key"
export EMBED_MODEL_PATH="./models/bge-base"
"""

# =============================================================================
# 测试配置验证
# =============================================================================

def validate_config():
    """验证配置是否正确"""
    issues = []

    # 检查API密钥
    if TOKEN in ["your token here", ""]:
        issues.append("❌ OpenAI API Token未设置")

    # 检查embed模型路径
    import os
    from pathlib import Path

    if DEFAULT_EMBED_ONLINE_MODEL.startswith("./"):
        model_path = Path(DEFAULT_EMBED_ONLINE_MODEL)
        if not model_path.exists():
            issues.append(f"❌ Embed模型路径不存在: {model_path}")

    # 检查网络连接
    try:
        import requests
        response = requests.get("https://api.openai.com/v1/models",
                              headers={"Authorization": f"Bearer {TOKEN}"},
                              timeout=5)
        if response.status_code != 200:
            issues.append(f"⚠️ OpenAI API响应异常: {response.status_code}")
    except:
        issues.append("⚠️ 无法连接到OpenAI API")

    if issues:
        print("配置问题:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("✅ 配置验证通过")
        return True

if __name__ == "__main__":
    print("🧪 验证SurveyX测试配置...")
    validate_config()
