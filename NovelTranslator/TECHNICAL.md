# 技术文档 - Technical Documentation

## 架构设计

### 模块划分

项目采用模块化设计，分为4个核心模块：

1. **config.py** - 配置管理模块
2. **resource_mgr.py** - 资源管理模块
3. **translator.py** - 翻译逻辑模块
4. **main.py** - GUI界面和主控制模块

### 数据流程

```
用户操作 → GUI (main.py)
    ↓
配置管理 (config.py) ← 读取/写入 → config.json
    ↓
资源分配 (resource_mgr.py) ← 读取/更新 → styles.json, names.json
    ↓
翻译执行 (translator.py) ← 调用 → OpenAI API
    ↓
结果保存 → output/*.txt, summary.json
    ↓
状态更新 → GUI显示
```

## 核心模块详解

### 1. config.py - 配置管理

**职责**:
- 读写用户配置（API Key、线程数、模型参数）
- 管理翻译记录
- 计算成本

**关键类**:
```python
class ConfigManager:
    def __init__(self, data_dir: str = "data")
    def load_config() -> dict
    def save_config(config: dict)
    def get_api_key() -> str
    def set_api_key(api_key: str)
    def calculate_cost(input_tokens: int, output_tokens: int) -> float
    def add_record(record: dict)
```

**设计亮点**:
- 单一职责原则：只负责配置管理
- 文件IO封装：统一的读写接口
- 成本计算：基于token数量精确计算

### 2. resource_mgr.py - 资源管理

**职责**:
- 管理风格库和人名库
- 批量分配资源给多个文件
- 避免重复和冲突

**关键类**:
```python
class ResourceManager:
    def allocate_resources(files: List[str]) -> List[Dict]
    def update_name_usage(used_names: List[str])
    def extract_genre(filename: str) -> str
```

**核心算法 - allocate_resources**:

```python
def allocate_resources(self, files):
    resources = []
    used_names_batch = set()  # 关键：追踪本批次已用名字

    for file in files:
        # 1. 选风格：找使用次数最少的
        genre_data = styles[genre]
        min_idx = genre_data['used'].index(min(genre_data['used']))
        genre_data['used'][min_idx] += 1  # 立即+1，避免下一个也选这个

        # 2. 选人名：排除本批次已用的
        available = [n for n in names if n not in used_names_batch]
        selected = available[:20]  # 取前20个

        # 标记为已使用
        used_names_batch.update(selected)

    return resources
```

**设计亮点**:
- 批量分配：一次性处理所有文件，确保无冲突
- 公平轮换：使用次数最少优先
- Set去重：O(1)时间复杂度检查重复

### 3. translator.py - 翻译逻辑

**职责**:
- 构建翻译Prompt
- 调用API执行翻译
- 提取使用的人名
- 保存结果

**关键类**:
```python
class Translator:
    def build_prompt(style: str, names: list) -> str
    def translate_one(file_path, resource, status_callback, api_caller) -> Dict
    def extract_used_names(content: str, available_names: list) -> list
    def test_api_connection(api_caller) -> Dict
```

**Prompt构建**:

```python
def build_prompt(self, style, names):
    base = """
    你是一个英语母语网文创作者...
    【翻译本土化要求】...
    【格式要求】...
    """
    style_part = f"\n\n【写作风格】\n{style}"
    names_part = f"\n\n【可用角色名】\n{', '.join(names)}"
    return base + style_part + names_part
```

**设计亮点**:
- 回调机制：通过callback实时更新状态
- 依赖注入：api_caller作为参数传入，方便测试
- 正则提取：精确识别使用的人名

### 4. main.py - GUI和主控制

**职责**:
- 创建用户界面
- 管理多线程翻译
- 实时状态更新
- 用户交互处理

**关键类**:
```python
class TranslatorApp:
    def __init__(self)
    def create_widgets(self)
    def start_translation(self)
    def translate_all(self)  # 在后台线程执行
    def update_status(self, title, status, elapsed, cost)
    def call_api(self, prompt, content) -> tuple
```

