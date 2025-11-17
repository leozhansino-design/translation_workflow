# macOS 完整设置指南 - Novel Translator

## 📋 目录
1. [环境准备](#环境准备)
2. [项目下载与设置](#项目下载与设置)
3. [运行程序](#运行程序)
4. [打包成macOS应用](#打包成macos应用)
5. [常见问题](#常见问题)

---

## 1. 环境准备

### 1.1 安装Homebrew（macOS包管理器）

打开**终端** (Terminal.app，在"应用程序 → 实用工具"中)，粘贴以下命令：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

等待安装完成（可能需要输入Mac密码）。

### 1.2 安装Python 3

```bash
brew install python@3.11
```

验证安装：
```bash
python3 --version
# 应该显示：Python 3.11.x
```

### 1.3 安装Git（如果还没有）

```bash
brew install git
```

---

## 2. 项目下载与设置

### 2.1 选择工作目录

**推荐位置**：`~/Documents/Projects`（您的文档文件夹下）

```bash
# 创建项目目录
mkdir -p ~/Documents/Projects

# 进入该目录
cd ~/Documents/Projects
```

**macOS文件夹说明**：
- `~` = 您的用户主目录 (例如 `/Users/您的用户名`)
- `~/Documents` = 文档文件夹
- `~/Desktop` = 桌面
- `~/Downloads` = 下载文件夹

### 2.2 克隆项目

```bash
# 克隆项目到本地
git clone <您的仓库URL> translation_workflow

# 进入项目目录
cd translation_workflow
```

### 2.3 创建Python虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境（⚠️ 重要！每次打开新终端都要执行）
source venv/bin/activate

# 激活后，终端提示符前面会显示 (venv)
```

### 2.4 安装依赖

```bash
# 确保虚拟环境已激活（提示符前有 (venv)）
pip install -r NovelTranslator/requirements.txt
```

---

## 3. 运行程序

### 3.1 直接运行（开发模式）

```bash
# 1. 进入项目目录
cd ~/Documents/Projects/translation_workflow

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 进入程序目录
cd NovelTranslator

# 4. 运行程序
python3 main.py
```

程序窗口会弹出，可以开始使用。

### 3.2 创建快速启动脚本

为了方便每次启动，创建一个启动脚本：

```bash
# 在项目根目录创建启动脚本
cat > ~/Documents/Projects/translation_workflow/start_translator.sh <<'EOF'
#!/bin/bash
cd ~/Documents/Projects/translation_workflow
source venv/bin/activate
cd NovelTranslator
python3 main.py
EOF

# 给脚本添加执行权限
chmod +x ~/Documents/Projects/translation_workflow/start_translator.sh
```

以后只需运行：
```bash
~/Documents/Projects/translation_workflow/start_translator.sh
```

---

## 4. 打包成macOS应用

### 4.1 安装PyInstaller

```bash
# 确保虚拟环境已激活
source venv/bin/activate

# 安装PyInstaller
pip install pyinstaller
```

### 4.2 创建应用图标（可选）

如果有PNG格式的图标，转换为`.icns`格式：

```bash
# 创建iconset文件夹
mkdir MyIcon.iconset

# 调整图片尺寸（需要安装imagemagick）
brew install imagemagick
convert icon.png -resize 16x16 MyIcon.iconset/icon_16x16.png
convert icon.png -resize 32x32 MyIcon.iconset/icon_16x16@2x.png
convert icon.png -resize 32x32 MyIcon.iconset/icon_32x32.png
convert icon.png -resize 64x64 MyIcon.iconset/icon_32x32@2x.png
convert icon.png -resize 128x128 MyIcon.iconset/icon_128x128.png
convert icon.png -resize 256x256 MyIcon.iconset/icon_128x128@2x.png
convert icon.png -resize 256x256 MyIcon.iconset/icon_256x256.png
convert icon.png -resize 512x512 MyIcon.iconset/icon_256x256@2x.png
convert icon.png -resize 512x512 MyIcon.iconset/icon_512x512.png
convert icon.png -resize 1024x1024 MyIcon.iconset/icon_512x512@2x.png

# 转换为icns
iconutil -c icns MyIcon.iconset
```

### 4.3 打包应用

```bash
# 进入程序目录
cd ~/Documents/Projects/translation_workflow/NovelTranslator

# 确保虚拟环境已激活
source ../venv/bin/activate

# 使用PyInstaller打包（无图标版本）
pyinstaller --name="NovelTranslator" \
    --windowed \
    --onefile \
    --add-data "data:data" \
    --hidden-import=tkinter \
    --hidden-import=openai \
    --hidden-import=pandas \
    --hidden-import=openpyxl \
    main.py

# 如果有图标文件，使用此命令：
# pyinstaller --name="NovelTranslator" \
#     --windowed \
#     --onefile \
#     --icon="path/to/MyIcon.icns" \
#     --add-data "data:data" \
#     --hidden-import=tkinter \
#     --hidden-import=openai \
#     --hidden-import=pandas \
#     --hidden-import=openpyxl \
#     main.py
```

**参数说明**：
- `--windowed`: 不显示终端窗口（GUI应用）
- `--onefile`: 打包成单个可执行文件
- `--name`: 应用名称
- `--icon`: 应用图标
- `--add-data`: 包含data文件夹到应用中

### 4.4 查找打包好的应用

```bash
# 打包完成后，应用位于：
ls dist/

# 会看到：NovelTranslator.app
```

### 4.5 移动应用到应用程序文件夹

```bash
# 将应用复制到应用程序文件夹
cp -r dist/NovelTranslator.app /Applications/

# 或者手动：
# 打开Finder → 进入 dist 文件夹 → 拖动 NovelTranslator.app 到"应用程序"文件夹
```

### 4.6 首次运行处理

macOS可能会阻止未签名的应用。解决方法：

**方法1：右键打开**
1. 在Finder中找到应用
2. **右键点击** → 选择"打开"
3. 点击"打开"确认

**方法2：通过系统设置允许**
1. 双击应用（会显示警告）
2. 打开"系统设置" → "隐私与安全性"
3. 在底部找到"仍要打开"按钮，点击确认

**方法3：完全禁用Gatekeeper（不推荐）**
```bash
sudo spctl --master-disable
```

---

## 5. 完整的工作流程总结

### 第一次设置（只需执行一次）

```bash
# 1. 安装Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. 安装Python和Git
brew install python@3.11 git

# 3. 创建项目目录
mkdir -p ~/Documents/Projects
cd ~/Documents/Projects

# 4. 克隆项目
git clone <仓库URL> translation_workflow
cd translation_workflow

# 5. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 6. 安装依赖
pip install -r NovelTranslator/requirements.txt
```

### 日常使用（开发模式）

```bash
# 打开终端，运行：
cd ~/Documents/Projects/translation_workflow
source venv/bin/activate
cd NovelTranslator
python3 main.py
```

### 打包发布（只需执行一次）

```bash
# 1. 安装PyInstaller
cd ~/Documents/Projects/translation_workflow
source venv/bin/activate
pip install pyinstaller

# 2. 打包
cd NovelTranslator
pyinstaller --name="NovelTranslator" \
    --windowed \
    --onefile \
    --add-data "data:data" \
    --hidden-import=tkinter \
    --hidden-import=openai \
    --hidden-import=pandas \
    --hidden-import=openpyxl \
    main.py

# 3. 复制到应用程序
cp -r dist/NovelTranslator.app /Applications/

# 4. 从启动台或应用程序文件夹启动
```

---

## 6. 常见问题

### Q1: 终端在哪里？
**A**: `应用程序 → 实用工具 → 终端` 或者按 `Cmd + 空格` 搜索"Terminal"

### Q2: 如何在Finder中显示隐藏文件？
**A**: 在Finder中按 `Cmd + Shift + .` (句点)

### Q3: 虚拟环境是什么？为什么需要激活？
**A**: 虚拟环境是独立的Python环境，避免不同项目的依赖冲突。每次打开新终端都需要重新激活：
```bash
source venv/bin/activate
```

### Q4: 打包后的应用很大（几百MB）怎么办？
**A**: 这是正常的，因为包含了Python解释器和所有依赖库。可以用以下方法减小：
```bash
# 使用 --onedir 而不是 --onefile（会创建应用包）
pyinstaller --windowed --onedir --name="NovelTranslator" main.py
```

### Q5: 应用打不开，显示"已损坏"
**A**: 这是macOS的Gatekeeper保护。解决方法：
```bash
# 移除隔离属性
sudo xattr -r -d com.apple.quarantine /Applications/NovelTranslator.app
```

### Q6: 如何更新代码？
```bash
cd ~/Documents/Projects/translation_workflow
git pull
source venv/bin/activate
pip install -r NovelTranslator/requirements.txt --upgrade
```

### Q7: 如何卸载？
```bash
# 删除应用
rm -rf /Applications/NovelTranslator.app

# 删除项目文件
rm -rf ~/Documents/Projects/translation_workflow

# 卸载Homebrew包（可选）
brew uninstall python@3.11
```

---

## 7. macOS特有的优化建议

### 7.1 创建Dock快捷方式

打包后的`.app`可以直接拖到Dock栏固定。

### 7.2 使用Automator创建双击启动脚本

1. 打开"Automator" → 新建"应用程序"
2. 添加"运行Shell脚本"
3. 粘贴启动命令：
```bash
cd ~/Documents/Projects/translation_workflow
source venv/bin/activate
cd NovelTranslator
python3 main.py
```
4. 保存为"启动翻译器.app"到桌面

### 7.3 文件路径适配

macOS推荐使用的目录：
- 用户文档：`~/Documents/`
- 应用数据：`~/Library/Application Support/NovelTranslator/`
- 配置文件：`~/.config/noveltranslator/`

---

## 8. 终端命令速查表

```bash
# 查看当前目录
pwd

# 列出文件
ls
ls -la  # 显示隐藏文件和详细信息

# 切换目录
cd ~/Documents/Projects
cd ..  # 返回上级目录
cd ~   # 返回主目录

# 创建文件夹
mkdir folder_name
mkdir -p path/to/folder  # 创建多级目录

# 复制文件
cp source.txt destination.txt
cp -r folder/ new_folder/  # 复制文件夹

# 移动/重命名
mv old_name.txt new_name.txt

# 删除
rm file.txt
rm -rf folder/  # 删除文件夹（⚠️ 谨慎使用）

# 查看文件内容
cat file.txt
less file.txt  # 分页查看（按Q退出）

# 编辑文件
nano file.txt  # 简单文本编辑器
```

---

## 9. 下一步

- ✅ 完成环境设置
- ✅ 成功运行程序
- ✅ 打包成.app应用
- 🔜 根据需要进行macOS特定优化（菜单栏、Retina屏幕支持等）

如有问题，请检查终端输出的错误信息！
