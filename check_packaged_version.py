#!/usr/bin/env python3
"""检查打包后的应用是否包含正确的数据"""

import os
import sys
import json
import zipfile
import tempfile
import shutil

def check_onedir_package(app_dir):
    """检查--onedir模式的打包（调试版本）"""
    print(f"\n检查目录: {app_dir}")

    # 查找styles.json
    styles_path = os.path.join(app_dir, 'data', 'styles.json')
    if not os.path.exists(styles_path):
        # 尝试其他可能的位置
        for root, dirs, files in os.walk(app_dir):
            if 'styles.json' in files:
                styles_path = os.path.join(root, 'styles.json')
                break

    if os.path.exists(styles_path):
        print(f"✓ 找到 styles.json: {styles_path}")

        with open(styles_path, 'r', encoding='utf-8') as f:
            styles = json.load(f)

        genres = list(styles.keys())
        print(f"  类型总数: {len(genres)}")

        if 'Humor' in genres:
            print(f"  ✓✓✓ Humor存在！")
            return True
        else:
            print(f"  ❌ Humor不存在")
            print(f"  类型列表: {', '.join(genres)}")
            return False
    else:
        print(f"❌ 找不到 styles.json")
        return False

def check_onefile_package(exe_path):
    """检查--onefile模式的打包（正式版本）"""
    print(f"\n检查单文件: {exe_path}")
    print("⚠️  单文件模式的检查需要解包，这个比较复杂")
    print("建议: 直接运行应用，然后查看它实际加载的类型")
    return None

print("=" * 60)
print("检查打包版本")
print("=" * 60)

# 检查dist目录
if not os.path.exists('dist'):
    print("\n❌ dist/ 目录不存在")
    print("请先运行: python3 build_package.py")
    sys.exit(1)

print("\ndist/ 目录内容:")
for item in os.listdir('dist'):
    print(f"  - {item}")

# 检查OutlineGenerator
outline_dirs = [
    'dist/OutlineGenerator',
    'dist/OutlineGenerator.app/Contents/MacOS',
]

found = False
for dir_path in outline_dirs:
    if os.path.exists(dir_path):
        print(f"\n{'='*60}")
        print(f"检查 OutlineGenerator")
        print(f"{'='*60}")
        result = check_onedir_package(dir_path)
        found = True

        # 同时检查上一级目录
        parent = os.path.dirname(dir_path)
        if os.path.exists(os.path.join(parent, 'data')):
            print(f"\n也检查父目录: {parent}")
            check_onedir_package(parent)

# 检查WriterTaskManager
writer_dirs = [
    'dist/WriterTaskManager',
    'dist/WriterTaskManager.app/Contents/MacOS',
]

for dir_path in writer_dirs:
    if os.path.exists(dir_path):
        print(f"\n{'='*60}")
        print(f"检查 WriterTaskManager")
        print(f"{'='*60}")
        result = check_onedir_package(dir_path)
        found = True

        parent = os.path.dirname(dir_path)
        if os.path.exists(os.path.join(parent, 'data')):
            print(f"\n也检查父目录: {parent}")
            check_onedir_package(parent)

# 检查单文件版本
for exe_name in ['OutlineGenerator', 'WriterTaskManager']:
    exe_path = os.path.join('dist', exe_name)
    if os.path.exists(exe_path) and os.path.isfile(exe_path):
        check_onefile_package(exe_path)
        found = True

if not found:
    print("\n❌ 找不到打包的应用")
    print("请确保已经运行了: python3 build_package.py")

print("\n" + "=" * 60)
print("建议")
print("=" * 60)
print("\n如果上面显示Humor不存在，请:")
print("1. 删除dist和build文件夹:")
print("   rm -rf dist/ build/ *.spec")
print("\n2. 确认styles.json有Humor:")
print("   python3 verify_before_package.py")
print("\n3. 重新打包:")
print("   python3 build_package.py --debug")
print("\n4. 再次检查:")
print("   python3 check_packaged_version.py")
