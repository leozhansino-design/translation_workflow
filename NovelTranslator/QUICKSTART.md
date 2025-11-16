# 快速开始指南 - Quick Start Guide

## 🚀 5分钟上手

### Windows用户

1. **安装依赖**
   ```cmd
   双击运行 install.bat
   ```

2. **启动程序**
   ```cmd
   双击运行 run.bat
   ```

3. **配置API Key**
   - 在程序界面输入你的OpenAI API Key
   - 点击"测试"按钮
   - 看到"✅ API连接成功"即可

4. **准备小说文件**
   - 文件命名格式: `书名_类型.txt`
   - 示例: `霸道总裁_Romance.txt`
   - 支持15种类型（见下方列表）

5. **开始翻译**
   - 点击"添加文件"选择txt文件
   - 设置线程数（建议5-10）
   - 点击"🚀 开始翻译"
   - 等待完成

6. **查看结果**
   - 翻译完成的文件在 `output/` 目录
   - 文件名: `书名_translated.txt`

### Linux/Mac用户

1. **安装依赖**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

2. **启动程序**
   ```bash
   chmod +x run.sh
   ./run.sh
   ```

3. 后续步骤同Windows

---

## 📁 文件命名规则

格式: `书名_类型.txt`

### 支持的类型（15种）

| 类型代码 | 说明 | 示例 |
|---------|------|------|
| `Romance` | 言情/爱情 | 霸道总裁_Romance.txt |
| `Fantasy` | 玄幻/奇幻 | 穿越异世_Fantasy.txt |
| `Urban` | 都市/现代 | 都市修仙_Urban.txt |
| `Sci-Fi` | 科幻 | 星际争霸_Sci-Fi.txt |
| `Mystery` | 悬疑/推理 | 密室逃脱_Mystery.txt |
| `Horror` | 恐怖/惊悚 | 午夜凶铃_Horror.txt |
| `Adventure` | 冒险 | 寻宝之旅_Adventure.txt |
| `Historical` | 历史/古代 | 大唐风云_Historical.txt |
| `Crime` | 犯罪/警匪 | 缉毒警察_Crime.txt |
| `LGBTQ+` | 同志文学 | 彩虹之恋_LGBTQ+.txt |
| `Paranormal` | 超自然 | 吸血鬼日记_Paranormal.txt |
| `System` | 系统流 | 无敌系统_System.txt |
| `Reborn` | 重生文 | 重生之首富_Reborn.txt |
| `Revenge` | 复仇文 | 复仇千金_Revenge.txt |
| `Fanfiction` | 同人文 | HP同人_Fanfiction.txt |

---

## ⚙️ 配置说明

### API Key获取

1. 访问 [OpenAI Platform](https://platform.openai.com)
2. 注册/登录账号
3. 进入 API Keys 页面
4. 创建新的API Key
5. 复制Key到程序中

### 线程数设置

| 线程数 | 适用场景 | 速度 | 成本 |
|-------|---------|------|------|
| 1-3 | 测试/单本 | 慢 | 低 |
| 5-10 | **推荐** | 快 | 中 |
| 10-20 | 大批量 | 很快 | 高（可能限流） |

### 模型选择

编辑 `data/config.json`:

```json
{
  "model": "gpt-4-turbo-preview"  // 推荐
  // "model": "gpt-4"  // 质量更好，成本更高
  // "model": "gpt-3.5-turbo"  // 成本低，质量稍差
}
```

---

## 💰 成本估算

| 小说字数 | 预计成本 | 翻译时间 |
|---------|---------|---------|
| 2万字 | $0.15-$0.25 | 2-5分钟 |
| 5万字 | $0.40-$0.60 | 5-10分钟 |
| 10万字 | $0.80-$1.20 | 10-20分钟 |

注: 使用 gpt-4-turbo-preview，10线程并发

---

## ❓ 常见问题

### Q1: API测试失败？

**解决**:
1. 检查API Key是否正确
2. 确认账户有余额
3. 检查网络连接
4. 尝试更换网络（VPN）

### Q2: 翻译卡住不动？

**解决**:
1. 检查网络连接
2. 降低线程数
3. 关闭程序重试
4. 查看 `data/summary.json` 是否有记录

### Q3: 翻译质量不满意？

**解决**:
1. 使用 gpt-4 模型
2. 编辑 `data/styles.json` 自定义风格
3. 在Prompt中添加更多要求
4. 找专业人员后期润色

### Q4: 人名重复怎么办？

**解决**:
1. 在 `data/names.json` 添加更多名字
2. 分批翻译（每批不超过10本）
3. 手动修改重复的人名

### Q5: 如何修改风格？

**步骤**:
1. 打开 `data/styles.json`
2. 找到对应类型（如 Romance）
3. 修改 `styles` 数组中的描述
4. 保存文件
5. 重新运行程序

---

## 📊 使用建议

### 第一次使用

1. ✅ 用1本小说测试
2. ✅ 检查翻译质量
3. ✅ 确认成本可接受
4. ✅ 再开始批量翻译

### 批量翻译

1. ✅ 同类型小说放一起翻译
2. ✅ 每批不超过10-20本
3. ✅ 设置合适的线程数
4. ✅ 留意API余额

### 质量控制

1. ✅ 选择合适的风格
2. ✅ 检查Blurb是否吸引人
3. ✅ 验证人名是否合理
4. ✅ 用Grammarly检查语法
5. ✅ 找母语者校对

---

## 🔧 故障排除

### 程序无法启动

```bash
# 检查Python版本（需要3.7+）
python --version

# 重新安装依赖
pip install -r requirements.txt

# 使用Python直接运行
python main.py
```

### 依赖安装失败

```bash
# 升级pip
python -m pip install --upgrade pip

# 使用镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### GUI显示异常

```bash
# Linux需要安装tkinter
sudo apt-get install python3-tk

# Mac需要
brew install python-tk
```

---

## 📚 进阶技巧

### 自定义Prompt

编辑 `translator.py` 中的 `build_prompt` 方法:

```python
def build_prompt(self, style, names):
    base = """
    你的自定义要求...
    """
    return base + style + names
```

### 批量重命名文件

使用Python脚本:

```python
import os

for f in os.listdir('.'):
    if f.endswith('.txt'):
        # 自动添加类型
        new_name = f.replace('.txt', '_Romance.txt')
        os.rename(f, new_name)
```

### 导出到Wattpad

1. 翻译完成后
2. 复制标题、Blurb、章节
3. 在Wattpad创建新书
4. 粘贴内容
5. 设置封面和标签

---

## 🎯 下一步

- [ ] 翻译你的第一本小说
- [ ] 自定义风格库
- [ ] 添加更多人名
- [ ] 分享给朋友
- [ ] 提供反馈

---

## 📞 获取帮助

- 📖 详细文档: 查看 `USAGE.md`
- 🔧 技术文档: 查看 `TECHNICAL.md`
- 📝 项目说明: 查看 `README.md`
- 💬 提问反馈: GitHub Issues

---

**提示**: 建议先用示例文件测试，熟悉流程后再翻译正式内容。

祝你翻译愉快！🎉
