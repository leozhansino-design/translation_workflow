# 小说翻译工具 - Novel Translator

极简中文小说批量翻译工具，支持多线程翻译，自动风格分配，人名去重。

## 功能特点

- ✅ **批量翻译**: 支持添加多个文件或整个文件夹
- ✅ **多线程**: 可配置线程数，最高支持20个并发
- ✅ **智能风格**: 根据小说类型自动分配写作风格（15种类型，40+风格）
- ✅ **人名去重**: 同批次翻译自动避免人名重复（100+英文名库）
- ✅ **成本追踪**: 实时显示翻译成本和耗时
- ✅ **翻译记录**: 自动保存翻译历史和使用统计

## 安装

### 方法1: 使用源码运行

```bash
# 1. 克隆或下载项目
git clone <repository-url>
cd NovelTranslator

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行程序
python main.py
```

### 方法2: 打包成exe

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行打包脚本
python build_exe.py

# 3. 在 dist/ 目录找到 NovelTranslator.exe
```

## 使用方法

### 1. 准备小说文件

文件命名格式: `书名_类型.txt`

支持的类型:
- Fantasy (玄幻/奇幻)
- Romance (言情)
- Urban (都市)
- Sci-Fi (科幻)
- Mystery (悬疑)
- Horror (恐怖)
- Adventure (冒险)
- Historical (历史)
- Crime (犯罪)
- LGBTQ+ (同志)
- Paranormal (超自然)
- System (系统流)
- Reborn (重生)
- Revenge (复仇)
- Fanfiction (同人)

示例:
```
霸道总裁_Romance.txt
穿越异世_Fantasy.txt
重生甜妻_Reborn.txt
```

### 2. 配置API Key

1. 打开程序
2. 输入OpenAI API Key
3. 点击"测试"验证连接

### 3. 添加文件

- 点击"添加文件"选择单个或多个txt文件
- 点击"添加文件夹"批量添加整个目录

### 4. 开始翻译

1. 设置线程数（建议5-10）
2. 点击"🚀 开始翻译"
3. 查看实时翻译状态

### 5. 查看结果

翻译完成的文件保存在 `output/` 目录，命名格式: `书名_translated.txt`

## 项目结构

```
NovelTranslator/
├── main.py              # 主程序+GUI
├── translator.py        # 翻译逻辑
├── resource_mgr.py      # 资源分配（风格+人名）
├── config.py            # 配置管理
├── build_exe.py         # 打包脚本
├── requirements.txt     # 依赖列表
├── data/
│   ├── styles.json      # 风格库（15种类型，40+风格）
│   ├── names.json       # 人名库（100+英文名）
│   ├── summary.json     # 翻译记录
│   └── config.json      # 用户配置
└── output/              # 翻译结果输出目录
```

## 核心逻辑

### 资源分配算法

1. **风格轮换**: 同类型小说自动轮流使用不同风格（按使用次数最少优先）
2. **人名去重**: 同批次翻译的小说人名不重复
3. **使用统计**: 自动记录每种风格和人名的使用次数

### 翻译流程

1. 批量分配资源（一次性分配所有风格和人名）
2. 创建线程池
3. 并发翻译多本小说
4. 实时更新状态显示
5. 保存结果和统计

## 配置说明

### config.json

```json
{
  "api_key": "your-openai-api-key",
  "max_workers": 10,
  "model": "gpt-4-turbo-preview",
  "temperature": 0.8,
  "max_tokens": 50000,
  "cost_per_1k_input": 0.01,
  "cost_per_1k_output": 0.03
}
```

## 成本估算

- 每本小说约2万字
- 预计成本: $0.15 - $0.25 / 本
- 10本并发翻译约10-15分钟

## 注意事项

1. **API Key**: 需要有效的OpenAI API Key
2. **余额**: 确保账户有足够余额
3. **网络**: 需要稳定的网络连接
4. **文件格式**: 仅支持UTF-8编码的txt文件
5. **线程数**: 不要设置过高，避免API限流

## 常见问题

### Q: 翻译失败怎么办？
A: 检查API Key是否正确，网络是否稳定，余额是否充足

### Q: 如何修改风格？
A: 编辑 `data/styles.json`，添加或修改对应类型的风格描述

### Q: 如何添加新的人名？
A: 编辑 `data/names.json`，在male或female数组中添加新名字

### Q: 翻译记录在哪里？
A: 查看 `data/summary.json`，包含所有翻译历史

## 技术栈

- **GUI**: tkinter
- **并发**: ThreadPoolExecutor
- **API**: OpenAI Chat Completion API
- **打包**: PyInstaller

## 许可证

MIT License

## 作者

Created with ❤️ by Claude Code

---

**提示**: 首次使用建议先用1-2本小说测试，确认翻译质量后再批量处理。
