"""
短篇小说直接生成工具 - Short Novel Direct Generator
一次性生成完整故事，包含标题、类型、年龄分级和正文
"""
print("="*60)
print("[启动] shortnovel_direct.py v2.0 - 带调试版本")
print("="*60)

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import json
import os
import sys
import uuid
import shutil
import re
import traceback
from datetime import datetime

print("[DEBUG] 基础模块导入成功")

try:
    from openai import OpenAI
    print("[DEBUG] OpenAI模块导入成功")
except Exception as e:
    print(f"[ERROR] OpenAI导入失败: {e}")
    traceback.print_exc()

# 修复Mac上的SSL证书验证问题
import ssl
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except AttributeError:
    pass

print("[DEBUG] SSL配置完成")

try:
    from resource_mgr import ResourceManager
    print("[DEBUG] ResourceManager导入成功")
except Exception as e:
    print(f"[ERROR] ResourceManager导入失败: {e}")
    traceback.print_exc()


def get_resource_path(relative_path):
    """获取资源文件的绝对路径（支持PyInstaller打包）"""
    if getattr(sys, 'frozen', False):
        app_name = "ShortNovelDirect"
        if sys.platform == 'darwin':
            support_dir = os.path.expanduser(f'~/Library/Application Support/{app_name}')
        elif sys.platform == 'win32':
            support_dir = os.path.join(os.getenv('APPDATA'), app_name)
        else:
            support_dir = os.path.expanduser(f'~/.{app_name}')
        user_path = os.path.join(support_dir, relative_path)
        if os.path.exists(user_path):
            return user_path
        try:
            bundled_path = os.path.join(sys._MEIPASS, relative_path)
            if os.path.exists(bundled_path):
                os.makedirs(os.path.dirname(user_path), exist_ok=True)
                shutil.copy2(bundled_path, user_path)
                return user_path
        except Exception:
            pass
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        return os.path.join(os.getcwd(), relative_path)


