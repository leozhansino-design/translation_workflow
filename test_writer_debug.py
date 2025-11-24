#!/usr/bin/env python3
"""
调试脚本 - 测试小说写作功能
用于查看详细的错误信息
"""
import sys
import os
import json
import traceback
from datetime import datetime

print("=" * 70)
print("Chapter Writer 调试测试")
print("=" * 70)

# 测试导入
print("\n1. 测试模块导入...")
try:
    from writer_worker_v2 import WriterWorker
    print("   ✓ writer_worker_v2 导入成功")
except Exception as e:
    print(f"   ✗ writer_worker_v2 导入失败: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    from universal_api import UniversalAPIClient
    print("   ✓ universal_api 导入成功")
except Exception as e:
    print(f"   ✗ universal_api 导入失败: {e}")
    traceback.print_exc()

try:
    from prompt_manager import PromptManager
    print("   ✓ prompt_manager 导入成功")
except Exception as e:
    print(f"   ✗ prompt_manager 导入失败: {e}")
    traceback.print_exc()

# 测试PIL
print("\n2. 测试PIL/Pillow...")
try:
    from PIL import Image
    print(f"   ✓ PIL 导入成功")

    # 测试Resampling兼容性
    try:
        resample = Image.Resampling.LANCZOS
        print(f"   ✓ 使用新版 Pillow (Image.Resampling.LANCZOS)")
    except AttributeError:
        resample = Image.LANCZOS
        print(f"   ✓ 使用旧版 Pillow (Image.LANCZOS)")

except ImportError as e:
    print(f"   ✗ PIL 未安装: {e}")

# 测试路径处理
print("\n3. 测试路径处理...")
task_id = "test_123"
progress_file = os.path.join('tasks', task_id, 'progress.json')
print(f"   Progress file: {progress_file}")
print(f"   Platform: {sys.platform}")

# 测试创建目录
try:
    test_dir = os.path.join('tasks', 'test_debug')
    os.makedirs(test_dir, exist_ok=True)
    print(f"   ✓ 目录创建成功: {test_dir}")

    # 测试写入文件
    test_file = os.path.join(test_dir, 'test.json')
    with open(test_file, 'w') as f:
        json.dump({'test': 'ok'}, f)
    print(f"   ✓ 文件写入成功: {test_file}")

    # 清理
    os.remove(test_file)
    os.rmdir(test_dir)
    print(f"   ✓ 清理成功")
except Exception as e:
    print(f"   ✗ 文件操作失败: {e}")
    traceback.print_exc()

# 测试配置文件
print("\n4. 测试配置...")
test_config = {
    'api_key': 'test_key',
    'base_url': 'https://yunwuapi.com',
    'model': 'gpt-4',
    'temperature': 0.8,
    'max_tokens': 20000,
    'outline_file': 'test.txt',
    'project_folder': './output',
    'start_chapter': 1,
    'end_chapter': 5,
    'batch_size': 3
}

config_dir = os.path.join('tasks', 'test_config')
config_file = os.path.join(config_dir, 'config.json')

try:
    os.makedirs(config_dir, exist_ok=True)
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(test_config, f, indent=2)
    print(f"   ✓ 配置文件创建成功: {config_file}")

    # 测试初始化 Worker
    print("\n5. 测试初始化 WriterWorker...")
    worker = WriterWorker('test_config', config_file)
    print(f"   ✓ WriterWorker 初始化成功")
    print(f"   - Task ID: {worker.task_id}")
    print(f"   - Progress file: {worker.progress_file}")

    # 清理
    os.remove(config_file)
    os.rmdir(config_dir)
    print(f"   ✓ 清理成功")

except Exception as e:
    print(f"   ✗ Worker 初始化失败: {e}")
    traceback.print_exc()

print("\n" + "=" * 70)
print("调试测试完成")
print("=" * 70)
print("\n如果以上测试都通过，请提供以下信息:")
print("1. Python版本:", sys.version)
print("2. 平台:", sys.platform)
print("3. 当前目录:", os.getcwd())
print("\n如果有错误，请将上面的完整输出发给我")
