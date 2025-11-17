# macOS快速开始指南 - Novel Translator

## 🚀 最快上手方式（5分钟）

### 步骤1: 安装Homebrew
打开终端（Terminal），粘贴并回车：
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 步骤2: 安装Python
```bash
brew install python@3.11
```

### 步骤3: 下载项目
```bash
# 进入文档文件夹
cd ~/Documents

# 克隆项目
git clone <您的仓库URL> translation_workflow
cd translation_workflow
```

### 步骤4: 安装依赖
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r NovelTranslator/requirements.txt
```

### 步骤5: 运行程序
```bash
cd NovelTranslator
python3 main.py
```

---

## 📦 打包成.app应用（一键完成）

### 使用自动化脚本
```bash
# 进入项目根目录
cd ~/Documents/translation_workflow

# 激活虚拟环境
source venv/bin/activate

# 运行打包脚本
./build_macos.sh
```

脚本会：
1. 检查PyInstaller
2. 自动打包应用
3. 询问是否复制到"应用程序"文件夹

完成后，您可以从启动台或应用程序文件夹启动！

---

## 🍎 Apple分支 vs 主分支

### 使用Apple专属优化版（推荐macOS用户）
```bash
git checkout claude/apple-compatible-01LUr12oHGeZAT97QzmkcziY
```

**Apple分支独有功能：**
- ✅ macOS原生菜单栏
- ✅ Retina屏幕优化
- ✅ 通知中心集成（翻译完成自动通知）
- ✅ 深色模式检测
- ✅ Command键快捷键
- ✅ macOS标准文件路径

### 使用跨平台通用版
```bash
git checkout claude/novel-translator-app-01LUr12oHGeZAT97QzmkcziY
```

---

## 🖥️ 终端基础操作

### 找到终端
**方法1:** `应用程序` → `实用工具` → `终端`
**方法2:** 按 `Command + 空格`，输入"Terminal"

### 常用命令
```bash
# 查看当前目录
pwd

# 列出文件
ls

# 进入文件夹
cd ~/Documents/translation_workflow

# 返回上一级
cd ..

# 返回主目录
cd ~
```

---

## ⚙️ 完整工作流程

### 第一次设置（只需一次）
```bash
# 1. 安装工具
brew install python@3.11 git

# 2. 下载项目
mkdir -p ~/Documents/Projects
cd ~/Documents/Projects
git clone <仓库URL> translation_workflow
cd translation_workflow

# 3. 切换到Apple分支（macOS优化）
git checkout claude/apple-compatible-01LUr12oHGeZAT97QzmkcziY

# 4. 安装依赖
python3 -m venv venv
source venv/bin/activate
pip install -r NovelTranslator/requirements.txt
```

### 日常使用（每次启动）
```bash
cd ~/Documents/Projects/translation_workflow
source venv/bin/activate
cd NovelTranslator
python3 main.py
```

### 打包成应用（一次即可）
```bash
cd ~/Documents/Projects/translation_workflow
source venv/bin/activate
./build_macos.sh
```

---

## 🔧 故障排除

### 问题1: 应用打不开，显示"无法验证开发者"
**解决方法：**
```bash
sudo xattr -r -d com.apple.quarantine /Applications/NovelTranslator.app
```

或者：
1. 右键点击应用
2. 选择"打开"
3. 点击"打开"确认

### 问题2: 虚拟环境未激活
**症状：** 提示符前没有 `(venv)`
**解决：**
```bash
cd ~/Documents/Projects/translation_workflow
source venv/bin/activate
```

### 问题3: 找不到模块
**解决：**
```bash
source venv/bin/activate
pip install -r NovelTranslator/requirements.txt --upgrade
```

### 问题4: 应用很大（几百MB）
**说明：** 这是正常的，因为包含了完整的Python环境和所有库。

---

## 📁 文件位置说明

### 开发模式（直接运行）
```
~/Documents/Projects/translation_workflow/
├── NovelTranslator/
│   ├── main.py           # 主程序
│   ├── data/             # 数据文件
│   └── output/           # 输出文件
└── venv/                 # 虚拟环境
```

### 打包后（.app应用）
```
/Applications/
└── NovelTranslator.app   # 双击即可运行
```

### macOS标准路径（Apple分支）
```
~/Library/Application Support/NovelTranslator/
├── data/                 # 配置和资源
├── output/               # 翻译结果
└── logs/                 # 日志文件
```

---

## 🎯 推荐配置

### 创建桌面快捷方式
打包后的`.app`可以直接拖到Dock栏固定。

### 使用Automator创建启动器
1. 打开"Automator"
2. 新建"应用程序"
3. 添加"运行Shell脚本"
4. 粘贴：
```bash
cd ~/Documents/Projects/translation_workflow
source venv/bin/activate
cd NovelTranslator
python3 main.py
```
5. 保存为"启动翻译器.app"

---

## 📚 详细文档

需要更详细的说明？查看：

- **MACOS_SETUP_GUIDE.md** - 完整设置指南
- **APPLE_BRANCH_DIFFERENCES.md** - Apple分支功能详解
- **MACOS_COMPATIBILITY.md** - macOS兼容性说明

---

## 🆘 获取帮助

遇到问题？
1. 查看终端的错误信息
2. 检查虚拟环境是否激活
3. 确认Python版本：`python3 --version`
4. 重新安装依赖：`pip install -r NovelTranslator/requirements.txt --upgrade`

---

## ✅ 检查清单

安装成功的标志：
- [ ] 终端可以运行 `python3 --version`
- [ ] 虚拟环境激活后提示符前有 `(venv)`
- [ ] 运行 `python3 main.py` 后窗口正常弹出
- [ ] （可选）打包后的 `.app` 可以双击启动

---

**恭喜！您已经完成macOS上的Novel Translator设置！** 🎉
