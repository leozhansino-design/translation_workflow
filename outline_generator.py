"""
Tool 1: 大纲生成器
从原文小说生成结构化英文大纲
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
import threading
import json
import os
from datetime import datetime
from openai import OpenAI

from config import config
from resource_mgr import ResourceManager
from prompt_manager import PromptManager
from utils import (
    extract_genre_from_filename,
    extract_title_from_filename,
    validate_genre,
    parse_json_from_llm_response
)


class OutlineGenerator:
    """大纲生成器主窗口"""

    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Tool 1: 大纲生成器")
        self.window.geometry("1000x850")

        # 初始化管理器
        self.resource_mgr = ResourceManager()
        self.prompt_mgr = PromptManager()
        self.client = None

        # 数据
        self.source_file = None
        self.detected_genre = None
        self.outline_data = None

        # 初始化界面
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        """设置界面"""
        # === 标题栏 ===
        title_frame = tk.Frame(self.window, bg="#2196F3", height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        tk.Label(
            title_frame,
            text="📝 大纲生成器",
            font=("Arial", 20, "bold"),
            bg="#2196F3",
            fg="white"
        ).pack(side=tk.LEFT, padx=20, pady=10)

        tk.Label(
            title_frame,
            text="第一步：从原文生成结构化大纲",
            font=("Arial", 11),
            bg="#2196F3",
            fg="white"
        ).pack(side=tk.LEFT, padx=10)

        # === API配置区域 ===
        api_frame = tk.LabelFrame(self.window, text="API 配置", padx=15, pady=10)
        api_frame.pack(fill=tk.X, padx=10, pady=10)

        # API Key
        tk.Label(api_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.api_key_var = tk.StringVar()
        tk.Entry(
            api_frame,
            textvariable=self.api_key_var,
            show="*",
            width=45
        ).grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)

        tk.Button(
            api_frame,
            text="测试连接",
            command=self.test_connection,
            width=10
        ).grid(row=0, column=2, pady=5, padx=5)

        self.connection_status = tk.Label(api_frame, text="", fg="gray")
        self.connection_status.grid(row=0, column=3, pady=5, padx=5)

        # Base URL
        tk.Label(api_frame, text="Base URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.base_url_var = tk.StringVar(value="https://yunwuapi.com/v1/")
        tk.Entry(
            api_frame,
            textvariable=self.base_url_var,
            width=45
        ).grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)

        # 模型选择
        tk.Label(api_frame, text="模型:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.model_var = tk.StringVar(value="gpt-4-turbo-preview")
        models = ["gemini-2.5-pro", "gpt-5.1", "gpt-5", "gemini-3-pro-preview", "gpt-4-turbo-preview"]
        ttk.Combobox(
            api_frame,
            textvariable=self.model_var,
            values=models,
            width=42,
            state="readonly"
        ).grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)

        # Temperature 和 Max Tokens
        tk.Label(api_frame, text="Temperature:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.temperature_var = tk.DoubleVar(value=0.8)
        tk.Scale(
            api_frame,
            from_=0,
            to=1,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=self.temperature_var,
            length=200
        ).grid(row=3, column=1, sticky=tk.W, pady=5, padx=5)

        tk.Label(api_frame, text="Max Tokens:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.max_tokens_var = tk.IntVar(value=8000)
        tk.Spinbox(
            api_frame,
            from_=1000,
            to=50000,
            increment=1000,
            textvariable=self.max_tokens_var,
            width=15
        ).grid(row=4, column=1, sticky=tk.W, pady=5, padx=5)

        # === 文件选择区域 ===
        file_frame = tk.LabelFrame(self.window, text="原文文件", padx=15, pady=10)
        file_frame.pack(fill=tk.X, padx=10, pady=10)

        self.file_label = tk.Label(
            file_frame,
            text="未选择文件（格式：书名_类型.txt）",
            fg="gray",
            font=("Arial", 10)
        )
        self.file_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(
            file_frame,
            text="选择文件",
            command=self.select_file,
            width=12
        ).pack(side=tk.RIGHT, padx=5)

        # 类型显示
        self.genre_label = tk.Label(file_frame, text="", fg="blue", font=("Arial", 10, "bold"))
        self.genre_label.pack(side=tk.RIGHT, padx=10)

        # === 参数配置区域 ===
        params_frame = tk.LabelFrame(self.window, text="生成参数", padx=15, pady=10)
        params_frame.pack(fill=tk.X, padx=10, pady=10)

        # 章节范围
        tk.Label(params_frame, text="章节范围:").grid(row=0, column=0, sticky=tk.W, pady=5)
        range_frame = tk.Frame(params_frame)
        range_frame.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)

        tk.Label(range_frame, text="第").pack(side=tk.LEFT)
        self.start_chapter_var = tk.IntVar(value=1)
        tk.Spinbox(
            range_frame,
            from_=1,
            to=500,
            textvariable=self.start_chapter_var,
            width=8
        ).pack(side=tk.LEFT, padx=5)

        tk.Label(range_frame, text="章 至 第").pack(side=tk.LEFT)
        self.end_chapter_var = tk.IntVar(value=100)
        tk.Spinbox(
            range_frame,
            from_=1,
            to=500,
            textvariable=self.end_chapter_var,
            width=8
        ).pack(side=tk.LEFT, padx=5)
        tk.Label(range_frame, text="章").pack(side=tk.LEFT)

        # 人名设置
        tk.Label(params_frame, text="男性人名数:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.male_count_var = tk.IntVar(value=10)
        tk.Spinbox(
            params_frame,
            from_=5,
            to=30,
            textvariable=self.male_count_var,
            width=10
        ).grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)

        tk.Label(params_frame, text="女性人名数:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.female_count_var = tk.IntVar(value=10)
        tk.Spinbox(
            params_frame,
            from_=5,
            to=30,
            textvariable=self.female_count_var,
            width=10
        ).grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)

        # Prompt管理按钮
        tk.Button(
            params_frame,
            text="📋 Prompt 管理",
            command=self.open_prompt_manager,
            bg="#FF9800",
            fg="white",
            width=15
        ).grid(row=3, column=0, columnspan=2, pady=10)

        # === 生成按钮 ===
        self.generate_button = tk.Button(
            self.window,
            text="🚀 生成大纲",
            command=self.generate_outline,
            font=("Arial", 14, "bold"),
            bg="#4CAF50",
            fg="white",
            height=2
        )
        self.generate_button.pack(fill=tk.X, padx=10, pady=10)

        # === 结果显示区域 ===
        result_frame = tk.LabelFrame(self.window, text="生成结果", padx=10, pady=10)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.result_text = scrolledtext.ScrolledText(
            result_frame,
            height=15,
            state=tk.DISABLED,
            wrap=tk.WORD,
            font=("Courier", 9)
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)

        # === 底部按钮 ===
        bottom_frame = tk.Frame(self.window)
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)

        self.save_button = tk.Button(
            bottom_frame,
            text="💾 保存大纲",
            command=self.save_outline,
            state=tk.DISABLED,
            width=15
        )
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.open_tool2_button = tk.Button(
            bottom_frame,
            text="➡️ 进入写作工具",
            command=self.open_tool2,
            state=tk.DISABLED,
            bg="#2196F3",
            fg="white",
            width=15
        )
        self.open_tool2_button.pack(side=tk.RIGHT, padx=5)

    def load_config(self):
        """加载配置"""
        api_key = config.get_api_key()
        if api_key:
            self.api_key_var.set(api_key)

    def save_config(self):
        """保存配置"""
        config.set_api_key(self.api_key_var.get())
        config.set('base_url', self.base_url_var.get())
        config.set('model', self.model_var.get())
        config.set('temperature', self.temperature_var.get())
        config.set('max_tokens', self.max_tokens_var.get())

    def test_connection(self):
        """测试API连接"""
        self.save_config()

        def test():
            self.connection_status.config(text="测试中...", fg="orange")
            try:
                client = OpenAI(
                    api_key=self.api_key_var.get(),
                    base_url=self.base_url_var.get()
                )
                response = client.chat.completions.create(
                    model=self.model_var.get(),
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=10
                )
                self.window.after(0, lambda: self.connection_status.config(
                    text="✅ 连接成功", fg="green"
                ))
            except Exception as e:
                error_msg = str(e)[:30]
                self.window.after(0, lambda: self.connection_status.config(
                    text=f"❌ {error_msg}", fg="red"
                ))

        threading.Thread(target=test, daemon=True).start()

    def select_file(self):
        """选择源文件"""
        file_path = filedialog.askopenfilename(
            title="选择原文文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if file_path:
            try:
                # 提取类型
                genre = extract_genre_from_filename(file_path)
                title = extract_title_from_filename(file_path)

                # 验证类型
                available_genres = self.resource_mgr.get_available_genres()
                validate_genre(genre, available_genres)

                # 保存数据
                self.source_file = file_path
                self.detected_genre = genre

                # 计算字数
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    char_count = len(content)

                # 更新界面
                self.file_label.config(
                    text=f"{os.path.basename(file_path)} ({char_count:,} 字符)",
                    fg="black"
                )
                self.genre_label.config(text=f"类型: {genre}")

            except ValueError as e:
                messagebox.showerror("文件名错误", str(e))
                self.source_file = None
                self.detected_genre = None

    def open_prompt_manager(self):
        """打开Prompt管理窗口"""
        PromptManagerWindow(self.window, self.prompt_mgr, "outline")

    def generate_outline(self):
        """生成大纲"""
        # 验证输入
        if not self.source_file:
            messagebox.showwarning("警告", "请先选择原文文件")
            return

        if not self.api_key_var.get():
            messagebox.showwarning("警告", "请先设置API Key")
            return

        start_ch = self.start_chapter_var.get()
        end_ch = self.end_chapter_var.get()

        if start_ch > end_ch:
            messagebox.showwarning("警告", "起始章节不能大于结束章节")
            return

        # 保存配置
        self.save_config()

        # 禁用按钮
        self.generate_button.config(state=tk.DISABLED, text="生成中...")
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "正在生成大纲，请稍候...\n\n")
        self.result_text.config(state=tk.DISABLED)

        # 在后台线程生成
        def generate():
            try:
                # 读取文件
                with open(self.source_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                self.append_result("✓ 文件读取完成\n")

                # 选择人名
                male_count = self.male_count_var.get()
                female_count = self.female_count_var.get()
                selected_names = self.resource_mgr.select_names(male_count, female_count)
                names_formatted = self.resource_mgr.format_names_for_prompt(selected_names)

                self.append_result(f"✓ 选择人名: {male_count}个男性, {female_count}个女性\n")

                # 选择风格
                genre_data = self.resource_mgr.styles[self.detected_genre]
                counts = genre_data['used']
                min_idx = counts.index(min(counts))
                style = genre_data['styles'][min_idx]
                author = genre_data['authors'][min_idx]

                # 更新使用次数
                self.resource_mgr.styles[self.detected_genre]['used'][min_idx] += 1
                self.resource_mgr.save_styles()

                self.append_result(f"✓ 选择风格: {author}\n")

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

                self.append_result("✓ Prompt准备完成\n")
                self.append_result("正在调用AI...\n")

                # 初始化客户端
                client = OpenAI(
                    api_key=self.api_key_var.get(),
                    base_url=self.base_url_var.get()
                )

                # 调用API
                response = client.chat.completions.create(
                    model=self.model_var.get(),
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"原文内容：\n\n{content}"}
                    ],
                    temperature=self.temperature_var.get(),
                    max_tokens=self.max_tokens_var.get()
                )

                result_text = response.choices[0].message.content

                self.append_result("✓ AI响应完成\n")

                # 解析JSON
                try:
                    outline = parse_json_from_llm_response(result_text)

                    # 保存大纲数据
                    self.outline_data = {
                        'outline': outline,
                        'source_file': self.source_file,
                        'original_title': extract_title_from_filename(self.source_file),
                        'chapter_range': [start_ch, end_ch],
                        'genre': self.detected_genre,
                        'selected_names': selected_names,
                        'style': style,
                        'author': author,
                        'created_at': datetime.now().isoformat()
                    }

                    # 显示大纲
                    self.display_outline(outline)

                    self.append_result("\n✅ 大纲生成成功！\n")

                    # 启用保存按钮
                    self.window.after(0, lambda: self.save_button.config(state=tk.NORMAL))
                    self.window.after(0, lambda: self.open_tool2_button.config(state=tk.NORMAL))

                except json.JSONDecodeError as e:
                    self.append_result(f"\n⚠️ JSON解析失败: {str(e)}\n\n原始响应：\n{result_text}\n")

            except Exception as e:
                self.append_result(f"\n❌ 生成失败: {str(e)}\n")

            finally:
                self.window.after(0, lambda: self.generate_button.config(
                    state=tk.NORMAL, text="🚀 生成大纲"
                ))

        threading.Thread(target=generate, daemon=True).start()

    def append_result(self, text):
        """添加结果文本"""
        def _append():
            self.result_text.config(state=tk.NORMAL)
            self.result_text.insert(tk.END, text)
            self.result_text.config(state=tk.DISABLED)
            self.result_text.see(tk.END)

        self.window.after(0, _append)

    def display_outline(self, outline):
        """显示大纲"""
        display = f"""
{'='*60}
标题: {outline.get('title', 'N/A')}
{'='*60}
类型: {outline.get('genre', 'N/A')}
年龄分类: {outline.get('age_category', 'N/A')}

