# Novel Translator - 优化版

## 🎯 核心优化

### 问题
- 旧版本在翻译过程中做太多处理，导致速度慢、体验差
- 人名检测、风格选择等在翻译时做，导致等待时间长

### 解决方案
1. **预处理前置**：所有准备工作在翻译前完成
2. **简化流程**：翻译阶段只做API调用+流式接收
3. **10个独立脚本**：简单暴力，不用复杂多线程
4. **实时流式写入**：边收边写，立即看到结果

## 📁 项目结构

```
translation_workflow/
├── config/
│   ├── api_config.json          # API配置（max_tokens=100000, timeout=3600）
│   ├── env_config.json          # 环境配置（windows1/windows2/mac1）
│   └── base_prompt.txt          # 基础prompt模板
├── core/
│   ├── name_manager.py          # 人名管理（提取+分配+文件锁）
│   ├── task_manager.py          # 任务管理
│   └── preprocessor.py          # 预处理器（前置所有准备工作）
├── translators/
│   ├── translator_base.py       # 翻译器基类
│   ├── translator_1.py          # 翻译器1
│   ├── ...
│   └── translator_10.py         # 翻译器10
├── data/
│   ├── names_windows1.json      # Windows环境1的人名库
│   ├── names_windows2.json      # Windows环境2的人名库
│   ├── names_mac1.json          # Mac环境1的人名库
│   └── styles.json              # 写作风格
├── outputs/                     # 输出目录
│   └── [task_id]/
│       ├── content.txt          # 翻译结果
│       ├── task_info.json       # 任务信息
│       └── name_mapping.json    # 人名对照表
├── queue/
│   └── tasks.json               # 任务队列
├── main_gui.py                  # 主GUI程序
├── run_gui.py                   # GUI启动脚本
└── start_translators.bat        # 批量启动翻译器（Windows）
```

## 🚀 使用方法

### 方法1：使用GUI（推荐）

1. **启动GUI**
   ```bash
   python run_gui.py
   ```

2. **操作步骤**
   - 选择小说文件
   - 选择类型和写作风格
   - 选择环境（windows1/windows2/mac1）
   - 查看已用人名（可选）
   - 点击"开始翻译"

3. **自动处理**
   - 系统会自动创建任务
   - 可选择是否立即启动翻译器
   - 翻译器在后台运行，实时写入结果

### 方法2：手动启动多个翻译器

1. **创建任务**（使用GUI或代码）

2. **启动翻译器**

   **Windows（批量启动）：**
   ```cmd
   REM 启动5个翻译器（windows1环境）
   start_translators.bat windows1 5

   REM 启动10个翻译器（mac1环境）
   start_translators.bat mac1 10
   ```

   **手动启动单个：**
   ```bash
   # 翻译器1（windows1环境）
   python translators/translator_1.py windows1

   # 翻译器2（windows2环境）
   python translators/translator_2.py windows2

   # 翻译器3（mac1环境）
   python translators/translator_3.py mac1
   ```

### 方法3：编程方式

```python
from core.task_manager import TaskManager

# 创建任务
tm = TaskManager()
task_id = tm.create_task(
    novel_path="path/to/novel.txt",
    genre="Horror",
    style_index=0
)

print(f"任务创建: {task_id}")

# 然后手动启动翻译器
# python translators/translator_1.py windows1
```

## ⚙️ 配置说明

### API配置（config/api_config.json）

```json
{
  "api_key": "your-api-key",
  "base_url": "https://yunwuapi.com/v1/",
  "model": "gemini-2.5-pro",
  "temperature": 0.7,
  "max_tokens": 100000,    // 改为100000
  "timeout": 3600           // 1小时
}
```

### 环境配置（config/env_config.json）

```json
{
  "environments": {
    "windows1": {
      "names_file": "data/names_windows1.json",
      "description": "Windows环境1"
    },
    "windows2": {
      "names_file": "data/names_windows2.json",
      "description": "Windows环境2"
    },
    "mac1": {
      "names_file": "data/names_mac1.json",
      "description": "Mac环境1"
    }
  },
  "current_env": "windows1"
}
```

**重要**：每个环境使用独立的names.json，互不影响！

## 📊 工作流程

```
1. 用户选择文件、风格、环境
   ↓
2. 创建任务 → 立即生成任务记录文档
   ↓
3. 【预处理阶段 - 翻译前完成】
   - 读取小说内容
   - 提取中文人名
   - 从names.json分配英文名（加文件锁，立即标记used）
   - 生成人名对照表
   - 组装最终prompt（包含人名映射+写作风格）
   ↓
4. 发送翻译请求（简化的prompt）
   ↓
5. 流式接收 → 边收边写入 outputs/[task_id]/content.txt
   ↓
6. 完成！
```

## 🎨 特点

1. **速度快**
   - 预处理前置，翻译阶段纯粹API调用
   - 流式接收，立即写入
   - 不再有卡顿等待

2. **简单可靠**
   - 10个独立脚本，不用复杂多线程
   - 每个脚本独立运行
   - 出错不影响其他脚本

3. **多环境支持**
   - 3个独立的names.json
   - 可同时在不同机器运行
   - 人名互不冲突

4. **实时反馈**
   - 流式写入content.txt
   - 随时查看翻译进度
   - 任务状态实时更新

## 📝 输出说明

每个任务会在`outputs/[task_id]/`目录下生成：

- **content.txt** - 翻译结果（实时写入）
- **task_info.json** - 任务信息（状态、时间等）
- **name_mapping.json** - 人名对照表（中文→英文）

## 🔧 常见问题

**Q: 如何同时翻译多个小说？**
A: 在GUI中创建多个任务，然后启动多个翻译器（最多10个）

**Q: 翻译器卡住了怎么办？**
A: 直接关闭该翻译器，启动另一个即可

**Q: 如何查看人名使用情况？**
A: 在GUI中点击"刷新人名统计"

**Q: 如何重置人名使用次数？**
A: 手动编辑对应的names_xxx.json，将"used"改为0

**Q: 可以自定义prompt吗？**
A: 可以，编辑`config/base_prompt.txt`

## 📦 依赖

```bash
pip install openai
```

## 🚀 快速开始

1. 安装依赖
   ```bash
   pip install openai
   ```

2. 配置API（编辑`config/api_config.json`）

3. 启动GUI
   ```bash
   python run_gui.py
   ```

4. 享受超快的翻译体验！
