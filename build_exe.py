"""
打包脚本 - 将应用打包成独立的可执行文件（支持Windows和Mac）
"""
import PyInstaller.__main__
import os
import sys
import platform


def build():
    """构建可执行文件"""

    # 检测操作系统
    is_windows = platform.system() == 'Windows'
    is_mac = platform.system() == 'Darwin'

    # 根据操作系统设置data分隔符
    if is_windows:
        data_separator = ';'
    else:
        data_separator = ':'

    # PyInstaller参数
    args = [
        'main.py',  # 主程序
        '--onefile',  # 打包成单个文件
        '--windowed',  # 窗口模式（不显示控制台）
        '--name=NovelTranslator',  # 应用名称
        f'--add-data=data{data_separator}data',  # 添加data文件夹
        '--hidden-import=openai',  # 隐式导入
        '--hidden-import=tiktoken',  # OpenAI依赖
        '--hidden-import=tiktoken_ext',
        '--hidden-import=tiktoken_ext.openai_public',
        '--clean',  # 清理临时文件
    ]

    # 如果有图标文件，添加图标
    if is_windows and os.path.exists('icon.ico'):
        args.append('--icon=icon.ico')
    elif is_mac and os.path.exists('icon.icns'):
        args.append('--icon=icon.icns')

    print("="*60)
    print("开始打包...")
    print(f"操作系统: {platform.system()}")
    print("参数:", ' '.join(args))
    print("="*60)

    # 运行PyInstaller
    PyInstaller.__main__.run(args)

    print("\n" + "="*60)
    print("✅ 打包完成！")
    print("="*60)

    if is_windows:
        print("生成的文件在: dist/NovelTranslator.exe")
        print("\n使用说明:")
        print("1. 将 dist/NovelTranslator.exe 复制到任意位置")
        print("2. 运行时会自动在同目录创建 data 文件夹")
        print("3. 双击 NovelTranslator.exe 运行即可")
    elif is_mac:
        print("生成的文件在: dist/NovelTranslator.app")
        print("\n使用说明:")
        print("1. 将 dist/NovelTranslator.app 复制到应用程序文件夹")
        print("2. 运行时会自动创建所需的 data 文件夹")
        print("3. 双击 NovelTranslator.app 运行即可")
    else:
        print("生成的文件在: dist/NovelTranslator")
        print("\n使用说明:")
        print("1. 将 dist/NovelTranslator 复制到任意位置")
        print("2. 添加执行权限: chmod +x NovelTranslator")
        print("3. 运行: ./NovelTranslator")


if __name__ == '__main__':
    build()
