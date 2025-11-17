# Apple分支与主分支的区别

## 分支说明

- **主分支**: `claude/novel-translator-app-01LUr12oHGeZAT97QzmkcziY`
  - 跨平台版本（Windows/Linux/macOS通用）
  - 标准功能实现

- **Apple分支**: `claude/apple-compatible-01LUr12oHGeZAT97QzmkcziY`
  - macOS专门优化版本
  - 包含macOS特有功能

---

## 主要差异

### 1. macOS特定功能模块 (macos_utils.py)

Apple分支新增 `macos_utils.py` 模块，提供：

```python
✅ is_macos()                    # macOS平台检测
✅ is_retina_display()           # Retina显示屏检测
✅ is_dark_mode()                # 深色模式检测
✅ setup_macos_menu()            # 原生菜单栏
✅ send_macos_notification()     # 通知中心集成
✅ optimize_for_retina()         # Retina优化
✅ apply_macos_theme()           # 原生主题适配
✅ get_macos_paths()             # macOS标准路径
```

### 2. main.py 差异

#### 导入部分
**主分支:**
```python
from config import ConfigManager
from resource_mgr import ResourceManager
from translator import Translator
```

**Apple分支:**
```python
from config import ConfigManager
from resource_mgr import ResourceManager
from translator import Translator

# 新增macOS功能
from macos_utils import (
    is_macos, setup_macos_menu, send_macos_notification,
    optimize_for_retina, apply_macos_theme, get_macos_paths
)
```

#### 窗口初始化
**主分支:**
```python
def __init__(self):
    self.window = tk.Tk()
    self.window.title("小说翻译工具 v1.1")
    self.window.geometry("900x900")
```

**Apple分支:**
```python
def __init__(self):
    self.window = tk.Tk()

    # macOS特定优化
    if MACOS_AVAILABLE and is_macos():
        self.window.title("Novel Translator")  # macOS使用英文标题
        optimize_for_retina(self.window)       # Retina优化
        setup_macos_menu(self.window)          # 原生菜单栏
    else:
        self.window.title("小说翻译工具 v1.1")
```

#### 翻译完成通知
**主分支:**
```python
def translation_complete(self):
    # 保存Excel
    self.save_to_excel()

    # 显示对话框
    messagebox.showinfo("完成", "翻译完成！...")
```

**Apple分支:**
```python
def translation_complete(self):
    # 保存Excel
    self.save_to_excel()

    # macOS通知中心 (新增)
    if MACOS_AVAILABLE and is_macos():
        send_macos_notification(
            "Novel Translator",
            f"翻译完成！共{self.completed_count}本小说",
            f"总成本: ${total_cost:.2f}"
        )

    # 显示对话框
    messagebox.showinfo("完成", "翻译完成！...")
```

### 3. 打包脚本差异

#### 主分支: build.bat (Windows)
```batch
pyinstaller --name="NovelTranslator" ^
    --windowed ^
    --onefile ^
    main.py
```

#### Apple分支: build_macos.sh (macOS)
```bash
pyinstaller \
    --name="NovelTranslator" \
    --windowed \
    --onefile \
    --add-data "data:data" \
    --hidden-import=tkinter \
    --hidden-import=openai \
    --hidden-import=aiohttp \
    main.py
```

---

## 功能对比表

| 功能 | 主分支 | Apple分支 |
|------|--------|-----------|
| 基础翻译功能 | ✅ | ✅ |
| Tags功能 | ✅ | ✅ |
| 异步并发 | ✅ | ✅ |
| Default Prompt编辑器 | ✅ | ✅ |
| **macOS原生菜单栏** | ❌ | ✅ |
| **Retina屏幕优化** | ❌ | ✅ |
| **通知中心集成** | ❌ | ✅ |
| **深色模式检测** | ❌ | ✅ |
| **macOS标准路径** | ❌ | ✅ |
| **macOS键盘快捷键** | ❌ | ✅ |

---

## macOS原生体验详解

### 1. 原生菜单栏
Apple分支在macOS上显示标准的应用菜单：

```
Novel Translator    文件    编辑    窗口
    ├─ 关于 Novel Translator
    ├─ ──────────
    └─ 退出 (⌘Q)
```

### 2. Retina显示优化
- 自动检测Retina显示屏
- 2x缩放渲染
- 清晰的界面元素

### 3. 通知中心集成
翻译完成时，macOS通知中心会弹出通知：

```
┌────────────────────────────┐
│ Novel Translator           │
│ 翻译完成！共5本小说，耗时120秒│
│ 总成本: $1.25              │
└────────────────────────────┘
```

### 4. macOS标准路径
Apple分支使用macOS推荐的文件路径：

```
主分支:
~/NovelTranslator/data
~/NovelTranslator/output

Apple分支:
~/Library/Application Support/NovelTranslator/data
~/Library/Application Support/NovelTranslator/output
~/Library/Caches/NovelTranslator
```

---

## 使用建议

### Windows用户
使用**主分支**，Windows上功能完整且稳定。

### Linux用户
使用**主分支**，跨平台兼容性最好。

### macOS用户
推荐使用**Apple分支**，获得最佳原生体验：
- 更符合macOS界面规范
- Retina屏幕显示更清晰
- 通知中心集成
- Command键快捷键支持

---

## 如何切换分支

### 切换到主分支
```bash
git checkout claude/novel-translator-app-01LUr12oHGeZAT97QzmkcziY
```

### 切换到Apple分支
```bash
git checkout claude/apple-compatible-01LUr12oHGeZAT97QzmkcziY
```

---

## 未来计划

### Apple分支后续优化
- [ ] Touch Bar支持（MacBook Pro）
- [ ] 深色模式自动切换
- [ ] macOS Finder集成（右键翻译）
- [ ] Apple Silicon (M1/M2) 特殊优化
- [ ] iCloud Drive集成

### 主分支后续优化
- [ ] Windows 11原生UI
- [ ] Linux Wayland支持
- [ ] 跨平台配置同步

---

## 技术细节

### 平台检测代码
```python
import platform

def is_macos():
    return platform.system() == 'Darwin'
```

### 条件功能加载
```python
if MACOS_AVAILABLE and is_macos():
    # 使用macOS特定功能
    setup_macos_menu(self.window)
else:
    # 使用标准功能
    pass
```

### 优雅降级
如果在非macOS系统上运行Apple分支：
- 自动禁用macOS特定功能
- 回退到标准tkinter界面
- 不会报错或崩溃

---

## 总结

**主分支**：跨平台通用版，所有平台均可使用
**Apple分支**：macOS专属优化版，提供最佳macOS体验

两个分支的核心功能完全相同，区别仅在于macOS平台的用户体验优化。
