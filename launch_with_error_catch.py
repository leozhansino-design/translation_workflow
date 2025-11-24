#!/usr/bin/env python3
"""
启动包装器 - 捕获和显示错误
用于调试打包后的应用闪退问题
"""
import sys
import traceback
import os

def main():
    """主函数 - 捕获所有错误"""
    try:
        print("="*70)
        print("启动包装器 - 错误捕获模式")
        print("="*70)
        print(f"Python版本: {sys.version}")
        print(f"工作目录: {os.getcwd()}")
        print(f"脚本路径: {os.path.abspath(__file__)}")
        print()

        # 检查是否在打包环境中
        if getattr(sys, 'frozen', False):
            print("✓ 检测到打包环境")
            print(f"  可执行文件: {sys.executable}")
            if hasattr(sys, '_MEIPASS'):
                print(f"  临时目录: {sys._MEIPASS}")
        else:
            print("✓ 检测到开发环境")

        print()
        print("正在导入模块...")

        # 测试导入关键模块
        try:
            import tkinter as tk
            print("  ✓ tkinter")
        except Exception as e:
            print(f"  ✗ tkinter: {e}")
            raise

        try:
            from PIL import Image
            print("  ✓ PIL")
        except Exception as e:
            print(f"  ✗ PIL: {e}")
            raise

        try:
            from openai import OpenAI
            print("  ✓ openai")
        except Exception as e:
            print(f"  ✗ openai: {e}")
            raise

        try:
            import config
            print("  ✓ config")
        except Exception as e:
            print(f"  ✗ config: {e}")
            raise

        try:
            import resource_mgr
            print("  ✓ resource_mgr")
        except Exception as e:
            print(f"  ✗ resource_mgr: {e}")
            raise

        try:
            import prompt_manager
            print("  ✓ prompt_manager")
        except Exception as e:
            print(f"  ✗ prompt_manager: {e}")
            raise

        print()
        print("所有模块导入成功！")
        print()

        # 根据脚本名称决定启动哪个工具
        script_name = os.path.basename(__file__)

        if 'outline' in script_name.lower() or len(sys.argv) > 1 and sys.argv[1] == 'outline':
            print("启动大纲生成器...")
            import outline_generator
            outline_generator.main()
        else:
            print("启动写作工具...")
            import main_task_manager
            main_task_manager.main()

    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
        sys.exit(0)

    except Exception as e:
        print("\n" + "="*70)
        print("❌ 发生错误！")
        print("="*70)
        print(f"\n错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        print("\n完整堆栈:")
        print("-"*70)
        traceback.print_exc()
        print("-"*70)

        # 等待用户按键
        print("\n按Enter键退出...")
        try:
            input()
        except:
            pass

        sys.exit(1)

if __name__ == '__main__':
    main()
