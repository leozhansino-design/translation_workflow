# 更新说明 v1.1.0

## 🎉 新功能

### 1. 自定义API URL配置

现在支持配置自定义的API base URL，可以使用：

- OpenAI官方API
- 国内API中转服务（如云雾API、API2D等）
- Azure OpenAI
- 本地部署的兼容模型

**配置方法**:

#### 通过GUI（推荐）
1. 打开程序
2. 在"API URL"输入框填入你的API地址
3. 例如：`https://yunwuapi.com/v1/`
4. 点击"Test Connection"测试

#### 通过配置文件
编辑 `data/config.json`:
```json
{
  "api_key": "你的API Key",
  "api_base_url": "https://yunwuapi.com/v1/",
  "model": "gpt-5.1",
  "max_tokens": 100000
}
```

详细配置说明请查看 [API_CONFIG.md](API_CONFIG.md)

---

### 2. 全新Apple风格UI

界面完全重新设计，采用现代化的苹果风格：

**设计特点**:
- ✨ 简洁扁平化设计
- ✨ 圆角按钮和卡片
- ✨ 柔和的配色方案
- ✨ 更大的间距和留白
- ✨ 清晰的视觉层次
- ✨ 悬停效果

**配色方案**:
- 主色：#007AFF（苹果蓝）
- 成功：#34C759（绿色）
- 警告：#FF9500（橙色）
- 危险：#FF3B30（红色）
- 背景：#F5F5F7（浅灰）
- 卡片：#FFFFFF（纯白）

**对比截图**:
- 旧版：传统深色标题栏 + 基础按钮
- 新版：现代白色卡片 + 圆角元素

---

### 3. 完整名字格式（Full Name）

人名系统全面升级，现在所有角色名都包含完整的firstname + lastname：

**之前**:
```
"Isabella", "Alexander", "Sophia"
```

**现在**:
```
"Isabella Rose", "Alexander Blake", "Sophia Clarke"
```

**影响范围**:
- ✅ names.json 格式升级（新增firstname, lastname, fullname字段）
- ✅ Prompt明确要求使用完整名字
- ✅ 人名提取算法支持firstname/lastname/fullname识别
- ✅ 避免人名冲突的逻辑优化

**示例**:
```json
{
  "firstname": "Alexander",
  "lastname": "Blake",
  "fullname": "Alexander Blake",
  "used": 0
}
```

**Prompt要求**:
> 首次介绍角色时必须使用完整全名（如 Alexander Blake），之后可以用firstname（Alexander）或lastname（Blake）或昵称。

---

### 4. 更新默认模型配置

**新的默认值**:
```json
{
  "model": "gpt-5.1",
  "max_tokens": 100000
}
```

**说明**:
- 模型更新为gpt-5.1（如果你的API支持）
- max_tokens提升到100000，支持更长的翻译输出
- 可根据实际API支持情况修改

---

## 🔧 改进优化

### API调用优化

升级到新版OpenAI SDK客户端：

**之前**:
```python
import openai
openai.api_key = api_key
response = openai.chat.completions.create(...)
```

**现在**:
```python
from openai import OpenAI
client = OpenAI(
    api_key=api_key,
    base_url=api_base_url  # 支持自定义URL
)
response = client.chat.completions.create(...)
```

**优势**:
- ✅ 更好的类型提示
- ✅ 更清晰的错误信息
- ✅ 原生支持base_url配置
- ✅ 更稳定的连接管理

---

### Prompt优化

**人名部分**:
```
【可用角色名（必须使用Full Name格式）】
Alexander Blake (first: Alexander, last: Blake),
Isabella Rose (first: Isabella, last: Rose),
...

重要：首次介绍角色时必须使用完整全名（如 Alexander Blake），
之后可以用firstname（Alexander）或lastname（Blake）或昵称。
确保不与其他小说重复。
```

**翻译要求**:
- 明确要求firstname + lastname格式
- 提供firstname和lastname的明确标注
- 强调首次出现必须用全名

---

## 📁 文件变更

### 新增文件
- `API_CONFIG.md` - API配置详细指南
- `main_old.py` - 旧版UI备份
- `UPDATE_v1.1.md` - 本更新说明