# 默认Prompt模板 - 直接生成完整故事
DEFAULT_DIRECT_PROMPT = """# ADDICTIVE SHORT STORY GENERATOR

## 【⚠️ 语言要求 - 最高优先级】

**输出必须100%英文。**

即使输入的txt文件是中文的，你的输出必须全部是英文。不允许出现任何中文字符。

---

## 【核心任务】

你会收到一个包含故事idea的txt文件。直接创作一个**完整的英文短篇爽文**。

**目标**：
- **快节奏、高密度爽点**（这是最重要的！）
- 完整story arc
- 不分章节
- 一气呵成
- 一次性输出完整故事+metadata

**核心原则：爽 > 长。快 > 慢。简洁 > 复杂。**

---

## 【参数】
- 建议男性名：{male_names}
- 建议女性名：{female_names}
- **长度：灵活，以爽为准**（通常20000-40000字符，但质量>字数）

**⚠️ 重要：必须使用英文名字，严禁拼音！**

---

## 【输入】

你会收到一个txt文件，内容可能是：
- 中文故事大纲
- 中文小说片段
- 故事idea描述
- 人物设定

你的任务是：
1. 理解核心故事和主要爽点
2. **提取所有可能的爽点**
3. **删除所有拖沓的部分**
4. 直接写出**完整故事**
5. **所有人名必须改成英文名**

---

## 【⚠️ 爽文的特点】

### 必须有

```
1. ⭐⭐⭐⭐⭐ 密集爽点
   - 每3000-5000字符至少1个爽点
   - 爽点要"够爽"

2. ⭐⭐⭐⭐⭐ 快节奏
   - 前3000字符进入核心冲突
   - 没有长铺垫
   - 直接开打

3. ⭐⭐⭐⭐ 完整结局
   - 所有冲突解决
   - 坏人得到惩罚
   - 主角得到满足

4. ⭐⭐⭐ 简单设定
   - 3-5个主要人物
   - 单线剧情
   - 设定一句话能说清
```

### 绝对不能有

```
❌ 长铺垫（超过3000字符才进入冲突）
❌ 复杂世界观
❌ 太多支线人物
❌ 拖沓的日常场景
❌ 未解决的悬念
❌ 慢热
```

---

## 【⚠️ 硬性规则】

### 规则1：对话密度
**40%以上必须是对话。**

连续超过300字符没有对话？立刻加对话。

### 规则2：段落长度
**禁止超过5句的段落。**

重要时刻单句成段。

### 规则3：爽点密度（最重要！）
**每3000-5000字符至少1个明确爽点**

爽点类型（按爽度排序）：
1. **Public face-slapping**（当众打脸）
2. **Revenge payoff**（复仇成功）
3. **Identity reveal + shock**（身份揭露）
4. **Villain public humiliation**（反派当众丢脸）
5. **Power display**（实力展示让人闭嘴）
6. **Recognition from doubters**（被质疑者认可）
7. **Regret from wrongdoers**（伤害主角的人后悔）

**不算爽点的：**
- 主角受虐但没反击
- 坏人"表情微变"
- 内心爽但外部没展示

### 规则4：快节奏

**前3000字符内必须：**
- 主角遇到核心冲突
- 第一个爽点出现
- 读者清楚知道故事要讲什么

**禁止：**
- 长背景介绍
- 慢慢建立世界观
- 花2000字介绍日常生活

### 规则5：角色命名

**必须英文名，严禁拼音**

❌ 错误示例（拼音）：
- Li Wei → 这是拼音，禁止使用
- Zhang Yue → 这是拼音，禁止使用
- Wang Chen → 这是拼音，禁止使用
- Sophia Chen → Chen是拼音姓氏，禁止使用
- Alexander Liu → Liu是拼音姓氏，禁止使用

❌ 常见拼音姓氏（禁止使用）：
Chen, Wang, Liu, Zhang, Li, Zhao, Zhou, Wu, Huang, Yang, Xu, Sun, Ma, Zhu, Hu, Guo, Lin, He, Gao, Liang, Zheng, Luo, Song, Xie, Tang, Han, Cao, Feng, Deng, Peng, Zeng, Xiao, Tian, Pan, Yuan, Dong, Yu, Jiang, Cai, Yu, Du, Ye, Cheng, Wei, Su, Lu, Ding, Ren, Shen, Yao, Lu, Jiang, Cui, Zhong, Tan, Lu, Wang, Fan, Liao, Shi, Jin, Wei, Jia, Xia, Fu, Fang, Bai, Zou, Meng, Xiong, Qin, Qiu, Jiang, Yin, Xue, Yan, Duan, Lei, Long, Li, Tao, He

**使用提供的英文名字列表，或常见英文名。**

常见英文姓氏参考：Smith, Johnson, Williams, Brown, Davis, Miller, Wilson, Moore, Taylor, Anderson, Thomas, Jackson, White, Harris, Martin, Thompson, Garcia, Martinez, Robinson, Clark, Rodriguez, Lewis, Lee, Walker, Hall, Allen, Young, King, Wright, Lopez, Hill, Scott, Green, Adams, Baker, Nelson, Carter, Mitchell, Roberts, Turner, Phillips, Campbell, Parker, Evans, Edwards, Collins, Stewart, Morris, Rogers, Reed, Cook, Morgan, Bell, Murphy, Bailey, Rivera, Cooper, Richardson, Cox, Howard, Ward, Torres, Peterson, Gray, Ramirez, James, Watson, Brooks, Kelly, Sanders, Price, Bennett, Wood, Barnes, Ross, Henderson, Coleman, Jenkins, Perry, Powell, Hughes, Flores, Washington, Butler, Foster, Bryant, Alexander, Russell, Griffin, Hayes

### 规则6：设定清晰简单

选择一个清晰的背景：
- **现代都市**：Harbor City, CEO, billionaire, Instagram
- **古代架空**：用英文名 + Emperor/Prince/Duke
- **现代+超自然**：现代城市 + 简单能力

**地点命名：**
- ✅ Harbor City, Riverside, Summit District, Lakeside, New York, Los Angeles
- ❌ Beijing, Shanghai, Guangzhou（不要直接用中国城市）

**机构命名：**
- ✅ StreamWave Entertainment, TechCore Industries, Summit Hospital
- ❌ Tencent, Alibaba, Baidu（不要用中国公司）

**不要中西混搭，不要复杂设定**

### 规则7：设定/背景解释
**最多3句话**，然后回到动作。

不要解释世界观、系统原理、能力来源。**直接展示效果。**

### 规则8：内心独白
**最多连续3句**，然后回到外部动作。

禁止大段内心活动。

### 规则9：禁止文学腔

**禁止比喻句：**
❌ "她的声音像X"
❌ "沉默像Y一样落下"
❌ "His words hung in the air like a blade"

**禁止诗意表达：**
❌ "patience wrapped in glass"
❌ "silence lands like a lid"
❌ "like a storm retreating"

**禁止哲理句：**
❌ 段落结尾加人生感悟
❌ "X is not Y, it is Z"式感悟
❌ "for a moment, he understood..."

**可以保留口语化比喻：**
✅ "He looked at me like I was trash"
✅ "That hit me like a truck"

### 规则10：开头直入
**第一句必须是动作或对话。**

禁止：
- 环境描写开头
- 背景介绍开头
- 内心独白开头

### 规则11：结尾完整且干脆

**必须完整：**
- 所有冲突解决
- 坏人得到惩罚
- 主角得到满足

**必须干脆：**
- 不拖沓
- 不反复强调
- 说完就停

---

## 【⚠️ GENRE分类 - 15个短篇专属】

**必须从以下15个中选1个：**

```
Age Gap
Billionaire Romance
Entertainment Circle
Face-Slapping
Group Pet
Healing/Redemption
Quick Transmigration
Rebirth
Regret
Revenge
Substitute
Survival/Apocalypse
Sweet Romance
System
True/Fake Identity
```

**判断方法：**
1. 主要爽点是什么？→ Face-Slapping / Revenge / Sweet Romance
2. 有特殊设定吗？→ Rebirth / System / True/Fake Identity
3. 主角/背景特点？→ Billionaire Romance / Entertainment Circle

---

## 【⚠️ TITLE创作规则】

### 硬性要求

**少于80字符**

### 创作原则

1. **口语化**，像聊天不像书名
2. **有对比/反转/冲突**
3. **制造好奇**
4. **一眼就懂核心冲突**
5. **独特**（不要和其他标题重复）

### ❌ 禁止的标题模式

**避免使用这些常见的开头词：**

```
❌ "I Died..." / "I Woke..." / "I [Verb]..."
❌ "Back to..." / "Back at..."
❌ "They Called..." / "They Said..." / "They [Verb]..."
❌ "Rejected..." / "Rejected by..."
❌ "He..." / "She..." (人称代词开头)
❌ "After..." / "After I..."
❌ "Married..." / "Divorced..." (单个动词开头)
❌ "When..." (时间状语开头)
❌ "The..." (冠词开头，除非非常特殊)
```

**尽量创造不同的标题结构，不要总用相同的模式。**

**不要使用以下模式：**

```
❌ "The [Someone]'s [Something]"
   例如："The CEO's Secret Wife"

❌ "When [Something Happened]"
   例如："When Love Returns"

❌ "A [Noun] of [Noun]"
   例如："A Tale of Two Hearts"

❌ "[Genre]: [Statement]"
   例如："Romance: She Found Love"

❌ 没有emotion或surprise的标题
   例如："The Story of My Life"

❌ 像书名不像话
   例如："Chronicles of a Forgotten Soul"

❌ 需要"品味"才能理解
   例如："Echoes in the Silence of Dawn"
```

### ❌ 禁止的标题特征

```
❌ 太长（超过80字符）
❌ 复杂从句
❌ 过于文学化
❌ 没有冲突感
❌ 太抽象
❌ 陈词滥调
❌ 重复的结构（和前面生成的标题一样的格式）
```

### 创作提醒

- 标题要独特且吸引人
- 尝试不同的标题结构（不要总用同一种模式）
- 专注核心冲突和反转
- 保持口语化
- 让人一眼就想点进来
- 避免使用上面列出的禁止模式

---

## 【⚠️ AI常见错误 - 必须删除】

写完后搜索以下内容，找到就改或删：

### 连接词
删除：However, Moreover, Furthermore, Nevertheless, Additionally, Subsequently, Consequently

### 陈词滥调
删除：
- let out a breath she didn't know she was holding
- heart raced in his/her chest
- blood ran cold
- shiver down spine
- time seemed to slow
- the air grew thick

### 万能形容词
删除：piercing eyes, chiseled jaw, dazzling smile, raven hair

### 情感分析句式
删除：
- couldn't help but feel
- part of him wanted to... while another part
- a complex mixture of emotions
- a wave of [emotion] washed over
- something in him shifted

### 比喻句式（禁止文艺比喻）
删除：
- ❌ "Silence fell like a lid"
- ❌ "His words hung in the air like a blade"
- ❌ "She folded it as one folds a map to a destination"
- ❌ "His steps were an argument for a life"

### 哲理/文艺句式
删除：
- "X and Y at once"（如"simpler and harder at once"）
- "felt like a [抽象名词]"（如"felt like a choice"）
- "as if [抽象概念]"
- "the sound/weight/taste of [抽象名词]"
- "in a way that [哲理解释]"
- "[动作] as one [哲理比喻]"
- "X is not Y, it is Z"式的人生感悟
- "for a moment/for a second [哲理感悟]"

### 长段落
- 超过3句的设定解释 → 砍到3句
- 超过3句的内心独白 → 砍到3句
- 超过5句的段落 → 拆开

### 重复
- 同一个意思说两遍 → 只保留一次
- 结尾反复强调同一件事 → 只说一次

---

## 【写作流程】

### 第1步：理解输入
- 读txt文件
- 找出核心冲突
- 识别主要爽点
- 确定genre

### 第2步：规划故事
**在心里（不输出）快速规划：**
- 开场冲突是什么？
- 6-10个主要爽点是什么？
- 高潮是什么？
- 结局怎么收？

### 第3步：创作metadata
- Title（少于80字符，独特，不重复）
- Genre（15个中选1）
- Age（4个等级选1）

### 第4步：写故事
- 从动作或对话开始
- 对话优先（40%+）
- **每3000字符检查：有爽点了吗？**
- 边写边控制：
  - 段落不超过5句
  - 没有文学腔
  - 设定解释不超过3句
- 一口气写完

### 第5步：检查并修复

**□ 爽点检查**（最重要）
- 至少6-10个爽点？
- 每个都够爽？
- 每3000-5000字符有一个？

**□ 对话密度**
- 40%以上？

**□ 文学腔检查**
搜索：However, Moreover, "couldn't help but", "a wave of", "at once"
找到就删

**□ 开头**
- 第一句是动作或对话？

**□ 结尾**
- 完整？
- 干脆？
- 有 `---END---`？

---

## 【⚠️ 输出格式 - 严格遵守】

```
===TITLE===
[英文标题，少于80字符，独特]

===GENRE===
[从15个Genre中选1个]

===AGE===
[All Ages 或 Teen 13+ 或 Mature 16+ 或 Explicit 18+]

===STORY===
[完整故事正文，纯英文，不要任何标题或章节号]

---END---
```

**禁止输出：**
- ❌ Outline
- ❌ Character list
- ❌ World setting
- ❌ "Chapter X"
- ❌ 作者注释
- ❌ 字数统计
- ❌ 任何说明文字
- ❌ 任何中文

**只要：**
- ✅ TITLE
- ✅ GENRE
- ✅ AGE
- ✅ 故事正文
- ✅ ---END---

---

**现在，开始创作。读取输入的txt文件，直接写出完整故事。**

**START WRITING.**"""


