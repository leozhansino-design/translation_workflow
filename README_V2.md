# 小说翻译工具 V2 - 两阶段工作流

一个高效的两阶段小说翻译系统，支持从原文生成英文大纲，然后分批生成完整小说内容。

## 🎯 核心特性

### 两阶段工作流
- **Tool 1 - 大纲生成器**: 从原文生成结构化英文大纲
- **Tool 2 - 内容写作器**: 基于大纲分批生成章节内容

### 关键优势
- ✅ 文件名自动识别类型
- ✅ Prompt管理系统（查看、编辑、多版本）
- ✅ 人名自动选择（使用次数最少优先）
- ✅ 分批生成（降低Token占用）
- ✅ 断点续写（支持中断后继续）
- ✅ 字符数验证（9000-30000/章）
- ✅ 模块化输出（title.txt, ch1.txt等）
- ✅ 多任务并行（独立进程）

## 📦 安装

### 方法1: 使用源代码

```bash
# 克隆项目
git clone <repository-url>
cd translation_workflow

# 安装依赖
pip install -r requirements.txt

# 运行Tool 1（大纲生成器）
python outline_generator.py

# 运行Tool 2（任务管理器）
python main.py
```

### 方法2: 使用打包版本

```bash
# 安装依赖
pip install -r requirements.txt

# 打包（Mac和Windows都支持）
python build_package.py

# 运行（在dist/文件夹中）
./dist/OutlineGenerator  # Tool 1
./dist/TaskManager       # Tool 2
```

## 📋 使用流程

### 第一步：准备原文

文件命名格式（**重要！**）：
```
[书名]_[类型].txt
```

支持的类型：
- Romance, Fantasy, Urban, Sci-Fi, Mystery
- Horror, Adventure, Historical, Crime
- LGBTQ+, Paranormal, System, Reborn
- Revenge, Fanfiction

示例：
```
霸道总裁的私宠_Romance.txt
龙族觉醒_Fantasy.txt
重生甜妻_Reborn.txt
```

### 第二步：使用Tool 1生成大纲

1. **运行Tool 1**
   ```bash
   python outline_generator.py
   ```

2. **配置API**
   - API Key: 你的OpenAI API密钥
   - Base URL: https://yunwuapi.com/v1/（或其他兼容API）
   - 模型选择: gemini-2.5-pro / gpt-5.1 / gpt-5等
   - Temperature: 0.8（默认）
   - Max Tokens: 8000（可调整）

3. **选择文件**
   - 点击"选择文件"
   - 系统自动识别类型（从文件名）

4. **设置参数**
   - 章节范围: 例如 1-100
   - 男性人名数: 10（默认）
   - 女性人名数: 10（默认）

5. **（可选）管理Prompt**
   - 点击"📋 Prompt 管理"
   - 查看默认Prompt
   - 编辑并保存自定义版本

6. **生成大纲**
   - 点击"🚀 生成大纲"
   - 等待AI生成（通常2-3分钟）

7. **保存结果**
   - 点击"💾 保存大纲"
   - 生成两个文件：
     - `outlines/[Title]_Outline.txt`（人类可读）
     - `outlines/[Title]_Outline.json`（机器可读）

### 第三步：使用Tool 2生成内容

1. **运行Tool 2**
   ```bash
   python main.py
   ```

2. **创建新任务**
   - 点击"新建任务"
   - 选择Tool 1生成的Outline.json
   - 配置参数：
     - 目标章节数: 100（例如）
     - 每批章节数: 3（推荐2-5）
     - API配置（同Tool 1）

3. **启动任务**
   - 点击"启动任务"
   - 系统创建独立进程开始生成

4. **监控进度**
   - 任务列表显示实时进度
   - 点击任务查看详细信息
   - 显示：当前章节、Token使用、预计费用

5. **断点续写**
   - 如果任务中断，重新选择项目文件夹
   - 系统自动检测已完成的章节
   - 从下一章继续生成

### 第四步：获取输出

生成的项目文件夹结构：
```
ProjectFolder_[Title]_[Genre]_[Timestamp]/
├── title.txt           # 书名
├── blurb.txt           # 简介
├── age.txt             # 年龄分类
├── tags.txt            # 标签
├── category.txt        # 分类
├── ch1.txt             # 第1章
├── ch2.txt             # 第2章
├── ch3.txt             # 第3章
└── ...
```

