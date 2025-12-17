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


def safe_format_prompt(template, **kwargs):
    """安全地格式化prompt模板，忽略未知的占位符"""
    import re
    result = template
    for key, value in kwargs.items():
        # 替换 {key} 格式的占位符
        result = result.replace('{' + key + '}', str(value))
    return result


def open_folder_in_explorer(path):
    """在系统文件管理器中打开文件夹"""
    import subprocess
    if not os.path.exists(path):
        return False
    try:
        if sys.platform == 'win32':
            os.startfile(path)
        elif sys.platform == 'darwin':
            subprocess.run(['open', path])
        else:
            subprocess.run(['xdg-open', path])
        return True
    except Exception as e:
        print(f"打开文件夹失败: {e}")
        return False


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

## ⚠️ ABSOLUTE PROHIBITIONS - READ FIRST

**1. NO CHINESE CHARACTERS**
- The story must be 100% English
- Even if you think about concepts using Chinese terms (like "爽点"), NEVER output them
- No mixing of English and Chinese under any circumstances

**2. NO META-COMMENTARY** ⚠️⚠️⚠️ CRITICAL ERROR IF VIOLATED
- Do NOT output planning labels like "Setup:", "Confrontation:", "Public Reaction:"
- Do NOT output "First satisfaction", "Second satisfaction", "Satisfaction seventh"
- Do NOT output "Satisfaction scene —" or any labels describing what type of scene follows
- Do NOT number or label story elements for readers
- These are internal planning tools ONLY - never part of the actual story
- **VIOLATION OF THIS RULE = STORY REJECTED**

**Examples of FORBIDDEN outputs:**
```
❌ "First satisfaction came when..."
❌ "Setup: Reed arrived at the office..."
❌ "Confrontation: She confronted him..."
❌ "Satisfaction scene — public ripple: the kiss went viral..."
❌ "Satisfaction scene — small power display: on a noisy set..."
❌ "Satisfaction scene — face-slapping of fake favorite..."
❌ "The second爽点 occurred..."
❌ Any label that describes the story structure TO the reader
```

**3. WRITE THE STORY DIRECTLY**
- Jump straight into scenes
- No structural labels
- No explanatory tags
- Just write what happens
- Readers should never see your planning process

---

## ⚠️ CRITICAL: LANGUAGE REQUIREMENT

**Output must be 100% English.**

Even if the input file contains Chinese text, your output must be entirely in English. No Chinese characters allowed in the story.

---

## CORE TASK

You will receive a text file containing a **truncated/incomplete Chinese story**.

**Your mission: Understand → Localize → Complete**

**What you're doing:**
1. **Understand** the original's creativity and plot direction
2. **Localize** it into English (translate names, places, cultural elements)
3. **Complete** the story following the original direction
4. Maintain **satisfaction-driven** pacing throughout

**This is NOT:**
- ❌ Pure translation (word-for-word)
- ❌ Creating a new story inspired by it
- ❌ Replacing the plot with generic templates

**This IS:**
- ✅ Understanding the original creative concept
- ✅ Translating/localizing for English readers
- ✅ Continuing and completing THAT specific story
- ✅ Keeping it fast-paced and satisfying

**Key principle:**
> "Absorb the original story's creativity and uniqueness, translate it into natural English with localized names and settings, then complete it in the same direction while maintaining satisfaction density."

---

**Your two-step approach:**

### STEP 1: UNDERSTAND THE ORIGINAL PLOT

**Read carefully to absorb the story's unique creativity:**

1. **What makes THIS story special?**
   - What's the unique premise? (body swap? hidden identity? special ability? competition?)
   - What's the creative hook that makes it interesting?
   - What's the specific conflict that drives this story?

2. **Identify the SPECIFIC plot (not generalizations):**
   - **Exact setting**: Hospital? Restaurant? Office? School? Stadium? Competition venue?
   - **Exact characters**: Who exists? What are their roles? Their relationships?
   - **Exact conflicts**: What SPECIFIC problem exists? (not "face-slapping" - the actual conflict)
   - **Exact events in progress**: What's happening or about to happen?

3. **Find the story's direction:**
   - Medical story → heading towards diagnosis? surgery? medical conference?
   - Cooking story → heading towards competition finals? restaurant opening? taste test?
   - Business story → heading towards board meeting? product launch? contract signing?
   - School story → heading towards exam? presentation? competition?
   - Sports story → heading towards championship? tryout? match?

4. **Understand the creative scenarios:**
   - What unique situations did the original create?
   - What creative confrontations were set up?
   - What interesting evidence or abilities exist?
   - What makes the satisfaction moments in THIS story different?

**Examples of absorbing creativity:**

**Example 1 - Unique Premise:**
```
Original: 医学实习生有预知病症能力...
Creative element: Supernatural medical ability
→ Absorb: Keep the precognition concept
→ Localize: Medical intern Sarah has diagnostic visions
→ Complete: Use this ability in medical scenarios throughout
```

**Example 2 - Unique Setting:**
```
Original: 地下拳击赛场的复仇故事...
Creative element: Underground fight club as venue
→ Absorb: Keep the underground fighting world
→ Localize: Harbor City underground circuit, fighters with street names
→ Complete: Continue revenge through fight matches
```

**Example 3 - Unique Relationship:**
```
Original: 姐姐和妹妹身份互换后的人生...
Creative element: Sisters swap identities
→ Absorb: Identity swap premise
→ Localize: Sisters Emma and Sophia switch lives
→ Complete: Continue complications from the swap
```

**Key point:** Every Chinese web novel has something that makes it unique. Your job is to find that uniqueness, translate it naturally, and complete it.

### STEP 2: LOCALIZE (Translate for English Readers)

**Now translate/localize the story for English-speaking readers while keeping the creative concept:**

**This is cultural adaptation, not plot change!**

**WHAT TO LOCALIZE (translate these):**
- ✅ Character names: 李伟 → Marcus Fletcher, 王美丽 → Sarah Chen
- ✅ Location names: 北京 → Harbor City, 上海医院 → Summit Medical Center
- ✅ Company names: 腾讯 → TechCore Industries, 阿里巴巴 → StreamWave Corp
- ✅ Social media: 微信 → Instagram/WhatsApp, 微博 → Twitter
- ✅ Cultural references: Adapt to Western context where needed
- ✅ Currency: 人民币 → dollars, yuan → USD

