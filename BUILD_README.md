# 打包说明

## 📦 一键打包两个工具

使用 `build_package.py` 可以一次性打包两个工具成独立的可执行文件。

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install pyinstaller openai
```

### 2. 运行打包脚本

```bash
python build_package.py
```

## 📂 输出文件

打包完成后，在 `dist/` 文件夹中会生成两个可执行文件：

**Windows:**
- `OutlineGenerator.exe` - 大纲生成器
- `NovelWriter.exe` - 小说生成器

**Mac:**
- `OutlineGenerator` - 大纲生成器
- `NovelWriter` - 小说生成器

## 🔄 完整工作流

```
1️⃣ 运行 OutlineGenerator.exe
   ├── 输入：原文小说文件（书名_类型.txt）
   └── 输出：大纲文件夹
       ├── _writing_prompt.txt
       ├── chapter_1_prompt.txt
       ├── chapter_2_prompt.txt
       └── ...

2️⃣ 运行 NovelWriter.exe
   ├── 输入：大纲文件夹（上一步生成的）
   └── 输出：小说内容
       ├── batch_1_ch1-3.txt
       ├── batch_2_ch4-6.txt
       └── [Title]_complete.txt
```

## 📋 打包特性

- ✅ 单文件可执行程序（无需安装Python）
- ✅ 自动包含所有依赖（Tkinter、OpenAI等）
- ✅ 包含数据文件（styles.json、names_1.json）
- ✅ 支持Windows/Mac/Linux多平台
- ✅ 自动清理旧构建文件

## 🐛 常见问题

### Q: 打包失败，提示找不到模块

**A:** 确保所有Python依赖都已安装：
```bash
pip install pyinstaller openai
```

### Q: 生成的exe文件很大

**A:** 正常现象。PyInstaller会打包Python解释器和所有依赖，通常每个exe在50-100MB左右。

### Q: Mac上提示"无法验证开发者"

**A:** 右键点击应用 → 选择"打开"，或在"系统偏好设置" → "安全性与隐私"中允许。

### Q: 如何只打包其中一个工具？

**A:** 修改 `build_package.py` 中的 `entry_points` 列表，注释掉不需要的工具。

## 📊 文件大小参考

- OutlineGenerator.exe: ~60MB
- NovelWriter.exe: ~60MB
- 总计: ~120MB

## 🔧 高级配置

### 自定义图标

在项目根目录放置图标文件：
- Windows: `icon.ico`
- Mac: `icon.icns`

打包时会自动使用。

### 版本信息（Windows）

创建 `version.txt` 文件，打包时会自动包含。

## 📝 打包流程说明

```
1. 清理旧构建文件（build/、dist/）
2. 打包 outline_generator.py → OutlineGenerator.exe
3. 打包 writer_app.py → NovelWriter.exe
4. 复制数据文件到dist/
5. 完成！
```

## 💡 使用建议

1. **首次使用**：先打包一个工具测试，确认没问题后再打包全部
2. **开发调试**：直接运行Python文件（`python outline_generator.py`）
3. **生产使用**：使用打包后的exe文件

---

**一键打包，双工具齐全！** 🎉
