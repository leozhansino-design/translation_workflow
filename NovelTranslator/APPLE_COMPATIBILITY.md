# Apple Platform Compatibility (iOS/macOS)

## 🍎 平台适配说明

本分支专门用于iOS和macOS平台的适配。

---

## ✅ 当前已兼容的部分

### 1. 文件路径处理
- ✅ 使用`os.path.join()`而非硬编码分隔符
- ✅ 使用`os.makedirs(exist_ok=True)`创建目录
- ✅ 使用相对路径`data/`, `output/`

### 2. 跨平台依赖
- ✅ tkinter（macOS系统自带）
- ✅ OpenAI SDK（跨平台）
- ✅ pandas, openpyxl（跨平台）
- ✅ aiohttp（跨平台）

### 3. 异步IO
- ✅ asyncio（Python标准库，跨平台）
- ✅ AsyncOpenAI（跨平台）

---

## 🔧 macOS特殊适配

### 1. GUI适配

#### tkinter在macOS上的特殊处理
```python
import platform

if platform.system() == 'Darwin':  # macOS
    # macOS特殊设置
    root.createcommand('tk::mac::Quit', self.on_quit)
    # 菜单栏适配
    menubar = tk.Menu(root)
    root.config(menu=menubar)
```

#### 文件对话框
macOS的文件对话框默认支持，无需特殊处理。

#### 字体
```python
# macOS默认字体
if platform.system() == 'Darwin':
    default_font = ("SF Pro", 11)
else:
    default_font = ("Arial", 10)
```

### 2. 权限管理

#### 文件访问权限
macOS的沙盒环境可能限制文件访问。

**解决方案**：
- 使用`filedialog`让用户主动选择文件/文件夹
- 避免直接访问系统目录
- 使用用户目录：
  ```python
  import os
  from pathlib import Path

  # macOS用户目录
  home = Path.home()
  data_dir = home / "Documents" / "NovelTranslator"
  data_dir.mkdir(parents=True, exist_ok=True)
  ```

#### 网络访问权限
- ✅ OpenAI API调用需要网络权限
- ✅ AsyncOpenAI使用aiohttp（自动处理）

### 3. 打包为.app

#### 使用PyInstaller
```bash
pyinstaller --name NovelTranslator \
    --windowed \
    --icon=icon.icns \
    --add-data "data:data" \
    --osx-bundle-identifier com.noveltranslator.app \
    main.py
```

#### Info.plist配置
```xml
<key>NSAppleEventsUsageDescription</key>
<string>需要访问文件系统以翻译小说</string>
<key>NSNetworkVolumesUsageDescription</key>
<string>需要网络访问以调用翻译API</string>
```

---

## 🍏 iOS特殊适配

### 1. GUI框架替换

**问题**：iOS不支持tkinter

**解决方案**：使用Kivy或BeeWare
```python
# 使用Kivy替代tkinter
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
```

### 2. 文件访问

#### 使用iOS文件选择器
```python
from kivy.utils import platform

if platform == 'ios':
    from jnius import autoclass
    Intent = autoclass('android.content.Intent')
    # 使用iOS文件选择器
```

### 3. 后台任务

iOS限制后台任务执行。

**解决方案**：
- 使用`UIApplication.beginBackgroundTask()`
- 或确保任务在前台完成

---

## 📝 代码适配清单

### 当前分支需要的修改

#### 1. main.py
```python
import platform

class TranslatorApp:
    def __init__(self):
        self.window = tk.Tk()

        # macOS特殊设置
        if platform.system() == 'Darwin':
            self.setup_macos_menu()

        # 数据目录适配
        self.data_dir = self.get_data_directory()

    def get_data_directory(self):
        """获取跨平台数据目录"""
        if platform.system() == 'Darwin':
            # macOS: ~/Documents/NovelTranslator
            from pathlib import Path
            data_dir = Path.home() / "Documents" / "NovelTranslator" / "data"
        else:
            # Windows/Linux: ./data
            data_dir = Path("data")

        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    def setup_macos_menu(self):
        """设置macOS菜单栏"""
        menubar = tk.Menu(self.window)

        # 应用菜单
        app_menu = tk.Menu(menubar, name='apple')
        menubar.add_cascade(menu=app_menu)
        app_menu.add_command(label='About Novel Translator')
        app_menu.add_separator()

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Add Files", command=self.add_files)
        file_menu.add_command(label="Export Excel", command=self.export_to_excel)

        self.window.config(menu=menubar)
```