**多线程架构**:

```python
def start_translation(self):
    # 1. 主线程：启动后台线程
    threading.Thread(target=self.translate_all, daemon=True).start()

    # 2. 定时更新UI
    self.update_progress()

def translate_all(self):
    # 后台线程：执行翻译
    executor = ThreadPoolExecutor(max_workers=10)

    futures = []
    for file, resource in zip(files, resources):
        future = executor.submit(translate_one, ...)
        futures.append(future)

    # 等待完成
    for future in as_completed(futures):
        result = future.result()

def update_status(self, title, status, elapsed, cost):
    # 工作线程 → 主线程：线程安全更新
    self.window.after(0, _update)
```

**设计亮点**:
- 三层线程结构：
  - 主线程（GUI）
  - 后台线程（管理）
  - 工作线程（翻译）
- 线程安全：使用 `window.after()` 跨线程更新GUI
- 非阻塞：用户界面始终响应

## 数据结构设计

### styles.json 结构

```json
{
  "类型名": {
    "authors": ["作者1", "作者2"],
    "styles": ["风格描述1", "风格描述2"],
    "used": [使用次数1, 使用次数2]
  }
}
```

**设计考虑**:
- 数组索引对应：authors[i] ↔ styles[i] ↔ used[i]
- 使用次数与风格绑定，便于轮换
- 可扩展：轻松添加新类型和风格

### names.json 结构

```json
{
  "male": [
    {"name": "Alexander", "used": 3}
  ],
  "female": [
    {"name": "Isabella", "used": 5}
  ]
}
```

**设计考虑**:
- 性别分类：方便按需选择
- 使用次数记录：实现公平分配
- 对象数组：便于扩展属性（如国籍、时代）

### summary.json 结构

```json
{
  "records": [
    {
      "date": "2025-01-16 10:30:00",
      "original": "霸道总裁",
      "translated": "output/霸道总裁_translated.txt",
      "genre": "Romance",
      "author_style": "Colleen Hoover",
      "names": ["Alexander", "Isabella"],
      "word_count": 20000,
      "time": 192,
      "cost": 0.15
    }
  ]
}
```

**设计考虑**:
- 完整记录：包含所有关键信息
- 便于分析：可统计成本、效率、风格使用
- 可追溯：通过date和names追踪历史

## 关键技术点

### 1. 线程安全的GUI更新

**问题**: tkinter不是线程安全的，工作线程直接更新GUI会崩溃

**解决方案**:
```python
def update_status(self, title, status, elapsed, cost):
    def _update():
        # 实际的UI更新代码
        self.status_text.insert(tk.END, text)

    # 在主线程中执行
    self.window.after(0, _update)
```

### 2. 资源分配的原子性

**问题**: 多个文件可能同时选择同一个风格或人名

**解决方案**:
```python
# 立即更新使用次数，而不是等翻译完成
genre_data['used'][min_idx] += 1

# 使用Set追踪本批次已分配的名字
used_names_batch = set()
```

### 3. 人名提取的准确性

**问题**: 简单的字符串查找会误匹配（如"Alex"匹配"Alexander"）

**解决方案**:
```python
# 使用单词边界正则
pattern = r'\b' + re.escape(name) + r'\b'
if re.search(pattern, content, re.IGNORECASE):
    used_names.append(name)
```

### 4. 成本计算的精度

**问题**: 浮点数精度问题可能导致成本不准确

**解决方案**:
```python
# 使用round保留两位小数
cost = round((input_tokens / 1000) * rate_in + (output_tokens / 1000) * rate_out, 2)
```

## 性能优化

### 1. 并发翻译

- 使用 `ThreadPoolExecutor` 管理线程池
- 线程数可配置（1-20）
- 使用 `as_completed()` 优先处理完成的任务

### 2. 批量资源分配

- 一次性分配所有资源，避免重复IO
- 使用Set快速检查重复（O(1)）
- 延迟保存：翻译全部完成后统一保存

