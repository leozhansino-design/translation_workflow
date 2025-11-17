# 快速开始 - Novel Translator 优化版

## 🎯 3分钟上手

### 1. 安装依赖
```bash
pip install openai
```

### 2. 配置API密钥
编辑 `config/api_config.json`，填入你的API密钥：
```json
{
  "api_key": "your-api-key-here",
  "base_url": "https://yunwuapi.com/v1/",
  ...
}
```

### 3. 启动GUI
```bash
python run_gui.py
```

### 4. 开始翻译
1. 点击"浏览"选择小说文件
2. 选择类型（如：Romance, Horror）
3. 选择写作风格
4. 选择环境（windows1/windows2/mac1）
5. 点击"开始翻译"
6. 确认启动翻译器

### 5. 查看结果
翻译结果保存在：`outputs/[task_id]/content.txt`

---

## 🚀 高级用法

### 同时翻译多个小说

**方法1：使用批处理脚本（Windows）**
```cmd
REM 创建多个任务后，批量启动10个翻译器
start_translators.bat windows1 10
```

**方法2：手动启动多个翻译器**
```bash
# 终端1
python translators/translator_1.py windows1

# 终端2
python translators/translator_2.py windows1

# 终端3
python translators/translator_3.py windows2
```

### 不同环境使用不同人名库

系统支持3个独立环境，每个环境有独立的人名库：

- **windows1** → `data/names_windows1.json`
- **windows2** → `data/names_windows2.json`
- **mac1** → `data/names_mac1.json`

这意味着你可以：
- 在不同机器上同时运行，人名互不冲突
- 为不同类型的小说使用不同的人名池

---

## 🔧 常见操作

### 查看人名使用情况
在GUI中点击"刷新人名统计"按钮

### 重置人名使用次数
编辑对应的 `data/names_xxx.json`，将所有 `"used"` 改为 `0`

### 自定义prompt
编辑 `config/base_prompt.txt`

### 添加新的写作风格
编辑 `data/styles.json`

---

## 📊 流程说明

```
用户创建任务
    ↓
系统预处理（2-5秒）
├─ 读取小说
├─ 提取中文人名
├─ 分配英文名（加锁）
├─ 生成人名对照表
└─ 组装最终prompt
    ↓
发送API请求
    ↓
流式接收（实时写入content.txt）
    ↓
完成！
```

**关键优化**：
- ✅ 所有准备工作在翻译前完成
- ✅ 翻译阶段只做API调用+接收
- ✅ 流式写入，实时可见
- ✅ 不再有长时间等待

---

## ❓ 问题排查

### API连接失败
1. 检查 `config/api_config.json` 中的API密钥
2. 确认网络连接正常
3. 验证base_url是否正确

### 人名提取不准确
系统使用简单规则提取人名（2-4个连续中文字符，出现≥3次）。
如果需要更准确的提取，可以：
1. 手动编辑 `outputs/[task_id]/name_mapping.json`
2. 修改 `core/name_manager.py` 中的提取逻辑

### 翻译结果不满意
1. 尝试不同的写作风格
2. 修改 `config/base_prompt.txt`
3. 调整 `config/api_config.json` 中的 `temperature`

---

## 🎓 技术细节

### 10个独立脚本的优势
- **简单**：不用复杂的多线程/多进程
- **稳定**：一个脚本出错不影响其他
- **灵活**：随时启动/停止
- **可扩展**：需要更多就再加脚本

### 文件锁机制
`name_manager.py` 使用 `fcntl.flock()` 保护 `names.json`，
确保多个翻译器同时运行时不会冲突。

### 流式输出
使用 OpenAI 的 `stream=True` 参数，实时接收翻译结果并写入文件。

---

## 💡 提示

1. **批量处理**：创建多个任务，然后启动多个翻译器并行处理
2. **监控进度**：实时查看 `outputs/[task_id]/content.txt` 的大小
3. **备份人名库**：定期备份 `data/names_xxx.json`
4. **日志记录**：翻译器会在终端输出详细日志

---

**享受超快的翻译体验！** 🚀
