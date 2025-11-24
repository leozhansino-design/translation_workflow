#!/usr/bin/env python3
"""
诊断 Chapter Writer 失败原因
运行这个脚本来模拟启动任务的完整流程，查看在哪一步失败
"""
import os
import sys
import json
import traceback
from datetime import datetime

def test_imports():
    """测试所有必要的模块导入"""
    print("=" * 70)
    print("1. 测试模块导入")
    print("=" * 70)

    modules = [
        ('os', 'os'),
        ('json', 'json'),
        ('tkinter', 'tkinter'),
        ('PIL', 'PIL'),
        ('openai', 'openai'),
        ('config', 'config'),
        ('resource_mgr', 'resource_mgr'),
        ('prompt_manager', 'prompt_manager'),
        ('universal_api', 'universal_api'),
        ('utils', 'utils'),
        ('writer_worker_v2', 'writer_worker_v2'),
    ]

    all_ok = True
    for name, module in modules:
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except Exception as e:
            print(f"  ✗ {name}: {e}")
            all_ok = False

    return all_ok

def test_config_creation():
    """测试创建任务配置"""
    print("\n" + "=" * 70)
    print("2. 测试创建任务配置")
    print("=" * 70)

    try:
        # 模拟配置
        test_config = {
            'api_key': 'test_key_12345',
            'base_url': 'https://yunwuapi.com',
            'model': 'gpt-4',
            'temperature': 0.8,
            'max_tokens': 20000,
            'outline_file': '/fake/path/outline.txt',
            'project_folder': '/fake/path/project',
            'start_chapter': 1,
            'end_chapter': 5,
            'batch_size': 3,
            'target_chapters': 5
        }

        # 创建tasks目录
        task_id = f'test_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        task_dir = os.path.join('tasks', task_id)
        os.makedirs(task_dir, exist_ok=True)
        print(f"  ✓ 创建任务目录: {task_dir}")

        # 写入配置文件
        config_file = os.path.join(task_dir, 'config.json')
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(test_config, f, indent=2, ensure_ascii=False)
        print(f"  ✓ 创建配置文件: {config_file}")

        # 读取配置文件验证
        with open(config_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        print(f"  ✓ 读取配置文件成功")

        # 清理
        os.remove(config_file)
        os.rmdir(task_dir)
        print(f"  ✓ 清理测试文件")

        return True, task_id, config_file

    except Exception as e:
        print(f"  ✗ 配置创建失败: {e}")
        traceback.print_exc()
        return False, None, None

def test_worker_initialization():
    """测试初始化 WriterWorker"""
    print("\n" + "=" * 70)
    print("3. 测试初始化 WriterWorker")
    print("=" * 70)

    try:
        from writer_worker_v2 import WriterWorker

        # 创建测试配置
        task_id = f'test_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        task_dir = os.path.join('tasks', task_id)
        os.makedirs(task_dir, exist_ok=True)

        test_config = {
            'api_key': 'sk-test-key-12345678901234567890',
            'base_url': 'https://yunwuapi.com',
            'model': 'gpt-4',
            'temperature': 0.8,
            'max_tokens': 20000,
            'outline_file': os.path.abspath('test_outline.txt'),
            'project_folder': os.path.abspath('test_project'),
            'start_chapter': 1,
            'end_chapter': 5,
            'batch_size': 3,
            'target_chapters': 5
        }

        config_file = os.path.join(task_dir, 'config.json')
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(test_config, f, indent=2, ensure_ascii=False)

        print(f"  • 任务ID: {task_id}")
        print(f"  • 配置文件: {config_file}")

        # 尝试初始化 Worker
        print(f"  • 初始化 WriterWorker...")
        worker = WriterWorker(task_id, config_file)
        print(f"  ✓ WriterWorker 初始化成功")
        print(f"  • Task ID: {worker.task_id}")
        print(f"  • Progress file: {worker.progress_file}")

        # 清理
        os.remove(config_file)
        os.rmdir(task_dir)

        return True

    except Exception as e:
        print(f"  ✗ Worker 初始化失败: {e}")
        print("\n完整错误堆栈:")
        traceback.print_exc()
        return False

def test_path_handling():
    """测试路径处理"""
    print("\n" + "=" * 70)
    print("4. 测试路径处理")
    print("=" * 70)

    try:
        # 测试 os.path.join
        task_id = "test_123"
        progress_file = os.path.join('tasks', task_id, 'progress.json')
        print(f"  • Progress file: {progress_file}")
        print(f"  • Platform: {sys.platform}")

        # 测试目录创建
        test_dir = os.path.join('tasks', 'test_path')
        os.makedirs(test_dir, exist_ok=True)
        print(f"  ✓ 目录创建成功: {test_dir}")

        # 测试文件写入
        test_file = os.path.join(test_dir, 'test.json')
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump({'test': 'ok'}, f)
        print(f"  ✓ 文件写入成功: {test_file}")

        # 测试文件读取
        with open(test_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"  ✓ 文件读取成功: {data}")

        # 清理
        os.remove(test_file)
        os.rmdir(test_dir)
        print(f"  ✓ 清理成功")

        return True

    except Exception as e:
        print(f"  ✗ 路径处理失败: {e}")
        traceback.print_exc()
        return False

def test_resource_files():
    """测试资源文件访问"""
    print("\n" + "=" * 70)
    print("5. 测试资源文件访问")
    print("=" * 70)

    try:
        from resource_mgr import ResourceManager

        print(f"  • 初始化 ResourceManager...")
        mgr = ResourceManager()
        print(f"  ✓ ResourceManager 初始化成功")

        # 测试获取类型
        genres = mgr.get_available_genres()
        print(f"  • 可用类型 ({len(genres)}): {', '.join(genres[:5])}...")

        # 测试获取风格
        if genres:
            test_genre = genres[0]
            style = mgr.get_random_style(test_genre)
            print(f"  ✓ 获取风格成功 ({test_genre})")

        return True

    except Exception as e:
        print(f"  ✗ 资源文件访问失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主测试流程"""
    print("=" * 70)
    print("Chapter Writer 故障诊断")
    print("=" * 70)
    print(f"Python版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")
    print(f"平台: {sys.platform}")
    print()

    results = []

    # 测试1: 模块导入
    results.append(("模块导入", test_imports()))

    # 测试2: 配置创建
    result, task_id, config_file = test_config_creation()
    results.append(("配置创建", result))

    # 测试3: Worker初始化
    results.append(("Worker初始化", test_worker_initialization()))

    # 测试4: 路径处理
    results.append(("路径处理", test_path_handling()))

    # 测试5: 资源文件
    results.append(("资源文件", test_resource_files()))

    # 总结
    print("\n" + "=" * 70)
    print("诊断总结")
    print("=" * 70)

    for name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"  {status}: {name}")

    all_passed = all(r[1] for r in results)

    if all_passed:
        print("\n✅ 所有测试通过！")
        print("\n如果任务仍然失败，请提供以下信息：")
        print("  1. 选择的大纲文件夹路径")
        print("  2. API Key 前几位 (sk-xxxx...)")
        print("  3. 使用的模型名称")
        print("  4. 点击启动后GUI上显示的错误信息")
    else:
        print("\n❌ 发现问题！请将上面的完整输出发给我。")

    print("\n" + "=" * 70)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ 诊断脚本本身出错: {e}")
        traceback.print_exc()
