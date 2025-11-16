# API配置指南

## 自定义API URL配置

本程序支持使用自定义的OpenAI兼容API，包括：
- OpenAI官方API
- 国内API中转服务
- Azure OpenAI
- 本地部署的兼容模型

---

## 配置方法

### 方法1: 通过GUI配置（推荐）

1. **启动程序**
   ```bash
   python main.py
   ```

2. **在界面中填写**
   - **API Key**: 输入你的API密钥
   - **API URL**: 输入API的base_url地址
   - **线程数**: 设置并发翻译数量

3. **测试连接**
   - 点击"测试"按钮验证配置是否正确
   - 看到"✅ API连接成功"即可开始使用

### 方法2: 直接编辑配置文件

编辑 `data/config.json`:

```json
{
  "api_key": "你的API Key",
  "api_base_url": "https://your-api-url.com/v1",
  "max_workers": 10,
  "model": "gpt-5.1",
  "temperature": 0.8,
  "max_tokens": 100000,
  "cost_per_1k_input": 0.01,
  "cost_per_1k_output": 0.03
}
```

---

## 常见API配置示例

### 1. OpenAI官方API（默认）

```json
{
  "api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxx",
  "api_base_url": "https://api.openai.com/v1",
  "model": "gpt-4-turbo-preview"
}
```

### 2. 云雾API（示例）

```json
{
  "api_key": "sk-4FqZoOFgSYHP6Vfk9HGqhGyrPJjNTVwnaB6zVAbLp8UdlCln",
  "api_base_url": "https://yunwuapi.com/v1/",
  "model": "gpt-5.1",
  "max_tokens": 100000
}
```

### 3. Azure OpenAI

```json
{
  "api_key": "你的Azure API Key",
  "api_base_url": "https://你的资源名.openai.azure.com/openai/deployments/你的部署名",
  "model": "gpt-4"
}
```

### 4. 本地部署（如Ollama、LM Studio等）

```json
{
  "api_key": "not-needed",
  "api_base_url": "http://localhost:1234/v1",
  "model": "llama2"
}
```

### 5. 其他中转服务

根据你使用的服务商提供的文档填写：

```json
{
  "api_key": "服务商提供的Key",
  "api_base_url": "服务商提供的URL",
  "model": "服务商支持的模型名"
}
```

---

## 配置参数说明

### 基础配置

| 参数 | 说明 | 示例 |
|------|------|------|
| `api_key` | API密钥 | `sk-xxxxx` |
| `api_base_url` | API基础URL | `https://api.openai.com/v1` |
| `model` | 模型名称 | `gpt-5.1`, `gpt-4`, `gpt-3.5-turbo` |

**注意**: URL结尾的 `/v1` 通常是必需的

### 模型参数

| 参数 | 说明 | 默认值 | 范围 |
|------|------|--------|------|
| `temperature` | 创意度/随机性 | 0.8 | 0.0-2.0 |
| `max_tokens` | 最大输出长度 | 100000 | 1-模型上限 |
| `max_workers` | 并发线程数 | 10 | 1-20 |

**temperature说明**:
- 0.0-0.3: 更准确、一致
- 0.5-0.8: 平衡（推荐）
- 1.0-2.0: 更有创意

### 成本参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `cost_per_1k_input` | 每1000输入tokens成本（美元） | 0.01 |
| `cost_per_1k_output` | 每1000输出tokens成本（美元） | 0.03 |

根据你的API服务商价格调整这些值。

---

## 模型推荐

### GPT-5.1（最新）
- **优点**: 质量最高，支持更长上下文
- **缺点**: 成本较高
- **适合**: 要求高质量翻译

### GPT-4 Turbo
- **优点**: 质量好，速度快
- **缺点**: 成本中等
- **适合**: 平衡质量和成本

### GPT-3.5 Turbo
- **优点**: 成本低，速度快
- **缺点**: 质量稍差
- **适合**: 预算有限或大批量翻译

---

## 故障排除

### 问题1: API测试失败

**可能原因**:
- API Key错误
- URL格式不正确
- 网络连接问题
- 服务商限流