### 修改文件
- `main.py` - 全新Apple风格UI
- `config.py` - 新增API URL管理方法
- `translator.py` - 优化Prompt和人名提取
- `resource_mgr.py` - 支持fullname格式
- `data/config.json` - 新增api_base_url字段
- `data/names.json` - 升级为完整名字格式

---

## 🚀 升级指南

### 从v1.0.0升级到v1.1.0

1. **备份数据** (如果有自定义配置):
   ```bash
   cp data/config.json data/config_backup.json
   cp data/names.json data/names_backup.json
   ```

2. **更新代码**:
   ```bash
   git pull origin main
   # 或下载最新版本覆盖
   ```

3. **检查配置**:
   - 打开 `data/config.json`
   - 确认 `api_base_url` 字段存在
   - 如果没有，添加：`"api_base_url": "https://api.openai.com/v1"`

4. **更新人名库** (可选):
   - 如果你自定义过names.json
   - 需要手动转换为新格式
   - 或者使用默认的新版本

5. **测试运行**:
   ```bash
   python main.py
   ```

6. **配置API**:
   - 在界面填入API Key和URL
   - 点击"Test Connection"测试
   - 确认连接成功后开始使用

---

## ⚠️ 注意事项

### 1. names.json格式变更

**如果你有自定义的人名库**，需要手动转换格式：

**旧格式**:
```json
{"name": "Alexander", "used": 0}
```

**新格式**:
```json
{
  "firstname": "Alexander",
  "lastname": "Blake",
  "fullname": "Alexander Blake",
  "used": 0
}
```

**转换脚本** (`convert_names.py`):
```python
import json

# 定义lastname列表
lastnames = ["Blake", "Cross", "Knight", "Hart", "Stone", ...]

# 读取旧文件
with open('data/names_old.json', 'r') as f:
    old = json.load(f)

new = {"male": [], "female": []}

for gender in ['male', 'female']:
    for i, name_obj in enumerate(old[gender]):
        firstname = name_obj['name']
        lastname = lastnames[i % len(lastnames)]
        new[gender].append({
            "firstname": firstname,
            "lastname": lastname,
            "fullname": f"{firstname} {lastname}",
            "used": name_obj['used']
        })

# 保存新文件
with open('data/names.json', 'w') as f:
    json.dump(new, f, indent=2)
```

### 2. API URL配置

**注意URL格式**:
- ✅ `https://api.openai.com/v1`（有/v1）
- ✅ `https://yunwuapi.com/v1/`（有/v1/）
- ❌ `https://api.openai.com`（缺少/v1）
- ❌ `api.openai.com/v1`（缺少https://）

### 3. 模型兼容性

- 确认你的API支持配置的模型名称
- gpt-5.1 可能不是所有API都支持
- 可以改为 `gpt-4` 或 `gpt-3.5-turbo`

---

## 🐛 已知问题

### 1. macOS字体显示

如果你在macOS上运行，系统会自动使用SF Pro字体。
在Windows/Linux上，会fallback到系统默认字体。

**解决方法**:
可以修改 `main.py` 中的字体配置：
```python
FONTS = {
    'title': ('Arial', 20, 'bold'),  # 改为Arial
    'heading': ('Arial', 14, 'bold'),
    'body': ('Arial', 11),
    ...
}
```

### 2. 圆角按钮在某些系统上显示异常

Tkinter的Canvas圆角绘制在某些系统上可能有锯齿。
这是正常现象，不影响功能。

---

## 📚 文档资源

- [API配置指南](API_CONFIG.md) - 详细的API配置说明
- [使用指南](USAGE.md) - 完整的使用教程
- [快速开始](QUICKSTART.md) - 5分钟上手
- [技术文档](TECHNICAL.md) - 架构和技术细节

---

## 🔮 下一版本计划 (v1.2.0)

- [ ] 支持暂停/恢复翻译
- [ ] 拖拽添加文件
- [ ] 更详细的进度条
- [ ] 翻译预览功能
- [ ] 自定义Prompt编辑器
- [ ] 支持更多AI模型（Claude, Gemini）

---

## 🙏 反馈与支持

如有问题或建议：
1. 查看文档：README.md、USAGE.md
2. 检查配置：data/config.json
3. 测试API：运行测试连接
4. 提交Issue：GitHub Issues

---

**版本**: v1.1.0
**发布日期**: 2025-11-16
**作者**: Claude Code

感谢使用！🎉
