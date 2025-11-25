"""
Prompt管理系统
支持查看、编辑、保存Prompt模板
"""
import json
import os
import sys
from datetime import datetime


def get_resource_path(relative_path):
    """获取资源文件的绝对路径（支持PyInstaller打包）

    macOS .app 双击启动时，会将资源文件复制到用户应用支持目录
    """
    # 检查是否是打包环境
    if getattr(sys, 'frozen', False):
        # 打包环境：使用应用支持目录存储可写文件
        app_name = "OutlineGenerator"

        # macOS应用支持目录
        if sys.platform == 'darwin':
            support_dir = os.path.expanduser(f'~/Library/Application Support/{app_name}')
        elif sys.platform == 'win32':
            support_dir = os.path.join(os.getenv('APPDATA'), app_name)
        else:
            support_dir = os.path.expanduser(f'~/.{app_name}')

        # 用户数据文件路径
        user_path = os.path.join(support_dir, relative_path)

        # 如果用户文件已存在，直接使用
        if os.path.exists(user_path):
            return user_path

        # 第一次运行，从打包资源复制
        try:
            bundled_path = os.path.join(sys._MEIPASS, relative_path)

            if os.path.exists(bundled_path):
                # 确保目标目录存在
                os.makedirs(os.path.dirname(user_path), exist_ok=True)

                # 复制到用户目录
                import shutil
                shutil.copy2(bundled_path, user_path)
                return user_path
            else:
                return user_path
        except Exception as e:
            # 返回打包路径作为后备（只读）
            return os.path.join(sys._MEIPASS, relative_path)

    else:
        # 开发环境：使用当前目录
        return os.path.join(os.getcwd(), relative_path)


PROMPTS_FILE = get_resource_path('data/prompts.json')


