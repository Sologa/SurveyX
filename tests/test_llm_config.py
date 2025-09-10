#!/usr/bin/env python3
"""
🧪 SurveyX LLM配置测试脚本

验证LLM相关的配置是否正确

作者: SurveyX Team
创建时间: 2024-01
"""

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.configs.logger import get_logger
from src.configs.config import (
    REMOTE_URL,
    TOKEN,
    DEFAULT_CHATAGENT_MODEL,
    ADVANCED_CHATAGENT_MODEL,
    DEFAULT_EMBED_ONLINE_MODEL,
    EMBED_REMOTE_URL,
    EMBED_TOKEN
)

logger = get_logger("test_llm_config")

class LLMConfigTester:
    """LLM配置测试类"""

    def __init__(self):
        self.config_status = {}

    def test_config_file_exists(self):
        """测试配置文件是否存在"""
        logger.info("🔄 检查配置文件...")

        config_path = project_root / "src" / "configs" / "config.py"
        if config_path.exists():
            logger.info(f"✅ 配置文件存在: {config_path}")
            self.config_status["config_file"] = True
            return True
        else:
            logger.error(f"❌ 配置文件不存在: {config_path}")
            self.config_status["config_file"] = False
            return False

    def test_api_configurations(self):
        """测试API配置"""
        logger.info("🔄 检查API配置...")

        configs = {
            "REMOTE_URL": REMOTE_URL,
            "TOKEN": TOKEN,
            "DEFAULT_CHATAGENT_MODEL": DEFAULT_CHATAGENT_MODEL,
            "ADVANCED_CHATAGENT_MODEL": ADVANCED_CHATAGENT_MODEL,
            "DEFAULT_EMBED_ONLINE_MODEL": DEFAULT_EMBED_ONLINE_MODEL,
            "EMBED_REMOTE_URL": EMBED_REMOTE_URL,
            "EMBED_TOKEN": EMBED_TOKEN
        }

        all_valid = True

        for key, value in configs.items():
            if value and value != f"your {key.lower()} here":
                logger.info(f"✅ {key}: 已配置")
                self.config_status[key] = True
            else:
                logger.warning(f"⚠️ {key}: 未配置或使用默认值")
                self.config_status[key] = False
                if key in ["TOKEN", "EMBED_TOKEN"]:
                    all_valid = False

        return all_valid

    def test_model_paths(self):
        """测试模型路径"""
        logger.info("🔄 检查模型路径...")

        # 检查embed模型路径
        embed_model_path = DEFAULT_EMBED_ONLINE_MODEL

        if embed_model_path.startswith("./") or embed_model_path.startswith("/"):
            # 本地路径
            full_path = project_root / embed_model_path.lstrip("./")
            if full_path.exists():
                logger.info(f"✅ Embed模型路径存在: {full_path}")
                self.config_status["embed_model_path"] = True

                # 检查模型文件
                model_files = [
                    "config.json",
                    "pytorch_model.bin",
                    "tokenizer_config.json",
                    "vocab.txt"
                ]

                missing_files = []
                for file in model_files:
                    if not (full_path / file).exists():
                        missing_files.append(file)

                if not missing_files:
                    logger.info("✅ Embed模型文件完整")
                else:
                    logger.warning(f"⚠️ 缺少模型文件: {missing_files}")
                    self.config_status["embed_model_complete"] = False
                return True
            else:
                logger.error(f"❌ Embed模型路径不存在: {full_path}")
                logger.error("💡 请下载模型: huggingface-cli download BAAI/bge-base-en-v1.5 --local-dir ./models/bge-base")
                self.config_status["embed_model_path"] = False
                return False
        else:
            # HuggingFace模型名
            logger.info(f"ℹ️ 使用HuggingFace模型: {embed_model_path}")
            self.config_status["embed_model_hf"] = True
            return True

    def test_network_connectivity(self):
        """测试网络连接"""
        logger.info("🔄 测试网络连接...")

        import requests

        # 测试OpenAI API连接
        try:
            # 只是测试连接，不发送实际请求
            response = requests.get("https://api.openai.com/v1/models",
                                  headers={"Authorization": f"Bearer {TOKEN}"},
                                  timeout=10)
            if response.status_code == 401:
                logger.info("✅ OpenAI API连接正常 (401表示认证问题，但连接成功)")
                self.config_status["openai_api"] = True
            elif response.status_code == 200:
                logger.info("✅ OpenAI API连接正常")
                self.config_status["openai_api"] = True
            else:
                logger.warning(f"⚠️ OpenAI API响应异常: {response.status_code}")
                self.config_status["openai_api"] = False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ OpenAI API连接失败: {e}")
            self.config_status["openai_api"] = False

        # 测试embed API连接 (如果使用远程embed)
        if EMBED_REMOTE_URL != "https://api.siliconflow.cn/v1/embeddings":
            try:
                response = requests.get(EMBED_REMOTE_URL, timeout=5)
                logger.info(f"✅ Embed API连接正常: {EMBED_REMOTE_URL}")
                self.config_status["embed_api"] = True
            except requests.exceptions.RequestException as e:
                logger.warning(f"⚠️ Embed API连接问题: {e}")
                self.config_status["embed_api"] = False

        return self.config_status.get("openai_api", False)

    def test_dependencies(self):
        """测试依赖包"""
        logger.info("🔄 检查Python依赖...")

        required_packages = [
            "openai",
            "llama_index",
            "transformers",
            "torch",
            "numpy",
            "tqdm"
        ]

        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                logger.info(f"✅ {package}: 已安装")
            except ImportError:
                logger.error(f"❌ {package}: 未安装")
                missing_packages.append(package)

        if not missing_packages:
            logger.info("✅ 所有必需依赖已安装")
            self.config_status["dependencies"] = True
            return True
        else:
            logger.error(f"❌ 缺少依赖包: {missing_packages}")
            logger.error("💡 请运行: pip install -r requirements.txt")
            self.config_status["dependencies"] = False
            return False

    def generate_config_report(self):
        """生成配置报告"""
        logger.info("🔄 生成配置报告...")

        report = {
            "timestamp": str(Path(__file__).stat().st_mtime),
            "config_status": self.config_status,
            "system_info": {
                "python_version": sys.version,
                "working_directory": str(project_root),
                "platform": sys.platform
            },
            "recommendations": []
        }

        # 生成建议
        if not self.config_status.get("config_file", False):
            report["recommendations"].append("配置文件不存在，请检查src/configs/config.py")

        if not self.config_status.get("TOKEN", False):
            report["recommendations"].append("OpenAI API Token未设置，请在config.py中配置TOKEN")

        if not self.config_status.get("embed_model_path", False) and not self.config_status.get("embed_model_hf", False):
            report["recommendations"].append("Embed模型路径未配置，请设置DEFAULT_EMBED_ONLINE_MODEL")

        if not self.config_status.get("dependencies", False):
            report["recommendations"].append("Python依赖不完整，请运行: pip install -r requirements.txt")

        if not self.config_status.get("openai_api", False):
            report["recommendations"].append("OpenAI API连接失败，请检查网络和API密钥")

        return report

    def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始LLM配置全面测试")
        logger.info("=" * 50)

        test_results = []

        # 1. 配置文件测试
        test_results.append(("配置文件", self.test_config_file_exists()))

        # 2. API配置测试
        test_results.append(("API配置", self.test_api_configurations()))

        # 3. 模型路径测试
        test_results.append(("模型路径", self.test_model_paths()))

        # 4. 网络连接测试
        test_results.append(("网络连接", self.test_network_connectivity()))

        # 5. 依赖测试
        test_results.append(("Python依赖", self.test_dependencies()))

        # 输出测试总结
        logger.info("=" * 50)
        logger.info("📊 测试结果总结:")

        passed = 0
        total = len(test_results)

        for test_name, result in test_results:
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"  {test_name}: {status}")
            if result:
                passed += 1

        logger.info("-" * 30)
        success_rate = passed / total if total > 0 else 0
        logger.info(f"✅ 通过率: {success_rate:.1%}")
        # 生成配置报告
        report = self.generate_config_report()

        logger.info("📋 配置建议:")
        for i, rec in enumerate(report["recommendations"], 1):
            logger.info(f"  {i}. {rec}")

        if passed == total:
            logger.info("🎉 所有配置测试通过！您的LLM配置正确。")
        else:
            logger.warning(f"⚠️ {total - passed}个配置测试失败，请根据建议进行修复。")

        return test_results, report

