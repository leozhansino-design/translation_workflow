# 小说生成器 (Writer Tool) - 完全重写版本

## 📝 概述

这是一个全新的小说生成器工具，**完全参考你的工作代码重写**。支持：

- ✅ **从文件夹自动抓取**：_writing_prompt.txt + chapter_X_prompt.txt
- ✅ **批次生成**：可配置每批生成1-5章
- ✅ **断点续写**：自动检测已完成批次，从下一批继续
- ✅ **前文context**：每批带上上一批结尾1500字符，保持连贯性
- ✅ **任务队列**：所有任务显示在底部任务栏
- ✅ **预览Prompt**：查看第一批次完整prompt
- ✅ **打开输出目录**：快速访问生成的文件
- ✅ **API测试**：测试API连接
- ✅ **多模型支持**：gpt-5-mini, gpt-5.1, gemini-2.5-pro等

## 🚀 快速开始

### 1. 准备Prompt文件夹

你的文件夹需要包含以下文件：

```
your_folder/
├── _writing_prompt.txt      # 必需：写作要求
├── chapter_1_prompt.txt      # 必需：第1章大纲
├── chapter_2_prompt.txt      # 必需：第2章大纲
├── chapter_3_prompt.txt      # 第3章大纲
├── ...
├── title.txt                 # 可选：书名
└── category.txt              # 可选：类型
```

**_writing_prompt.txt 示例：**
```
Genre: Urban Romance
Setting: Modern Manhattan
Style: Fast-paced, emotional, addictive

Key Requirements:
- Short paragraphs (1-3 sentences)
- Punchy dialogue
- Cliffhanger endings
- 3-5 爽点 per chapter
```

**chapter_1_prompt.txt 示例：**
```
Chapter 1: The Proposal Gone Wrong

Emma catches her boyfriend cheating at their engagement party.
爽点1: She dumps champagne on him in front of everyone
爽点2: His rich boss offers to help her
爽点3: She discovers she's the heir to a fortune
Hook: Mysterious text from unknown number
```

### 2. 启动工具

**Windows:**
```bash
run_writer.bat
```

**Mac/Linux:**
```bash
python writer_app.py
```

### 3. 配置API

在界面上配置：
- **API Key**: 你的API密钥
- **Base URL**: https://yunwuapi.com/v1/
- **模型**: 选择模型（默认gpt-5-mini）

点击**"测试API"**确保连接正常。

### 4. 选择Prompt文件夹

点击**"选择文件夹"**，选择包含prompt文件的文件夹。

系统会自动：
- 检测_writing_prompt.txt
- 检测所有chapter_X_prompt.txt文件
- 读取title.txt和category.txt（如果存在）
- 显示总章节数

### 5. 配置任务参数

- **每批章节数**: 每次生成几章（建议3章）
  - 1章/批：最安全，最连贯
  - 2-3章/批：**推荐**，平衡速度和质量
  - 4-5章/批：最快，但可能影响连贯性

- **Temperature**: 0.85（默认）
  - 0.7: 更保守
  - 0.85: 平衡
  - 1.0: 更有创意

- **Max Tokens**: 120000（默认）

### 6. 添加到队列

点击**"➕ 添加到队列"**，任务会被添加到下方的任务队列中。

你可以添加多个任务！

### 7. 启动任务

**单个任务**：
- 点击任务卡片上的**"▶️ 开始"**按钮

**所有任务**：
- 点击**"🚀 启动所有任务"**按钮

### 8. 监控进度

任务卡片显示：
- 🔄 **运行中** - 正在生成（批次X/总批次）
- ✅ **完成** - 生成成功
- ❌ **失败** - 生成失败

实时更新：
- 批次进度
- 章节进度
- 百分比进度条

### 9. 管理任务

每个任务卡片有以下按钮：

- **👁️ 预览Prompt** - 查看第一批次的完整prompt
  - System Prompt（固定）
  - Writing Prompt（_writing_prompt.txt）
  - 章节Prompts（第一批）

- **📂 打开目录** - 打开输出文件夹（任务开始后可用）

- **🗑️ 删除** - 删除任务

## 📂 输出结构

生成的文件夹结构：

```
output/[Title]_[Category]_[Timestamp]/
├── batch_1_ch1-3.txt      # 第1批次（第1-3章）
├── batch_2_ch4-6.txt      # 第2批次（第4-6章）
├── batch_3_ch7-9.txt      # 第3批次（第7-9章）
├── ...
└── [Title]_complete.txt   # 完整版（所有章节合并）
```

**批次文件内容**：
- 只包含本批次的章节内容

**完整版文件内容**：
```
Title: [书名]
Category: [类型]

================================================================================

[所有章节内容...]
```

