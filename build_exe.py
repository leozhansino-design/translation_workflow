"""
打包脚本 - 将应用打包成独立的exe文件
"""
import PyInstaller.__main__
import os
import sys


def build():
    """构建exe文件"""

    # PyInstaller参数
    args = [
        'main.py',  # 主程序
        '--onefile',  # 打包成单个文件
        '--windowed',  # 窗口模式（不显示控制台）
        '--name=NovelTranslator',  # 应用名称
        '--add-data=data;data',  # 添加data文件夹
        '--hidden-import=openai',  # 隐式导入
        '--hidden-import=tiktoken',  # OpenAI依赖
        '--hidden-import=tiktoken_ext',
        '--hidden-import=tiktoken_ext.openai_public',
        '--clean',  # 清理临时文件
    ]

    # 如果有图标文件，添加图标
    if os.path.exists('icon.ico'):
        args.append('--icon=icon.ico')

    print("开始打包...")
    print("参数:", ' '.join(args))

    # 运行PyInstaller
    PyInstaller.__main__.run(args)

    print("\n打包完成！")
    print("生成的文件在: dist/NovelTranslator.exe")
    print("\n使用说明:")
    print("1. 将 dist/NovelTranslator.exe 复制到任意位置")
    print("2. 确保同目录下有 data 文件夹（包含配置文件）")
    print("3. 双击运行即可")


if __name__ == '__main__':
    build()
