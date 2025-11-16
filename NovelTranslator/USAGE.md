# 使用指南

## 快速开始

### 第一步：安装依赖

```bash
cd NovelTranslator
pip install -r requirements.txt
```

### 第二步：运行程序

```bash
python main.py
```

### 第三步：配置API Key

1. 在程序界面输入你的OpenAI API Key
2. 点击"测试"按钮验证连接
3. 看到"✅ API连接成功"即可

### 第四步：准备小说文件

**重要**: 文件必须按照 `书名_类型.txt` 格式命名

示例:
```
霸道总裁爱上我_Romance.txt
穿越异世界_Fantasy.txt
重生之都市修仙_Urban.txt
星际争霸_Sci-Fi.txt
```

支持的15种类型:
- `Fantasy` - 玄幻/奇幻
- `Romance` - 言情/爱情
- `Urban` - 都市/现代
- `Sci-Fi` - 科幻
- `Mystery` - 悬疑/推理
- `Horror` - 恐怖/惊悚
- `Adventure` - 冒险
- `Historical` - 历史/古代
- `Crime` - 犯罪/警匪
- `LGBTQ+` - 同志文学
- `Paranormal` - 超自然
- `System` - 系统流
- `Reborn` - 重生文
- `Revenge` - 复仇文
- `Fanfiction` - 同人文

### 第五步：添加文件

**方法1**: 添加单个或多个文件
- 点击"添加文件"
- 选择一个或多个txt文件

**方法2**: 添加整个文件夹
- 点击"添加文件夹"
- 选择包含多个txt文件的文件夹
- 程序会自动添加所有txt文件

### 第六步：设置线程数

- 线程数决定同时翻译多少本书
- 建议设置: 5-10
- 太高可能触发API限流
- 太低会浪费时间

### 第七步：开始翻译

1. 点击"🚀 开始翻译"按钮
2. 确认翻译数量和线程数
3. 等待翻译完成

### 第八步：查看结果

翻译完成的文件在 `output/` 目录:
```
output/
├── 霸道总裁爱上我_translated.txt
├── 穿越异世界_translated.txt
└── 重生之都市修仙_translated.txt
```

## 进阶功能

### 自定义风格

编辑 `data/styles.json`:

```json
{
  "Romance": {
    "authors": ["Colleen Hoover", "Nicholas Sparks"],
    "styles": [
      "你的自定义风格描述...",
      "另一个风格描述..."
    ],
    "used": [0, 0]
  }
}
```

### 添加新人名

编辑 `data/names.json`:

```json
{
  "male": [
    {"name": "YourName", "used": 0}
  ],
  "female": [
    {"name": "YourName", "used": 0}
  ]
}
```

### 查看翻译历史

打开 `data/summary.json`:

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

### 修改模型配置

编辑 `data/config.json`:

```json
{
  "api_key": "your-key",
  "max_workers": 10,
  "model": "gpt-4-turbo-preview",  // 可改为 gpt-4, gpt-3.5-turbo
  "temperature": 0.8,               // 创意度 0-1
  "max_tokens": 50000,              // 最大输出长度
  "cost_per_1k_input": 0.01,        // 输入成本/千tokens
  "cost_per_1k_output": 0.03        // 输出成本/千tokens
}
```

## 打包成exe

如果你想分享给不懂编程的朋友:

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行打包脚本
python build_exe.py

# 3. 在 dist/ 目录找到
# NovelTranslator.exe
```

把整个文件夹（包括data/和output/）打包给朋友即可。

## 故障排除

### 问题1: API测试失败

**原因**:
- API Key错误
- 网络连接问题
- 余额不足

**解决**:
1. 检查API Key是否正确
2. 测试网络连接
3. 登录OpenAI查看余额

### 问题2: 翻译失败

**原因**:
- 文件编码不是UTF-8
- 文件太大超过token限制
- API调用超时

**解决**:
1. 用记事本另存为UTF-8编码
2. 把大文件拆分成多个小文件
3. 降低线程数，避免并发过高

### 问题3: 人名重复

**原因**:
- 人名库太小
- 同时翻译的书太多

**解决**:
1. 在 `data/names.json` 添加更多人名
2. 分批翻译，不要一次翻译太多

### 问题4: 风格不满意

**原因**:
- 默认风格不适合你的小说类型

**解决**:
1. 编辑 `data/styles.json`
2. 修改对应类型的风格描述
3. 添加更多细节要求

## 成本控制

### 预估成本

- **2万字小说**: ~$0.15 - $0.25
- **5万字小说**: ~$0.40 - $0.60
- **10万字小说**: ~$0.80 - $1.20

### 降低成本

1. 使用 `gpt-3.5-turbo` 而不是 `gpt-4`
2. 降低 `max_tokens`
3. 删除小说中的无用内容（广告、作者说等）

### 批量优惠

OpenAI有批量API价格，可以:
1. 攒够一批小说
2. 使用批量API（需要修改代码）
3. 成本可降低50%

## 最佳实践

### 文件准备

1. ✅ 使用UTF-8编码
2. ✅ 删除广告和无关内容
3. ✅ 确保章节分明
4. ✅ 正确命名（书名_类型.txt）
5. ❌ 不要包含图片或特殊字符

### 翻译设置

1. **首次测试**: 用1-2本书测试质量
2. **批量翻译**: 确认质量后再批量处理
3. **线程数**: 5-10最佳
4. **文件大小**: 单个文件最好不超过10万字

### 质量检查

翻译完成后检查:
1. 标题是否吸引人
2. Blurb是否精彩
3. 人名是否合理
4. 章节标题是否有创意
5. 文风是否自然

### 后期处理

1. 用Grammarly检查语法
2. 找英语母语者校对
3. 调整章节长度（保持1000词以上）
4. 优化Blurb（关键的推广文案）

## 高级技巧

### 技巧1: 风格混搭

在 `styles.json` 中组合多个作者风格:

```
"Write in Colleen Hoover's emotional style combined with Emily Henry's witty dialogue..."
```

### 技巧2: 针对平台优化

为Wattpad/Kindle/Webnovel等平台定制风格:

```
"Write for Wattpad readers: short chapters, cliffhangers, present tense, diverse cast..."
```

### 技巧3: 保留关键词

在翻译时保留某些中文特色:

```
"Keep martial arts terms like 'Qi', 'Dantian', 'Meridian' when translating cultivation novels..."
```

### 技巧4: 批量重命名

如果文件命名不规范，使用Python脚本批量重命名:

```python
import os
for f in os.listdir('.'):
    if f.endswith('.txt'):
        # 自动添加类型
        new_name = f.replace('.txt', '_Romance.txt')
        os.rename(f, new_name)
```

## 常见问题

**Q: 能同时翻译100本书吗？**
A: 技术上可以，但建议分批（每批10-20本），避免API限流。

**Q: 翻译质量如何？**
A: 使用GPT-4质量很好，GPT-3.5稍差但够用。建议先测试。

**Q: 能翻译成其他语言吗？**
A: 可以，修改translator.py中的prompt即可。

**Q: 能自动发布到Wattpad吗？**
A: 目前不支持，需要手动发布。可以考虑用Wattpad API实现。

**Q: 翻译速度如何？**
A: 取决于文件大小和线程数，通常2万字需要2-5分钟。

---

**需要帮助？**
- 查看 README.md
- 检查 data/ 目录的配置文件
- 阅读代码中的注释
