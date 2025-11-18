# 小说翻译工具 - 使用说明

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 运行应用
```bash
python main.py
```

## 功能特点

### ✅ 已实现的优化
1. **快速翻译** - 去除所有后处理，直接流式接收结果
2. **并行翻译** - 每个文件独立线程，互不阻塞
3. **简化输出** - 只创建 `output/文件名/content.txt`
4. **自动识别** - 从文件名自动提取genre（如：`xxx_Horror.txt` → Horror）
5. **人名预分配** - 翻译前就分配好人名，避免重复检测
6. **Prompt预览** - 每个文件一个标签页，可查看完整prompt
7. **灵活配置** - 支持多模型、多人名库、自定义prompt

### 📋 界面功能

#### API配置
- **API Key**: 默认值已填写
- **Base URL**: 默认 `https://yunwuapi.com/v1/`
- **模型选择**:
  - gpt-5.1
  - gemini-2.5-pro（默认）
  - 自定义（可输入任意模型名）
- **人名库**: 选择1/2/3号人名库（各5000个名字）
- **测试连接**: 点击测试API是否可用

#### 文件管理
- **添加文件**: 选择单个或多个txt文件
- **添加文件夹**: 批量添加整个文件夹的txt文件
- **清空列表**: 清除所有待翻译文件
- **自动识别genre**: 文件名格式 `xxx_Fantasy.txt` 会自动识别为Fantasy

#### Prompt管理
- **编辑默认Prompt**: 修改并保存默认的翻译提示词模板
- **Prompt预览**: 查看每个文件即将使用的完整prompt（含人名列表）

#### 翻译控制
- **开始翻译**: 一键启动所有文件的并行翻译
- **实时状态**: 显示每个文件的翻译进度
- **独立线程**: 多个文件同时翻译，互不影响

## 支持的Genre类型

```
Fantasy, Urban, Romance, Sci-Fi, Mystery, Action,
Adventure, Horror, Crime, LGBTQ+, Paranormal, System,
Reborn, Revenge, Fanfiction
```

## 文件命名规范

为了自动识别genre，请使用以下命名格式：
```
书名_Genre.txt

例如：
76死亡运动会_Horror.txt
浪漫爱情故事_Romance.txt
未来世界_Sci-Fi.txt
```

如果文件名不包含genre，默认使用 `Fantasy`。

## 输出结构

```
output/
  ├── 76死亡运动会_Horror/
  │   └── content.txt       # 翻译后的完整内容
  ├── 浪漫爱情故事_Romance/
  │   └── content.txt
  └── ...
```

## 人名库管理

人名库位于 `data/names_1.json`, `data/names_2.json`, `data/names_3.json`

格式：
```json
{
  "male": ["Alexander Blake", "James Cooper", ...],
  "female": ["Isabella Rose", "Emma Wilson", ...]
}
```

每个库应包含约5000个名字（男女各2500个）。

## 打包成可执行文件

### Windows
```bash
python build_exe.py
```
生成 `dist/NovelTranslator.exe`

### Mac
```bash
python build_exe.py
```
生成 `dist/NovelTranslator.app`

### 使用打包后的程序
1. 双击运行可执行文件
2. 程序会自动创建 `data` 文件夹
3. 首次运行需要填充人名库（将名字列表复制到对应的JSON文件）

## 注意事项

1. **人名库**: 首次使用需要填充3个人名库JSON文件
2. **并行翻译**: 同时翻译多个文件时，请确保API的rate limit足够
3. **文件大小**: 单个文件建议不超过15000字符（受max_tokens=16000限制）
4. **网络连接**: 翻译过程需要稳定的网络连接

## 常见问题

**Q: 为什么翻译这么快？**
A: 我们去除了所有后处理（人名检测、总结等），直接接收和保存结果。

**Q: 可以同时翻译多少个文件？**
A: 理论上无限制，每个文件独立线程。实际受限于API rate limit。

**Q: Prompt在哪里配置？**
A: 点击"编辑默认Prompt"按钮可以修改 `data/default_prompt.txt`

**Q: 如何更换人名库？**
A: 在主界面选择"人名库1/2/3"单选按钮即可切换。

## 技术架构

- **GUI**: tkinter（跨平台）
- **API**: OpenAI兼容接口
- **并发**: threading（每个文件独立线程）
- **打包**: PyInstaller

## 版本历史

### v2.0 (当前版本)
- ✅ 完全重构，去除复杂后处理
- ✅ 支持真正的并行翻译
- ✅ Prompt预览功能
- ✅ 简化输出结构
- ✅ 跨平台打包支持

### v1.0
- 基础翻译功能
- 使用ThreadPoolExecutor
- 包含后处理逻辑
