# 小说翻译工具 - 极简版

一个专为网文翻译设计的桌面应用，支持多线程批量翻译，智能分配作者风格和人名，确保每本小说独特且本土化。

## 功能特点

- **多线程并发翻译**：支持同时翻译多本小说，最多20个线程
- **智能资源分配**：自动为每本小说分配不同的作者风格和人名，避免重复
- **实时进度显示**：每本小说独立计时，显示翻译状态和费用
- **本土化翻译**：将中文网文翻译成符合英语母语读者习惯的作品
- **费用估算**：翻译前估算费用，翻译后显示实际费用
- **翻译记录**：自动保存翻译历史，包括使用的风格、人名、耗时和费用

## 安装

### 方法1: 使用源代码

```bash
# 克隆或下载项目
git clone <repository-url>
cd NovelTranslator

# 安装依赖
pip install -r requirements.txt

# 运行应用
python main.py
```

### 方法2: 打包成exe

```bash
# 安装依赖
pip install -r requirements.txt

# 打包
python build_exe.py

# 生成的文件在 dist/NovelTranslator.exe
```

## 使用方法

### 1. 准备文件

文件命名格式：`书名_类型.txt`

支持的类型：
- Fantasy, Romance, Urban, Sci-Fi, Mystery
- Horror, Adventure, Historical, Crime
- LGBTQ+, Paranormal, System, Reborn
- Revenge, Fanfiction

示例：
```
霸道总裁_Romance.txt
重生甜妻_Reborn.txt
穿越异世_Fantasy.txt
```

### 2. 配置API

1. 打开应用
2. 输入OpenAI API Key
3. 点击"测试"确认连接
4. 设置并发线程数（建议10）

### 3. 添加文件

- 点击"添加文件"选择单个文件
- 点击"添加文件夹"批量添加
- 查看预计费用

### 4. 开始翻译

1. 点击"🚀 开始翻译"
2. 查看实时进度
3. 等待翻译完成
4. 翻译结果保存在 `output` 文件夹

### 5. 查看结果

翻译完成后：
- 查看 `output` 文件夹中的翻译结果
- 查看 `data/summary.json` 中的翻译记录

## 项目结构

```
NovelTranslator/
├── main.py              # 主程序+GUI
├── translator.py        # 翻译逻辑
├── resource_mgr.py      # 资源分配
├── config.py            # 配置管理
├── data/
│   ├── styles.json      # 风格库
│   ├── names.json       # 人名库
│   ├── summary.json     # 翻译记录
│   └── config.json      # 配置文件
├── output/              # 翻译结果
├── build_exe.py         # 打包脚本
├── requirements.txt     # 依赖列表
└── README.md           # 说明文档
```

## 数据文件说明

### styles.json
包含15种类型的写作风格，每种类型有2-3个作者风格可选。系统会自动轮流分配，确保同类型小说使用不同风格。

### names.json
包含50个男性名字和50个女性名字，每本书分配20个男名和20个女名。系统会跟踪使用次数，优先分配使用较少的名字。

### summary.json
记录每次翻译的详细信息：
- 原始书名和翻译后文件名
- 类型和使用的作者风格
- 使用的角色名
- 翻译耗时和费用

## 高级设置

点击"设置"按钮可以配置：
- **模型选择**：gpt-4-turbo-preview, gpt-4, gpt-3.5-turbo
- **Temperature**：0-1，控制创意程度（默认0.8）
- **Max Tokens**：最大输出长度（默认50000）

## 翻译质量

应用使用专业的翻译提示词，确保：

1. **本土化**：地名、人名、文化元素完全本土化
2. **流畅性**：使用地道的英语表达，避免中式英语
3. **风格化**：模仿知名英语作者的写作风格
4. **独特性**：每本书使用不同的风格和人名

## 费用说明

费用取决于：
- 使用的模型（GPT-4更贵但质量更好）
- 小说长度（按字符数计费）
- 输出长度（翻译通常比原文长）

示例：
- 2万字小说 ≈ $0.15-0.30

## 常见问题

### Q: 翻译失败怎么办？
A: 检查API Key是否正确，网络是否通畅，OpenAI账户是否有余额。

### Q: 可以中断翻译吗？
A: 当前版本不支持中断，请等待翻译完成。未完成的任务不会保存。

### Q: 如何添加新的作者风格？
A: 编辑 `data/styles.json`，在对应类型下添加新的风格描述。

### Q: 如何添加更多人名？
A: 编辑 `data/names.json`，在 `male` 或 `female` 数组中添加新名字。

### Q: 翻译结果保存在哪里？
A: 保存在 `output` 文件夹，文件名格式为 `书名_类型_translated.txt`

## 技术栈

- **GUI**: Tkinter
- **并发**: ThreadPoolExecutor
- **API**: OpenAI GPT-4
- **打包**: PyInstaller

## 许可证

MIT License

## 贡献

欢迎提交Issues和Pull Requests！

## 更新日志

### v1.0.0 (2025-01-16)
- 初始版本
- 支持15种小说类型
- 多线程并发翻译
- 智能资源分配
- 实时进度显示

---

**享受翻译吧！**