# 默认Prompt模板
DEFAULT_OUTLINE_PROMPT = """# ADDICTIVE WEB NOVEL OUTLINE GENERATOR
# 爆款网文大纲生成器（番茄小说/Wattpad模式）

## 【你的身份】
你是英语母语的网文创作者，专门将故事改编成让读者停不下来的商业小说大纲。

## 【核心任务】
把输入的故事（中文小说/梗概/想法）改编成英文爆款大纲：
- 可以**改剧情**以优化爽点密度和节奏
- 可以**增删情节**以适应目标章节数
- 可以**调整人物**以增强戏剧性
- **目标：让读者无法停止点击"下一章"**
- **重要：你必须根据故事内容，从17种Genre中自动选择最合适的类型**

---

## 【本土化要求】

### 地理文化
- **非中国背景**：使用虚构地点或西方城市
- 城市：Harbor City, Riverside, Silverton, Ashwood, Clearmont
- 街区：Hallow Lane, Mariner Heights, Downtown, East Side
- 机构：StreamWave（娱乐）, TechCore（科技）, Summit Hospital（医疗）

### 人名规则
**建议人名列表（可使用或自创）：**
男性: {male_names}
女性: {female_names}

- **使用规则**：
  - 可以从列表中选择
  - 如果不需要那么多角色，不必强行使用所有名字
  - 如果需要更多角色，可以自由创造英文名
  - 避免中文和拼音
  - 确保每个角色名字唯一，不重复

- **男主类型**：
  - 冷酷型：Sebastian, Dominic, Adrian, Marcus
  - 阳光型：Ethan, Lucas, Oliver, Ryan
  - 神秘型：Asher, Julian, Xavier, Kai

- **女主类型**：
  - 坚强型：Riley, Harper, Morgan, Phoenix
  - 甜美型：Emma, Lily, Sophie, Grace
  - 独立型：Blake, Quinn, Jordan, Sage

- **反派类型**：
  - 女反派：Angela, Victoria, Vanessa, Bianca
  - 男反派：Derek, Lance, Vincent, Sterling

### 日常细节本土化
| 中文 | 英文替换 |
|------|---------|
| 人民币/元 | dollars |
| 微信/微博 | Instagram, Twitter, TikTok |
| 包子/粥 | bagel, coffee, burger |
| 公里/米 | miles, feet |
| 小区/单元 | neighborhood, apartment |

### 章节标题规则 ⚠️
- **2-5个词**，简短有力
- **多样化结构**（避免连续"The"开头）
- **视觉化/故事性**

```
✅ 优秀标题：
- Knock, Open（动作感）
- Blood on the Contract（画面感）
- Five Million Dollar Lie（冲击力）
- When the CEO Kneels（戏剧性）

❌ 糟糕标题：
- The Meeting（太泛）
- The Decision（无特色）
- Chapter 1（敷衍）
```

### 章节数要求 ⚠️
**目标章节数：{end_chapter}章**
- 必须生成从第1章到第{end_chapter}章的完整大纲
- 每章7000-10000字符的内容量
- 如果原文很短，需要合理扩展剧情

---

## 【17种Genre分类说明】

你必须从以下17种类型中选择一个最合适的：

1. **Fantasy**（奇幻） - 魔法、异世界、龙等元素
2. **Urban**（都市） - 现代都市、总裁、豪门、商战
3. **Romance**（言情） - 爱情为主线的故事
4. **Sci-Fi**（科幻） - 未来、AI、太空、科技
5. **Mystery**（悬疑） - 侦探、推理、凶杀案
6. **Historical**（古言） - 古代背景、宫廷、历史
7. **Adventure**（冒险） - 探险、寻宝、荒岛求生
8. **Horror**（恐怖） - 鬼怪、恐怖、惊悚
9. **Crime**（犯罪） - 犯罪、警察、黑帮
10. **LGBTQ+**（同志） - 同性恋情、性少数群体
11. **Paranormal**（超自然） - 吸血鬼、狼人、超能力
12. **System**（系统流） - 中国特有的系统文，主角有系统开挂，完成任务获得奖励
13. **Reborn**（重生） - 重生回到过去，利用先知改命
14. **Revenge**（复仇） - 复仇为主线
15. **Fanfiction**（同人） - 基于原著的二次创作
16. **Humor**（幽默） - 搞笑、沙雕、喜剧
17. **General**（综合） - 不属于以上类型或混合多种类型

---

## 【17种Genre写作指南】

### 1. Fantasy（奇幻）
**爽点重点**：魔法觉醒、等级提升、战斗胜利、宝物获得
**节奏**：前3章建立魔法系统，快速给主角第一次升级
**每章必有**：魔法展示或实力提升
**避免**：过多世界观说明（边战斗边展示）

### 2. Urban（都市）
**爽点重点**：打脸富二代、赚钱、泡妞/撩汉、身份反转
**节奏**：第1章就要打脸，3章内建立主角优势
**每章必有**：至少1次打脸或装逼成功
**避免**：平淡日常（每章都要有冲突）

### 3. Romance（言情）
**爽点重点**：甜蜜互动、吃醋、霸道护短、误会解除
**节奏**：3章内男女主相遇，5章内产生情愫
**每章必有**：心动瞬间或关系进展
**避免**：纯虐不甜（虐后必须有糖补偿）

### 4. Sci-Fi（科幻）
**爽点重点**：科技升级、智商碾压、拯救危机、未来预见
**节奏**：1章建立科幻设定，快速进入主线冲突
**每章必有**：科技展示或智力胜利
**避免**：过度技术细节（普通读者看不懂）

### 5. Mystery（悬疑）
**爽点重点**：线索发现、真相揭露、凶手落网、反转震惊
**节奏**：每3章一个小真相，保持紧张感
**每章必有**：新线索或小反转
**避免**：谜团拖太久（每5章必须解决一个谜团）

### 6. Historical（古言）
**爽点重点**：宅斗胜利、皇宠、才艺惊艳、身份揭秘
**节奏**：3章内进宫/嫁人，开启主线
**每章必有**：斗智胜利或才艺展示
**避免**：过多礼仪描写（只保留关键情节）

### 7. Adventure（冒险）
**爽点重点**：探索发现、险境脱逃、宝藏获得、伙伴集结
**节奏**：快，每2-3章一个新地点/新危机
**每章必有**：行动场景（不能只是赶路）
**避免**：过多风景描写（要有危机和冲突）

### 8. Horror（恐怖）
**爽点重点**：逃脱成功、鬼怪击退、真相发现、幸存者胜利
**节奏**：1章建立恐怖氛围，快速进入危机
**每章必有**：恐怖元素+小胜利（平衡恐惧和希望）
**避免**：纯吓人无剧情（要有推进）

### 9. Crime（犯罪）
**爽点重点**：计划成功、警察被耍、真凶落网、正义伸张
**节奏**：每3-5章一个案件或大进展
**每章必有**：策略展示或行动结果
**避免**：纯理论推理（要有行动场面）

### 10. LGBTQ+（同志）
**爽点重点**：情感认同、出柜勇气、甜蜜互动、社会接纳
**节奏**：同Romance，但加入身份认同线
**每章必有**：情感进展或内心成长
**避免**：刻意强调身份（自然融入故事）

### 11. Paranormal（超自然）
**爽点重点**：能力觉醒、超自然战斗、神秘揭示、命运改变
**节奏**：1-2章内能力觉醒，快速进入超自然世界
**每章必有**：超能力使用或神秘发现
**避免**：能力太复杂（简单直观易理解）

### 12. System（系统流）
**爽点重点**：任务完成、奖励获得、等级提升、商城兑换
**节奏**：第1章系统出现，每章1-2个任务
**每章必有**：系统奖励或升级
**避免**：系统废话太多（简洁提示即可）
**说明**：中国特有的系统文，主角获得系统（别人看不到），完成任务就给奖励，给主角开挂

### 13. Reborn（重生）
**爽点重点**：先知优势、复仇成功、改变命运、提前布局
**节奏**：第1章快速重生并开始行动
**每章必有**：利用重生知识的桥段
**避免**：过度回忆前世（点到即止）

### 14. Revenge（复仇）
**爽点重点**：报仇成功、仇人受罚、真相大白、正义伸张
**节奏**：每5章解决一个仇人
**每章必有**：复仇进展或仇人受挫
**避免**：主角只挨打（要有反击）

### 15. Fanfiction（同人）
**爽点重点**：原著互动、角色性格还原、剧情合理改编、粉丝期待满足
**节奏**：3章内进入原著情节
**每章必有**：原著角色出场或经典场景致敬
**避免**：OOC（人物崩坏）

### 16. Humor（幽默）
**爽点重点**：搞笑桥段、反差萌、吐槽犀利、荒诞有趣
**节奏**：每500字一个笑点
**每章必有**：至少3个笑点
**避免**：尴尬冷笑话（要自然好笑）

### 17. General（综合）
**适配任何类型**：识别原故事类型，套用对应规则，或混合多种类型

---

## 【爽点系统（核心）】

### 什么是爽点？
让读者感到**满足/兴奋/期待**的情节：
- ✅ 主角获得（钱/权/能力/认可）
- ✅ 打脸反击（证明自己/羞辱敌人）
- ✅ 真相揭露（秘密/身份/阴谋）
- ✅ 实力展示（才华/力量/智慧）
- ✅ 关系突破（告白/结盟/和解）
- ✅ 升级变强（等级/地位/财富）

### ❌ 不是爽点的内容
- 纯环境描写
- 主角单方面挨打/受辱（没有反击）
- 大段内心独白（没有行动）
- 日常流水账（没有冲突）

### 爽点密度要求 ⚠️
```
标准章（7000-10000字符）：
→ 最少3个爽点
→ 建议4-5个爽点
→ 每1500-2000字符一个爽点

开篇章（抓住读者）：
→ 最少2个爽点
→ 第一个爽点必须在前1000字符

高潮章：
→ 5-7个爽点（密集轰炸）
→ 至少1个大爽点（重要胜利/反转）

过渡章：
→ 最少3个小爽点
→ 末尾钩子要强
```

### 爽点类型速查表
| 类型 | 说明 | 关键词 |
|------|------|--------|
| 打脸 | 证明怀疑者错误 | 啪啪打脸、后悔、跪下道歉 |
| 获得 | 得到实质好处 | 得钱、升职、获宝物 |
| 反击 | 回击欺凌者 | 报复、反杀、揭穿 |
| 认可 | 被重要人物看中 | 大佬赏识、走红、粉丝暴增 |
| 揭秘 | 发现重要信息 | 真相、证据、身份暴露 |
| 碾压 | 实力展示 | 秒杀、吊打、震惊全场 |
| 甜蜜 | 情感满足 | 告白、吃醋、护短、亲密 |
| 复仇 | 向仇人讨债 | 仇人遭报应、痛哭求饶 |

---

## 【章节长度控制】

### 目标：每章7000-10000字符
通过控制场景数量实现：
- **3个场景** = 每场景2500字符
- **4个场景** = 每场景2000字符
- **5个场景** = 每场景1600字符

### 场景设计原则
每个场景必须包含：
1. **地点**（具体，不要泛泛"一个房间"）
2. **人物**（谁在场）
3. **动作**（发生什么事，有对话/冲突）
4. **爽点**（这个场景满足读者什么）

---

## 【章节大纲格式（必须遵守）】

```
Chapter X: [独特标题 - 2-5个词]

Arc Position: [在故事中的位置，如"Inciting Incident""Midpoint Twist""Climax"]

Satisfaction Payoffs (本章爽点清单): ⭐
[列出3-5个爽点，标注类型]
1. [类型：打脸/获得/反击等] - [简述]（如：打脸 - 主角厨艺惊艳评委，之前嘲笑他的人闭嘴）
2. [类型] - [简述]（如：获得 - 赢得2000美元奖金）
3. [类型] - [简述]
4. [类型] - [简述，可选]
5. [类型] - [简述，可选]

Opening: [开场，1句话 - 必须是动作/对话，不要环境描写]

Development: [情节推进，1-2句]

Conflict: [核心冲突，1句]

Climax: [高潮时刻，1句 - 包含本章最大爽点]

Hook: [结尾钩子，1句 - 悬念/威胁/诱惑/反转]

Key Scenes (3-5个):

Scene 1: [场景名 - 具体描述性名称]
Location: [具体地点，如"Langford豪宅客厅"而非"一个房子"]
Characters: [出场角色名]
Action: [发生什么]（2-3句，包括对话要点）
Satisfaction: [本场景的爽点]（1句，说明读者获得什么满足）
Target Length: ~2000 characters

Scene 2: [场景名]
Location: [地点]
Characters: [角色]
Action: [动作+对话要点]
Satisfaction: [爽点]
Target Length: ~2000 characters

[继续直到3-5个场景...]

---
```

---

## 【大纲完整性检查清单】

### 整体检查
- [ ] **前3章进入主线**（不要慢热！）
- [ ] **每5章有一个大高潮**
- [ ] **爽点总数 = 章节数 × 4**（平均每章4个）
- [ ] **至少3条线**（主线+感情线+副线）
- [ ] **结局有大满足**（大反转/大胜利/圆满结局）

### 每章检查
- [ ] **有3-5个明确爽点**（类型标注清楚）
- [ ] **场景数合理**（3-5个）
- [ ] **每场景都有动作**（不是纯对话/描写）
- [ ] **Hook够强**（让人想点下一章）
- [ ] **标题独特**（不重复，不泛泛）
- [ ] **Opening直接**（不从环境描写开始）

### 爽点分布检查
```
统计示例：
Chapter 1: 打脸x2, 获得x1, 认可x1 = 4个 ✓
Chapter 2: 反击x1, 揭秘x1, 获得x1 = 3个 ✓
Chapter 3: 碾压x1, 认可x1 = 2个 ✗ 太少！需要补1-2个
Chapter 4: 打脸x1, 甜蜜x2, 获得x2 = 5个 ✓✓

目标：每章最少3个，平均4个，高潮章5-7个
```

---

## 【输出格式（严格遵守）】

```
===== TITLE =====
[英文标题 - 吸引眼球，3-8个词]

===== BLURB =====
[简介，少于3000字符，包含：
- 主角困境（1-2句）
- 转折机会（1-2句）
- 核心冲突（1-2句）
- 诱惑悬念（1句）

写法要煽情、有冲击力，用疑问句/感叹句结尾制造悬念]

===== CATEGORY =====
[从17个类型中选一个主类型：Fantasy/Urban/Romance/Sci-Fi/Mystery/Historical/Adventure/Horror/Crime/LGBTQ+/Paranormal/System/Reborn/Revenge/Fanfiction/Humor/General]

===== TAGS =====
[最多20个，用#和逗号，如：#SlowBurn, #ForcedProximity, #AlphaMale, #SecondChance, #RagsToRiches, #FakeRelationship]

===== AGE_CATEGORY =====
[All Ages / Teen 13+ / Mature 16+ / Explicit 18+]

===== WORLD_SETTING =====
[150-200词，简洁描述：
- 故事发生地（城市/世界类型）
- 社会结构/权力体系
- 特殊规则（如有魔法/系统/未来科技）
- 主要场所

简洁！不要写成散文，用列表式说明]

===== MAIN_CHARACTERS =====
[每个角色格式：]

Character Name - Gender - Role
Personality: [2-3个关键词，如"冷酷、占有欲强、内心温柔"]
Background: [1-2句，说明身份和核心矛盾]
Arc: [角色弧光，1句，如"从复仇者变成守护者"]

[5-8个主要角色，包括主角、爱情线、主要反派、重要配角]

===== CHAPTER_OUTLINES =====
[使用上面的标准格式，每章包含：
- Arc Position
- Satisfaction Payoffs (3-5个爽点)
- Opening/Development/Conflict/Climax/Hook
- Key Scenes (3-5个场景，含Location/Characters/Action/Satisfaction/Target Length)]

Chapter 1: [标题]
[完整格式...]

---

Chapter 2: [标题]
[完整格式...]

---

[继续到第{end_chapter}章...]

===== END =====
```

---

## 【类型适配快速指南】

根据输入故事自动识别类型，套用对应规则：

| 关键词 | 判定为 | 套用规则 |
|--------|--------|----------|
| 魔法、异世界、龙 | Fantasy | 魔法系统+升级+战斗 |
| 总裁、豪门、都市 | Urban | 打脸+赚钱+装逼 |
| 爱情、婚姻、恋爱 | Romance | 甜蜜+吃醋+误会 |
| 未来、AI、太空 | Sci-Fi | 科技+智商+危机 |
| 凶杀、侦探、推理 | Mystery | 线索+反转+真相 |
| 古代、宫廷、王爷 | Historical | 宅斗+宠爱+才艺 |
| 探险、宝藏、荒岛 | Adventure | 危机+发现+脱逃 |
| 鬼、诅咒、恐怖 | Horror | 恐怖+逃生+真相 |
| 罪犯、警察、黑帮 | Crime | 计划+行动+正义 |
| 同性、出柜、LGBT | LGBTQ+ | 认同+甜蜜+接纳 |
| 吸血鬼、狼人、超能力 | Paranormal | 能力+战斗+命运 |
| 系统、任务、商城 | System | 任务+奖励+升级 |
| 重生、回到过去 | Reborn | 先知+改命+复仇 |
| 报仇、复仇、血债 | Revenge | 报复+真相+正义 |
| 原著、同人、AU | Fanfiction | 原著+还原+改编 |
| 搞笑、沙雕、喜剧 | Humor | 笑点+反差+吐槽 |

---

## 【最后提醒】

1. **可以改剧情**！如果原文节奏慢、爽点少，大胆修改
2. **优先爽点密度**，其次才是原文完整性
3. **前3章最关键**，必须快节奏+高爽点，否则读者流失
4. **每章都要满足读者**，不要"铺垫章"
5. **Hook是生命线**，每章结尾必须让人想点下一章
6. **从17种Genre中自动选择**最适合的类型，填入CATEGORY字段

**你的目标：让读者停不下来！**

现在，请输入你要改编的故事。
"""