## 🔄 断点续写

如果任务中断（关闭程序、断网、错误等）：

1. **重新打开Writer工具**
2. **选择相同的Prompt文件夹**
3. **使用相同的配置添加任务**
4. **启动任务**

系统会自动：
- 检测output文件夹中已生成的batch_X文件
- 找到最大的批次号（例如batch_3）
- 从下一批次继续（例如batch_4）
- 加载上一批次的结尾1500字符作为context

**示例**：
```
已有文件：
- batch_1_ch1-3.txt
- batch_2_ch4-6.txt
- batch_3_ch7-9.txt

重新启动后：
✓ 检测到已完成批次: 1-3
✓ 从批次4继续
✓ 加载前文context: 1500字符（来自batch_3）
📝 开始生成批次4: 第10-12章
```

## 🎯 核心特性详解

### 1. 批次生成系统

每批次生成过程：

```
批次1（第1-3章）:
├── System Prompt（固定）
├── Writing Prompt
├── 第1章prompt
├── 第2章prompt
└── 第3章prompt
    ↓
生成 → batch_1_ch1-3.txt
提取结尾1500字符 → context

批次2（第4-6章）:
├── System Prompt（固定）
├── Writing Prompt
├── Context（批次1的结尾1500字符）← 保持连贯
├── 第4章prompt
├── 第5章prompt
└── 第6章prompt
    ↓
生成 → batch_2_ch4-6.txt
```

### 2. 前文Context管理

- **第1批**: 无context（全新开始）
- **第2批起**: 带上上一批结尾1500字符
  - 保持情节连贯性
  - 保持角色一致性
  - 避免突兀的衔接

### 3. 智能Prompt构建

每次发送给API的完整Prompt：

```
【System Message】
[固定的SYSTEM_PROMPT]

【User Message】
【写作要求】
[_writing_prompt.txt的内容]

============================================================

【前文结尾（保持连贯）】← 第2批起
[上一批的结尾1500字符]

============================================================

【本批次章节大纲】

===== 第X章 =====
[chapter_X_prompt.txt的内容]

===== 第Y章 =====
[chapter_Y_prompt.txt的内容]

===== 第Z章 =====
[chapter_Z_prompt.txt的内容]

============================================================

现在写第X-Z章。
要求：每章15,000-20,000英文单词，只输出小说正文。

开始写作：
```

### 4. 任务队列管理

- 可以添加多个任务
- 每个任务独立运行（独立进程）
- 实时监控所有任务进度
- 支持同时运行多个任务

### 5. 预览Prompt功能

点击**"👁️ 预览Prompt"**可以看到：
- 第一批次的完整prompt
- System Prompt
- Writing Prompt
- 章节Prompts（第一批）

**用途**：
- 检查prompt是否正确
- 调试生成质量问题
- 了解发送给API的内容

## 💡 使用技巧

### 每批章节数建议

| 每批章节数 | 速度 | 连贯性 | 适用场景 |
|-----------|------|--------|---------|
| 1章 | 慢 | ⭐⭐⭐⭐⭐ | 高质量、长篇巨作 |
| 2章 | 适中 | ⭐⭐⭐⭐ | 短篇、中篇 |
| **3章** | **快** | **⭐⭐⭐⭐** | **推荐！平衡** |
| 4章 | 很快 | ⭐⭐⭐ | 快速生成、简单剧情 |
| 5章 | 最快 | ⭐⭐ | 大批量生产 |

### Temperature设置

- **0.7** - 更保守，严格遵循大纲
- **0.85** - **推荐**，平衡创意和一致性
- **1.0** - 更有创意，可能偏离大纲

### 文件夹组织建议

```
projects/
├── Book1_Romance/
│   ├── _writing_prompt.txt
│   ├── chapter_1_prompt.txt
│   ├── ...
│   └── title.txt
│
├── Book2_Fantasy/
│   ├── _writing_prompt.txt
│   ├── chapter_1_prompt.txt
│   └── ...
│
└── Book3_Urban/
    ├── _writing_prompt.txt
    └── chapter_1_prompt.txt
```

### 并行任务建议

- **1-2个任务**: 保守，逐个完成
- **3-5个任务**: **推荐**，充分利用API
- **6+个任务**: 可能触发API限流

## 🐛 故障排除

### API连接失败

1. 检查API Key是否正确
2. 检查Base URL格式（需要包含https://）
3. 点击"测试API"
4. 检查网络连接

### 找不到_writing_prompt.txt

- 确保文件名完全一致（包括下划线）
- 确保文件在选择的文件夹中
- 确保文件编码为UTF-8

### 章节文件格式错误

