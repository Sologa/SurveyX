#!/usr/bin/env python3
"""
🧪 SurveyX ChatAgent测试脚本

测试ChatAgent与LLM API的连接和功能

作者: SurveyX Team
创建时间: 2024-01
"""

import os
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.configs.logger import get_logger
from src.models.LLM.ChatAgent import ChatAgent
from src.configs.config import (
    REMOTE_URL,
    TOKEN,
    DEFAULT_CHATAGENT_MODEL,
    ADVANCED_CHATAGENT_MODEL,
    REASONING_MODELS,
    DEFAULT_REASONING_EFFORT,
)

logger = get_logger("test_chat_agent")

class ChatAgentTester:
    """ChatAgent测试类"""

    def __init__(self):
        self.agent = None
        self.test_prompts = {
            "simple": "Hello, can you respond with 'Hello from SurveyX!'?",
            "technical": "Explain what reinforcement learning is in one sentence.",
            "chinese": "请用中文解释什么是大型语言模型。",
            "long": """
            Write a brief summary about the evolution of natural language processing
            from rule-based systems to modern transformer architectures.
            Keep it under 100 words.
            """
        }

    def test_agent_initialization(self):
        """测试ChatAgent初始化"""
        logger.info("🔄 测试ChatAgent初始化...")
        try:
            start_time = time.time()
            self.agent = ChatAgent()
            init_time = time.time() - start_time

            logger.info(f"✅ ChatAgent初始化成功，耗时: {init_time:.3f}秒")
            logger.info(f"🔗 API URL: {REMOTE_URL}")
            logger.info(f"🤖 默认模型: {DEFAULT_CHATAGENT_MODEL}")
            logger.info(f"🚀 高级模型: {ADVANCED_CHATAGENT_MODEL}")

            # 检查token是否设置
            if TOKEN and TOKEN != "your token here":
                logger.info("✅ API Token已设置")
            else:
                logger.warning("⚠️ API Token未设置或使用默认值")

            return True

        except Exception as e:
            logger.error(f"❌ ChatAgent初始化失败: {e}")
            return False

    def test_env_loading(self):
        """测试 .env 读取与环境变量优先级"""
        logger.info("🔄 测试 .env 读取与优先级...")
        import importlib
        import sys as _sys
        import tempfile

        # 备份原始环境变量
        original_env = {
            "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
            "OPENAI_REASONING_EFFORT": os.environ.get("OPENAI_REASONING_EFFORT"),
            "SURVEYX_ENV_FILE": os.environ.get("SURVEYX_ENV_FILE"),
        }

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                env_path = Path(tmpdir) / ".env"
                env_path.write_text(
                    "OPENAI_API_KEY=sk-from-env-file\nOPENAI_REASONING_EFFORT=high\n",
                    encoding="utf-8",
                )

                # 指定测试用 .env 文件，并清空相关环境变量，确保从文件读取
                os.environ["SURVEYX_ENV_FILE"] = str(env_path)
                os.environ.pop("OPENAI_API_KEY", None)
                os.environ.pop("OPENAI_REASONING_EFFORT", None)

                # 重新加载配置模块
                if "src.configs.config" in _sys.modules:
                    del _sys.modules["src.configs.config"]
                config = importlib.import_module("src.configs.config")

                assert config.TOKEN == "sk-from-env-file"
                assert config.DEFAULT_REASONING_EFFORT == "high"

                # 环境变量应覆盖 .env 文件
                os.environ["OPENAI_API_KEY"] = "sk-from-env-var"
                os.environ["OPENAI_REASONING_EFFORT"] = "low"
                del _sys.modules["src.configs.config"]
                config = importlib.import_module("src.configs.config")
                assert config.TOKEN == "sk-from-env-var"
                assert config.DEFAULT_REASONING_EFFORT == "low"

            logger.info("✅ .env 读取与优先级测试通过")
            return True
        except AssertionError as e:
            logger.error(f"❌ .env 读取测试断言失败: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ .env 读取测试异常: {e}")
            return False
        finally:
            # 恢复环境变量并重载模块，避免影响其他测试
            for k, v in original_env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
            try:
                if "src.configs.config" in _sys.modules:
                    del _sys.modules["src.configs.config"]
                importlib.import_module("src.configs.config")
            except Exception:
                pass

    def test_simple_api_call(self, model_name):
        """测试简单API调用"""
        logger.info(f"🔄 测试{model_name}模型API调用...")

        try:
            prompt = self.test_prompts["simple"]
            start_time = time.time()

            # 若为推理模型（含家族前綴），則附帶 reasoning_effort 並走 Responses API
            is_reasoning = False
            try:
                is_reasoning = model_name in REASONING_MODELS or any(
                    model_name.startswith(prefix) for prefix in REASONING_MODELS
                )
            except Exception:
                is_reasoning = False

            kwargs = {
                "text_content": prompt,
                "model": model_name,
                "temperature": 0.1,
            }
            if is_reasoning:
                kwargs["reasoning_effort"] = DEFAULT_REASONING_EFFORT or "medium"

            response = self.agent.remote_chat(**kwargs)

            call_time = time.time() - start_time

            logger.info(f"✅ API调用成功，耗时: {call_time:.3f}秒")
            logger.info(f"📝 响应长度: {len(response)} 字符")

            # 检查响应是否合理
            if len(response.strip()) > 10:
                logger.info("✅ 响应内容合理")
            else:
                logger.warning("⚠️ 响应内容过短")

            # 检查是否包含预期内容
            if "SurveyX" in response or "Hello" in response:
                logger.info("✅ 响应内容符合预期")
            else:
                logger.info("ℹ️ 响应内容: " + response[:100] + "...")

            return True

        except Exception as e:
            logger.error(f"❌ {model_name}模型API调用失败: {e}")
            return False

    def test_multiple_models(self):
        """测试多个模型"""
        models_to_test = [
            DEFAULT_CHATAGENT_MODEL,
            ADVANCED_CHATAGENT_MODEL,
            "gpt-5-nano",  # 務必測試 gpt-5-nano
        ]
        results = {}

        for model in models_to_test:
            logger.info(f"🎯 测试模型: {model}")
            result = self.test_simple_api_call(model)
            results[model] = result

        return results

    def test_token_monitoring(self):
        """测试token监控功能"""
        logger.info("🔄 测试token监控功能...")

        try:
            from src.models.monitor.token_monitor import TokenMonitor

            # 创建token monitor
            monitor = TokenMonitor("test_task", "test_operation")

            # 进行一次API调用
            prompt = "Count to 10."
            response = self.agent.remote_chat(
                text_content=prompt,
                model=DEFAULT_CHATAGENT_MODEL
            )

            logger.info("✅ Token监控测试完成")
            logger.info(f"📝 响应: {response}")

            return True

        except Exception as e:
            logger.error(f"❌ Token监控测试失败: {e}")
            return False

    def test_error_handling(self):
        """测试错误处理"""
        logger.info("🔄 测试错误处理...")

        try:
            # 测试无效的model名称
            invalid_model = "non-existent-model-12345"
            response = self.agent.remote_chat(
                text_content="Test error handling",
                model=invalid_model,
                temperature=0.1
            )

            logger.info("⚠️ 错误处理测试: 未按预期失败")
            return False

        except Exception as e:
            logger.info(f"✅ 错误处理正常: {type(e).__name__}")
            return True

    def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始ChatAgent全面测试")
        logger.info("=" * 50)

        test_results = []

        # 0. .env 读取测试
        test_results.append((".env读取", self.test_env_loading()))

        # 1. 初始化测试
        test_results.append(("初始化", self.test_agent_initialization()))

        if not test_results[-1][1]:
            logger.error("❌ 初始化失败，跳过后续测试")
            return test_results

        # 2. 多模型测试
        model_results = self.test_multiple_models()
        for model, result in model_results.items():
            test_results.append((f"{model}调用", result))

        # 3. Token监控测试
        test_results.append(("Token监控", self.test_token_monitoring()))

        # 4. 错误处理测试
        test_results.append(("错误处理", self.test_error_handling()))

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
        if passed == total:
            logger.info("🎉 所有测试通过！ChatAgent运行正常")
        else:
            logger.warning(f"⚠️ {total - passed}个测试失败，请检查配置")

        return test_results