每个章节文件格式：
```
[正文内容]

---
Character Count: 12450
Generated At: 2025-01-20 10:35:00 UTC
Model: gpt-5.1
Valid: Yes
```

## 🔧 高级功能

### Prompt管理系统

**Tool 1 - 大纲生成Prompt**
- 点击"Prompt 管理"查看当前Prompt
- 编辑Prompt内容
- 保存为新版本
- 支持变量替换：
  - `{genre}` - 小说类型
  - `{male_names}` - 男性名字列表
  - `{female_names}` - 女性名字列表
  - `{style}` - 作者风格
  - `{start_chapter}` - 起始章节
  - `{end_chapter}` - 结束章节

**Tool 2 - 写作Prompt**
- 为每个角色配置独立Prompt（未来功能）
- 控制写作风格和视角

### 断点续写

**场景1: 任务中断**
- 任务运行中被中断（关闭程序、断网等）
- 重新打开Tool 2
- 选择项目文件夹
- 设置目标章节数
- 系统自动从最后一章继续

**场景2: 增加章节**
- 已完成100章的项目
- 想继续写到150章
- 选择项目文件夹
- 设置目标：150章
- 系统自动从第101章开始

### 字符数控制

- 每章最少：9000字符
- 每章最多：30000字符
- 不符合要求的章节会在元数据中标注
- 可手动重新生成

## 📊 效率分析

### 单本书时间估算

**假设：**
- 100章
- 每批3章
- 并发数：1（单进程）
- 每批耗时：3分钟

**时间计算：**
- 大纲生成：3分钟
- 分批写作：100章 ÷ 3章/批 × 3分钟 = 100分钟
- **总计：约103分钟/本**

### 并行优化

运行多个任务（多本书同时生成）：
- 每个任务独立进程
- 建议并发：3-5个任务
- 月产量：可达1000+本

## 🛠️ 技术栈

- **GUI**: Tkinter
- **并发**: subprocess（多进程）
- **API**: OpenAI兼容接口
- **数据**: JSON格式
- **打包**: PyInstaller（Mac/Windows）

## 📂 项目结构

```
translation_workflow/
├── outline_generator.py      # Tool 1: 大纲生成器
├── main.py                   # Tool 2: 任务管理器主窗口
├── writer_worker.py          # 独立写作进程
├── task_manager.py           # 任务管理逻辑
├── prompt_manager.py         # Prompt管理系统
├── resource_mgr.py           # 资源管理（人名、风格）
├── utils.py                  # 工具函数
├── config.py                 # 配置管理
├── data/
│   ├── styles.json           # 风格库
│   ├── names_1.json          # 人名库（新格式）
│   └── prompts.json          # Prompt版本
├── outlines/                 # 生成的大纲
├── projects/                 # 生成的项目
├── tasks/                    # 任务状态文件
├── build_package.py          # 打包脚本
├── requirements.txt          # 依赖列表
└── README_V2.md             # 本文档
```

## ❓ 常见问题

### Q: 文件名格式错误会怎样？
A: Tool 1会提示错误并拒绝处理。请确保格式为 `[书名]_[类型].txt`

### Q: 可以修改Prompt吗？
A: 可以！点击"Prompt 管理"查看和编辑，支持多版本保存。

### Q: 任务中断后如何恢复？
A: 重新打开Tool 2，选择项目文件夹，系统自动检测已完成章节并继续。

### Q: 章节字符数不符合要求怎么办？
A: 查看章节文件的元数据，标注为"Valid: No"的可以手动重新生成。

### Q: 如何同时生成多本书？
A: 在Tool 2中创建多个任务，每个任务独立运行。

### Q: 支持哪些API？
A: 支持所有OpenAI兼容的API（OpenAI、yunwuapi、本地LLM等）

### Q: 费用如何计算？
A: 根据使用的Token数量自动计算（输入Token × $0.01/1K + 输出Token × $0.03/1K）

### Q: Mac和Windows都能用吗？
A: 是的！使用PyInstaller打包后可在Mac和Windows上运行。

## 📝 更新日志

### v2.0.0 (2025-01-20)
- ✅ 全新两阶段工作流
- ✅ Tool 1: 大纲生成器
- ✅ Tool 2: 内容写作器
- ✅ Prompt管理系统
- ✅ 断点续写功能
- ✅ 多任务并行
- ✅ 模块化输出

## 📄 许可证

MIT License

---

**享受高效的翻译流程！** 🚀
