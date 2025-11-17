"""
macOS特定功能和优化
"""

import os
import sys
import platform


def is_macos():
    """检测是否运行在macOS上"""
    return platform.system() == 'Darwin'


def is_retina_display():
    """检测是否为Retina显示屏（仅macOS）"""
    if not is_macos():
        return False
    try:
        import subprocess
        result = subprocess.run(
            ['system_profiler', 'SPDisplaysDataType'],
            capture_output=True,
            text=True
        )
        return 'Retina' in result.stdout
    except:
        return False


def is_dark_mode():
    """检测macOS是否开启深色模式"""
    if not is_macos():
        return False
    try:
        import subprocess
        result = subprocess.run(
            ['defaults', 'read', '-g', 'AppleInterfaceStyle'],
            capture_output=True,
            text=True
        )
        return 'Dark' in result.stdout
    except:
        return False


def get_default_documents_path():
    """获取macOS默认文档路径"""
    if is_macos():
        return os.path.expanduser('~/Documents/NovelTranslator')
    else:
        return os.path.expanduser('~/NovelTranslator')


def setup_macos_menu(window):
    """设置macOS原生菜单栏"""
    if not is_macos():
        return

    try:
        # macOS上，tkinter窗口会自动使用原生菜单栏
        # 创建菜单栏
        from tkinter import Menu
        menubar = Menu(window)

        # 应用菜单（macOS上会自动添加应用名称）
        app_menu = Menu(menubar, name='apple')
        menubar.add_cascade(menu=app_menu)

        app_menu.add_command(label='关于 Novel Translator', command=lambda: show_about())
        app_menu.add_separator()

        # 文件菜单
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label='文件', menu=file_menu)
        file_menu.add_command(label='退出', command=window.quit, accelerator='Command-Q')

        # 编辑菜单
        edit_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label='编辑', menu=edit_menu)
        edit_menu.add_command(label='剪切', accelerator='Command-X')
        edit_menu.add_command(label='复制', accelerator='Command-C')
        edit_menu.add_command(label='粘贴', accelerator='Command-V')

        # 窗口菜单
        window_menu = Menu(menubar, name='window', tearoff=0)
        menubar.add_cascade(label='窗口', menu=window_menu)

        # 设置菜单栏
        window.config(menu=menubar)

        return menubar

    except Exception as e:
        print(f"设置macOS菜单栏失败: {str(e)}")
        return None


def show_about():
    """显示关于对话框"""
    from tkinter import messagebox
    messagebox.showinfo(
        "关于 Novel Translator",
        "Novel Translator v1.1\n\n"
        "AI驱动的小说翻译工具\n"
        "专为macOS优化\n\n"
        "© 2025 All Rights Reserved"
    )


def send_macos_notification(title, message, subtitle=""):
    """发送macOS通知中心通知"""
    if not is_macos():
        return False

    try:
        import subprocess
        # 使用osascript发送通知
        script = f'''
        display notification "{message}" with title "{title}" subtitle "{subtitle}"
        '''
        subprocess.run(['osascript', '-e', script], check=True)
        return True
    except Exception as e:
        print(f"发送macOS通知失败: {str(e)}")
        return False


def optimize_for_retina(window):
    """优化Retina显示屏显示效果"""
    if not is_macos():
        return

    try:
        # 在macOS上，Tk 8.6.8+会自动处理Retina显示
        # 但我们可以设置一些优化参数
        window.tk.call('tk', 'scaling', 2.0)  # 2x缩放用于Retina
    except:
        pass


def set_app_icon_macos(window, icon_path=None):
    """设置macOS应用图标"""
    if not is_macos():
        return

    try:
        if icon_path and os.path.exists(icon_path):
            window.iconbitmap(icon_path)
    except Exception as e:
        print(f"设置应用图标失败: {str(e)}")


def create_app_support_directory():
    """创建macOS应用支持目录"""
    if is_macos():
        app_support = os.path.expanduser('~/Library/Application Support/NovelTranslator')
        os.makedirs(app_support, exist_ok=True)

        # 创建子目录
        os.makedirs(os.path.join(app_support, 'data'), exist_ok=True)
        os.makedirs(os.path.join(app_support, 'output'), exist_ok=True)
        os.makedirs(os.path.join(app_support, 'logs'), exist_ok=True)

        return app_support
    else:
        return os.path.expanduser('~/.noveltranslator')


def get_macos_paths():
    """获取macOS推荐的文件路径结构"""
    if is_macos():
        base = os.path.expanduser('~/Library/Application Support/NovelTranslator')
        return {
            'data': os.path.join(base, 'data'),
            'output': os.path.join(base, 'output'),
            'config': os.path.join(base, 'config'),
            'logs': os.path.join(base, 'logs'),
            'cache': os.path.expanduser('~/Library/Caches/NovelTranslator')
        }
    else:
        # Windows/Linux路径
        base = os.path.expanduser('~/.noveltranslator')
        return {
            'data': os.path.join(base, 'data'),
            'output': os.path.join(base, 'output'),
            'config': os.path.join(base, 'config'),
            'logs': os.path.join(base, 'logs'),
            'cache': os.path.join(base, 'cache')
        }


def apply_macos_theme(window):
    """应用macOS原生主题"""
    if not is_macos():
        return

    # 检测深色模式
    dark_mode = is_dark_mode()

    # macOS上tkinter会自动使用Aqua主题
    # 我们可以根据深色模式调整颜色
    if dark_mode:
        colors = {
            'bg': '#1e1e1e',
            'fg': '#ffffff',
            'button_bg': '#3a3a3a',
            'entry_bg': '#2d2d2d',
            'text_bg': '#252525'
        }
    else:
        colors = {
            'bg': '#f0f0f0',
            'fg': '#000000',
            'button_bg': '#e0e0e0',
            'entry_bg': '#ffffff',
            'text_bg': '#ffffff'
        }

    return colors


# macOS键盘快捷键映射
MACOS_SHORTCUTS = {
    'quit': 'Command-Q',
    'new': 'Command-N',
    'open': 'Command-O',
    'save': 'Command-S',
    'copy': 'Command-C',
    'paste': 'Command-V',
    'cut': 'Command-X',
    'undo': 'Command-Z',
    'redo': 'Command-Shift-Z',
    'select_all': 'Command-A',
    'find': 'Command-F',
    'preferences': 'Command-,',
}


def get_shortcut_key(action):
    """获取平台特定的快捷键"""
    if is_macos():
        return MACOS_SHORTCUTS.get(action, '')
    else:
        # Windows/Linux使用Ctrl
        return MACOS_SHORTCUTS.get(action, '').replace('Command', 'Ctrl')