### 3. GUI响应性

- 长时间操作在后台线程执行
- 定时器（1秒）更新进度，避免过于频繁
- 使用ScrolledText自动滚动，无需手动管理

## 错误处理

### 1. API调用失败

```python
try:
    response = openai.chat.completions.create(...)
except Exception as e:
    return {
        'success': False,
        'error': str(e)
    }
```

### 2. 文件读写失败

```python
def read_file(self, file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise Exception(f"文件读取失败: {str(e)}")
```

### 3. JSON解析失败

```python
def load_config(self):
    if os.path.exists(self.config_file):
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default_config
    return default_config
```

## 扩展性设计

### 1. 添加新的翻译引擎

在 `translator.py` 中，API调用通过回调函数注入：

```python
def translate_one(self, file_path, resource, status_callback, api_caller):
    # api_caller 可以是任何实现 (prompt, content) -> (result, in_tokens, out_tokens) 的函数
    translated, in_tokens, out_tokens = api_caller(prompt, content)
```

只需实现新的 `api_caller` 函数即可支持其他API。

### 2. 添加新的小说类型

编辑 `data/styles.json`：

```json
{
  "NewGenre": {
    "authors": ["Author1", "Author2"],
    "styles": ["Style description 1", "Style description 2"],
    "used": [0, 0]
  }
}
```

### 3. 自定义Prompt模板

在 `translator.py` 中修改 `build_prompt` 方法，或添加模板系统：

```python
def build_prompt(self, style, names, template="default"):
    if template == "custom":
        return custom_template.format(style=style, names=names)
    else:
        return default_template
```

## 测试策略

### 单元测试

```python
# test_resource_mgr.py
def test_allocate_resources():
    mgr = ResourceManager()
    files = ["book1_Romance.txt", "book2_Romance.txt"]
    resources = mgr.allocate_resources(files)

    # 测试风格不重复
    assert resources[0]['style'] != resources[1]['style']

    # 测试人名不重复
    names1 = {n['name'] for n in resources[0]['names']}
    names2 = {n['name'] for n in resources[1]['names']}
    assert len(names1 & names2) == 0
```

### 集成测试

```python
# test_integration.py
def test_full_translation():
    app = TranslatorApp()

    # 模拟API调用
    def mock_api(prompt, content):
        return ("translated text", 1000, 2000)

    # 执行翻译
    result = app.translator.translate_one(
        "test.txt",
        resource,
        lambda *args: None,
        mock_api
    )

    assert result['success'] == True
```

## 部署指南

### Windows打包

```bash
python build_exe.py
```

生成: `dist/NovelTranslator.exe`

### Linux打包

使用 PyInstaller：

```bash
pyinstaller --onefile --windowed main.py
```

或使用Docker:

```dockerfile
FROM python:3.9
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
```

## 性能指标

### 翻译速度
- 2万字小说: 2-5分钟
- 取决于API响应速度和网络延迟

### 资源占用
- 内存: 约50-100MB
- CPU: 主要等待IO，占用低
- 磁盘: 每本书约50-200KB

### 并发效率
- 5个线程: 约5倍速度提升
- 10个线程: 约8倍速度提升（受API限流影响）
- 20个线程: 可能触发限流，实际效率下降

## 安全考虑

### API Key保护
- 不提交config.json到git（.gitignore）
- 界面显示为•••••
- 仅本地存储，不上传云端

### 文件安全
- 仅读取txt文件
- 输出到独立output目录
- 不执行用户输入的代码

### 错误信息
- 不在错误信息中暴露API Key
- 记录错误但不记录敏感信息

## 贡献指南

### 代码风格
- 遵循PEP 8
- 使用类型注解
- 添加文档字符串

### 提交规范
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- refactor: 重构代码
- test: 添加测试

### Pull Request流程
1. Fork项目
2. 创建特性分支
3. 提交代码并测试
4. 发起Pull Request
5. 代码审查
6. 合并到main

---

**维护者**: Claude Code
**最后更新**: 2025-11-16