class DirectPromptManager:
    """直接生成Prompt管理器"""

    def __init__(self):
        self.prompts_file = get_resource_path('data/shortnovel_direct_prompts.json')
        self.prompts = self.load_prompts()

    def load_prompts(self):
        """加载Prompt配置"""
        try:
            if os.path.exists(self.prompts_file):
                with open(self.prompts_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载Prompt配置失败: {e}")

        return {
            'direct': {
                'default': DEFAULT_DIRECT_PROMPT,
                'versions': {},
                'active': 'default'
            }
        }

    def save_prompts(self):
        """保存Prompt配置"""
        try:
            os.makedirs(os.path.dirname(self.prompts_file), exist_ok=True)
            with open(self.prompts_file, 'w', encoding='utf-8') as f:
                json.dump(self.prompts, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存Prompt配置失败: {e}")

    def get_prompt(self, version=None):
        """获取Prompt（默认使用活跃版本）"""
        if version is None:
            version = self.prompts['direct'].get('active', 'default')
        if version != 'default' and version in self.prompts['direct'].get('versions', {}):
            return self.prompts['direct']['versions'][version]
        return self.prompts['direct']['default']

    def get_active_version(self):
        """获取活跃版本名称"""
        return self.prompts['direct'].get('active', 'default')

    def set_active_version(self, version):
        """设置活跃版本"""
        self.prompts['direct']['active'] = version
        self.save_prompts()

    def save_prompt_version(self, name, content):
        """保存Prompt版本"""
        if 'versions' not in self.prompts['direct']:
            self.prompts['direct']['versions'] = {}
        self.prompts['direct']['versions'][name] = content
        self.save_prompts()

    def delete_prompt_version(self, name):
        """删除Prompt版本"""
        if name in self.prompts['direct'].get('versions', {}):
            del self.prompts['direct']['versions'][name]
            if self.prompts['direct'].get('active') == name:
                self.prompts['direct']['active'] = 'default'
            self.save_prompts()


class GenerationTask:
    """生成任务"""
    def __init__(self, task_id, source_file, config_params):
        self.task_id = task_id
        self.source_file = source_file
        self.config = config_params
        self.status = 'pending'
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.output_folder = None
        self.char_count = 0
        self.title = None
        self.genre = None
        self.age = None
        self.has_end_marker = False
        self.error_msg = None
        self.warning_msg = None


class ShortNovelDirect:
    """短篇小说直接生成工具"""

    MAX_TASKS = 1000

    def __init__(self):
        self.window = tk.Tk()
        self.window.title("📚 短篇小说直接生成 - Direct Generator")
        self.window.geometry("1400x900")

        # 初始化资源
        self.resource_mgr = ResourceManager()
        self.prompt_mgr = DirectPromptManager()

        # 任务列表
        self.tasks = []
        self.task_frames = {}
        self.current_page = 0
        self.tasks_per_page = 50
        self.cards_per_row = 5

        # API预设
        self.api_presets = {
            "BLTCY API (api.bltcy.ai)": {
                "api_key": "sk-z4a6qvhXCbfboOyBwL33BR66mJdHTKj5NO4pfIUSkLBm2jGF",
                "base_url": "https://api.bltcy.ai"
            },
            "自定义配置": {
                "api_key": "",
                "base_url": ""
            }
        }

        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        # 顶部：API配置
        self.setup_api_config()

        # 中间：控制面板
        self.setup_control_panel()

        # 下方：任务队列
        self.setup_task_queue()

    def setup_api_config(self):
        """设置API配置区域"""
        api_frame = tk.LabelFrame(self.window, text="🔧 API 配置", font=("Arial", 11, "bold"), padx=10, pady=5)
        api_frame.pack(fill=tk.X, padx=10, pady=5)

        # 第一行
        row1 = tk.Frame(api_frame)
        row1.pack(fill=tk.X, pady=2)

        tk.Label(row1, text="API预设:").pack(side=tk.LEFT)
        self.api_preset_var = tk.StringVar(value="BLTCY API (api.bltcy.ai)")
        api_combo = ttk.Combobox(row1, textvariable=self.api_preset_var, width=25)
        api_combo['values'] = list(self.api_presets.keys())
        api_combo.pack(side=tk.LEFT, padx=5)
        api_combo.bind('<<ComboboxSelected>>', self.on_api_preset_change)

        tk.Label(row1, text="模型:").pack(side=tk.LEFT, padx=(20, 0))
        self.model_var = tk.StringVar(value="gpt-5-mini")
        model_combo = ttk.Combobox(row1, textvariable=self.model_var, width=20)
        model_combo['values'] = ["gpt-5-mini"]
        model_combo.pack(side=tk.LEFT, padx=5)

        tk.Button(row1, text="测试连接", command=self.test_api, width=10).pack(side=tk.LEFT, padx=10)
        self.api_status = tk.Label(row1, text="", fg="gray")
        self.api_status.pack(side=tk.LEFT)

        # 第二行
        row2 = tk.Frame(api_frame)
        row2.pack(fill=tk.X, pady=2)

        tk.Label(row2, text="API Key:").pack(side=tk.LEFT)
        self.api_key_var = tk.StringVar(value="sk-z4a6qvhXCbfboOyBwL33BR66mJdHTKj5NO4pfIUSkLBm2jGF")
        tk.Entry(row2, textvariable=self.api_key_var, show="*", width=50).pack(side=tk.LEFT, padx=5)

        tk.Label(row2, text="Base URL:").pack(side=tk.LEFT, padx=(20, 0))
        self.base_url_var = tk.StringVar(value="https://api.bltcy.ai")
        tk.Entry(row2, textvariable=self.base_url_var, width=30).pack(side=tk.LEFT, padx=5)

    def on_api_preset_change(self, event=None):
        """API预设改变"""
        preset = self.api_preset_var.get()
        if preset in self.api_presets:
            self.api_key_var.set(self.api_presets[preset]['api_key'])
            self.base_url_var.set(self.api_presets[preset]['base_url'])

    def _normalize_base_url(self, url):
        """规范化Base URL"""
        url = url.strip().rstrip('/')
        if url.endswith('/v1'):
            return url
        return url + '/v1'

    def test_api(self):
        """测试API连接"""
        self.api_status.config(text="测试中...", fg="blue")
        self.window.update()

        try:
            base_url = self._normalize_base_url(self.base_url_var.get())
            client = OpenAI(api_key=self.api_key_var.get(), base_url=base_url)
            response = client.chat.completions.create(
                model=self.model_var.get(),
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=100,
                temperature=0.85
            )
            self.api_status.config(text="✅ 连接成功", fg="green")
        except Exception as e:
            print(f"API测试失败: {e}")
            self.api_status.config(text=f"❌ 失败: {str(e)[:50]}", fg="red")

    def setup_control_panel(self):
        """设置控制面板"""
        control_frame = tk.LabelFrame(self.window, text="📝 生成配置", font=("Arial", 11, "bold"), padx=10, pady=5)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        # 第一行：文件选择
        row1 = tk.Frame(control_frame)
        row1.pack(fill=tk.X, pady=2)

        tk.Button(row1, text="选择文件", command=self.select_files, width=10).pack(side=tk.LEFT)
        tk.Button(row1, text="选择文件夹", command=self.select_folder, width=10).pack(side=tk.LEFT, padx=5)
        self.file_label = tk.Label(row1, text="未选择文件", fg="gray")
        self.file_label.pack(side=tk.LEFT, padx=10)

        tk.Button(row1, text="添加任务", command=self.add_tasks, width=10, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=20)

        # 第二行：人名配置
        row2 = tk.Frame(control_frame)
        row2.pack(fill=tk.X, pady=2)

        tk.Label(row2, text="人名数量 - 男:").pack(side=tk.LEFT)
        self.male_count = tk.IntVar(value=10)
        tk.Spinbox(row2, from_=1, to=50, textvariable=self.male_count, width=5).pack(side=tk.LEFT, padx=2)

        tk.Label(row2, text="女:").pack(side=tk.LEFT, padx=(10, 0))
        self.female_count = tk.IntVar(value=10)
        tk.Spinbox(row2, from_=1, to=50, textvariable=self.female_count, width=5).pack(side=tk.LEFT, padx=2)

        tk.Label(row2, text="目标字符数:").pack(side=tk.LEFT, padx=(20, 0))
        self.min_chars = tk.IntVar(value=25000)
        tk.Entry(row2, textvariable=self.min_chars, width=8).pack(side=tk.LEFT, padx=2)
        tk.Label(row2, text="-").pack(side=tk.LEFT)
        self.max_chars = tk.IntVar(value=50000)
        tk.Entry(row2, textvariable=self.max_chars, width=8).pack(side=tk.LEFT, padx=2)

        # 第三行：输出路径
        row3 = tk.Frame(control_frame)
        row3.pack(fill=tk.X, pady=2)

        tk.Label(row3, text="输出路径:").pack(side=tk.LEFT)
        self.output_var = tk.StringVar(value="D:\\shortnovels_output")
        tk.Entry(row3, textvariable=self.output_var, width=50).pack(side=tk.LEFT, padx=5)
        tk.Button(row3, text="浏览", command=self.select_output_folder, width=6).pack(side=tk.LEFT)

        tk.Button(row3, text="管理Prompt", command=self.open_prompt_manager, width=12).pack(side=tk.LEFT, padx=20)

        # 第四行：批量操作
        row4 = tk.Frame(control_frame)
        row4.pack(fill=tk.X, pady=5)

        tk.Button(row4, text="▶ 全部开始", command=self.start_all_tasks, width=12, bg="#2196F3", fg="white").pack(side=tk.LEFT)
        tk.Button(row4, text="⏹ 清空任务", command=self.clear_all_tasks, width=12).pack(side=tk.LEFT, padx=10)

        # 进度条
        self.progress_bar = ttk.Progressbar(row4, length=300, mode='determinate')
        self.progress_bar.pack(side=tk.LEFT, padx=20)
        self.progress_label = tk.Label(row4, text="进度: 0/0 (0%)")
        self.progress_label.pack(side=tk.LEFT)

    def setup_task_queue(self):
        """设置任务队列"""
        queue_frame = tk.LabelFrame(self.window, text="📋 任务队列", font=("Arial", 11, "bold"), padx=10, pady=5)
        queue_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 分页控制
        page_frame = tk.Frame(queue_frame)
        page_frame.pack(fill=tk.X)

        tk.Button(page_frame, text="◀ 上一页", command=self.prev_page).pack(side=tk.LEFT)
        self.page_label = tk.Label(page_frame, text="0/0 页")
        self.page_label.pack(side=tk.LEFT, padx=10)
        tk.Button(page_frame, text="下一页 ▶", command=self.next_page).pack(side=tk.LEFT)

        # 任务卡片容器
        canvas = tk.Canvas(queue_frame, bg="#f0f0f0")
        scrollbar = ttk.Scrollbar(queue_frame, orient="vertical", command=canvas.yview)
        self.queue_frame = tk.Frame(canvas, bg="#f0f0f0")

        self.queue_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.queue_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def select_files(self):
        """选择文件"""
        files = filedialog.askopenfilenames(
            title="选择故事idea文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if files:
            self.selected_files = list(files)
            self.file_label.config(text=f"已选择 {len(files)} 个文件", fg="black")

    def select_folder(self):
        """选择文件夹"""
        folder = filedialog.askdirectory(title="选择包含故事idea的文件夹")
        if folder:
            import glob
            files = glob.glob(os.path.join(folder, "*.txt"))
            if files:
                self.selected_files = files
                self.file_label.config(text=f"已选择 {len(files)} 个文件", fg="black")
            else:
                messagebox.showwarning("警告", "文件夹中没有txt文件")

    def select_output_folder(self):
        """选择输出文件夹"""
        folder = filedialog.askdirectory(title="选择输出文件夹")
        if folder:
            self.output_var.set(folder)

    def add_tasks(self):
        """添加任务"""
        if not hasattr(self, 'selected_files') or not self.selected_files:
            messagebox.showwarning("警告", "请先选择文件")
            return

        if len(self.tasks) + len(self.selected_files) > self.MAX_TASKS:
            messagebox.showwarning("警告", f"任务数量超过上限 {self.MAX_TASKS}")
            return

        added = 0
        for file_path in self.selected_files:
            if any(t.source_file == file_path for t in self.tasks):
                continue

            task = GenerationTask(
                task_id=str(uuid.uuid4()),
                source_file=file_path,
                config_params={
                    'model': self.model_var.get(),
                    'api_key': self.api_key_var.get(),
                    'base_url': self.base_url_var.get(),
                    'male_count': self.male_count.get(),
                    'female_count': self.female_count.get(),
                    'min_chars': self.min_chars.get(),
                    'max_chars': self.max_chars.get(),
                    'max_tokens': 65000,
                    'output_path': self.output_var.get()
                }
            )
            self.tasks.append(task)
            added += 1

        self.selected_files = []
        self.file_label.config(text="未选择文件", fg="gray")
        self.refresh_display()
        self.update_progress()

        if added > 0:
            messagebox.showinfo("成功", f"已添加 {added} 个任务")

    def refresh_display(self):
        """刷新任务显示"""
        for widget in self.queue_frame.winfo_children():
            widget.destroy()
        self.task_frames.clear()

        if not self.tasks:
            tk.Label(self.queue_frame, text="暂无任务", font=("Arial", 10), bg="#f0f0f0").pack(pady=20)
            self.page_label.config(text="0/0 页")
            return

        total_pages = max(1, (len(self.tasks) - 1) // self.tasks_per_page + 1)
        self.current_page = min(self.current_page, total_pages - 1)

        start_idx = self.current_page * self.tasks_per_page
        end_idx = min(start_idx + self.tasks_per_page, len(self.tasks))

        self.page_label.config(text=f"{self.current_page + 1}/{total_pages} 页 (共{len(self.tasks)}个)")

        current_tasks = self.tasks[start_idx:end_idx]
        for idx, task in enumerate(current_tasks):
            row = idx // self.cards_per_row
            col = idx % self.cards_per_row
            self.create_task_card(task, row, col)

    def create_task_card(self, task, row, col):
        """创建任务卡片"""
        card = tk.Frame(self.queue_frame, bg="#ffffff", relief=tk.RAISED, borderwidth=2, width=260, height=90)
        card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
        card.grid_propagate(False)

        # 顶部色条
        status_colors = {
            'pending': '#9E9E9E',
            'running': '#2196F3',
            'completed': '#4CAF50',
            'incomplete': '#FF9800',
            'failed': '#f44336'
        }
        top_bar = tk.Frame(card, bg=status_colors.get(task.status, '#9E9E9E'), height=4)
        top_bar.place(x=0, y=0, width=260)

        # 文件名
        filename = os.path.basename(task.source_file)
        display_name = filename[:25] + "..." if len(filename) > 25 else filename
        tk.Label(card, text=display_name, font=("Arial", 9), bg="#ffffff", anchor="w").place(x=8, y=8, width=200)

        # 状态图标
        status_info = {
            'pending': ('⏳', '#9E9E9E'),
            'running': ('🔄', '#2196F3'),
            'completed': ('✅', '#4CAF50'),
            'incomplete': ('⚠️', '#FF9800'),
            'failed': ('❌', '#f44336')
        }
        icon, color = status_info.get(task.status, ('?', 'black'))
        tk.Label(card, text=icon, fg=color, bg="#ffffff", font=("Arial", 12)).place(x=220, y=6)

        # 信息行
        info_text = "等待开始"
        info_color = "#757575"
        if task.status == 'running' and task.started_at:
            info_text = f"⏱ 开始于 {task.started_at.strftime('%H:%M:%S')}"
            info_color = "#2196F3"
        elif task.status == 'completed':
            info_text = f"✓ {task.char_count:,} 字符"
            info_color = "#4CAF50"
        elif task.status == 'incomplete':
            warning = getattr(task, 'warning_msg', '未完成')
            info_text = f"⚠️ {task.char_count:,}字符 - {warning}"
            info_color = "#FF9800"
        elif task.status == 'failed':
            info_text = f"❌ 失败"
            info_color = "#f44336"

        tk.Label(card, text=info_text, fg=info_color, bg="#ffffff", font=("Arial", 9)).place(x=8, y=32)

        # 底部按钮
        btn_frame = tk.Frame(card, bg="#f5f5f5", height=30)
        btn_frame.place(x=0, y=60, width=260, height=30)

        tk.Button(btn_frame, text="▶ 开始", command=lambda t=task: self.start_task(t),
                 width=6, font=("Arial", 8), bg="#4CAF50", fg="white",
                 state=tk.NORMAL if task.status != 'running' else tk.DISABLED).place(x=8, y=3)

        tk.Button(btn_frame, text="🗑 删除", command=lambda t=task: self.remove_task(t),
                 width=6, font=("Arial", 8), bg="#f44336", fg="white").place(x=80, y=3)

        tk.Button(btn_frame, text="📋 预览", command=lambda t=task: self.preview_prompt(t),
                 width=6, font=("Arial", 8), bg="#2196F3", fg="white").place(x=152, y=3)

        self.task_frames[task.task_id] = card

    def start_task(self, task):
        """开始任务"""
        if task.status == 'running':
            return

        task.status = 'running'
        task.started_at = datetime.now()
        self.refresh_display()

        thread = threading.Thread(target=self._execute_task, args=(task,), daemon=True)
        thread.start()

    def _execute_task(self, task):
        """执行生成任务"""
        import traceback

        try:
            print(f"[DEBUG] 步骤1: 开始执行任务 {task.task_id[:8]}...")
            print(f"[DEBUG] task.config keys: {list(task.config.keys())}")

            # 读取输入文件
            print(f"[DEBUG] 步骤2: 读取输入文件 {task.source_file}")
            with open(task.source_file, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"[DEBUG] 步骤2完成: 文件内容长度 {len(content)}")

            # 获取人名
            print(f"[DEBUG] 步骤3: 获取人名 male={task.config['male_count']}, female={task.config['female_count']}")
            selected_names = self.resource_mgr.select_names(
                task.config['male_count'],
                task.config['female_count']
            )
            print(f"[DEBUG] 步骤3完成: 获取到 {len(selected_names.get('male', []))} 男名, {len(selected_names.get('female', []))} 女名")

            names_formatted = self.resource_mgr.format_names_for_prompt(selected_names)
            print(f"[DEBUG] 步骤3.5: 人名格式化完成")

            # 构建Prompt
            print(f"[DEBUG] 步骤4: 构建Prompt")
            prompt_template = self.prompt_mgr.get_prompt()

            # 使用安全的格式化方法，处理未知占位符
            try:
                system_prompt = prompt_template.format(
                    male_names=names_formatted['male_names'],
                    female_names=names_formatted['female_names']
                )
            except KeyError as ke:
                print(f"[WARNING] Prompt模板包含未知占位符: {ke}")
                print(f"[WARNING] 使用默认Prompt模板...")
                # 回退到默认模板
                system_prompt = DEFAULT_DIRECT_PROMPT.format(
                    male_names=names_formatted['male_names'],
                    female_names=names_formatted['female_names']
                )
            print(f"[DEBUG] 步骤4完成: Prompt长度 {len(system_prompt)}")

            # 添加字符数要求
            min_chars = task.config['min_chars']
            max_chars = task.config['max_chars']
            print(f"[DEBUG] 步骤5: 字符要求 {min_chars}-{max_chars}")

            full_prompt = f"""{system_prompt}

【字符数要求】：{min_chars} - {max_chars} 字符

【输入内容】：
{content}"""

            # 调用API
            print(f"[DEBUG] 步骤6: 调用API, model={task.config['model']}, base_url={task.config['base_url']}")
            client = OpenAI(
                api_key=task.config['api_key'],
                base_url=self._normalize_base_url(task.config['base_url'])
            )
            print(f"[DEBUG] 步骤6.5: OpenAI client创建成功")

            response = client.chat.completions.create(
                model=task.config['model'],
                messages=[{"role": "user", "content": full_prompt}],
                max_tokens=task.config['max_tokens'],
                temperature=0.85
            )
            print(f"[DEBUG] 步骤7: API响应成功")

            result = response.choices[0].message.content
            task.char_count = len(result)
            print(f"[DEBUG] 步骤7完成: 响应长度 {task.char_count}")

            # 检测END标记
            has_end = '---END---' in result
            task.has_end_marker = has_end
            print(f"[DEBUG] 步骤8: END标记检测 = {has_end}")

            # 解析结果
            print(f"[DEBUG] 步骤9: 解析结果")
            parsed = self._parse_result(result)
            task.title = parsed.get('title', '')
            task.genre = parsed.get('genre', '')
            task.age = parsed.get('age', '')
            story = parsed.get('story', '')
            print(f"[DEBUG] 步骤9完成: title={task.title[:30] if task.title else 'N/A'}, genre={task.genre}, story_len={len(story)}")

            # 判断是否完成
            is_complete = has_end and len(story) >= min_chars
            task.story_complete = is_complete
            print(f"[DEBUG] 步骤10: is_complete={is_complete}")

            # 确定输出文件夹名
            if task.title:
                folder_name = self._sanitize_folder_name(task.title)
            else:
                folder_name = os.path.splitext(os.path.basename(task.source_file))[0]
            print(f"[DEBUG] 步骤11: folder_name={folder_name}")

            # 创建输出文件夹
            output_base = task.config.get('output_path', '')
            if output_base and os.path.isdir(output_base):
                output_folder = os.path.join(output_base, folder_name)
            else:
                output_folder = os.path.join(os.path.dirname(task.source_file), folder_name + '_output')
            print(f"[DEBUG] 步骤12: output_folder={output_folder}")

            os.makedirs(output_folder, exist_ok=True)

            # 保存文件
            print(f"[DEBUG] 步骤13: 保存文件")
            with open(os.path.join(output_folder, 'title.txt'), 'w', encoding='utf-8') as f:
                f.write(task.title)
            with open(os.path.join(output_folder, 'genre.txt'), 'w', encoding='utf-8') as f:
                f.write(task.genre)
            with open(os.path.join(output_folder, 'age.txt'), 'w', encoding='utf-8') as f:
                f.write(task.age)
            with open(os.path.join(output_folder, 'story.txt'), 'w', encoding='utf-8') as f:
                f.write(story)
            with open(os.path.join(output_folder, 'full_response.txt'), 'w', encoding='utf-8') as f:
                f.write(result)
            print(f"[DEBUG] 步骤13完成: 文件保存成功")

            task.output_folder = output_folder

            # 设置状态
            if is_complete:
                task.status = 'completed'
            else:
                task.status = 'incomplete'
                if not has_end:
                    task.warning_msg = "缺少END标记"
                elif len(story) < min_chars:
                    task.warning_msg = f"字符数不足({len(story)}<{min_chars})"

            task.completed_at = datetime.now()
            print(f"[DEBUG] 任务完成: status={task.status}")

        except Exception as e:
            task.status = 'failed'
            task.error_msg = str(e)
            print(f"="*50)
            print(f"[ERROR] 任务失败!")
            print(f"[ERROR] 错误类型: {type(e).__name__}")
            print(f"[ERROR] 错误信息: {e}")
            print(f"[ERROR] 完整堆栈:")
            traceback.print_exc()
            print(f"="*50)

        self.window.after(0, self.refresh_display)
        self.window.after(0, self.update_progress)

    def _parse_result(self, result):
        """解析API返回结果"""
        parsed = {'title': '', 'genre': '', 'age': '', 'story': ''}

        # 提取TITLE
        title_match = re.search(r'===TITLE===\s*(.*?)\s*(?====|$)', result, re.DOTALL)
        if title_match:
            parsed['title'] = title_match.group(1).strip()

        # 提取GENRE
        genre_match = re.search(r'===GENRE===\s*(.*?)\s*(?====|$)', result, re.DOTALL)
        if genre_match:
            parsed['genre'] = genre_match.group(1).strip()

        # 提取AGE
        age_match = re.search(r'===AGE===\s*(.*?)\s*(?====|$)', result, re.DOTALL)
        if age_match:
            parsed['age'] = age_match.group(1).strip()

        # 提取STORY
        story_match = re.search(r'===STORY===\s*(.*?)\s*(?=---END---|$)', result, re.DOTALL)
        if story_match:
            parsed['story'] = story_match.group(1).strip()

        return parsed

    def _sanitize_folder_name(self, name):
        """清理文件夹名称"""
        sanitized = re.sub(r'[\\/:*?"<>|]', '', name)
        sanitized = sanitized.strip().strip('.')
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        return sanitized if sanitized else 'untitled'

    def preview_prompt(self, task):
        """预览Prompt"""
        try:
            with open(task.source_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 预览人名
            names_data = self.resource_mgr.load_names()
            male_sorted = sorted(names_data.get('male', []), key=lambda x: x.get('used', 0))
            female_sorted = sorted(names_data.get('female', []), key=lambda x: x.get('used', 0))

            male_count = task.config.get('male_count', 10)
            female_count = task.config.get('female_count', 10)

            preview_male = [n['fullname'] for n in male_sorted[:male_count]]
            preview_female = [n['fullname'] for n in female_sorted[:female_count]]

            male_names_str = ", ".join(preview_male)
            female_names_str = ", ".join(preview_female)

            # 构建Prompt
            prompt_template = self.prompt_mgr.get_prompt()
            full_prompt = prompt_template.format(
                male_names=male_names_str,
                female_names=female_names_str
            )

            # 显示预览
            preview_win = tk.Toplevel(self.window)
            preview_win.title(f"Prompt预览 - {os.path.basename(task.source_file)}")
            preview_win.geometry("900x700")

            # 配置信息
            info_frame = tk.Frame(preview_win, bg="#e3f2fd")
            info_frame.pack(fill=tk.X, padx=10, pady=5)
            tk.Label(info_frame, text=f"模型: {task.config.get('model')}\n字符要求: {task.config.get('min_chars'):,} - {task.config.get('max_chars'):,}",
                    bg="#e3f2fd", justify=tk.LEFT).pack(padx=10, pady=5, anchor="w")

            # Prompt
            tk.Label(preview_win, text="📋 Prompt:", font=("Arial", 10, "bold")).pack(anchor="w", padx=10)
            prompt_text = scrolledtext.ScrolledText(preview_win, height=15, wrap=tk.WORD)
            prompt_text.pack(fill=tk.X, padx=10, pady=5)
            prompt_text.insert(tk.END, full_prompt)
            prompt_text.config(state=tk.DISABLED)

            # 输入内容
            tk.Label(preview_win, text="📄 输入内容:", font=("Arial", 10, "bold")).pack(anchor="w", padx=10)
            content_text = scrolledtext.ScrolledText(preview_win, height=15, wrap=tk.WORD)
            content_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            content_text.insert(tk.END, content)
            content_text.config(state=tk.DISABLED)

            tk.Button(preview_win, text="关闭", command=preview_win.destroy, width=10).pack(pady=10)

        except Exception as e:
            messagebox.showerror("错误", f"预览失败: {e}")

    def start_all_tasks(self):
        """开始所有任务"""
        pending_tasks = [t for t in self.tasks if t.status == 'pending']
        if not pending_tasks:
            messagebox.showinfo("提示", "没有等待中的任务")
            return

        for task in pending_tasks:
            task.status = 'running'
            task.started_at = datetime.now()
            thread = threading.Thread(target=self._execute_task, args=(task,), daemon=True)
            thread.start()

        self.refresh_display()

    def remove_task(self, task):
        """移除任务"""
        if task.status == 'running':
            messagebox.showwarning("警告", "无法移除运行中的任务")
            return
        self.tasks.remove(task)
        self.refresh_display()
        self.update_progress()

    def clear_all_tasks(self):
        """清空所有任务"""
        running = [t for t in self.tasks if t.status == 'running']
        if running:
            messagebox.showwarning("警告", f"有 {len(running)} 个任务正在运行，无法清空")
            return

        if messagebox.askyesno("确认", "确定要清空所有任务吗？"):
            self.tasks.clear()
            self.refresh_display()
            self.update_progress()

    def update_progress(self):
        """更新进度"""
        total = len(self.tasks)
        completed = len([t for t in self.tasks if t.status == 'completed'])
        incomplete = len([t for t in self.tasks if t.status == 'incomplete'])
        failed = len([t for t in self.tasks if t.status == 'failed'])
        done = completed + incomplete + failed

        if total > 0:
            percent = int(done / total * 100)
            self.progress_bar['value'] = percent
            status_text = f"进度: {done}/{total} ({percent}%) - ✓{completed}"
            if incomplete > 0:
                status_text += f" ⚠{incomplete}"
            if failed > 0:
                status_text += f" ✗{failed}"
            self.progress_label.config(text=status_text)
        else:
            self.progress_bar['value'] = 0
            self.progress_label.config(text="进度: 0/0 (0%)")

    def prev_page(self):
        """上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_display()

    def next_page(self):
        """下一页"""
        total_pages = max(1, (len(self.tasks) - 1) // self.tasks_per_page + 1)
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.refresh_display()

    def open_prompt_manager(self):
        """打开Prompt管理器"""
        manager_win = tk.Toplevel(self.window)
        manager_win.title("Prompt管理")
        manager_win.geometry("900x650")

        # 活跃版本信息
        info_frame = tk.Frame(manager_win, bg="#e3f2fd", height=40)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        active_version = self.prompt_mgr.get_active_version()
        active_label = tk.Label(info_frame, text=f"🔹 当前活跃版本: {active_version}",
                               font=("Arial", 10, "bold"), bg="#e3f2fd", fg="#1565C0")
        active_label.pack(side=tk.LEFT, padx=10, pady=8)

        # 版本选择
        version_frame = tk.Frame(manager_win)
        version_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(version_frame, text="选择版本:").pack(side=tk.LEFT)

        versions = ['default'] + list(self.prompt_mgr.prompts['direct'].get('versions', {}).keys())
        version_var = tk.StringVar(value=active_version)
        version_combo = ttk.Combobox(version_frame, textvariable=version_var, values=versions, width=20)
        version_combo.pack(side=tk.LEFT, padx=5)

        def set_active():
            version = version_var.get()
            self.prompt_mgr.set_active_version(version)
            active_label.config(text=f"🔹 当前活跃版本: {version}")
            messagebox.showinfo("成功", f"已将 '{version}' 设为活跃版本")

        tk.Button(version_frame, text="⭐ 设为活跃", command=set_active, bg="#FFC107").pack(side=tk.LEFT, padx=5)

        # Prompt编辑
        tk.Label(manager_win, text="Prompt内容:", font=("Arial", 10, "bold")).pack(anchor="w", padx=10)
        prompt_text = scrolledtext.ScrolledText(manager_win, wrap=tk.WORD, height=25)
        prompt_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        def load_prompt(*args):
            version = version_var.get()
            content = self.prompt_mgr.get_prompt(version)
            prompt_text.delete('1.0', tk.END)
            prompt_text.insert(tk.END, content)

        version_combo.bind('<<ComboboxSelected>>', load_prompt)
        load_prompt()

        # 保存按钮
        btn_frame = tk.Frame(manager_win)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        def save_as_new():
            name = tk.simpledialog.askstring("保存", "输入新版本名称:")
            if name:
                self.prompt_mgr.save_prompt_version(name, prompt_text.get('1.0', tk.END).strip())
                version_combo['values'] = ['default'] + list(self.prompt_mgr.prompts['direct'].get('versions', {}).keys())
                version_var.set(name)
                messagebox.showinfo("成功", f"已保存为 '{name}'")

        import tkinter.simpledialog as simpledialog
        tk.simpledialog = simpledialog

        tk.Button(btn_frame, text="💾 保存为新版本", command=save_as_new, bg="#4CAF50", fg="white").pack(side=tk.LEFT)
        tk.Button(btn_frame, text="关闭", command=manager_win.destroy).pack(side=tk.RIGHT)

    def run(self):
        """运行程序"""
        self.window.mainloop()


if __name__ == "__main__":
    print("[DEBUG] 开始创建应用...")
    try:
        app = ShortNovelDirect()
        print("[DEBUG] 应用创建成功，启动主循环...")
        app.run()
    except Exception as e:
        print(f"="*50)
        print(f"[FATAL ERROR] 应用启动失败!")
        print(f"[FATAL ERROR] 错误类型: {type(e).__name__}")
        print(f"[FATAL ERROR] 错误信息: {e}")
        print(f"[FATAL ERROR] 完整堆栈:")
        traceback.print_exc()
        print(f"="*50)
        input("按回车键退出...")
