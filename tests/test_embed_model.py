#!/usr/bin/env python3
"""
🧪 SurveyX Embed模型测试脚本

测试BAAI/bge-base-en-v1.5模型的加载和运行功能

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
from src.models.LLM.EmbedAgent import EmbedAgent
from src.configs.config import DEFAULT_EMBED_ONLINE_MODEL

logger = get_logger("test_embed_model")

class EmbedModelTester:
    """Embed模型测试类"""

    def __init__(self):
        self.agent = None
        self.test_texts = {
            "english": "This is a test sentence for embedding model validation.",
            "chinese": "这是一个用于测试嵌入模型的中文句子。",
            "technical": "Large Language Models (LLMs) have revolutionized natural language processing.",
            "long_text": """
            Reinforcement Learning (RL) is a type of machine learning where an agent learns to make decisions
            by interacting with an environment. The goal is to maximize cumulative rewards through trial and error.
            Deep RL combines reinforcement learning with deep neural networks to handle complex, high-dimensional
            state spaces that traditional RL methods struggle with.
            """
        }

    def test_model_loading(self):
        """测试模型加载"""
        logger.info("🔄 测试模型加载...")
        try:
            start_time = time.time()
            self.agent = EmbedAgent()
            load_time = time.time() - start_time

            logger.info(f"✅ 模型加载成功，耗时: {load_time:.2f}秒")
            logger.info(f"✅ 模型路径: {DEFAULT_EMBED_ONLINE_MODEL}")
            return True

        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            logger.error(f"💡 请检查模型路径: {DEFAULT_EMBED_ONLINE_MODEL}")
            logger.error("💡 如果模型不存在，请运行以下命令下载:")
            logger.error("   huggingface-cli download BAAI/bge-base-en-v1.5 --local-dir ./models/bge-base")
            return False

    def test_single_embedding(self, text, text_type):
        """测试单文本嵌入"""
        logger.info(f"🔄 测试{text_type}文本嵌入...")

        try:
            start_time = time.time()
            embedding = self.agent.local_embed(text)
            embed_time = time.time() - start_time

            logger.info(f"✅ 嵌入成功，耗时: {embed_time:.3f}秒")
            logger.info(f"📏 向量维度: {len(embedding)}")
            logger.info(f"📊 前5个值: [{', '.join([f'{x:.4f}' for x in embedding[:5]])}]")

            # 验证向量维度
            expected_dim = 768  # BAAI/bge-base-en-v1.5的输出维度
            if len(embedding) == expected_dim:
                logger.info(f"✅ 向量维度正确: {len(embedding)} == {expected_dim}")
            else:
                logger.warning(f"⚠️ 向量维度异常: {len(embedding)} != {expected_dim}")

            return True

        except Exception as e:
            logger.error(f"❌ {text_type}文本嵌入失败: {e}")
            return False

    def test_batch_embedding(self):
        """测试批量嵌入"""
        logger.info("🔄 测试批量嵌入...")

        try:
            texts = list(self.test_texts.values())
            start_time = time.time()
            embeddings = self.agent.batch_local_embed(texts)
            batch_time = time.time() - start_time

            logger.info(f"✅ 批量嵌入成功，耗时: {batch_time:.3f}秒")
            logger.info(f"📊 批量大小: {len(embeddings)}")
            logger.info(f"📏 每个向量维度: {len(embeddings[0])}")

            # 验证所有向量维度一致
            dims = [len(emb) for emb in embeddings]
            if len(set(dims)) == 1:
                logger.info(f"✅ 所有向量维度一致: {dims[0]}")
            else:
                logger.warning(f"⚠️ 向量维度不一致: {dims}")

            return True

        except Exception as e:
            logger.error(f"❌ 批量嵌入失败: {e}")
            return False

    def test_similarity_calculation(self):
        """测试相似度计算"""
        logger.info("🔄 测试相似度计算...")

        try:
            text1 = "Large language models are powerful AI systems."
            text2 = "LLMs represent advanced artificial intelligence technology."

            emb1 = self.agent.local_embed(text1)
            emb2 = self.agent.local_embed(text2)

            # 计算余弦相似度（優先用 numpy，否則使用純 Python 後備）
            try:
                import numpy as np
                from numpy.linalg import norm

                cosine_sim = np.dot(emb1, emb2) / (norm(emb1) * norm(emb2))
            except Exception:
                import math

                def _dot(a, b):
                    return sum(x * y for x, y in zip(a, b))

                def _norm(a):
                    return math.sqrt(sum(x * x for x in a))

                denom = _norm(emb1) * _norm(emb2)
                cosine_sim = _dot(emb1, emb2) / (denom + 1e-12)

            logger.info(f"🔢 余弦相似度: {cosine_sim:.4f}")
            logger.info("✅ 相似度计算成功")

            return True

        except Exception as e:
            logger.error(f"❌ 相似度计算失败: {e}")
            return False

    def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始Embed模型全面测试")
        logger.info("=" * 50)

        test_results = []

        # 1. 模型加载测试
        test_results.append(("模型加载", self.test_model_loading()))

        if not test_results[-1][1]:
            logger.error("❌ 模型加载失败，跳过后续测试")
            return test_results

        # 2. 单文本嵌入测试
        for text_type, text in self.test_texts.items():
            result = self.test_single_embedding(text, text_type)
            test_results.append((f"{text_type}嵌入", result))

        # 3. 批量嵌入测试
        test_results.append(("批量嵌入", self.test_batch_embedding()))

        # 4. 相似度计算测试
        test_results.append(("相似度计算", self.test_similarity_calculation()))

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
            logger.info("🎉 所有测试通过！Embed模型运行正常")
        else:
            logger.warning(f"⚠️ {total - passed}个测试失败，请检查配置")

        return test_results

def main():
    """主函数"""
    print("🧪 SurveyX Embed模型测试工具")
    print("=" * 40)

    # 检查环境
    print(f"📍 当前工作目录: {os.getcwd()}")
    print(f"🐍 Python版本: {sys.version}")
    print(f"📦 项目根目录: {project_root}")

    # 检查模型文件是否存在
    model_path = project_root / "models" / "bge-base"
    if model_path.exists():
        print(f"✅ 模型目录存在: {model_path}")
        model_files = list(model_path.glob("*"))
        print(f"📁 模型文件数量: {len(model_files)}")
        if len(model_files) > 0:
            print("📄 部分文件列表:")
            for f in model_files[:5]:  # 只显示前5个
                print(f"   - {f.name}")
    else:
        print(f"❌ 模型目录不存在: {model_path}")
        print("💡 请先下载模型:")
        print("   huggingface-cli download BAAI/bge-base-en-v1.5 --local-dir ./models/bge-base")

    print()

    # 运行测试
    tester = EmbedModelTester()
    results = tester.run_all_tests()

    # 返回退出码
    passed = sum(1 for _, result in results if result)
    total = len(results)
    success_rate = passed / total if total > 0 else 0

    if success_rate == 1.0:
        print("\n🎉 所有测试通过！您的Embed模型配置正确。")
        return 0
    elif success_rate >= 0.5:
        print(f"\n⚠️ 大部分测试通过 ({passed}/{total})，但有一些问题需要检查。")
        return 1
    else:
        print(f"\n❌ 大多数测试失败 ({passed}/{total})，请检查配置和环境。")
        return 2

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
