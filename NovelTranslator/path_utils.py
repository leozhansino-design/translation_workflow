"""
路径工具 - 处理打包后的资源路径问题
"""

import os
import sys


def get_resource_path(relative_path: str) -> str:
    """
    获取资源文件的绝对路径

    开发模式：返回相对于脚本的路径
    打包模式：返回相对于.app bundle的路径

    Args:
        relative_path: 相对路径（如 "data/config.json"）

    Returns:
        绝对路径
    """
    try:
        # PyInstaller打包后的路径
        base_path = sys._MEIPASS
    except AttributeError:
        # 开发模式：使用脚本所在目录
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)


def get_data_dir() -> str:
    """
    获取data目录的绝对路径

    Returns:
        data目录的绝对路径
    """
    data_path = get_resource_path("data")

    # 确保data目录存在
    os.makedirs(data_path, exist_ok=True)

    return data_path


def get_output_dir() -> str:
    """
    获取output目录的绝对路径

    打包后使用用户文档目录，避免写入.app bundle内部

    Returns:
        output目录的绝对路径
    """
    try:
        # 检查是否在.app bundle中运行
        _ = sys._MEIPASS
        # 打包模式：使用用户文档目录
        output_path = os.path.expanduser("~/Documents/NovelTranslator/output")
    except AttributeError:
        # 开发模式：使用当前目录的output
        output_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "output"
        )

    # 确保output目录存在
    os.makedirs(output_path, exist_ok=True)

    return output_path


def is_packaged() -> bool:
    """
    检查是否在打包模式下运行

    Returns:
        True if packaged, False if development mode
    """
    return hasattr(sys, '_MEIPASS')


def get_app_dir() -> str:
    """
    获取应用程序目录

    Returns:
        应用程序目录的绝对路径
    """
    if is_packaged():
        return sys._MEIPASS
    else:
        return os.path.dirname(os.path.abspath(__file__))