标签 ({len(outline.get('tags', []))} 个):
{' '.join(outline.get('tags', []))}

简介:
{outline.get('blurb', 'N/A')}

{'='*60}
世界观:
{'='*60}
{outline.get('world_setting', 'N/A')}

{'='*60}
主要角色 ({len(outline.get('main_characters', []))} 个):
{'='*60}
"""
        for char in outline.get('main_characters', []):
            display += f"\n• {char.get('name')} ({char.get('role')})\n"
            display += f"  性别: {char.get('gender')}\n"
            display += f"  性格: {char.get('personality', '')}\n"
            display += f"  背景: {char.get('background', '')}\n"

        display += f"\n{'='*60}\n"
        display += f"章节大纲 ({len(outline.get('chapter_outlines', []))} 章):\n"
        display += f"{'='*60}\n"

        for ch in outline.get('chapter_outlines', [])[:10]:  # 显示前10章
            display += f"\nChapter {ch.get('chapter_number')}: {ch.get('title')}\n"
            display += f"  {ch.get('summary', '')}\n"

        if len(outline.get('chapter_outlines', [])) > 10:
            display += f"\n... 还有 {len(outline.get('chapter_outlines', [])) - 10} 章\n"

        self.append_result(display)

    def save_outline(self):
        """保存大纲"""
        if not self.outline_data:
            messagebox.showwarning("警告", "没有可保存的大纲")
            return

        # 创建大纲文件夹
        os.makedirs('outlines', exist_ok=True)

        # 生成文件名
        title = self.outline_data['outline']['title']
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))
        safe_title = safe_title.replace(' ', '_')

        filename = f"outlines/{safe_title}_Outline.txt"

        # 生成大纲文本
        outline_text = self.generate_outline_text(self.outline_data)

        # 保存
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(outline_text)

        # 同时保存JSON
        json_filename = f"outlines/{safe_title}_Outline.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.outline_data, f, indent=2, ensure_ascii=False)

        messagebox.showinfo("成功", f"大纲已保存:\n{filename}\n{json_filename}")

    def generate_outline_text(self, data):
        """生成格式化的大纲文本"""
        outline = data['outline']

        text = f"""{'='*70}
