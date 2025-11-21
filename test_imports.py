#!/usr/bin/env python3
"""
测试所有依赖模块是否可以正常导入
"""
import sys

def test_imports():
    print("测试依赖导入...\n")
    
    modules_to_test = [
        ('prompt_manager', 'PromptManager'),
        ('resource_mgr', 'ResourceManager'),
        ('utils', 'extract_genre_from_filename'),
        ('config', 'config'),
        ('outline_worker', 'OutlineWorker'),
        ('writer_worker', 'WriterWorker'),
    ]
    
    failed = []
    
    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name)
            if hasattr(module, class_name):
                print(f"✅ {module_name}.{class_name}")
            else:
                print(f"⚠️  {module_name} 导入成功，但找不到 {class_name}")
        except ImportError as e:
            print(f"❌ {module_name}: {e}")
            failed.append(module_name)
    
    # 测试数据文件
    import os
    data_files = ['data/styles.json', 'data/names_1.json']
    print("\n测试数据文件...\n")
    for file_path in data_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} 不存在")
            failed.append(file_path)
    
    print("\n" + "="*60)
    if failed:
        print(f"❌ 有 {len(failed)} 个依赖缺失")
        return False
    else:
        print("✅ 所有依赖都已就绪，可以运行打包！")
        print("\n运行打包命令：")
        print("  python build_package.py")
        return True

if __name__ == '__main__':
    success = test_imports()
    sys.exit(0 if success else 1)
