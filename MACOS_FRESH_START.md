# macOS 从头开始完整指南

## 🗑️ 第一步：完全清理旧版本

打开终端，执行以下命令：

```bash
# 1. 删除旧的.app应用
rm -rf /Applications/NovelTranslator.app

# 2. 删除旧的项目文件夹
rm -rf ~/Documents/translation_workflow

# 3. 删除可能的缓存
rm -rf ~/Library/Caches/NovelTranslator
rm -rf ~/Library/Application\ Support/NovelTranslator

# 4. 清理PyInstaller缓存（如果之前安装过）
rm -rf ~/.pyinstaller_cache
```

---

## 📥 第二步：重新安装环境

```bash
# 1. 确认已安装Homebrew（如果没有，先安装）
brew --version

# 如果没有Homebrew，运行这个：
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. 安装或更新Python
brew install python@3.11

# 3. 验证Python版本
python3 --version
# 应该显示：Python 3.11.x
```

---

## 📦 第三步：重新下载项目

```bash
# 1. 进入文档目录
cd ~/Documents

# 2. 克隆项目
git clone <您的仓库URL> translation_workflow

# 3. 进入项目
cd translation_workflow

# 4. 切换到主分支（或Apple分支）
# 主分支（跨平台）：
git checkout claude/novel-translator-app-01LUr12oHGeZAT97QzmkcziY

# 或 Apple分支（macOS优化）：
# git checkout claude/apple-compatible-01LUr12oHGeZAT97QzmkcziY

# 5. 确保是最新代码
git pull
```

---

## 🔧 第四步：创建虚拟环境和安装依赖

```bash
# 1. 创建虚拟环境
python3 -m venv venv

# 2. 激活虚拟环境
source venv/bin/activate

# 确认虚拟环境已激活（提示符前应该有 (venv)）

# 3. 升级pip
pip install --upgrade pip

# 4. 安装所有依赖
pip install -r NovelTranslator/requirements.txt

# 5. 额外安装PyInstaller（用于打包）
pip install pyinstaller

# 6. 验证安装
pip list | grep -E "openai|pandas|openpyxl|aiohttp|pyinstaller"
```

---

## ✅ 第五步：测试开发模式（重要！）

**在打包之前，先确保程序能正常运行：**

```bash
# 1. 进入程序目录
cd NovelTranslator

# 2. 运行程序
python3 main.py
```

**预期结果：**
- ✅ 窗口正常弹出
- ✅ 界面显示完整
- ✅ 没有错误信息

**如果这一步失败了，不要打包！** 先解决运行问题。

---

## 📦 第六步：打包应用

```bash
# 1. 返回项目根目录
cd ~/Documents/translation_workflow

# 2. 确保虚拟环境已激活
source venv/bin/activate

# 3. 运行打包脚本
./build_macos.sh
```

**脚本会：**
1. 检查PyInstaller
2. 清理旧的打包文件
3. 自动打包.app
4. 询问是否复制到应用程序文件夹

---

## 🔍 第七步：调试打包后的应用

如果.app还是点开就关闭，使用以下方法查看错误信息：

### 方法1: 从终端启动（推荐）

```bash
# 直接运行.app的可执行文件，可以看到错误信息
/Applications/NovelTranslator.app/Contents/MacOS/NovelTranslator
```

这会显示详细的错误信息，告诉我们为什么崩溃。

### 方法2: 查看系统日志

```bash
# 查看最近的崩溃日志
log show --predicate 'process == "NovelTranslator"' --last 5m
```

### 方法3: 检查.app结构

```bash
# 查看.app包内容
ls -la /Applications/NovelTranslator.app/Contents/MacOS/

# 检查data文件夹是否存在
ls -la /Applications/NovelTranslator.app/Contents/MacOS/data/
```

---

## 🛠️ 常见问题和解决方案

### 问题1: "权限被拒绝"

```bash
# 添加执行权限
chmod +x /Applications/NovelTranslator.app/Contents/MacOS/NovelTranslator
```

