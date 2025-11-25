# Windows 打包完整指南 - 解决 Prompts 不更新问题

## 🎯 问题原因

1. **prompts.json 被缓存在 Windows AppData 目录**
2. **打包时没有包含最新的 prompts.json**
3. **Python 缓存文件干扰**

---

## 📋 完整解决步骤

### 第 1 步：清理 Windows 应用缓存 ⚠️ **必须做！**

#### 方法 A：使用批处理脚本（推荐）
```cmd
cd C:\path\to\translation_workflow
clean_windows_cache.bat
```

#### 方法 B：使用 Python 脚本
```cmd
cd C:\path\to\translation_workflow
python clean_cache.py
```

#### 方法 C：手动删除
```cmd
# 打开文件资源管理器，输入：
%APPDATA%\OutlineGenerator

# 或在命令行：
rmdir /s /q "%APPDATA%\OutlineGenerator"
```

---

### 第 2 步：清理 Python 编译缓存

```cmd
# 在项目根目录运行：
rmdir /s /q __pycache__
rmdir /s /q build
rmdir /s /q dist
del /s /q *.pyc
del /s /q *.spec
```

---

### 第 3 步：验证 prompts.json

```cmd
# 检查 prompts.json 是否包含 18 个类别
python -c "import json; data = json.load(open('data/prompts.json', encoding='utf-8')); print('✅ Found 18 genres' if 'Werewolf' in data['outline']['default'] and 'Vampire' in data['outline']['default'] else '❌ Missing new genres')"
```

如果显示 "❌ Missing new genres"，运行：
```cmd
python regenerate_prompts.py
```

---

### 第 4 步：重新打包（使用 --clean）

```cmd
# 完全清理打包
python build_package.py

# 或者如果失败，手动运行：
pyinstaller --clean ^
    --name="OutlineGenerator" ^
    --windowed ^
    --add-data="data/prompts.json;data" ^
    --add-data="data/styles.json;data" ^
    --add-data="data/names_1.json;data" ^
    outline_generator.py
```

---

### 第 5 步：验证打包结果

```cmd
# 检查打包后的文件是否包含 prompts.json
dir dist\OutlineGenerator\_internal\data\prompts.json
```

应该看到文件存在，且大小约 86KB。

---

### 第 6 步：测试新应用

1. **删除旧的 .exe**
2. **运行新的 `dist/OutlineGenerator/OutlineGenerator.exe`**
3. **打开 Prompt 管理界面**
4. **验证看到 18 个类别**：
   - Fantasy, Urban, Romance, Sci-Fi, Mystery, Historical, Adventure, Horror, Crime, LGBTQ+, **Paranormal**, **Werewolf** 🆕, **Vampire** 🆕, System, Reborn, Revenge, Fanfiction, Humor

---

## 🔧 常见问题排查

### 问题 1：打包后 prompts.json 不存在

**原因**：`build_package.py` 的 `data_files` 列表没有包含 `prompts.json`

**解决**：检查 `build_package.py` 的第 105-109 行：
```python
data_files = [
    ('data/prompts.json', 'data'),  # ← 必须有这一行！
    ('data/styles.json', 'data'),
    ('data/names_1.json', 'data'),
]
```

### 问题 2：打包时报错 "file not found"

**原因**：`data/prompts.json` 不存在

**解决**：
```cmd
python regenerate_prompts.py
```

### 问题 3：应用显示旧的 prompts

**原因**：Windows AppData 缓存

**解决**：
```cmd
# 删除缓存并重启应用
rmdir /s /q "%APPDATA%\OutlineGenerator"
```

### 问题 4：打包很慢或失败

**原因**：`names_1.json` 太大（12MB）

**说明**：这是正常的，因为包含 10 万个名字。打包时间约 2-5 分钟。

---

## ✅ 验证清单

打包完成后，确认以下内容：

- [ ] `dist/OutlineGenerator/_internal/data/prompts.json` 存在（约 86KB）
- [ ] `dist/OutlineGenerator/_internal/data/names_1.json` 存在（约 12MB）
- [ ] 删除了 `%APPDATA%\OutlineGenerator` 目录
- [ ] 运行新应用，看到 18 个类别
- [ ] Prompt 中包含 "从18个类型中选一个"
- [ ] 看到 Werewolf 和 Vampire 类别

---

## 📝 完整命令清单（复制粘贴执行）

```cmd
REM 1. 清理缓存
rmdir /s /q "%APPDATA%\OutlineGenerator"
rmdir /s /q __pycache__
rmdir /s /q build
rmdir /s /q dist
del /s /q *.pyc
del /s /q *.spec

REM 2. 验证 prompts.json
python regenerate_prompts.py

REM 3. 重新打包
python build_package.py

REM 4. 验证打包结果
dir dist\OutlineGenerator\_internal\data\prompts.json

REM 5. 运行新应用
dist\OutlineGenerator\OutlineGenerator.exe
```

---

## 🎉 成功标志

打开应用后，在 Prompt 管理界面应该看到：

```
【18种Genre分类说明】

你必须从以下18种类型中选择一个最合适的：

1. Fantasy（奇幻）
2. Urban（都市）
...
12. Werewolf（狼人）← 新增！
13. Vampire（吸血鬼）← 新增！
...
18. Humor（幽默）

===== CATEGORY =====
[从18个类型中选一个主类型：Fantasy/Urban/.../Werewolf/Vampire/.../Humor]
```

如果看到这个，说明打包成功！🎊
