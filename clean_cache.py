#!/usr/bin/env python3
"""
清理应用缓存脚本
解决打包后 prompts 不更新的问题
"""

import os
import sys
import shutil
from pathlib import Path

def get_app_support_dir():
    """获取应用支持目录路径"""
    app_name = "OutlineGenerator"

    if sys.platform == 'darwin':
        # macOS
        return Path.home() / 'Library' / 'Application Support' / app_name
    elif sys.platform == 'win32':
        # Windows
        return Path(os.getenv('APPDATA')) / app_name
    else:
        # Linux
        return Path.home() / f'.{app_name}'

def main():
    print("=" * 60)
    print("  清理 OutlineGenerator 应用缓存")
    print("=" * 60)
    print()

    app_support_dir = get_app_support_dir()

    print(f"📁 应用支持目录位置：")
    print(f"   {app_support_dir}")
    print()

    if app_support_dir.exists():
        print("📋 当前缓存的文件：")
        data_dir = app_support_dir / 'data'
        if data_dir.exists():
            for file in data_dir.iterdir():
                size = file.stat().st_size / (1024 * 1024)  # MB
                print(f"   - {file.name}: {size:.2f} MB")
        else:
            print("   (无 data 目录)")
        print()

        response = input("是否删除整个应用支持目录? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            try:
                shutil.rmtree(app_support_dir)
                print("✅ 已删除应用支持目录")
                print()
                print("下次启动应用时会重新创建，使用最新的 prompts.json 和配置")
            except Exception as e:
                print(f"❌ 删除失败: {e}")
        else:
            print("❌ 取消删除")
    else:
        print("ℹ️  应用支持目录不存在，无需清理")

    print()
    print("=" * 60)
    print("  其他清理建议：")
    print("=" * 60)
    print("1. 删除旧的 .app 或 .exe 文件")
    print("2. 清理 Python 缓存：")
    print("   rm -rf __pycache__ build dist")
    print("3. 清理 .pyc 文件：")
    print("   find . -name '*.pyc' -delete")
    print("4. 重新打包：")
    print("   pyinstaller --clean your_spec_file.spec")
    print()
    print("完成！")

if __name__ == '__main__':
    main()