**WHAT NOT TO CHANGE (keep these):**
- ❌ The plot direction: If heading towards a medical diagnosis showdown, keep that direction
- ❌ The conflict type: If it's a cooking competition, don't change to business fraud
- ❌ The locations: If set in a restaurant, keep restaurant scenes
- ❌ The scenarios: If there's a medical conference coming up, keep that medical conference
- ❌ The character roles: If someone is a chef, keep them a chef (don't make them a CEO)
- ❌ The event type: If there's a cooking finals, don't replace with a charity gala

**CRITICAL EXAMPLES:**

**Example 1 - Medical Diagnosis Story:**
```
Original (Chinese):
实习医生在医院诊断疑难病症...
主任医生质疑她的诊断...
即将参加医学研讨会证明自己...

✅ CORRECT continuation:
- Continue with: medical conference, diagnosis challenge, hospital colleagues watching
- Localize to: Harbor Medical Center, Dr. Sarah Chen, Chief of Medicine Dr. Rodriguez
- Keep: medical setting, diagnosis conflict, professional competition

❌ WRONG continuation:
- Abandon medical plot
- Replace with: charity gala fraud, courtroom trial, business contract dispute
- Change character to CEO or lawyer
```

**Example 2 - Cooking Competition:**
```
Original (Chinese):
参加厨艺大赛...
评委看不起她的乡村菜...
决赛要做一道家乡特色菜证明自己...

✅ CORRECT continuation:
- Continue with: cooking competition finals, judges tasting her signature dish
- Localize to: Harbor City Culinary Championship, Judge Martinez, regional American cuisine
- Keep: cooking competition, culinary challenge, judges' reactions

❌ WRONG continuation:
- Abandon cooking competition
- Replace with: corporate takeover, legal battle, entertainment industry scandal
- Change character to businesswoman or actress
```

**Example 3 - Business Takeover:**
```
Original (Chinese):
公司董事会斗争...
她要在股东大会夺回控制权...
准备揭露竞争对手的财务造假...

✅ CORRECT continuation:
- Continue with: shareholder meeting, financial evidence reveal, board vote
- Localize to: TechCore Industries, CEO Walker, Harbor City headquarters
- Keep: corporate setting, business conflict, shareholder meeting

❌ WRONG continuation:
- Replace shareholder meeting with charity gala
- Add irrelevant courtroom trial (unless original had legal subplot)
- Change to entertainment industry drama
```

**KEY PRINCIPLE:**
```
Original plot path: A (hospital) → B (diagnosis challenge) → C (medical conference) → [truncated]
Your task: Continue → D (conference confrontation) → E (diagnosis success) (SAME path)

NOT: Abandon and create → X (charity gala) → Y (fraud scandal) → Z (courtroom) (DIFFERENT path)
```

**Common mistakes to AVOID:**
- ❌ "Original is about restaurant opening → I write charity gala scandal"
- ❌ "Original is about academic competition → I write business fraud trial"
- ❌ "Original is about family dinner conflict → I write courtroom battle"
- ❌ "Original is about sports championship → I write contract dispute"
- ❌ "Original is about [ANY specific scenario] → I default to charity gala/courtroom/business fraud"

**Goals:**
- **Complete the truncated story following its own direction** (most important!)
- Maintain original plot path and scenarios
- Localize names, places, cultural elements to English/Western context
- Fast-paced, dialogue-driven
- Complete story arc

**Core Principle: Follow Original Plot Path + Localize to English. Don't Replace Original Scenarios with Your Default Templates.**

---

## PARAMETERS
- Suggested male names: {male_names}
- Suggested female names: {female_names}

### LENGTH REQUIREMENTS ⚠️ CRITICAL

**MINIMUM: 20,000 characters** (hard requirement - stories under 20K will be rejected)
**OPTIMAL: 25,000-35,000 characters** (sweet spot for satisfaction density)
**MAXIMUM: 45,000 characters** (rarely needed)

**Why minimum 20,000 characters:**
- Need space for 6-8 satisfaction scenes (each 300-500 chars) = 2,400-4,000 chars
- Need dialogue-heavy writing (40%+ dialogue naturally takes more space)
- Need complete story arc with proper setup and payoff
- Need multiple antagonist confrontations
- Stories under 20K feel rushed and unsatisfying

**How to reach 20,000+ without padding:**
- Write 6-8 full satisfaction scenes (300-500 chars each)
- High dialogue density (40%+) naturally adds length
- Multiple confrontations with different antagonists
- Show reactions and consequences after each scene
- Add witness dialogues and crowd responses
- Include aftermath scenes showing impact

**What NOT to do to add length:**
- ❌ Don't pad with environmental descriptions
- ❌ Don't add slow "daily life" filler scenes
- ❌ Don't write long internal monologues
- ❌ Don't repeat the same information
- ❌ Don't drag out non-confrontational scenes

**What TO do if story is too short:**
- ✅ Add more satisfaction scenes (more antagonists to confront)
- ✅ Expand existing satisfaction scenes with more dialogue
- ✅ Add more witness reactions and comments
- ✅ Show more consequences and aftermath
- ✅ Add supporting character confrontations
- ✅ Extend climax scene with detailed back-and-forth

**Length checkpoint during writing:**
- At 15,000 chars: Should have 4-5 satisfaction scenes completed
- If under 15K with fewer scenes: Add more confrontations
- At final check: Count total characters
- If under 20K: DO NOT finish - add more satisfaction scenes

**⚠️ CRITICAL: Use English names only. No pinyin!**

---

## INPUT HANDLING

The input file typically contains:
- Incomplete/truncated Chinese web novel content
- Story that was cut off mid-plot
- Character introductions and initial conflicts
- Setup for events that haven't happened yet

**Your approach:**

### 1. **Analyze what's already there:**
   - Who are the characters? What are their names and roles?
   - What's the setting? (hospital? restaurant? office? school? competition venue?)
   - What conflicts have been introduced?
   - What events are set up but not completed?
   - What was the last scene before truncation?

### 2. **Identify the story's direction:**
   - Is this heading towards a medical showdown? Cooking finals? Business meeting? Academic competition?
   - What specific scenario was being built up to?
   - What evidence or skills will the protagonist use?
   - What type of confrontation is coming?

### 3. **Plan your continuation:**
   - Continue from the exact cut-off point
   - Complete the events that were set up
   - Use the same locations and scenarios
   - Resolve the conflicts that were introduced
   - Don't introduce completely new plot lines

### 4. **Localize while continuing:**
   - Keep the plot: If it's a cooking competition, continue the cooking competition
   - Keep the setting: If it's in a restaurant, keep restaurant scenes
   - Change the names: 李伟 → English names like Marcus Fletcher
   - Change the locations: 北京 → Harbor City or similar
   - Adapt cultural references: 微信 → Instagram

### 5. **What NOT to do:**
   - ❌ Don't abandon the original plot to create a generic story
   - ❌ Don't replace specific scenarios (hospital→courtroom, cooking→gala, etc.)
   - ❌ Don't ignore what was set up in the original
   - ❌ Don't default to your "comfortable" scenarios (charity gala, courtroom, board meeting)
   - ❌ Don't change character roles (doctor→CEO, chef→lawyer, etc.)

**Example of proper continuation:**

```
INPUT CONTENT:
医学院学生李婷在医院实习，她诊断出一个疑难病例。主任医生王明不相信她，说她太年轻。医院即将举办医学研讨会，她决定在会上证明自己...（truncated）

✅ CORRECT approach:
1. Analyze: Medical student Li Ting, hospital setting, diagnosis conflict with Chief Dr. Wang, medical conference coming up
2. Localize names: Li Ting → Sarah Martinez, Dr. Wang → Dr. Harrison
3. Continue: Write the medical conference scene, diagnosis presentation, colleagues' reactions
4. Complete: Sarah proves diagnosis correct, Dr. Harrison acknowledges, colleagues impressed

❌ WRONG approach:
1. Ignore medical setting
2. Create new character who's a CEO
3. Write about charity gala and financial fraud
4. Add courtroom trial
→ This completely abandons the original story!
```

**Key principle: You're completing a story that started, not creating a new story inspired by it.**

---

## SATISFACTION-DRIVEN FICTION REQUIREMENTS

### Must Have

```
1. ⭐⭐⭐⭐⭐ Dense Satisfaction Moments
   - At least 1 major satisfaction every 3,000-5,000 characters
   - "Satisfying enough" = readers want to cheer

2. ⭐⭐⭐⭐⭐ Fast Pace
   - Enter core conflict within first 3,000 characters
   - No long setup
   - Jump straight into action

3. ⭐⭐⭐⭐ Complete Resolution
   - All conflicts resolved
   - Villains punished
   - Protagonist gets what they deserve

4. ⭐⭐⭐ Simple Setup
   - 3-5 main characters
   - Single plotline
   - Setting explained in one sentence
```

### Must NOT Have

```
❌ Long setup (taking 3,000+ characters to start conflict)
❌ Complex worldbuilding
❌ Too many side characters
❌ Dragging daily life scenes
❌ Unresolved cliffhangers
❌ Slow burn
```

---

## HARD RULES

### Rule 1: Dialogue Density (CRITICAL FOR ALL SETTINGS)
**Minimum 40% dialogue - THIS APPLIES TO ALL SETTINGS.**

Whether modern, historical, or fantasy - dialogue must be 40%+ of your story.

**Self-check while writing:**
- Count dialogue lines every 500 characters
- If under 40%, STOP immediately and add dialogue
- If you write 300 characters of pure narration, STOP and add dialogue NOW

**Convert narration to dialogue:**
❌ Wrong: "She worked with herbs and made a poultice. The boy recovered."
✅ Right:
"Let me try," she said.
"You?" The magistrate scoffed.
She pressed the herbs to his chest. The boy coughed.
"He's breathing!" someone gasped.

**This rule applies equally to:**
- Modern office confrontations
- Medieval court scenes
- Fantasy battle sequences
- ANY setting you choose

### Rule 2: Paragraph Length
**Maximum 5 sentences per paragraph.**

Important moments: single sentence paragraphs.

### Rule 3: Satisfaction Density (MOST IMPORTANT!)

**At least 1 clear satisfaction moment every 3,000-5,000 characters**

Satisfaction types (by intensity):
1. **Public face-slapping** - antagonist humiliated in public
2. **Revenge payoff** - protagonist succeeds in payback
3. **Identity reveal + shock** - hidden identity exposed, everyone stunned
4. **Villain public humiliation** - antagonist's reputation destroyed publicly
5. **Power display** - protagonist's abilities shut down doubters
6. **Recognition from doubters** - people who mocked now acknowledge
7. **Regret from wrongdoers** - those who hurt protagonist now regret

**NOT satisfaction moments:**
- Protagonist suffers without fighting back
- Antagonist's "expression changes slightly" (must actually suffer!)
- Internal satisfaction without external display
- Summary of satisfaction ("it was satisfying")
- Vague descriptions ("everyone was shocked")

---

**CRITICAL: HOW TO WRITE SATISFACTION MOMENTS**

Every satisfaction moment MUST be written as a **specific scene** with:

**1. DIALOGUE-DRIVEN**
- The satisfaction must happen through spoken words
- Protagonist speaks/acts, antagonist reacts
- Bystanders comment or gasp
- Minimum 60% dialogue in satisfaction scenes

**2. SPECIFIC REACTIONS**
- Don't write: "He was shocked"
- Write: His specific physical reaction (face went white, stumbled, voice cracked)
- Write: What he says when shocked
- Write: What others around him say/do

**3. PUBLIC WITNESSES**
- Most satisfying moments need an audience
- Write their reactions: gasps, whispers, camera flashes
- Write what they say to each other
- Show the antagonist's public humiliation

**4. IMMEDIATE CONSEQUENCES**
- Show what happens right after
- Antagonist tries to defend, fails
- Someone in authority reacts (judge, boss, crowd)
- Protagonist gets immediate validation

**5. LENGTH**
- Each major satisfaction scene: 300-500 characters minimum
- Don't rush through it
- Let readers savor the moment
- Use multiple short paragraphs with dialogue

**6. AVOID SUMMARIZING (CRITICAL FOR ALL SETTINGS)**
- Don't tell readers "it was satisfying"
- Don't write "public face-slapping occurred"
- Don't skip the actual scene
- Show the entire interaction

**This applies to ALL settings:**

❌ Wrong (Modern): "The board meeting ended with Conway's arrest."
✅ Right (Modern):
"You're under arrest," the officer said.
Conway's face went white. "You can't—"
Board members gasped. Cameras flashed.

❌ Wrong (Historical): "The duchess was humiliated at court."
✅ Right (Historical):
"You stole from the treasury," the Queen said.
The duchess stumbled. "I—Your Majesty—"
Nobles whispered. "Disgraceful!" someone hissed.

❌ Wrong (Fantasy): "The hero defeated the villain publicly."
✅ Right (Fantasy):
"You're finished," the hero said, sword raised.
The villain fell to his knees. "Mercy!"
The crowd roared. Guards moved forward.

**Every satisfaction scene needs:**
- Specific dialogue exchanges
- Physical reactions described
- Witness responses shown
- Immediate consequences visible

**Regardless of setting - ancient, modern, or fantasy.**

---

**SATISFACTION SCENE STRUCTURE:**

Use this structure for INTERNAL PLANNING ONLY - **NEVER OUTPUT THESE LABELS**:

```
[FOR YOUR PLANNING - DO NOT OUTPUT THESE LABELS IN THE STORY]

Setup (1-2 sentences):
[Situation that leads to satisfaction]

Confrontation (dialogue-heavy, 200-300 chars):
[Protagonist acts/speaks]
[Antagonist's initial reaction]
[Protagonist delivers the blow]
[Antagonist's shocked response]

Public Reaction (100-150 chars):
[Witnesses respond]
[Authority figure reacts]
[Antagonist realizes they're exposed]

Immediate Aftermath (50-100 chars):
[Quick consequence]
[Protagonist's position secured]

[END INTERNAL STRUCTURE - NEVER OUTPUT THIS]
```

**⚠️⚠️⚠️ CRITICAL: HOW TO WRITE THE ACTUAL SCENE:**

**The structure above is for YOUR PLANNING ONLY. Readers must NEVER see these labels.**

❌ WRONG (outputting labels):
```
Setup: Reed arrived at the office.
Confrontation: "You're fired," she said.
Public Reaction: Whispers erupted.
```

❌ WRONG (describing scene type):
```
Satisfaction scene — public ripple: Reed and Gianna arrived at the office.

Satisfaction scene — small power display: She confronted him in front of everyone.
```

✅ CORRECT (no labels, direct scene):
```
Reed and Gianna arrived at the office. The receptionist looked up, startled.

"You're fired," she said, holding up the documents.

His face went white. "What are you—"

"These prove everything." She spread the papers on the desk.

Whispers erupted around them. Someone gasped.
```

**Remember:** The structure helps you plan, but readers only see the scene itself.

**Forbidden phrases in your output:**
- ❌ "Setup:"
- ❌ "Confrontation:"
- ❌ "Public Reaction:"
- ❌ "Satisfaction scene"
- ❌ "First/Second/Third satisfaction"
- ❌ Any label describing story structure

---

**QUALITY CHECK FOR EACH SATISFACTION MOMENT:**

Before moving on, ask:
- [ ] Is this written as a full scene with dialogue?
- [ ] Can readers clearly see what happened?
- [ ] Did I show the antagonist's specific reaction?
- [ ] Are there witnesses and their reactions?
- [ ] Is this at least 300 characters long?
- [ ] Would readers feel satisfied reading this?
- [ ] Did I write it WITHOUT any labels or meta-commentary?

If any answer is NO, expand and rewrite the scene.

### Rule 4: Fast Pace (ALL SETTINGS)

**Within first 3,000 characters:**
- Protagonist faces core conflict
- First satisfaction moment happens
- Readers know what the story is about

**Forbidden (in ANY setting - modern, historical, fantasy):**
- Long background exposition
- Slow worldbuilding
- 2,000 characters of daily life intro
- "Weeks passed and she learned..." → SKIP TO ACTION
- "Days turned to months..." → SKIP TO NEXT SCENE
- Describing setting in detail → Keep minimal

**Jump cuts are your friend:**
❌ Wrong: "Over the next three weeks, she practiced herbs daily, learning each plant's properties. She woke early, studied late, and slowly became proficient..."
✅ Right: "Three weeks later, she stood before the sick boy with her herbs ready."

**Time passage in ONE sentence, then ACTION:**
✅ "Months later, she faced the duchess in court."
✅ "A year passed. Then the general returned."
✅ "That night, everything changed."

**This applies to ALL settings:**
- Modern tech startup drama → Fast
- Medieval court intrigue → Fast
- Fantasy quest story → Fast
- NO setting gets special permission to be slow

### Rule 5: Character Naming

**English names ONLY. Pinyin FORBIDDEN.**

❌ WRONG Examples (pinyin):
- Li Wei → This is pinyin, forbidden
- Zhang Yue → This is pinyin, forbidden
- Wang Chen → This is pinyin, forbidden
- Sophia Chen → Chen is pinyin surname, forbidden
- Alexander Liu → Liu is pinyin surname, forbidden

❌ Common Pinyin Surnames (DO NOT USE):
Chen, Wang, Liu, Zhang, Li, Zhao, Zhou, Wu, Huang, Yang, Xu, Sun, Ma, Zhu, Hu, Guo, Lin, He, Gao, Liang, Zheng, Luo, Song, Xie, Tang, Han, Cao, Feng, Deng, Peng, Zeng, Xiao, Tian, Pan, Yuan, Dong, Yu, Jiang, Cai, Du, Ye, Cheng, Wei, Su, Lu, Ding, Ren, Shen, Yao, Cui, Zhong, Tan, Fan, Liao, Shi, Jin, Jia, Xia, Fu, Fang, Bai, Zou, Meng, Xiong, Qin, Qiu, Yin, Xue, Yan, Duan, Lei, Long, Tao

**Use the provided English name lists in the parameters section above.**

The male_names and female_names lists have been curated to ensure authentic English names. Randomly select from these lists for your characters.

### Rule 6: Clear Simple Setting

Choose ONE clear background that you can write FAST:
- **Modern Urban**: Harbor City, CEO, billionaire, Instagram, New York
- **Historical**: Use English names + Duke/Prince/King - keep it SIMPLE
- **Modern + Supernatural**: Modern city + simple abilities - keep it SIMPLE

**CRITICAL: Regardless of setting choice:**
- Explain setting in MAX 3 sentences
- Don't spend time on worldbuilding
- Don't describe costumes, architecture, customs in detail
- Focus on DIALOGUE and ACTION, not setting description

**Setting examples:**

Modern (Simple):
✅ "She worked at TechCore Industries in Harbor City."
❌ "The glass towers of Harbor City's financial district gleamed in the morning sun, each building a monument to..."

Historical (Simple):
✅ "Duke Fletcher ruled the northern territory."
❌ "In the grand duchy of Fletcher, where ancient traditions held sway and the hierarchies of nobility..."

Fantasy (Simple):
✅ "She had a healing ability she kept secret."
❌ "The mystical arts of the ancient healers, passed down through generations of..."

**The setting is a BACKDROP, not the story. Keep it minimal.**

**Location naming:**
- ✅ Harbor City, Riverside, Summit District, Lakeside, New York, Los Angeles
- ✅ (For historical) Northern Territory, The Kingdom, The Court
- ❌ Beijing, Shanghai, Guangzhou (don't use Chinese cities directly)

**Organization naming:**
- ✅ StreamWave Entertainment, TechCore Industries, Summit Hospital
- ✅ (For historical) The Royal Court, The Duke's Manor, The Guild
- ❌ Tencent, Alibaba, WeChat, Baidu (don't use Chinese companies)

**Social media references (modern only):**
- ✅ Instagram, Twitter, Facebook, TikTok
- ❌ Weibo, WeChat

**No mixing Chinese and Western elements regardless of setting.**

### Rule 7: Setting/Background Explanation
**Maximum 3 sentences**, then return to action.

Don't explain worldview, system mechanics, power origins. **Show effects directly.**

### Rule 8: Internal Monologue
**Maximum 3 consecutive sentences**, then return to external action.

No long internal thought paragraphs.

### Rule 9: Forbidden Literary Language (ALL SETTINGS)

**These rules apply whether you write modern, historical, or fantasy.**

**Forbidden metaphors (in ANY setting):**
❌ "Her voice was like X"
❌ "Silence fell like a lid"
❌ "His words hung in the air like a blade"
❌ Any comparison using "like" or "as" that sounds poetic
❌ "She worked with hands that trembled and did not"

**Forbidden poetic expressions (in ANY setting):**
❌ "patience wrapped in glass"
❌ "silence lands like a lid"
❌ "like a storm retreating"
❌ "the taste of the air changed"
❌ "looked like a stage set"
❌ Any abstract metaphorical descriptions

**Forbidden philosophical statements (in ANY setting):**
❌ Paragraph-ending life reflections
❌ "X is not Y, it is Z" style wisdom
❌ "for a moment, he understood the meaning of..."
❌ Any contemplative insights about life/humanity

**Forbidden time-wasting descriptions (in ANY setting):**
❌ "Weeks passed. She learned to..." → Skip to next scene
❌ "Days turned to months..." → Jump to action
❌ "The castle/office was magnificent..." → Don't describe buildings
❌ "She wore a dress/suit of..." → Don't describe clothes in detail

**Allowed comparisons (in ANY setting):**
✓ Only use comparisons if they are:
  - Extremely colloquial (how people actually talk)
  - Immediately clear without interpretation
  - Used for emphasis, not beauty
  - Short and punchy

**General principle for ALL settings:**
- Write like you're telling a story to a friend, not writing literature
- Use concrete actions and reactions, not abstract descriptions
- If a sentence sounds "poetic" or "deep," delete it
- Default to simple, direct language
- Action and dialogue > description and reflection

**This applies equally to:**
- Modern office politics
- Medieval court intrigue
- Fantasy realm conflicts
- ANY story you write

### Rule 10: Opening Scene
**First sentence must be action or dialogue.**

Forbidden:
- Environmental description opening
- Background introduction opening
- Internal monologue opening

### Rule 11: Complete Crisp Ending

**Must be complete:**
- All conflicts resolved
- Villains punished
- Protagonist satisfied

**Must be crisp:**
- No dragging
- No repetition
- Say it once and stop

---

## GENRE CLASSIFICATION - 15 Short Fiction Categories

**Choose ONE from these 15:**

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

**Decision method:**
1. Main satisfaction type? → Face-Slapping / Revenge / Sweet Romance
2. Special setting? → Rebirth / System / True/Fake Identity
3. Protagonist type/background? → Billionaire Romance / Entertainment Circle

---

## TITLE CREATION RULES

### Hard Requirement

**Under 80 characters**

### Creation Principles

1. **Colloquial** - sounds like talking, not book titles
2. **Has contrast/reversal/conflict**
3. **Creates curiosity**
4. **Core conflict immediately clear**
5. **Unique** (don't repeat patterns)

### ❌ Forbidden Title Patterns

**Avoid these common opening words:**

```
❌ "I Died..." / "I Woke..." / "I [Verb]..."
❌ "Back to..." / "Back at..."
❌ "They Called..." / "They Said..." / "They [Verb]..."
❌ "Rejected..." / "Rejected by..."
❌ "He..." / "She..." (pronoun openings)
❌ "After..." / "After I..."
❌ "Married..." / "Divorced..." (single verb openings)
❌ "When..." (temporal clause openings)
❌ "The..." (article openings, unless very special)
```

**Try different title structures, don't always use the same pattern.**

**Don't use these patterns:**

```
❌ "The [Someone]'s [Something]"
   Example: "The CEO's Secret Wife"

❌ "When [Something Happened]"
   Example: "When Love Returns"

❌ "A [Noun] of [Noun]"
   Example: "A Tale of Two Hearts"

❌ "[Genre]: [Statement]"
   Example: "Romance: She Found Love"

❌ No emotion or surprise
   Example: "The Story of My Life"

❌ Sounds like book title not speech
   Example: "Chronicles of a Forgotten Soul"

❌ Requires "appreciation" to understand
   Example: "Echoes in the Silence of Dawn"
```

### ❌ Forbidden Title Characteristics

```
❌ Too long (over 80 characters)
❌ Complex clauses
❌ Overly literary
❌ No sense of conflict
❌ Too abstract
❌ Clichéd
❌ Repetitive structures
```

### Creation Reminders

- Title must be unique and attractive
- Try different structures (don't always use same pattern)
- Focus on core conflict and reversal
- Keep colloquial
- Make people want to click
- Avoid listed forbidden patterns

---

## AI COMMON ERRORS - MUST DELETE

After writing, search for these and fix/delete:

### Transition Words
Delete: However, Moreover, Furthermore, Nevertheless, Additionally, Subsequently, Consequently

### Clichés
Delete:
- let out a breath she didn't know she was holding
- heart raced in his/her chest
- blood ran cold
- shiver down spine
- time seemed to slow
- the air grew thick

### Generic Adjectives
Delete: piercing eyes, chiseled jaw, dazzling smile, raven hair

### Emotion Analysis Phrases
Delete:
- couldn't help but feel
- part of him wanted to... while another part
- a complex mixture of emotions
- a wave of [emotion] washed over
- something in him shifted

### Metaphor Phrases (forbidden literary metaphors)
Delete:
- ❌ "Silence fell like a lid"
- ❌ "His words hung in the air like a blade"
- ❌ "She folded it as one folds a map to a destination"
- ❌ "His steps were an argument for a life"

### Philosophical/Literary Phrases
Delete:
- "X and Y at once" (like "simpler and harder at once")
- "felt like a [abstract noun]" (like "felt like a choice")
- "as if [abstract concept]"
- "the sound/weight/taste of [abstract noun]"
- "in a way that [philosophical explanation]"
- "[action] as one [philosophical metaphor]"
- "X is not Y, it is Z" style life wisdom
- "for a moment/for a second [philosophical insight]"

### Meta-Commentary (CRITICAL - DELETE IMMEDIATELY)
Delete ANY labels or descriptions of story structure:
- ❌ "Setup:"
- ❌ "Confrontation:"
- ❌ "Public Reaction:"
- ❌ "Satisfaction scene"
- ❌ "First/Second/Third satisfaction"
- ❌ "Satisfaction scene — [description]"
- ❌ Any phrase that describes what type of scene is happening

### Long Paragraphs
- Setting explanation over 3 sentences → cut to 3 sentences
- Internal monologue over 3 sentences → cut to 3 sentences
- Paragraph over 5 sentences → split

### Repetition
- Same meaning said twice → keep only once
- Ending repeatedly emphasizing same thing → say once only

---

## WRITING PROCESS

### Step 1: Analyze Original Content (CRITICAL - Don't Skip!)

**Read the input file carefully and identify:**

**A. Story Specifics (not generalizations):**
- **Exact setting**: Hospital? Restaurant? Office? School? Stadium? Competition venue?
- **Exact characters**: Who exists? What are their roles? Their relationships?
- **Exact conflicts**: What SPECIFIC problem exists? (not "face-slapping" - the actual conflict)
- **Exact events in progress**: What's happening or about to happen?

**B. Cut-off Point:**
- What was the last complete scene?
- What was being built up to?
- What event/confrontation is coming next?

**C. Story Direction:**
- Medical story → heading towards diagnosis? surgery? medical conference?
- Cooking story → heading towards competition finals? restaurant opening? taste test?
- Business story → heading towards board meeting? product launch? contract signing?
- School story → heading towards exam? presentation? competition?
- Sports story → heading towards championship? tryout? match?

**D. Specific Scenarios to Continue:**
- If original mentions "医学研讨会" (medical conference) → continue with medical conference
- If original mentions "厨艺决赛" (cooking finals) → continue with cooking finals
- If original mentions "公司董事会" (board meeting) → continue with board meeting
- **Continue what was set up, don't replace with different scenarios**

**E. Evidence/Skills Already Established:**
- What abilities does protagonist have? (diagnosis skill? cooking talent? business acumen?)
- What evidence exists? (test results? recipes? financial documents?)
- What will be used in the confrontation?

**Common mistakes to avoid:**
- ❌ Reading "hospital story" and thinking "I'll write a courtroom story"
- ❌ Reading "cooking competition" and thinking "I'll write about business fraud"
- ❌ Seeing specific setup and replacing with generic template
- ❌ Ignoring the actual content and writing your default scenario

**Before moving to Step 2, you should be able to answer:**
- [ ] What exact setting does this continue in? (specific answer, not "modern" or "urban")
- [ ] What exact event comes next? (specific answer, not "confrontation")
- [ ] What exact skills/evidence will be used? (specific answer, not "proves herself")
- [ ] What exact scenario was set up? (specific answer, not "face-slapping")

**If you can't answer these specifically, you haven't analyzed the original carefully enough.**

### Step 2: Plan Continuation (Critical - Based on Original!)

**Mentally (don't output) plan these BEFORE writing:**

**A. Continuation Structure:**
- Opening: Pick up exactly where original left off (don't restart)
- Middle: Complete the events that were set up in original
- Climax: The confrontation/event that was being built towards
- Resolution: Resolve the conflicts that were introduced

**B. Specific Scenarios to Write:**

**Based on what original set up:**
- If medical conference was mentioned → Plan the medical conference scene
- If cooking competition finals were set up → Plan the cooking finals
- If board meeting was coming → Plan the board meeting
- If academic presentation was scheduled → Plan that presentation
- **Don't replace these with different scenarios!**

**For each scenario, plan:**
- Location: Same type as original (hospital stays hospital, kitchen stays kitchen)
- Characters present: Who was involved in original?
- Conflict type: Same as original (medical doubt? cooking criticism? business rivalry?)
- Evidence/skill used: What was established in original?

**C. Satisfaction Moments (6-10 total):**

**Continue the pattern from original:**
- If original had medical diagnosis moments → More diagnosis wins
- If original had cooking victories → More cooking triumphs
- If original had business wins → More business successes

**For each satisfaction moment, plan:**
- Which scenario from original it happens in
- What specific skill/evidence from original is used
- Who from original cast witnesses it
- What specific reaction fits the setting

**Example:**
```
Original set up: Medical diagnosis + conference + doubting chief

Plan satisfaction moments:
1. Successfully diagnoses rare disease (hospital scene)
2. Presents findings at conference (medical conference)
3. Chief physician acknowledges error (conference aftermath)
4. Other doctors request her consultation (hospital follow-up)

DON'T plan:
❌ Charity gala confrontation (not in original)
❌ Courtroom testimony (not in original)
❌ Business fraud reveal (not in original)
```

**D. Character Arcs (continue from original):**
- Protagonist: Continue their journey in the SAME field
- Antagonist: Same person from original, same conflict type
- Supporting characters: Same roles as original

**E. Pacing Checkpoints:**
Based on original setup:
- 3,000 chars: First satisfaction in original's context
- 8,000 chars: Second satisfaction in original's setting
- 15,000 chars: Major event that was set up in original
- 25,000 chars: Climax of original's main conflict
- 35,000 chars: Resolution

**CRITICAL QUESTIONS before writing:**
- [ ] Am I continuing the SAME plot or creating new one?
- [ ] Am I using the SAME setting or changing it?
- [ ] Am I completing events SET UP in original or inventing new ones?
- [ ] Are my scenarios based on ORIGINAL or my defaults?

**If you're planning charity galas, courtrooms, or business meetings but original didn't set those up - YOU'RE DOING IT WRONG.**

**Don't start writing until:**
- You can list 3 specific scenarios FROM the original to continue
- You can name the specific event original was building towards
- You know what specific setting/location continues
- You've planned satisfaction moments IN THAT SAME CONTEXT

### Step 3: Create Metadata
- Title (under 80 chars, unique)
- Genre (choose 1 from 15)
- Age (choose 1 from 4 levels)

### Step 4: Write Continuation

**Start:**
- First sentence: Continue from where original left off
- No restart, jump straight to next scene in original's sequence
- Keep the momentum going

**While writing:**

**CRITICAL - Stay in original's context:**
- If original is in hospital → Keep writing hospital scenes
- If original is in restaurant → Keep writing restaurant scenes
- If original is in office → Keep writing office scenes
- If original has competition → Continue that competition
- **Don't switch to charity galas, courtrooms, or boardrooms if original didn't have them!**

**Every 3,000 characters, STOP and check:**
- [ ] Am I still in the SAME setting as original? (hospital/restaurant/office/school)
- [ ] Am I continuing ORIGINAL plot or did I switch to generic template?
- [ ] Are my scenarios based on what ORIGINAL set up?
- [ ] Did I just write a satisfaction scene IN THE ORIGINAL's CONTEXT?
- [ ] Was it a full scene with dialogue (300+ chars)?
- [ ] Did I show antagonist's reaction?
- [ ] Were there witnesses appropriate to THIS setting?
- [ ] Did I write it WITHOUT any labels like "Setup:" or "Satisfaction scene"?
- [ ] If NO to any: Fix immediately before continuing

**Example self-check:**
```
Original: Medical diagnosis story in hospital
My writing at 5,000 chars: Still writing medical scenes? ✅ or Switched to courtroom? ❌

Original: Cooking competition story
My writing at 10,000 chars: Still writing cooking scenes? ✅ or Switched to charity gala? ❌

Original: Business contract negotiation
My writing at 15,000 chars: Still writing business meetings? ✅ or Added unrelated lawsuit? ❌
```

**Dialogue priority (40%+ minimum):**
- Count dialogue lines every 1,000 characters
- If below 40%, stop and add dialogue
- Turn narration into dialogue exchanges
- Use dialogue to reveal information, not description

**Paragraph control:**
- After every paragraph, count sentences
- If over 5 sentences: split immediately
- Important moments: single sentence paragraphs

**Setting/background:**
- Already established in original - don't re-explain
- Maximum 3 sentences for any new location
- Immediately return to action/dialogue after

**Internal monologue:**
- Maximum 3 consecutive sentences
- Then cut to external action/dialogue

**Write continuously:**
- Don't stop to edit yet
- Focus on hitting satisfaction moments in ORIGINAL's scenarios
- Maintain fast pace
- Keep dialogue flowing
- NEVER output labels like "Setup:" or "Satisfaction scene"
- Stay true to original plot direction

**WARNING SIGNS you've gone off track:**
- ❌ Writing charity gala when original had none
- ❌ Writing courtroom when original was about hospital/restaurant/school
- ❌ Writing business fraud when original was about competition/family/relationships
- ❌ Characters suddenly in different careers than original
- ❌ Completely different setting than original

**If you catch yourself doing any of above - STOP and return to original plot!**

**Length guidance:**
- Target: 25,000-35,000 characters
- Minimum: 20,000 characters (check at end)
- If under 20K at finish: Add more satisfaction scenes IN THE SAME CONTEXT
- Quality of satisfaction > total length, but don't go under 20K

### Step 5: Check and Fix

**⚠️⚠️⚠️ META-COMMENTARY CHECK (DO THIS FIRST - CRITICAL)**

**Scan entire story for these FORBIDDEN phrases:**
- [ ] "Setup:"
- [ ] "Confrontation:"
- [ ] "Public Reaction:"
- [ ] "Satisfaction scene"
- [ ] "First satisfaction" / "Second satisfaction"
- [ ] "First/Second/Third [anything]" used as scene labels
- [ ] Any colons (:) followed by scene descriptions
- [ ] Any phrase that describes what type of scene is happening

**If you find ANY of these:**
- DELETE the label immediately
- Rewrite the paragraph to jump straight into the scene
- Check surrounding text for more labels
- Make sure no structural commentary remains

**Example fixes:**
❌ "Satisfaction scene — public ripple: the kiss went viral"
✅ "The kiss went viral within an hour."

❌ "First satisfaction came when she confronted him."
✅ "She confronted him in the boardroom."

❌ "Setup: Reed arrived at the office."
✅ "Reed arrived at the office."

---

**□ Satisfaction Check** (MOST IMPORTANT - Check Second)

**Count all satisfaction moments:**
- List each one by character position
- Verify distribution: one every 3,000-5,000 chars?
- Total count: at least 6-10?

**For EACH satisfaction moment, verify:**
- [ ] Written as full scene (not summary)?
- [ ] Has dialogue (60%+ in that scene)?
- [ ] Shows antagonist's specific reaction?
- [ ] Has witnesses/public element?
- [ ] At least 300 characters long?
- [ ] Would readers feel "YES!" reading it?
- [ ] NO labels or meta-commentary?

**If any satisfaction moment fails these checks:**
- Locate it in the text
- Expand it with dialogue
- Add specific reactions
- Add witness responses
- Make it at least 300 characters
- Remove any labels

**Common satisfaction problems to fix:**
- "He was shocked" → Write what he said, how he looked, what he did
- "Everyone was surprised" → Write specific gasps, whispers, comments
- "It was satisfying" → Delete this, show the scene instead
- Scene under 200 chars → Expand with dialogue and reactions

---

**□ Length Check**
- Count total characters in story
- Is it at least 20,000 characters?
- If under 20,000: Add more satisfaction scenes or expand existing ones
- If under 18,000: CRITICAL - story too short, add significant content

---

**□ Dialogue Density**
- Rough count: dialogue lines vs total lines
- Should be 40%+ of the story
- If under 40%: convert narration to dialogue

---

**□ Paragraph Length**
- Scan for paragraphs over 5 sentences
- Split them immediately
- No exceptions

---

**□ Literary Language Check**
Search and delete/fix:
- "However," / "Moreover," / "Furthermore,"
- "couldn't help but"
- "a wave of [emotion]"
- "at once"
- "felt like a [abstract noun]"
- "as if [abstract concept]"
- Any sentence that sounds poetic

---

**□ Opening**
- First sentence is action or dialogue?
- No environment description?
- No background explanation?

---

**□ Ending**
- All conflicts resolved?
- Antagonists punished/humbled?
- Protagonist gets satisfaction?
- Crisp ending (not dragging)?
- Has `---END---` marker?

---

**□ Character Names**
- Search for: Chen, Wang, Liu, Zhang, Li, Zhao, Zhou
- If found: change to English surnames immediately

---

**□ Localization**
- Search for: WeChat, Weibo, Beijing, Shanghai
- If found: change to Instagram/Twitter or Harbor City/New York

---

## OUTPUT FORMAT - STRICT COMPLIANCE

```
===TITLE===
[English title, under 80 characters, unique]

===GENRE===
[Choose 1 from 15 genres]

===AGE===
[All Ages OR Teen 13+ OR Mature 16+ OR Explicit 18+]

===STORY===
[Complete story text, pure English, no titles or chapter numbers, NO LABELS OR META-COMMENTARY]

---END---
```

**Forbidden to output:**
- ❌ Outline
- ❌ Character list
- ❌ World setting
- ❌ "Chapter X"
- ❌ Author notes
- ❌ Word count statistics
- ❌ Any explanatory text
- ❌ Any Chinese characters
- ❌ Any labels like "Setup:", "Satisfaction scene", etc.

**Only output:**
- ✅ TITLE
- ✅ GENRE
- ✅ AGE
- ✅ Story text (direct narration only, no structural labels)
- ✅ ---END---

---

## FINAL REMINDERS BEFORE YOU START

**The FIVE Non-Negotiables:**

1. **FOLLOW ORIGINAL PLOT** (NEW - MOST CRITICAL)
   - Continue the SAME story, don't create new one
   - Use the SAME setting (hospital stays hospital, restaurant stays restaurant)
   - Complete the SPECIFIC events original set up
   - Don't replace with your default templates (charity gala, courtroom, board meeting)
   - If original didn't mention it, don't add it

2. **SATISFACTION DENSITY**
   - Every 3,000-5,000 characters = 1 full satisfaction scene
   - Each scene = 300+ characters with dialogue
   - Show reactions, witnesses, consequences
   - Never summarize satisfaction
   - BUT: Satisfaction must be IN THE CONTEXT of original story!

3. **DIALOGUE DOMINANCE**
   - 40%+ of story must be dialogue
   - Check every 3,000 characters
   - Convert narration to dialogue exchanges
   - Satisfaction scenes must be 60%+ dialogue

4. **NO LITERARY LANGUAGE**
   - No poetic metaphors
   - No philosophical insights
   - No abstract descriptions
   - Write like you're telling a friend, not writing literature

5. **⚠️⚠️⚠️ NO META-COMMENTARY OR LABELS (ABSOLUTE CRITICAL)**
   - Never output: "Setup:", "Confrontation:", "First satisfaction"
   - Never output: "Satisfaction scene —" or any scene type descriptions
   - Never number satisfaction moments for readers
   - Never explain story structure to readers
   - Just write what happens directly
   - **VIOLATION = STORY REJECTED**

**Forbidden Output Examples:**

❌ "First satisfaction came when..."
❌ "Setup: The protagonist arrived..."
❌ "Confrontation: She said..."
❌ "Satisfaction scene — public ripple: the kiss went viral..."
❌ "Satisfaction scene — small power display: on a noisy set..."
❌ "The second爽点 occurred..."
❌ "Satisfaction seventh and final..."

**Correct Output:**

✅ "That afternoon, she arrived at the office..."
✅ "The kiss went viral within an hour."
✅ "On a noisy set, she intervened..."
✅ Direct scene with dialogue and action
✅ No labels, no numbering, no meta-commentary

**CRITICAL: Plot Fidelity Check**

Before you write ANYTHING, answer these:
- [ ] What exact setting does the original have? (Write specific answer)
- [ ] What exact event is coming next in original? (Write specific answer)
- [ ] What scenarios did original set up? (List them)
- [ ] Am I continuing THOSE scenarios or replacing with my defaults?

**If you're planning to write:**
- Charity gala → Was there one in original? If NO, don't write it!
- Courtroom trial → Was there legal plot in original? If NO, don't write it!
- Business fraud → Was original about business? If NO, don't write it!
- Board meeting → Was original in corporate setting? If NO, don't write it!

**Common Default Templates to AVOID unless original has them:**
- ❌ Charity gala scandal
- ❌ Courtroom testimony
- ❌ Corporate fraud reveal
- ❌ Board meeting showdown
- ❌ Contract dispute
- ❌ Media press conference

**Length Requirements:**
- Minimum: 20,000 characters (HARD REQUIREMENT)
- Optimal: 25,000-35,000 characters
- Don't pad, add more satisfaction scenes IF they fit original context
- But DON'T go under 20,000

**Quality Over Everything (but stay true to original):**
- Better to have 25,000 characters with great satisfaction IN ORIGINAL CONTEXT
- Than 40,000 characters with generic scenarios NOT from original
- Every scene must either build to or deliver satisfaction
- But maintain minimum 20,000 character requirement
- Stay faithful to original plot direction

**Remember:**
- You're CONTINUING a story, not creating new one
- You're LOCALIZING names/places, not changing plot
- You're COMPLETING what was started, not replacing it
- Readers want to see THAT story finished, not a different story
- Specific original plot > vague generic plot
- Action and dialogue > description and reflection
- Write the story continuation, not commentary about it
- NO LABELS OR META-COMMENTARY EVER

---

**Now, start creating. Read the input txt file carefully, understand its SPECIFIC plot and setting, and continue THAT story with English localization.**

**START WRITING THE CONTINUATION.**"""


class DirectPromptManager:
    """直接生成Prompt管理器"""

    def __init__(self):
        self.prompts_file = get_resource_path('data/shortnovel_direct_prompts.json')
        self.prompts = self.load_prompts()

    def load_prompts(self):
        """加载Prompt配置"""
        prompts = {
            'direct': {
                'default': DEFAULT_DIRECT_PROMPT,
                'versions': {},
                'active': 'default'
            }
        }

        try:
            if os.path.exists(self.prompts_file):
                with open(self.prompts_file, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    # 保留用户的自定义版本和活跃版本设置，但始终使用代码中的默认prompt
                    if 'direct' in saved:
                        if 'versions' in saved['direct']:
                            prompts['direct']['versions'] = saved['direct']['versions']
                        if 'active' in saved['direct']:
                            prompts['direct']['active'] = saved['direct']['active']
        except Exception as e:
            print(f"加载Prompt配置失败: {e}")

        return prompts

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

        # 批次管理
        self.current_batch_folder = None  # 当前批次输出文件夹
        self.current_source_folder = None  # 原文件夹路径
        self.batch_task_count = 0  # 批次任务数量

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

        # 第三行：输出路径（固定）
        row3 = tk.Frame(control_frame)
        row3.pack(fill=tk.X, pady=2)

        tk.Label(row3, text="输出路径:").pack(side=tk.LEFT)
        self.fixed_output_path = "D:/shortnovels_translation_readytoupload"
        tk.Label(row3, text=self.fixed_output_path, fg="#2196F3", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)

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
                    'output_path': self.fixed_output_path
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

        tk.Button(btn_frame, text="▶开始", command=lambda t=task: self.start_task(t),
                 width=5, font=("Arial", 8), bg="#4CAF50", fg="white",
                 state=tk.NORMAL if task.status != 'running' else tk.DISABLED).place(x=4, y=3)

        tk.Button(btn_frame, text="🗑删除", command=lambda t=task: self.remove_task(t),
                 width=5, font=("Arial", 8), bg="#f44336", fg="white").place(x=60, y=3)

        tk.Button(btn_frame, text="📋预览", command=lambda t=task: self.preview_prompt(t),
                 width=5, font=("Arial", 8), bg="#2196F3", fg="white").place(x=116, y=3)

        # 打开文件夹按钮 - 只在任务完成后可用
        can_open = task.status in ('completed', 'incomplete') and hasattr(task, 'output_folder') and task.output_folder
        tk.Button(btn_frame, text="📂打开", command=lambda t=task: self.open_task_folder(t),
                 width=5, font=("Arial", 8), bg="#9C27B0", fg="white",
                 state=tk.NORMAL if can_open else tk.DISABLED).place(x=172, y=3)

        self.task_frames[task.task_id] = card

    def open_task_folder(self, task):
        """打开任务输出文件夹"""
        if hasattr(task, 'output_folder') and task.output_folder:
            if os.path.exists(task.output_folder):
                open_folder_in_explorer(task.output_folder)
            else:
                messagebox.showwarning("警告", f"文件夹不存在:\n{task.output_folder}")
        else:
            messagebox.showinfo("提示", "任务尚未完成，无输出文件夹")

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

            # 使用安全格式化，忽略未知占位符
            system_prompt = safe_format_prompt(
                prompt_template,
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

            # 创建输出文件夹 - 优先使用批次文件夹
            if hasattr(task, 'batch_folder') and task.batch_folder and os.path.isdir(task.batch_folder):
                output_folder = os.path.join(task.batch_folder, folder_name)
            else:
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

            # 复制源文件到输出文件夹
            source_filename = os.path.basename(task.source_file)
            shutil.copy2(task.source_file, os.path.join(output_folder, source_filename))
            print(f"[DEBUG] 步骤13完成: 文件保存成功，源文件已复制")

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
        # 检查是否所有任务都完成
        self.window.after(100, self._check_batch_completion)

    def _check_batch_completion(self):
        """检查批次是否全部完成，如果完成则重命名文件夹加 _done"""
        # 检查是否有批次文件夹
        if not self.current_batch_folder:
            return

        # 检查所有任务状态
        running_tasks = [t for t in self.tasks if t.status == 'running']
        if running_tasks:
            return  # 还有任务在运行

        # 所有任务都完成了（completed, incomplete, 或 failed）
        completed_count = len([t for t in self.tasks if t.status in ('completed', 'incomplete', 'failed')])
        if completed_count < self.batch_task_count:
            return  # 还没有全部完成

        print(f"[DEBUG] 批次全部完成! 开始重命名文件夹...")

        # 重命名输出批次文件夹，加 _done
        if self.current_batch_folder and os.path.exists(self.current_batch_folder):
            if not self.current_batch_folder.endswith('_done'):
                new_batch_folder = self.current_batch_folder + '_done'
                try:
                    os.rename(self.current_batch_folder, new_batch_folder)
                    print(f"[DEBUG] 输出文件夹重命名: {self.current_batch_folder} -> {new_batch_folder}")
                    # 更新所有任务的 output_folder 路径
                    for task in self.tasks:
                        if hasattr(task, 'output_folder') and task.output_folder:
                            task.output_folder = task.output_folder.replace(self.current_batch_folder, new_batch_folder)
                    self.current_batch_folder = new_batch_folder
                except Exception as e:
                    print(f"[ERROR] 重命名输出文件夹失败: {e}")

        # 重命名原文件夹，加 _done
        if self.current_source_folder and os.path.exists(self.current_source_folder):
            if not self.current_source_folder.endswith('_done'):
                new_source_folder = self.current_source_folder + '_done'
                try:
                    os.rename(self.current_source_folder, new_source_folder)
                    print(f"[DEBUG] 原文件夹重命名: {self.current_source_folder} -> {new_source_folder}")
                    self.current_source_folder = new_source_folder
                except Exception as e:
                    print(f"[ERROR] 重命名原文件夹失败: {e}")

        # 刷新显示
        self.refresh_display()

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

            # 构建Prompt - 使用安全格式化，忽略未知占位符
            prompt_template = self.prompt_mgr.get_prompt()
            full_prompt = safe_format_prompt(
                prompt_template,
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

        # 创建批次文件夹: 202512171540-100shortnovels
        batch_time = datetime.now().strftime("%Y%m%d%H%M")
        batch_count = len(pending_tasks)
        batch_folder_name = f"{batch_time}-{batch_count}shortnovels"
        self.current_batch_folder = os.path.join(self.fixed_output_path, batch_folder_name)
        os.makedirs(self.current_batch_folder, exist_ok=True)
        self.batch_task_count = batch_count
        print(f"[DEBUG] 创建批次文件夹: {self.current_batch_folder}")

        # 记录原文件夹（取第一个任务的源文件夹）
        if pending_tasks:
            self.current_source_folder = os.path.dirname(pending_tasks[0].source_file)
            print(f"[DEBUG] 原文件夹: {self.current_source_folder}")

        for task in pending_tasks:
            task.status = 'running'
            task.started_at = datetime.now()
            # 将批次文件夹路径传给任务
            task.batch_folder = self.current_batch_folder
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