正确格式：
- ✅ `chapter_1_prompt.txt`
- ✅ `chapter_10_prompt.txt`
- ✅ `chapter_100_prompt.txt`

错误格式：
- ❌ `chapter1_prompt.txt`（缺少下划线）
- ❌ `chapter_01_prompt.txt`（有前导零）
- ❌ `ch1_prompt.txt`（缺少"chapter"）

### 任务卡在"运行中"

1. 查看任务目录：`tasks/[task_id]/`
2. 检查`progress.json`文件
3. 检查输出目录是否有文件
4. 检查API是否响应

### 断点续写不工作

确保：
- 选择的是**相同的Prompt文件夹**
- Output文件夹存在且包含batch_X文件
- 批次文件命名格式正确

### 字数偏少

如果平均字数低于12000：
- 在_writing_prompt.txt中强调字数要求
- 降低Temperature（0.7）
- 减少每批章节数（例如改为2章/批）
- 增加章节prompt的详细程度

## 📊 与原版本的区别

| 功能 | 原writer.py | 新writer_app.py |
|------|-------------|-----------------|
| 文件加载 | 单个JSON | 文件夹（自动抓取） |
| GUI界面 | ❌ 无 | ✅ 完整GUI |
| 模型选择 | ❌ 硬编码 | ✅ 可选择 |
| API测试 | ❌ 无 | ✅ 支持 |
| 批次生成 | ❌ 无 | ✅ 支持 |
| 断点续写 | ✅ 基本 | ✅ 完整支持 |
| 前文context | ❌ 无 | ✅ 支持 |
| 任务队列 | ❌ 无 | ✅ 支持 |
| 并行任务 | ❌ 无 | ✅ 支持 |
| Prompt预览 | ❌ 无 | ✅ 支持 |
| 进度监控 | ❌ 命令行 | ✅ 实时GUI |

## 🎓 完整工作流示例

### 示例1：从零开始

```bash
# 1. 准备文件夹
mkdir Urban_Romance
cd Urban_Romance

# 2. 创建_writing_prompt.txt
echo "Genre: Urban Romance
Style: Fast-paced, emotional
Requirements: 15,000-20,000 words per chapter" > _writing_prompt.txt

# 3. 创建章节prompts
echo "Chapter 1: Emma discovers betrayal..." > chapter_1_prompt.txt
echo "Chapter 2: She meets her mysterious boss..." > chapter_2_prompt.txt
echo "Chapter 3: A shocking revelation..." > chapter_3_prompt.txt

# 4. 启动工具
python writer_app.py

# 5. 在GUI中：
#    - 测试API
#    - 选择文件夹
#    - 设置每批3章
#    - 添加到队列
#    - 点击开始
```

### 示例2：断点续写

```bash
# 已有批次：
output/My_Novel_Romance_20251121/
├── batch_1_ch1-3.txt
├── batch_2_ch4-6.txt
└── batch_3_ch7-9.txt  ← 到这里中断了

# 重新启动：
python writer_app.py

# 在GUI中：
#    - 选择相同的prompt文件夹
#    - 添加任务
#    - 点击开始
#
# 系统自动：
#    ✓ 检测到批次1-3已完成
#    ✓ 从批次4继续
#    ✓ 加载batch_3的结尾1500字符
#    📝 生成batch_4_ch10-12.txt
```

## 📄 技术架构

```
writer_app.py          # 主GUI应用
├── WriterTask         # 任务数据类
├── NovelWriterApp     # 主窗口类
│   ├── 文件夹加载
│   ├── 任务队列管理
│   ├── 进度轮询
│   └── UI更新
└── 启动独立进程 ──────> writer_worker.py

writer_worker.py       # 独立工作进程
├── WriterWorker       # 工作进程类
│   ├── 加载prompts
│   ├── 批次生成
│   ├── 断点检测
│   ├── Context管理
│   └── API调用
└── 输出文件
```

## 📝 更新日志

### v2.1.0 (2025-11-21) - 完全重写
- ✅ 完全参考用户工作代码重写
- ✅ 从文件夹自动抓取prompts
- ✅ 批次生成系统
- ✅ 断点续写功能
- ✅ 前文context管理
- ✅ 任务队列管理
- ✅ Prompt预览功能
- ✅ 实时进度监控
- ✅ API测试功能

### v2.0.0 (2025-11-21) - 初始版本
- ✅ 基础GUI界面
- ✅ 多模型选择
- ✅ 基本任务管理

---

**参考你的工作代码重写，功能完全一致！** ✍️

## 🙏 致谢

本工具的核心逻辑完全参考用户提供的工作代码：
- 批次生成机制
- 断点续写逻辑
- 前文context管理
- Prompt构建方式

特别感谢提供了清晰、高效、可工作的代码示例！