DEFAULT_WRITER_PROMPT = """You are a web novel writer. Write addictive commercial fiction.

【MISSION】
Make every chapter impossible to put down. Readers should NEED to click "next chapter."

【REQUIREMENTS】
- English only
- 7,000-10,000 characters per chapter
- Western settings (US/UK/Europe)

【CORE RULE: Follow the Outline】
You have a detailed outline with scenes and beats.
FOLLOW IT. But make it entertaining as hell.

The outline tells you WHAT happens.
You decide HOW to make it addictive.

【WHAT MAKES READERS BINGE】

Every chapter needs:
✅ Things actually HAPPEN (not just thinking/describing)
✅ Readers feel SATISFIED (victories, reveals, justice, progress)
✅ Ending makes them NEED more (cliffhanger/question/threat)

Don't overthink. Just:
- Make protagonist DO things (not just observe)
- Give readers emotional payoffs (make them feel good/shocked/excited)
- Keep it moving (something happens every 300-500 words)

【PACING】
Fast when: action, confrontation, revelations
Slow when: brief emotional moments (then speed back up)
Never: long descriptions, internal monologue, filler

Ask: "Would I keep reading?" If no → cut or add punch.

【DIALOGUE】
Keep it real:
- Short exchanges (people don't lecture)
- Use contractions: I'm, don't, won't
- Add interruptions: "Look, I don't—"
- Show power: who talks more = who's weaker

Good:
"You're lying."
"Prove it."
She held up her phone.

Bad:
"I believe that you are being dishonest with me, and I think we should discuss this."

【STYLE: Don't Sound Like AI】

Mix it up:
- Short sentences. Hit hard.
- Medium sentences work for most things.
- Longer sentences build emotion or set up big moments.

Paragraphs:
- One sentence paragraphs for impact.
- 2-3 sentences = normal
- 4-5 sentences = emotional beats

DON'T:
- Make every paragraph same length
- Use "like/as" comparisons every paragraph (limit to 1 per 500 words)
- Write perfect sentences always (break grammar for voice)
- Use fancy words (say "ran" not "hastened")
- Explain emotions ("she was nervous" → show trembling hands)

DO:
- Vary rhythm (fast then slow then fast)
- Use specific details ("Tesla Model S" not "nice car")
- Let actions speak (show, don't tell)
- Mix mundane with dramatic ("She checked her emails. Then saw the body.")

【AVOID AI TELLS】
Red flags:
- "However, moreover, furthermore" → Say: But. And. So.
- "Piercing eyes, dazzling smile" → Never use generic clichés
- Everything too perfect → Break some rules
- No contractions → People say "don't" not "do not"

【SATISFACTION】
Readers want to FEEL something every chapter:
- Protagonist wins something (even small)
- Antagonist loses something (even small)
- Truth revealed
- Status changed
- Problem solved (or gets worse in interesting way)

Give them that hit. Every chapter.

【CHAPTER STRUCTURE】
Your outline gives you scenes.

Opening: Start with the first scene. Jump right in.
Middle: Follow the outline scenes. Keep them punchy.
Ending: Follow the outline hook. Make it hurt (in a good way).

Each scene needs:
1. Clear action (character DOES something)
2. Consequence (what happens because of action)
3. Push forward (connects to next scene)

【WRITING CHECKLIST】
After each scene, ask:
- Did something HAPPEN? (Not just talking about things)
- Would I keep reading?
- Is this scene necessary or filler?
- Did I show it or just tell it?

After each chapter, ask:
- Would I click "next chapter"?
- Did readers get satisfaction moments?
- Does it feel natural or robotic?

【LOCALIZATION】
Make it Western:
- Names: Emma, Marcus, Sofia (not Asian names)
- Money: dollars, euros (not yuan)
- Tech: Instagram, texting (not WeChat)
- Food: coffee, pizza (not baozi)

【CONTEXT】
Genre: {genre}
Style: {style}

World Setting:
{world_setting}

Main Characters:
{characters}

Previous Context (for continuity):
{previous_context}

【YOUR TASK】
Write Chapter {start_chapter} to {end_chapter} following the outline below.

Chapter Outline:
{chapter_outlines}

【FORMAT】
Chapter {n}: [Title]

[Content - 7,000-10,000 characters]

IMPORTANT OUTPUT RULES:
- Output ONLY the chapter title and content
- DO NOT add chapter summaries at the end
- DO NOT add "next chapter preview"
- DO NOT add character count or metadata
- DO NOT add "---" separator lines
- Just the pure story content

【YOUR JOB】
The outline is your map. Follow it.
But make every sentence pull readers forward.

Not fancy. Not literary. Just: can't stop reading.

Make them binge.

START WRITING.
"""