BOOK METADATA
{'='*70}
Original Title: {data['original_title']}
English Title: {outline['title']}
Genre: {outline['genre']}
Age Category: {outline.get('age_category', 'N/A')}
Chapter Range: {data['chapter_range'][0]}-{data['chapter_range'][1]}
Total Chapters: {len(outline.get('chapter_outlines', []))}

Blurb:
{outline.get('blurb', '')}

Tags:
{' '.join(outline.get('tags', []))}

{'='*70}
WORLD BUILDING
{'='*70}
{outline.get('world_setting', '')}

{'='*70}
CHARACTERS
{'='*70}
"""
        for i, char in enumerate(outline.get('main_characters', []), 1):
            text += f"\n{i}. {char['name']} ({char['gender']})\n"
            text += f"   Role: {char['role']}\n"
            text += f"   Personality: {char.get('personality', '')}\n"
            text += f"   Background: {char.get('background', '')}\n"

        text += f"\n{'='*70}\n"
        text += "WRITING STYLE\n"
        text += f"{'='*70}\n"
        text += f"Style: {data['author']}\n"
        text += f"Description: {data['style']}\n"

        text += f"\n{'='*70}\n"
        text += "CHAPTER OUTLINE\n"
        text += f"{'='*70}\n"

        for ch in outline.get('chapter_outlines', []):
            text += f"\nChapter {ch['chapter_number']}: {ch['title']}\n"
            text += f"- Plot: {ch.get('summary', '')}\n"
            if ch.get('key_events'):
                text += f"- Key Events: {', '.join(ch['key_events'])}\n"
            if ch.get('characters_involved'):
                text += f"- Characters: {', '.join(ch['characters_involved'])}\n"

        return text

    def open_tool2(self):
        """打开Tool 2（暂未实现）"""
        messagebox.showinfo("提示", "Tool 2 写作工具正在开发中...")

    def run(self):
        """运行应用"""
        self.window.mainloop()


class PromptManagerWindow:
    """Prompt管理窗口"""

    def __init__(self, parent, prompt_mgr, prompt_type):
        self.prompt_mgr = prompt_mgr
        self.prompt_type = prompt_type  # 'outline' or 'writer'

        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("Prompt 管理")
        self.window.geometry("800x600")

        self.setup_ui()
        self.load_prompt()

    def setup_ui(self):
        """设置界面"""
        # 版本选择
        top_frame = tk.Frame(self.window)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(top_frame, text="Prompt 版本:").pack(side=tk.LEFT)

        if self.prompt_type == 'outline':
            versions = self.prompt_mgr.get_outline_versions()
        else:
            versions = self.prompt_mgr.get_writer_versions()

        self.version_var = tk.StringVar()
        self.version_combo = ttk.Combobox(
            top_frame,
            textvariable=self.version_var,
            values=versions,
            state="readonly",
            width=30
        )
        self.version_combo.pack(side=tk.LEFT, padx=10)
        self.version_combo.bind('<<ComboboxSelected>>', lambda e: self.load_prompt())

        if versions:
            self.version_combo.current(0)

        # Prompt编辑区
        tk.Label(self.window, text="Prompt 内容:", font=("Arial", 10, "bold")).pack(
            anchor=tk.W, padx=10, pady=(10, 5)
        )

        self.prompt_text = scrolledtext.ScrolledText(
            self.window,
            height=25,
            wrap=tk.WORD,
            font=("Courier", 9)
        )
        self.prompt_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 按钮
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(
            btn_frame,
            text="保存为新版本",
            command=self.save_new_version,
            bg="#4CAF50",
            fg="white",
            width=15
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="恢复默认",
            command=self.restore_default,
            width=15
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="关闭",
            command=self.window.destroy,
            width=15
        ).pack(side=tk.RIGHT, padx=5)

    def load_prompt(self):
        """加载Prompt内容"""
        version = self.version_var.get()
        if not version:
            return

        if self.prompt_type == 'outline':
            content = self.prompt_mgr.get_outline_prompt(version)
        else:
            content = self.prompt_mgr.get_writer_prompt(version)

        self.prompt_text.delete(1.0, tk.END)
        self.prompt_text.insert(1.0, content)

    def save_new_version(self):
        """保存为新版本"""
        name = tk.simpledialog.askstring("保存", "请输入版本名称:")
        if not name:
            return

        content = self.prompt_text.get(1.0, tk.END).strip()

        if self.prompt_type == 'outline':
            self.prompt_mgr.save_custom_outline_prompt(name, content)
            versions = self.prompt_mgr.get_outline_versions()
        else:
            self.prompt_mgr.save_custom_writer_prompt(name, content)
            versions = self.prompt_mgr.get_writer_versions()

        # 更新下拉列表
        self.version_combo['values'] = versions
        self.version_var.set(name)

        messagebox.showinfo("成功", f"Prompt已保存为版本: {name}")

    def restore_default(self):
        """恢复默认Prompt"""
        if messagebox.askyesno("确认", "确定要恢复默认Prompt吗？"):
            if self.prompt_type == 'outline':
                self.prompt_mgr.restore_default_outline()
                content = self.prompt_mgr.get_outline_prompt('Default')
            else:
                self.prompt_mgr.restore_default_writer()
                content = self.prompt_mgr.get_writer_prompt('Default')

            self.prompt_text.delete(1.0, tk.END)
            self.prompt_text.insert(1.0, content)
            self.version_var.set('Default')

            messagebox.showinfo("成功", "已恢复默认Prompt")


def main():
    """主函数"""
    app = OutlineGenerator()
    app.run()


if __name__ == '__main__':
    main()