def main():
    """主函数"""
    print("🧪 SurveyX LLM配置测试工具")
    print("=" * 40)

    # 检查环境
    print(f"📍 项目根目录: {project_root}")
    print(f"🐍 Python版本: {sys.version}")
    print(f"🖥️ 操作系统: {sys.platform}")

    # 检查关键文件
    key_files = [
        "src/configs/config.py",
        "requirements.txt",
        "models/bge-base/config.json"  # 如果使用本地模型
    ]

    print("\n📁 关键文件状态:")
    for file_path in key_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} (不存在)")

    print()

    # 运行测试
    tester = LLMConfigTester()
    results, report = tester.run_all_tests()

    # 保存报告
    report_path = project_root / "tests" / "config_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n💾 配置报告已保存: {report_path}")

    # 返回退出码
    passed = sum(1 for _, result in results if result)
    total = len(results)
    success_rate = passed / total if total > 0 else 0

    if success_rate == 1.0:
        print("\n🎉 所有配置测试通过！您的SurveyX环境已准备就绪。")
        return 0
    elif success_rate >= 0.5:
        print(f"\n⚠️ 大部分配置正确 ({passed}/{total})，但需要进行一些调整。")
        return 1
    else:
        print(f"\n❌ 配置存在严重问题 ({passed}/{total})，请仔细检查。")
        return 2

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