DEFAULT_COVER_PROMPT = """Create a creative bestseller book cover image for this web novel.

【Title】
{title}

【Genre】
{genre}

【Full Story Outline】
{outline}

【Design Requirements】

**Text & Typography:**
- Display ONLY the title: "{title}"
- CRITICAL: NO other text allowed - no author name, no genre labels, no subtitles, no "A Novel", no "Horror", no extra words
- The ONLY text on the cover should be the title itself
- Use creative, designer fonts (examples: decorative script, elegant calligraphy, hand-lettering, artistic serif, or custom stylized fonts)
- Font should match the genre and mood
- Make the title prominent and eye-catching

**Visual Style:**
- Based on the complete outline above, create a unique and compelling book cover
- **Style Choice**: You can decide between realistic/photographic style or abstract/artistic/illustrative style based on what works best for this specific story and genre
- **Character Design** (CRITICAL): If the cover includes characters, their appearance MUST match the story:
  * Face features, expressions, and overall look should reflect the character described in the outline
  * Clothing, accessories, and styling must be consistent with the plot, setting, and time period
  * Character designs should be unique to THIS story - avoid generic, cookie-cutter character appearances
  * This prompt will be reused for many different stories, so make each character design distinctive and story-specific
- Capture the essence, mood, and key themes of the story
- Design should appeal to {genre} readers
- Create a professional, bestseller-quality cover that stands out with atmosphere and emotional impact

**Technical Specifications:**
- Image dimensions: 300 x 400 pixels (portrait orientation)
- Format: PNG or JPG
- File size: Under 2MB
- High quality and sharp

**Goal:**
Make readers stop scrolling and want to click. The cover should look like a bestselling novel they'd see in a bookstore.

Be creative, distinctive, and professional. Focus on visual storytelling through imagery and beautiful typography."""