def main():
    """主函数"""
    print("🧪 SurveyX ChatAgent测试工具")
    print("=" * 40)

    # 检查环境
    print(f"📍 当前工作目录: {os.getcwd()}")
    print(f"🐍 Python版本: {sys.version}")
    print(f"🔗 API URL: {REMOTE_URL}")
    print(f"🔑 Token状态: {'已设置' if TOKEN and TOKEN != 'your token here' else '未设置'}")

    # 检查配置文件
    config_path = project_root / "src" / "configs" / "config.py"
    if config_path.exists():
        print(f"✅ 配置文件存在: {config_path}")
    else:
        print(f"❌ 配置文件不存在: {config_path}")

    print()

    # 运行测试
    tester = ChatAgentTester()
    results = tester.run_all_tests()

    # 返回退出码
    passed = sum(1 for _, result in results if result)
    total = len(results)
    success_rate = passed / total if total > 0 else 0

    if success_rate == 1.0:
        print("\n🎉 所有测试通过！您的ChatAgent配置正确。")
        return 0
    elif success_rate >= 0.5:
        print(f"\n⚠️ 大部分测试通过 ({passed}/{total})，但有一些问题需要检查。")
        return 1
    else:
        print(f"\n❌ 大多数测试失败 ({passed}/{total})，请检查API配置。")
        return 2

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