#### 2. config.py
```python
import platform
from pathlib import Path

class ConfigManager:
    def __init__(self):
        # 跨平台配置目录
        if platform.system() == 'Darwin':
            self.config_dir = Path.home() / "Documents" / "NovelTranslator" / "data"
        else:
            self.config_dir = Path("data")

        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "config.json"
```

#### 3. translator.py
```python
import platform

class Translator:
    def __init__(self, config_manager, resource_manager, output_dir: str = None):
        # 跨平台输出目录
        if output_dir is None:
            if platform.system() == 'Darwin':
                output_dir = str(Path.home() / "Documents" / "NovelTranslator" / "output")
            else:
                output_dir = "output"

        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
```

---

## 🔒 沙盒环境处理

### macOS沙盒
```xml
<!-- Entitlements.plist -->
<key>com.apple.security.files.user-selected.read-write</key>
<true/>
<key>com.apple.security.network.client</key>
<true/>
```

### iOS沙盒
- 使用Document Picker
- 使用URLBookmark保存文件访问权限

---

## 📦 打包脚本

### macOS .app打包
```bash
#!/bin/bash
# build_macos.sh

pyinstaller \
    --name "Novel Translator" \
    --windowed \
    --icon=resources/icon.icns \
    --add-data "data:data" \
    --osx-bundle-identifier "com.noveltranslator.app" \
    --target-arch universal2 \
    main.py

# 签名（可选）
codesign --force --deep --sign "Developer ID Application: Your Name" \
    "dist/Novel Translator.app"
```

### iOS .ipa打包
需要使用Xcode和BeeWare/Kivy框架。

---

## 🧪 测试清单

### macOS测试
- [ ] 应用启动正常
- [ ] 文件对话框工作正常
- [ ] 菜单栏显示正确
- [ ] 数据保存到~/Documents/NovelTranslator
- [ ] API调用成功
- [ ] 异步并发工作正常
- [ ] Excel导出正常
- [ ] 历史记录显示正常

### iOS测试
- [ ] GUI框架替换完成（Kivy/BeeWare）
- [ ] 文件选择器工作
- [ ] 后台任务不被杀掉
- [ ] API调用成功

---

## 📋 已完成的适配

1. ✅ 使用`os.path`而非硬编码路径
2. ✅ 使用`os.makedirs(exist_ok=True)`
3. ✅ 异步IO使用aiohttp（跨平台）
4. ✅ 所有依赖都是跨平台的

---

## 🚧 待完成的适配

### macOS
1. [ ] 添加macOS菜单栏
2. [ ] 数据目录改为~/Documents/NovelTranslator
3. [ ] 添加Info.plist权限说明
4. [ ] 创建PyInstaller打包脚本
5. [ ] 测试沙盒环境

### iOS
1. [ ] 替换tkinter为Kivy/BeeWare
2. [ ] 实现iOS文件选择器
3. [ ] 处理后台任务限制
4. [ ] 创建Xcode项目
5. [ ] 测试真机运行

---

## 💡 建议

### 优先级

#### 高优先级（macOS）
- macOS菜单栏
- 数据目录适配
- PyInstaller打包

#### 中优先级（iOS）
- GUI框架替换研究
- 文件访问权限

#### 低优先级
- App Store上架准备
- 代码签名

---

## 📚 参考资料

### macOS
- [PyInstaller macOS Guide](https://pyinstaller.org/en/stable/usage.html#macos-specific-options)
- [tkinter on macOS](https://docs.python.org/3/library/tkinter.html)

### iOS
- [Kivy Documentation](https://kivy.org/doc/stable/)
- [BeeWare](https://beeware.org/)
- [Python on iOS](https://github.com/beeware/Python-iOS-support)

---

**分支**: apple-compatible
**日期**: 2025-11-16
**状态**: 准备开始适配