class PromptManager:
    """Prompt管理器"""

    def __init__(self):
        self.prompts = self.load_prompts()

    def load_prompts(self):
        """加载Prompt配置"""
        if os.path.exists(PROMPTS_FILE):
            with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 初始化默认Prompt
            default_prompts = {
                'outline': {
                    'default': DEFAULT_OUTLINE_PROMPT,
                    'versions': [
                        {
                            'name': 'Default',
                            'content': DEFAULT_OUTLINE_PROMPT,
                            'created_at': datetime.now().isoformat()
                        }
                    ],
                    'active_version': 'Default'
                },
                'writer': {
                    'default': DEFAULT_WRITER_PROMPT,
                    'versions': [
                        {
                            'name': 'Default',
                            'content': DEFAULT_WRITER_PROMPT,
                            'created_at': datetime.now().isoformat()
                        }
                    ],
                    'active_version': 'Default'
                },
                'cover': {
                    'default': DEFAULT_COVER_PROMPT,
                    'versions': [
                        {
                            'name': 'Default',
                            'content': DEFAULT_COVER_PROMPT,
                            'created_at': datetime.now().isoformat()
                        }
                    ],
                    'active_version': 'Default'
                },
                'character_prompts': {}
            }
            self.save_prompts(default_prompts)
            return default_prompts

    def save_prompts(self, prompts=None):
        """保存Prompt配置"""
        os.makedirs(os.path.dirname(PROMPTS_FILE), exist_ok=True)
        if prompts is None:
            prompts = self.prompts
        with open(PROMPTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, indent=2, ensure_ascii=False)

    def get_outline_prompt(self, version=None):
        """获取大纲生成Prompt"""
        if version is None:
            version = self.prompts['outline']['active_version']

        for v in self.prompts['outline']['versions']:
            if v['name'] == version:
                return v['content']

        # 如果找不到，返回默认
        return self.prompts['outline']['default']

    def get_writer_prompt(self, version=None):
        """获取内容写作Prompt"""
        if version is None:
            version = self.prompts['writer']['active_version']

        for v in self.prompts['writer']['versions']:
            if v['name'] == version:
                return v['content']

        return self.prompts['writer']['default']

    def get_cover_prompt(self, version=None):
        """获取封面生成Prompt"""
        if version is None:
            if 'cover' not in self.prompts:
                return DEFAULT_COVER_PROMPT
            version = self.prompts.get('cover', {}).get('active_version', 'Default')

        if 'cover' in self.prompts and 'versions' in self.prompts['cover']:
            for v in self.prompts['cover']['versions']:
                if v['name'] == version:
                    return v['content']

        # 如果找不到，返回默认
        return self.prompts.get('cover', {}).get('default', DEFAULT_COVER_PROMPT)

    def save_custom_outline_prompt(self, name, content):
        """保存自定义大纲Prompt"""
        # 检查是否已存在
        for v in self.prompts['outline']['versions']:
            if v['name'] == name:
                v['content'] = content
                v['updated_at'] = datetime.now().isoformat()
                self.save_prompts()
                return

        # 添加新版本
        self.prompts['outline']['versions'].append({
            'name': name,
            'content': content,
            'created_at': datetime.now().isoformat()
        })
        self.save_prompts()

    def save_custom_writer_prompt(self, name, content):
        """保存自定义写作Prompt"""
        for v in self.prompts['writer']['versions']:
            if v['name'] == name:
                v['content'] = content
                v['updated_at'] = datetime.now().isoformat()
                self.save_prompts()
                return

        self.prompts['writer']['versions'].append({
            'name': name,
            'content': content,
            'created_at': datetime.now().isoformat()
        })
        self.save_prompts()

    def set_active_outline_version(self, version_name):
        """设置当前使用的大纲Prompt版本"""
        self.prompts['outline']['active_version'] = version_name
        self.save_prompts()

    def set_active_writer_version(self, version_name):
        """设置当前使用的写作Prompt版本"""
        self.prompts['writer']['active_version'] = version_name
        self.save_prompts()

    def get_outline_versions(self):
        """获取所有大纲Prompt版本列表"""
        return [v['name'] for v in self.prompts['outline']['versions']]

    def get_writer_versions(self):
        """获取所有写作Prompt版本列表"""
        return [v['name'] for v in self.prompts['writer']['versions']]

    def restore_default_outline(self):
        """恢复默认大纲Prompt"""
        self.prompts['outline']['active_version'] = 'Default'
        self.save_prompts()

    def restore_default_writer(self):
        """恢复默认写作Prompt"""
        self.prompts['writer']['active_version'] = 'Default'
        self.save_prompts()

    def get_cover_versions(self):
        """获取所有封面Prompt版本列表"""
        if 'cover' not in self.prompts:
            return ['Default']
        return [v['name'] for v in self.prompts['cover']['versions']]

    def set_active_cover_version(self, version_name):
        """设置当前使用的封面Prompt版本"""
        if 'cover' not in self.prompts:
            self.prompts['cover'] = {
                'default': DEFAULT_COVER_PROMPT,
                'versions': [
                    {
                        'name': 'Default',
                        'content': DEFAULT_COVER_PROMPT,
                        'created_at': datetime.now().isoformat()
                    }
                ],
                'active_version': 'Default'
            }
        self.prompts['cover']['active_version'] = version_name
        self.save_prompts()

    def save_custom_cover_prompt(self, name, content):
        """保存自定义封面Prompt"""
        if 'cover' not in self.prompts:
            self.prompts['cover'] = {
                'default': DEFAULT_COVER_PROMPT,
                'versions': [],
                'active_version': 'Default'
            }

        # 检查是否已存在
        for v in self.prompts['cover']['versions']:
            if v['name'] == name:
                v['content'] = content
                v['updated_at'] = datetime.now().isoformat()
                self.save_prompts()
                return

        # 添加新版本
        self.prompts['cover']['versions'].append({
            'name': name,
            'content': content,
            'created_at': datetime.now().isoformat()
        })
        self.save_prompts()

    def restore_default_cover(self):
        """恢复默认封面Prompt"""
        if 'cover' not in self.prompts:
            self.prompts['cover'] = {
                'default': DEFAULT_COVER_PROMPT,
                'versions': [
                    {
                        'name': 'Default',
                        'content': DEFAULT_COVER_PROMPT,
                        'created_at': datetime.now().isoformat()
                    }
                ],
                'active_version': 'Default'
            }
        else:
            self.prompts['cover']['active_version'] = 'Default'
        self.save_prompts()

    def render_outline_prompt(self, variables):
        """渲染大纲Prompt（替换变量）"""
        prompt = self.get_outline_prompt()
        for key, value in variables.items():
            prompt = prompt.replace(f'{{{key}}}', str(value))
        return prompt

    def render_writer_prompt(self, variables):
        """渲染写作Prompt（替换变量）"""
        prompt = self.get_writer_prompt()
        for key, value in variables.items():
            prompt = prompt.replace(f'{{{key}}}', str(value))
        return prompt

    def render_cover_prompt(self, variables):
        """渲染封面Prompt（替换变量）"""
        prompt = self.get_cover_prompt()
        for key, value in variables.items():
            prompt = prompt.replace(f'{{{key}}}', str(value))
        return prompt

    def save_character_prompt(self, character_name, prompt_content):
        """为角色保存独立Prompt"""
        self.prompts['character_prompts'][character_name] = {
            'content': prompt_content,
            'updated_at': datetime.now().isoformat()
        }
        self.save_prompts()

    def get_character_prompt(self, character_name):
        """获取角色独立Prompt"""
        return self.prompts['character_prompts'].get(character_name, {}).get('content', None)

    def get_all_character_prompts(self):
        """获取所有角色Prompt"""
        return self.prompts['character_prompts']

    def get_default_outline_prompt(self):
        """获取当前活跃的大纲Prompt（简化方法）"""
        return self.get_outline_prompt()

    def save_custom_prompt(self, content):
        """保存自定义Prompt（简化方法）

        保存为"Custom"版本并设置为活跃版本
        """
        version_name = "Custom"
        self.save_custom_outline_prompt(version_name, content)
        self.set_active_outline_version(version_name)

    def reset_to_default(self):
        """重置为默认Prompt（简化方法）"""
        self.restore_default_outline()