**解决方法**:
```bash
# 1. 检查URL格式（注意末尾的/v1）
正确: https://yunwuapi.com/v1/
错误: https://yunwuapi.com/v1  (少了斜杠)
错误: https://yunwuapi.com/    (少了v1)

# 2. 检查API Key（复制时注意不要有空格）

# 3. 测试网络
curl https://your-api-url.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### 问题2: 翻译时报错

**检查清单**:
- [ ] model名称是否正确（区分大小写）
- [ ] max_tokens是否超过模型限制
- [ ] API余额是否充足
- [ ] 是否触发了限流（降低线程数）

### 问题3: 成本显示不准确

编辑 `data/config.json`，修改成本参数：

```json
{
  "cost_per_1k_input": 0.005,   // 根据实际价格调整
  "cost_per_1k_output": 0.015   // 根据实际价格调整
}
```

---

## URL格式要求

### 正确格式

✅ `https://api.openai.com/v1`
✅ `https://yunwuapi.com/v1/`
✅ `http://localhost:1234/v1`

### 错误格式

❌ `https://api.openai.com` (缺少 /v1)
❌ `api.openai.com/v1` (缺少 https://)
❌ `https://api.openai.com/v1/chat/completions` (太详细了)

**规则**:
- 必须包含协议（http:// 或 https://）
- 通常以 `/v1` 结尾（某些服务可能不同）
- 只需要base URL，不需要具体的endpoint

---

## 安全建议

### 1. 保护API Key

- ✅ 不要在代码中硬编码
- ✅ 不要提交到Git仓库
- ✅ 不要分享给他人
- ✅ 定期轮换Key

### 2. 控制成本

```json
{
  "max_workers": 5,      // 降低并发数
  "max_tokens": 50000    // 限制输出长度
}
```

### 3. 测试配置

在批量翻译前：
1. 先用1本小说测试
2. 检查翻译质量
3. 确认成本可接受
4. 再开始大规模翻译

---

## 高级配置

### 使用环境变量

创建 `.env` 文件:

```bash
OPENAI_API_KEY=sk-xxxxxxxx
OPENAI_BASE_URL=https://api.openai.com/v1
```

修改代码读取环境变量（需要安装python-dotenv）：

```python
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
```

### 多配置切换

创建多个配置文件:

```
data/
├── config_official.json  # OpenAI官方
├── config_yunwu.json     # 云雾API
└── config_azure.json     # Azure
```

使用时复制到 `config.json`：

```bash
cp data/config_yunwu.json data/config.json
```

---

## 国内用户建议

如果无法访问OpenAI官方API，可以使用：

1. **API中转服务** (推荐)
   - 云雾API: https://yunwuapi.com
   - API2D: https://api2d.com
   - OpenAI-SB: https://openai-sb.com

2. **国内AI服务**
   - 通义千问
   - 文心一言
   - ChatGLM

   注意：需要确保API兼容OpenAI格式

3. **本地部署**
   - Ollama + llama2/mistral
   - LM Studio
   - Text Generation WebUI

---

## 验证配置

创建测试脚本 `test_api.py`:

```python
from openai import OpenAI

client = OpenAI(
    api_key="你的API Key",
    base_url="你的API URL"
)

response = client.chat.completions.create(
    model="gpt-5.1",
    messages=[
        {"role": "user", "content": "Hello, this is a test."}
    ],
    max_tokens=100
)

print(response.choices[0].message.content)
print(f"Tokens: {response.usage.total_tokens}")
```

运行测试:

```bash
python test_api.py
```

---

## 常见服务商对照表

| 服务商 | Base URL | 模型名称 | 备注 |
|--------|----------|----------|------|
| OpenAI官方 | https://api.openai.com/v1 | gpt-4, gpt-3.5-turbo | 需要国际网络 |
| 云雾API | https://yunwuapi.com/v1/ | gpt-5.1, gpt-4 | 国内可访问 |
| Azure OpenAI | 自定义 | gpt-4 | 企业用户 |
| API2D | https://api2d.com/v1 | 同OpenAI | 国内中转 |
| Ollama | http://localhost:11434/v1 | llama2, mistral | 本地部署 |

---

## 获取帮助

如有问题，请：
1. 查看本文档
2. 检查服务商文档
3. 查看程序错误信息
4. 提交Issue到GitHub

---

**最后更新**: 2025-11-16
**支持的OpenAI SDK版本**: >=1.0.0