### 问题2: "无法验证开发者"

```bash
# 移除隔离属性
sudo xattr -r -d com.apple.quarantine /Applications/NovelTranslator.app
```

### 问题3: 缺少tkinter

macOS的Python可能缺少tkinter，重新安装：

```bash
# 卸载并重新安装Python（包含tkinter）
brew reinstall python@3.11 python-tk@3.11
```

### 问题4: .app内缺少data文件夹

检查打包脚本是否正确包含了data：

```bash
# 查看build_macos.sh的内容，确保有这一行：
grep "add-data.*data:data" build_macos.sh
```

### 问题5: 依赖库缺失

重新打包，添加更详细的依赖：

```bash
cd ~/Documents/translation_workflow/NovelTranslator

pyinstaller \
    --name="NovelTranslator" \
    --windowed \
    --onefile \
    --add-data "data:data" \
    --hidden-import=tkinter \
    --hidden-import=tkinter.ttk \
    --hidden-import=tkinter.filedialog \
    --hidden-import=tkinter.messagebox \
    --hidden-import=tkinter.scrolledtext \
    --hidden-import=openai \
    --hidden-import=pandas \
    --hidden-import=openpyxl \
    --hidden-import=aiohttp \
    --hidden-import=path_utils \
    --hidden-import=config \
    --hidden-import=resource_mgr \
    --hidden-import=translator \
    --collect-all openai \
    --collect-all aiohttp \
    --clean \
    main.py
```

---

## 🎯 完整检查清单

在打包前确认：

- [ ] Python 3.11已安装：`python3 --version`
- [ ] 虚拟环境已创建并激活：提示符前有 `(venv)`
- [ ] 所有依赖已安装：`pip list`
- [ ] **开发模式可以运行**：`python3 main.py` 能弹出窗口
- [ ] data文件夹存在：`ls NovelTranslator/data/`
- [ ] data文件夹内有文件：
  - `names.json`
  - `styles.json`
  - `default_prompt.json`（可选）

打包后确认：

- [ ] .app文件已创建：`ls dist/NovelTranslator.app`
- [ ] .app包含data：`ls dist/NovelTranslator.app/Contents/MacOS/data/`
- [ ] 从终端运行没有错误：`dist/NovelTranslator.app/Contents/MacOS/NovelTranslator`

---

## 🚀 推荐的完整流程

```bash
# === 清理 ===
rm -rf ~/Documents/translation_workflow
rm -rf /Applications/NovelTranslator.app

# === 重新开始 ===
cd ~/Documents
git clone <仓库URL> translation_workflow
cd translation_workflow
git pull

# === 环境设置 ===
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r NovelTranslator/requirements.txt
pip install pyinstaller

# === 测试运行 ===
cd NovelTranslator
python3 main.py
# 确认窗口正常弹出，然后关闭

# === 打包 ===
cd ..
./build_macos.sh

# === 调试测试 ===
dist/NovelTranslator.app/Contents/MacOS/NovelTranslator
# 看是否有错误信息

# === 如果没有错误，复制到应用程序 ===
cp -r dist/NovelTranslator.app /Applications/

# === 移除隔离属性 ===
sudo xattr -r -d com.apple.quarantine /Applications/NovelTranslator.app

# === 启动应用 ===
open /Applications/NovelTranslator.app
```

---

## 📞 如果还是不行

请从终端运行并**复制错误信息**：

```bash
/Applications/NovelTranslator.app/Contents/MacOS/NovelTranslator 2>&1 | tee ~/Desktop/error_log.txt
```

这会将错误信息保存到桌面的 `error_log.txt`，告诉我错误内容，我可以针对性解决。

---

## ✨ 成功的标志

双击 `NovelTranslator.app` 后：

- ✅ 程序窗口立即弹出
- ✅ 显示"小说翻译工具 v1.1"标题
- ✅ 所有按钮和界面正常显示
- ✅ 日志区显示"小说翻译工具 v1.1 启动"

---

**从头开始，一步一步来，肯定能成功！** 🎉
