#!/usr/bin/env python3
"""
🧪 SurveyX测试运行器

统一运行所有测试脚本

作者: SurveyX Team
创建时间: 2024-01
"""

import os
import sys
import argparse
import subprocess
import time
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

def run_test(test_file: str, verbose: bool = False) -> tuple:
    """运行单个测试文件"""
    test_path = PROJECT_ROOT / "tests" / test_file

    if not test_path.exists():
        print(f"❌ 测试文件不存在: {test_path}")
        return False, 0

    print(f"🚀 运行测试: {test_file}")
    print("-" * 40)

    try:
        # 设置环境变量
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT)

        # 运行测试
        cmd = [sys.executable, str(test_path)]
        if verbose:
            cmd.append("--verbose")

        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=not verbose,
            text=True,
            timeout=300  # 5分钟超时
        )

        success = result.returncode == 0

        if verbose:
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)

        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} {test_file} (退出码: {result.returncode})")

        return success, result.returncode

    except subprocess.TimeoutExpired:
        print(f"⏰ {test_file} 运行超时")
        return False, -1
    except Exception as e:
        print(f"💥 {test_file} 运行出错: {e}")
        return False, -2

def run_all_tests(test_pattern: str = "*", verbose: bool = False, parallel: bool = False):
    """运行所有测试"""
    print("🧪 SurveyX 测试套件")
    print("=" * 50)
    print(f"项目目录: {PROJECT_ROOT}")
    print(f"测试模式: {'并行' if parallel else '串行'}")
    print(f"详细输出: {'是' if verbose else '否'}")
    print()

    # 查找所有测试文件
    tests_dir = PROJECT_ROOT / "tests"
    test_files = []

    if test_pattern == "*":
        # 运行所有test_*.py文件
        for file_path in tests_dir.glob("test_*.py"):
            test_files.append(file_path.name)
    else:
        # 运行指定模式的文件
        for file_path in tests_dir.glob(f"test_{test_pattern}*.py"):
            test_files.append(file_path.name)

    if not test_files:
        print(f"❌ 未找到匹配的测试文件 (模式: test_{test_pattern}*.py)")
        return False

    print(f"📋 发现 {len(test_files)} 个测试文件:")
    for i, file in enumerate(test_files, 1):
        print(f"  {i}. {file}")
    print()

    # 运行测试
    results = []
    total_start_time = time.time()

    if parallel:
        # 并行运行 (简单实现)
        print("🚀 开始并行运行测试...")
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(test_files))) as executor:
            future_to_test = {
                executor.submit(run_test, test_file, verbose): test_file
                for test_file in test_files
            }

            for future in concurrent.futures.as_completed(future_to_test):
                test_file = future_to_test[future]
                try:
                    success, returncode = future.result()
                    results.append((test_file, success, returncode))
                except Exception as e:
                    print(f"💥 {test_file} 执行异常: {e}")
                    results.append((test_file, False, -3))
    else:
        # 串行运行
        print("🚀 开始串行运行测试...")
        for test_file in test_files:
            success, returncode = run_test(test_file, verbose)
            results.append((test_file, success, returncode))

    # 计算总时间
    total_time = time.time() - total_start_time

    # 输出结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print("=" * 50)

    # 统计通过数量
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    print(f"总测试文件: {total}")
    success_rate = passed / total if total > 0 else 0
    print(f"✅ 通过测试: {passed}")
    print(f"❌ 失败测试: {total - passed}")
    print(f"📊 通过率: {success_rate:.1%}")
    print()

    print("详细结果:")
    for test_file, success, returncode in results:
        status = "✅" if success else "❌"
        print(f"  {status} {test_file} (退出码: {returncode})")

    print("\n" + "=" * 50)

    if passed == total:
        print("🎉 所有测试通过！您的SurveyX环境配置正确。")
        return True
    else:
        print(f"⚠️ {total - passed} 个测试失败，请检查上述错误信息。")
        print("\n💡 常见解决方案:")
        print("  1. 检查API密钥是否正确配置")
        print("  2. 确认embed模型是否已下载")
        print("  3. 验证网络连接是否正常")
        print("  4. 运行单个测试以获取详细错误信息")
        return False

def show_help():
    """显示帮助信息"""
    print("🧪 SurveyX 测试运行器")
    print("=" * 50)
    print()
    print("用法:")
    print("  python tests/run_tests.py [选项]")
    print()
    print("选项:")
    print("  -t, --test PATTERN    指定测试模式 (默认: *)")
    print("  -v, --verbose         显示详细输出")
    print("  -p, --parallel        并行运行测试")
    print("  -l, --list            列出所有可用测试")
    print("  -h, --help           显示此帮助信息")
    print()
    print("示例:")
    print("  python tests/run_tests.py                    # 运行所有测试")
    print("  python tests/run_tests.py -t embed          # 只运行embed相关测试")
    print("  python tests/run_tests.py -v -p             # 并行运行并显示详细信息")
    print("  python tests/run_tests.py -l                # 列出所有测试文件")
    print()
    print("测试文件说明:")
    print("  test_embed_model.py    - 测试BAAI/bge-base-en-v1.5模型")
    print("  test_chat_agent.py     - 测试ChatAgent与LLM API")
    print("  test_llm_config.py     - 验证LLM配置")
    print()

def list_tests():
    """列出所有测试文件"""
    print("📋 可用的测试文件:")
    print("=" * 30)

    tests_dir = PROJECT_ROOT / "tests"

    test_files = list(tests_dir.glob("test_*.py"))
    test_files.sort()

    for i, file_path in enumerate(test_files, 1):
        file_name = file_path.name
        description = get_test_description(file_name)
        print(f"  {i}. {file_name} - {description}")

    print(f"\n总计: {len(test_files)} 个测试文件")

def get_test_description(file_name: str) -> str:
    """获取测试文件的描述"""
    descriptions = {
        "test_embed_model.py": "测试BAAI/bge-base-en-v1.5 embed模型",
        "test_chat_agent.py": "测试ChatAgent与LLM API连接",
        "test_llm_config.py": "验证LLM配置和环境设置",
        "run_tests.py": "测试运行器主脚本"
    }

    return descriptions.get(file_name, "未描述")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="SurveyX测试运行器", add_help=False)
    parser.add_argument("-t", "--test", default="*", help="测试模式 (默认: *)")
    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细输出")
    parser.add_argument("-p", "--parallel", action="store_true", help="并行运行测试")
    parser.add_argument("-l", "--list", action="store_true", help="列出所有测试文件")
    parser.add_argument("-h", "--help", action="store_true", help="显示帮助信息")

    args = parser.parse_args()

    if args.help:
        show_help()
        return 0

    if args.list:
        list_tests()
        return 0

    # 检查测试目录是否存在
    tests_dir = PROJECT_ROOT / "tests"
    if not tests_dir.exists():
        print(f"❌ 测试目录不存在: {tests_dir}")
        print("请确保您在正确的项目目录中运行此脚本。")
        return 1

    # 运行测试
    success = run_all_tests(
        test_pattern=args.test,
        verbose=args.verbose,
        parallel=args.parallel
    )

    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 运行器出现异常: {e}")
        sys.exit(1)
