"""
这是给outline_generator.py添加预览功能的补丁代码
将以下代码添加到OutlineGenerator类中
"""

# 在类的import部分添加：
from prompt_preview import PromptPreviewWindow

# 在generate_outline方法之前添加以下方法：

def preview_prompt(self):
    """预览Prompt（不发送到AI）"""
    # 验证输入
    if not self.source_file:
        messagebox.showwarning("警告", "请先选择原文文件")
        return

    start_ch = self.start_chapter_var.get()
    end_ch = self.end_chapter_var.get()

    if start_ch > end_ch:
        messagebox.showwarning("警告", "起始章节不能大于结束章节")
        return

    try:
        # 读取文件（只读取前10000字符用于预览）
        with open(self.source_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if len(content) > 10000:
                content_preview = content[:10000] + "\n\n... (内容过长，仅显示前10000字符) ..."
            else:
                content_preview = content

        # 选择人名
        male_count = self.male_count_var.get()
        female_count = self.female_count_var.get()
        selected_names = self.resource_mgr.select_names(male_count, female_count)
        names_formatted = self.resource_mgr.format_names_for_prompt(selected_names)

        # 选择风格
        genre_data = self.resource_mgr.styles[self.detected_genre]
        counts = genre_data['used']
        min_idx = counts.index(min(counts))
        style = genre_data['styles'][min_idx]
        author = genre_data['authors'][min_idx]

        # 构建Prompt变量
        total_chapters = end_ch - start_ch + 1
        prompt_vars = {
            'genre': self.detected_genre,
            'male_names': names_formatted['male_names'],
            'female_names': names_formatted['female_names'],
            'style': style,
            'start_chapter': start_ch,
            'end_chapter': end_ch,
            'total_chapters': total_chapters
        }

        # 渲染Prompt
        system_prompt = self.prompt_mgr.render_outline_prompt(prompt_vars)

        # 构建完整的Prompt预览
        full_prompt = f"""{'='*70}
系统Prompt (System Message)
{'='*70}

{system_prompt}

{'='*70}
用户消息 (User Message)
{'='*70}

原文内容：

{content_preview}

{'='*70}
元数据 (Metadata)
{'='*70}

文件: {os.path.basename(self.source_file)}
类型: {self.detected_genre}
作者风格: {author}
章节范围: {start_ch}-{end_ch} (共{total_chapters}章)

选择的人名 (将会被标记为已使用):
男性 ({male_count}个): {names_formatted['male_names']}
女性 ({female_count}个): {names_formatted['female_names']}

⚠️ 注意: 预览时已经选择了人名并更新了used计数，以确保多任务并发时不会重复。
"""

        # 显示预览窗口
        PromptPreviewWindow(self.window, full_prompt, "大纲生成 - Prompt 预览")

    except Exception as e:
        messagebox.showerror("错误", f"预览失败: {str(e)}")
