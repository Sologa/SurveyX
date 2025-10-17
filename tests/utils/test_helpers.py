#!/usr/bin/env python3
"""
🧪 SurveyX测试辅助函数

提供测试过程中常用的辅助功能

作者: SurveyX Team
创建时间: 2024-01
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def setup_test_environment():
    """设置测试环境"""
    # 确保输出目录存在
    output_dir = project_root / "outputs"
    output_dir.mkdir(exist_ok=True)

    # 确保日志目录存在
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)

    return {
        "project_root": project_root,
        "output_dir": output_dir,
        "log_dir": log_dir
    }

def check_file_exists(file_path: str, description: str = "") -> bool:
    """检查文件是否存在"""
    path = Path(file_path)
    exists = path.exists()

    status = "✅ 存在" if exists else "❌ 不存在"
    desc = f" - {description}" if description else ""

    print(f"{status} {file_path}{desc}")

    return exists

def check_directory_contents(dir_path: str, expected_files: List[str] = None) -> Dict[str, Any]:
    """检查目录内容"""
    path = Path(dir_path)

    if not path.exists():
        return {"exists": False, "error": f"目录不存在: {dir_path}"}

    contents = {
        "exists": True,
        "total_files": 0,
        "directories": [],
        "files": []
    }

    for item in path.iterdir():
        if item.is_file():
            contents["files"].append(item.name)
        elif item.is_dir():
            contents["directories"].append(item.name)
        contents["total_files"] += 1

    # 检查预期文件
    if expected_files:
        missing_files = []
        for expected in expected_files:
            if expected not in contents["files"]:
                missing_files.append(expected)

        contents["missing_files"] = missing_files
        contents["expected_files_present"] = len(missing_files) == 0

    return contents

def measure_execution_time(func, *args, **kwargs) -> tuple:
    """测量函数执行时间"""
    start_time = time.time()
    try:
        result = func(*args, **kwargs)
        success = True
        error = None
    except Exception as e:
        result = None
        success = False
        error = str(e)

    execution_time = time.time() - start_time

    return {
        "result": result,
        "success": success,
        "error": error,
        "execution_time": execution_time
    }

def validate_embedding_vector(embedding: List[float], expected_dim: int = 768) -> Dict[str, Any]:
    """验证embedding向量"""
    validation = {
        "is_list": isinstance(embedding, list),
        "length": len(embedding) if isinstance(embedding, list) else 0,
        "expected_dim": expected_dim,
        "dimension_correct": False,
        "value_range": {"min": 0, "max": 0},
        "all_finite": False
    }

    if not isinstance(embedding, list):
        return validation

    validation["dimension_correct"] = len(embedding) == expected_dim

    if embedding:
        import math
        validation["value_range"]["min"] = min(embedding)
        validation["value_range"]["max"] = max(embedding)
        validation["all_finite"] = all(math.isfinite(x) for x in embedding)

    return validation

def test_api_connectivity(url: str, headers: Dict[str, str] = None, timeout: int = 10) -> Dict[str, Any]:
    """测试API连接性"""
    import requests

    result = {
        "url": url,
        "reachable": False,
        "status_code": None,
        "response_time": 0,
        "error": None
    }

    try:
        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=timeout)
        result["response_time"] = time.time() - start_time
        result["status_code"] = response.status_code
        result["reachable"] = True

    except requests.exceptions.Timeout:
        result["error"] = "连接超时"
    except requests.exceptions.ConnectionError:
        result["error"] = "连接错误"
    except requests.exceptions.RequestException as e:
        result["error"] = f"请求错误: {str(e)}"

    return result

def load_test_data(file_path: str) -> Optional[Any]:
    """加载测试数据"""
    path = Path(file_path)

    if not path.exists():
        print(f"❌ 测试数据文件不存在: {file_path}")
        return None

    try:
        if file_path.endswith('.json'):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        elif file_path.endswith('.txt'):
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            print(f"❌ 不支持的文件格式: {file_path}")
            return None
    except Exception as e:
        print(f"❌ 加载测试数据失败: {e}")
        return None

def save_test_results(results: Dict[str, Any], output_file: str):
    """保存测试结果"""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 添加时间戳
    results["timestamp"] = time.time()
    results["timestamp_str"] = time.strftime("%Y-%m-%d %H:%M:%S")

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"✅ 测试结果已保存: {output_file}")
    except Exception as e:
        print(f"❌ 保存测试结果失败: {e}")

def print_test_summary(test_results: Dict[str, Any]):
    """打印测试总结"""
    print("\n" + "="*50)
    print("📊 测试总结")
    print("="*50)

    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result.get("success", False))

    print(f"总测试数: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {total_tests - passed_tests}")
    success_rate = passed_tests / total_tests if total_tests > 0 else 0
    print(f"通过率: {success_rate:.1%}")
    for test_name, result in test_results.items():
        status = "✅" if result.get("success", False) else "❌"
        exec_time = result.get("execution_time", 0)
        print(f"  {status} {test_name}: {exec_time:.3f}秒")
        if not result.get("success", False) and "error" in result:
            print(f"      错误: {result['error']}")

    print("="*50)

    if passed_tests == total_tests:
        print("🎉 所有测试通过！")
    else:
        print(f"⚠️ {total_tests - passed_tests} 个测试失败，请检查上述错误信息。")

def create_sample_markdown_content() -> str:
    """创建示例Markdown内容用于测试"""
    return """
# Sample Research Paper

## Abstract

This is a sample research paper for testing SurveyX embed model functionality.
It contains various sections and content types.

## Introduction

Large Language Models (LLMs) have revolutionized the field of natural language processing.
This paper explores the latest developments in this area.

## Methodology

### Data Collection

We collected data from multiple sources including academic papers and web content.

### Model Architecture

The model uses transformer architecture with attention mechanisms.

## Results

Our experiments show significant improvements over baseline methods.

### Performance Metrics

- Accuracy: 95.2%
- F1-Score: 94.8%
- Precision: 96.1%

## Conclusion

This study demonstrates the effectiveness of our approach for various NLP tasks.

## References

[1] Smith, J. et al. "Advances in NLP". Journal of AI, 2023.
[2] Johnson, A. "Transformer Models". Conference on ML, 2024.
"""

def benchmark_embedding_speed(embed_agent, texts: List[str], num_runs: int = 3) -> Dict[str, Any]:
    """基准测试embedding速度"""
    import statistics

    results = {
        "num_texts": len(texts),
        "num_runs": num_runs,
        "times": [],
        "avg_time": 0,
        "min_time": 0,
        "max_time": 0,
        "texts_per_second": 0
    }

    for i in range(num_runs):
        start_time = time.time()
        embeddings = embed_agent.batch_local_embed(texts)
        end_time = time.time()

        run_time = end_time - start_time
        results["times"].append(run_time)

    if results["times"]:
        results["avg_time"] = statistics.mean(results["times"])
        results["min_time"] = min(results["times"])
        results["max_time"] = max(results["times"])
        results["texts_per_second"] = len(texts) / results["avg_time"]

    return results

if __name__ == "__main__":
    print("🧪 SurveyX测试辅助函数")
    print("这些是测试工具函数，请通过具体的测试文件调用。")

    # 演示基本功能
    env = setup_test_environment()
    print(f"项目根目录: {env['project_root']}")
    print(f"输出目录: {env['output_dir']}")

    # 检查关键文件
    check_file_exists("src/configs/config.py", "主配置文件")
    check_file_exists("requirements.txt", "依赖文件")
    check_file_exists("models/bge-base/config.json", "Embed模型配置")
