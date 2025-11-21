"""
Tool 1: 大纲生成器（带任务队列）
从原文小说生成结构化英文大纲，支持多任务队列管理
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import json
import os
import re
import subprocess
import sys
import uuid
from datetime import datetime
from openai import OpenAI

from config import config
from resource_mgr import ResourceManager
from prompt_manager import PromptManager
from prompt_preview import PromptPreviewWindow
from utils import (
    extract_genre_from_filename,
    extract_title_from_filename,
    validate_genre,
    parse_json_from_llm_response
)


class OutlineTask:
    """大纲生成任务"""

    def __init__(self, task_id, source_file, genre, config_params):
        self.task_id = task_id
        self.source_file = source_file
        self.genre = genre
        self.config = config_params
        self.status = 'pending'  # pending, running, completed, failed
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.output_folder = None
        self.prompt_cache = None  # 缓存生成的prompt

    def to_dict(self):
        return {
            'task_id': self.task_id,
            'source_file': self.source_file,
            'genre': self.genre,
            'config': self.config,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'output_folder': self.output_folder
        }


class OutlineGeneratorWithQueue:
    """大纲生成器（带任务队列）"""

    def __init__(self):
        self.window = tk.Tk()
        self.window.title("大纲生成器 - 多任务队列")
        self.window.geometry("1200x900")

        # 初始化管理器
        self.resource_mgr = ResourceManager()
        self.prompt_mgr = PromptManager()

        # 任务队列
        self.tasks = []  # 任务列表
        self.task_frames = {}  # task_id -> frame widget

        # 当前配置
        self.current_source_file = None
        self.current_genre = None

        # 初始化界面
        self.setup_ui()

    def setup_ui(self):
        """设置界面"""
        # === 标题栏 ===
        title_frame = tk.Frame(self.window, bg="#2196F3", height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        tk.Label(
            title_frame,
            text="📝 大纲生成器 - 多任务队列",
            font=("Arial", 20, "bold"),
            bg="#2196F3",
            fg="white"
        ).pack(side=tk.LEFT, padx=20, pady=10)

        # === 上半部分：配置和添加任务 ===
        top_container = tk.Frame(self.window)
        top_container.pack(fill=tk.X, padx=10, pady=10)

        # API配置区域（简化版）
        api_frame = tk.LabelFrame(top_container, text="API 配置", padx=15, pady=10)
        api_frame.pack(fill=tk.X, pady=(0, 10))

        # 第一行：API Key
        tk.Label(api_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.api_key_var = tk.StringVar(value="sk-4FqZoOFgSYHP6Vfk9HGqhGyrPJjNTVwnaB6zVAbLp8UdlCln")
        tk.Entry(
            api_frame,
            textvariable=self.api_key_var,
            show="*",
            width=50
        ).grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)

        tk.Button(
            api_frame,
            text="测试API",
            command=self.test_api_connection,
            width=10
        ).grid(row=0, column=2, pady=5, padx=5)

        self.api_status_label = tk.Label(api_frame, text="", fg="gray")
        self.api_status_label.grid(row=0, column=3, pady=5, padx=5)

        # 第二行：模型和Prompt管理
        tk.Label(api_frame, text="模型:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.model_var = tk.StringVar(value="gpt-5.1")
        models = ["gpt-5.1", "gemini-2.5-pro", "gpt-5", "gemini-3-pro-preview", "gpt-4-turbo-preview"]
        model_combo = ttk.Combobox(
            api_frame,
            textvariable=self.model_var,
            values=models,
            width=20,
            state='normal'  # 明确允许自定义输入
        )
        model_combo.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)

        tk.Label(api_frame, text="💡 可自定义", fg="gray", font=("Arial", 8)).grid(row=1, column=3, sticky=tk.W, padx=5)

        tk.Button(
            api_frame,
            text="📝 Prompt管理",
            command=self.manage_prompts,
            width=12
        ).grid(row=1, column=2, pady=5, padx=5)

        # 任务配置区域
        task_frame = tk.LabelFrame(top_container, text="新建任务", padx=15, pady=10)
        task_frame.pack(fill=tk.X)

        # 第一行：文件选择
        tk.Label(task_frame, text="原文文件:", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, pady=5
        )

        file_select_frame = tk.Frame(task_frame)
        file_select_frame.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5, columnspan=3)

        self.file_label = tk.Label(
            file_select_frame,
            text="未选择文件（格式：书名_类型.txt）",
            fg="gray",
            font=("Arial", 9)
        )
        self.file_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(
            file_select_frame,
            text="选择文件",
            command=self.select_file
        ).pack(side=tk.LEFT, padx=5)

        self.genre_label = tk.Label(file_select_frame, text="", fg="blue", font=("Arial", 10, "bold"))
        self.genre_label.pack(side=tk.LEFT, padx=10)

        # 第二行：参数配置
        tk.Label(task_frame, text="人名数量:").grid(row=1, column=0, sticky=tk.W, pady=5)

        names_frame = tk.Frame(task_frame)
        names_frame.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)

        tk.Label(names_frame, text="男:").pack(side=tk.LEFT)
        self.male_count_var = tk.IntVar(value=10)
        tk.Spinbox(
            names_frame,
            from_=5,
            to=30,
            textvariable=self.male_count_var,
            width=8
        ).pack(side=tk.LEFT, padx=5)

        tk.Label(names_frame, text="女:").pack(side=tk.LEFT, padx=(10, 0))
        self.female_count_var = tk.IntVar(value=10)
        tk.Spinbox(
            names_frame,
            from_=5,
            to=30,
            textvariable=self.female_count_var,
            width=8
        ).pack(side=tk.LEFT, padx=5)

        tk.Label(task_frame, text="要求章节数:").grid(row=1, column=2, sticky=tk.W, pady=5, padx=(20, 5))
        self.chapter_count_var = tk.IntVar(value=15)
        tk.Spinbox(
            task_frame,
            from_=5,
            to=200,
            increment=5,
            textvariable=self.chapter_count_var,
            width=8
        ).grid(row=1, column=3, sticky=tk.W, pady=5, padx=5)

        tk.Label(task_frame, text="Max Tokens:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.max_tokens_var = tk.IntVar(value=100000)
        tk.Spinbox(
            task_frame,
            from_=10000,
            to=200000,
            increment=10000,
            textvariable=self.max_tokens_var,
            width=12
        ).grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)

        # 第三行：添加到队列按钮
        button_frame = tk.Frame(task_frame)
        button_frame.grid(row=3, column=0, columnspan=4, pady=10)

        tk.Button(
            button_frame,
            text="➕ 添加到任务队列",
            command=self.add_to_queue,
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            height=2,
            width=20
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            button_frame,
            text="📥 导入网页版大纲",
            command=self.import_web_outline,
            font=("Arial", 12, "bold"),
            bg="#2196F3",
            fg="white",
            height=2,
            width=20
        ).pack(side=tk.LEFT, padx=10)

        # === 下半部分：任务队列 ===
        queue_container = tk.LabelFrame(
            self.window,
            text="📋 任务队列",
            font=("Arial", 12, "bold"),
            padx=10,
            pady=10
        )
        queue_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 队列工具栏
        queue_toolbar = tk.Frame(queue_container)
        queue_toolbar.pack(fill=tk.X, pady=(0, 10))

        tk.Button(
            queue_toolbar,
            text="🗑️ 清空队列",
            command=self.clear_all_tasks,
            bg="#f44336",
            fg="white",
            width=12
        ).pack(side=tk.RIGHT, padx=5)

        # 创建滚动区域
        canvas = tk.Canvas(queue_container, bg="white")
        scrollbar = ttk.Scrollbar(queue_container, orient="vertical", command=canvas.yview)

        self.queue_frame = tk.Frame(canvas, bg="white")

        self.queue_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.queue_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 空队列提示
        self.empty_label = tk.Label(
            self.queue_frame,
            text="暂无任务\n点击上方「添加到任务队列」按钮添加任务",
            font=("Arial", 12),
            fg="gray",
            bg="white",
            pady=50
        )
        self.empty_label.pack()

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

                # 验证类型
                available_genres = self.resource_mgr.get_available_genres()
                validate_genre(genre, available_genres)

                # 保存数据
                self.current_source_file = file_path
                self.current_genre = genre

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
                self.current_source_file = None
                self.current_genre = None

    def add_to_queue(self):
        """添加任务到队列"""
        if not self.current_source_file:
            messagebox.showwarning("警告", "请先选择原文文件")
            return

        if not self.api_key_var.get():
            messagebox.showwarning("警告", "请输入API Key")
            return

        # 创建任务
        task_id = f"outline_{uuid.uuid4().hex[:8]}"

        config_params = {
            'api_key': self.api_key_var.get(),
            'base_url': 'https://yunwuapi.com/v1/',
            'model': self.model_var.get(),
            'male_count': self.male_count_var.get(),
            'female_count': self.female_count_var.get(),
            'chapter_count': self.chapter_count_var.get(),
            'max_tokens': self.max_tokens_var.get(),
        }

        task = OutlineTask(task_id, self.current_source_file, self.current_genre, config_params)
        self.tasks.append(task)

        # 添加到UI
        self.add_task_to_ui(task)

        # 隐藏空队列提示
        if self.empty_label.winfo_exists():
            self.empty_label.pack_forget()

        messagebox.showinfo("成功", f"任务已添加到队列\n文件: {os.path.basename(self.current_source_file)}")

    def import_web_outline(self):
        """导入网页版生成的大纲（格式：BookTitle_Genre.txt）"""
        # 选择文件
        file_path = filedialog.askopenfilename(
            title="选择网页版大纲文件（格式：书名_类型.txt）",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if not file_path:
            return

        try:
            # 从文件名提取书名和类型
            filename = os.path.basename(file_path)
            match = re.match(r'(.+?)_([A-Za-z+\-]+)\.txt$', filename)

            if not match:
                messagebox.showerror("错误", "文件名格式不正确！\n正确格式：书名_类型.txt\n例如：MyBook_Romance.txt")
                return

            book_title = match.group(1)
            genre = match.group(2)

            # 验证类型
            available_genres = self.resource_mgr.get_available_genres()
            if genre not in available_genres:
                messagebox.showerror("错误", f"类型'{genre}'不存在！\n可用类型：{', '.join(available_genres)}")
                return

            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                result_text = f.read()

            if not result_text.strip():
                messagebox.showerror("错误", "文件内容为空！")
                return

            # 创建虚拟任务对象（用于复用保存逻辑）
            class WebOutlineTask:
                def __init__(self, genre):
                    self.genre = genre
                    self.config = {}

            virtual_task = WebOutlineTask(genre)

            # 使用现有的保存方法
            output_folder = self._save_outline_text(virtual_task, result_text)

            # 成功提示
            messagebox.showinfo(
                "导入成功",
                f"大纲已成功导入！\n\n书名：{book_title}\n类型：{genre}\n输出文件夹：{output_folder}"
            )

            # 询问是否打开文件夹
            if messagebox.askyesno("打开文件夹", "是否打开输出文件夹查看？"):
                try:
                    if sys.platform == 'win32':
                        os.startfile(output_folder)
                    elif sys.platform == 'darwin':
                        subprocess.Popen(['open', output_folder])
                    else:
                        subprocess.Popen(['xdg-open', output_folder])
                except Exception as e:
                    messagebox.showerror("错误", f"打开文件夹失败: {str(e)}")

        except Exception as e:
            messagebox.showerror("导入失败", f"导入大纲时出错:\n{str(e)}\n\n请确保文件格式正确。")

    def add_task_to_ui(self, task):
        """添加任务到UI"""
        # 创建任务框架
        task_container = tk.Frame(self.queue_frame, relief=tk.RIDGE, borderwidth=2, bg="#f5f5f5")
        task_container.pack(fill=tk.X, padx=5, pady=5)

        self.task_frames[task.task_id] = task_container

        # 左侧：任务信息
        info_frame = tk.Frame(task_container, bg="#f5f5f5")
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 标题行
        title_frame = tk.Frame(info_frame, bg="#f5f5f5")
        title_frame.pack(fill=tk.X)

        tk.Label(
            title_frame,
            text=f"📄 {os.path.basename(task.source_file)}",
            font=("Arial", 11, "bold"),
            bg="#f5f5f5",
            anchor="w"
        ).pack(side=tk.LEFT)

        status_label = tk.Label(
            title_frame,
            text=f"⏸ {task.status}",
            font=("Arial", 10),
            bg="#f5f5f5",
            fg="orange"
        )
        status_label.pack(side=tk.LEFT, padx=10)
        task_container.status_label = status_label  # 保存引用

        # 详情行
        details_frame = tk.Frame(info_frame, bg="#f5f5f5")
        details_frame.pack(fill=tk.X, pady=(5, 0))

        # 动态显示的详情标签
        details_label = tk.Label(
            details_frame,
            text=f"类型: {task.genre}  |  模型: {task.config['model']}",
            font=("Arial", 9),
            bg="#f5f5f5",
            fg="gray"
        )
        details_label.pack(side=tk.LEFT)
        task_container.details_label = details_label  # 保存引用

        # 右侧：操作按钮
        button_frame = tk.Frame(task_container, bg="#f5f5f5")
        button_frame.pack(side=tk.RIGHT, padx=10, pady=10)

        # 预览Prompt按钮
        tk.Button(
            button_frame,
            text="👁️ 预览Prompt",
            command=lambda: self.preview_task_prompt(task),
            width=15,
            bg="#FF9800",
            fg="white"
        ).pack(side=tk.LEFT, padx=3)

        # 开始按钮
        start_btn = tk.Button(
            button_frame,
            text="▶️ 开始生成",
            command=lambda: self.start_task(task),
            width=15,
            bg="#4CAF50",
            fg="white"
        )
        start_btn.pack(side=tk.LEFT, padx=3)
        task_container.start_btn = start_btn  # 保存引用

        # 打开文件夹按钮
        folder_btn = tk.Button(
            button_frame,
            text="📂 打开文件夹",
            command=lambda: self.open_output_folder(task),
            width=15,
            state=tk.DISABLED
        )
        folder_btn.pack(side=tk.LEFT, padx=3)
        task_container.folder_btn = folder_btn  # 保存引用

        # 删除按钮
        tk.Button(
            button_frame,
            text="🗑️ 删除",
            command=lambda: self.remove_task(task),
            width=10,
            bg="#f44336",
            fg="white"
        ).pack(side=tk.LEFT, padx=3)

    def preview_task_prompt(self, task):
        """预览任务的Prompt"""
        try:
            # 清空缓存，确保使用最新配置重新生成
            task.prompt_cache = None

            # 生成Prompt
            with open(task.source_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if len(content) > 10000:
                    content_preview = content[:10000] + "\n\n... (内容已截断)"
                else:
                    content_preview = content

            # 选择名字和风格
            selected_names = self.resource_mgr.select_names(
                task.config['male_count'],
                task.config['female_count']
            )
            names_formatted = self.resource_mgr.format_names_for_prompt(selected_names)

            selected_style = self.resource_mgr.select_style(task.genre)

            # 构建Prompt变量
            prompt_vars = {
                'genre': task.genre,
                'style': selected_style['style'],
                'male_names': names_formatted['male_names'],
                'female_names': names_formatted['female_names'],
                'end_chapter': task.config.get('chapter_count', 15),
            }

            # 渲染Prompt
            system_prompt = self.prompt_mgr.render_outline_prompt(prompt_vars)

            # 构建完整预览文本
            full_prompt = f"""
系统Prompt (System Message)
{'='*70}
{system_prompt}

用户消息 (User Message)
{'='*70}
{content_preview}

元数据 (Metadata)
{'='*70}
文件: {os.path.basename(task.source_file)}
类型: {task.genre}
模型: {task.config['model']}
要求章节数: {task.config.get('chapter_count', 15)}
Max Tokens: {task.config['max_tokens']}

选择的人名:
男性: {names_formatted['male_names']}
女性: {names_formatted['female_names']}

选择的风格:
{selected_style['author']} - {selected_style['style'][:100]}...
"""

            # 缓存Prompt
            task.prompt_cache = full_prompt

            # 显示预览窗口
            PromptPreviewWindow(self.window, full_prompt, f"Prompt预览 - {os.path.basename(task.source_file)}")

        except Exception as e:
            messagebox.showerror("错误", f"预览Prompt失败: {str(e)}")

    def start_task(self, task):
        """开始执行任务"""
        if task.status == 'running':
            messagebox.showinfo("提示", "任务正在运行中")
            return

        if task.status == 'completed':
            if not messagebox.askyesno("确认", "任务已完成，是否重新生成？"):
                return

        # 更新状态
        task.status = 'running'
        task.started_at = datetime.now()

        # 更新UI
        frame = self.task_frames[task.task_id]
        frame.status_label.config(text="🔄 运行中", fg="blue")
        frame.start_btn.config(state=tk.DISABLED)

        # 更新详情显示开始时间
        frame.details_label.config(
            text=f"类型: {task.genre}  |  模型: {task.config['model']}  |  开始时间: {task.started_at.strftime('%H:%M:%S')}"
        )

        # 在新线程中执行
        thread = threading.Thread(target=self._execute_task, args=(task,), daemon=True)
        thread.start()

    def _execute_task(self, task):
        """执行任务（在后台线程）"""
        try:
            # 读取原文
            with open(task.source_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 选择资源
            selected_names = self.resource_mgr.select_names(
                task.config['male_count'],
                task.config['female_count']
            )
            names_formatted = self.resource_mgr.format_names_for_prompt(selected_names)

            selected_style = self.resource_mgr.select_style(task.genre)

            # 构建Prompt
            prompt_vars = {
                'genre': task.genre,
                'style': selected_style['style'],
                'male_names': names_formatted['male_names'],
                'female_names': names_formatted['female_names'],
                'end_chapter': task.config.get('chapter_count', 15),
            }

            system_prompt = self.prompt_mgr.render_outline_prompt(prompt_vars)

            # 调用API
            client = OpenAI(
                api_key=task.config['api_key'],
                base_url=task.config.get('base_url', 'https://yunwuapi.com/v1/')
            )

            response = client.chat.completions.create(
                model=task.config['model'],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                temperature=0.8,
                max_tokens=task.config['max_tokens']
            )

            result_text = response.choices[0].message.content

            # 检查返回内容是否为空
            if not result_text:
                raise ValueError("API返回内容为空，请检查API配置或稍后重试")

            # 保存结果（纯文本格式）
            output_folder = self._save_outline_text(task, result_text)
            task.output_folder = output_folder

            # 标记完成
            task.status = 'completed'
            task.completed_at = datetime.now()

            # 更新UI（在主线程）
            self.window.after(0, lambda: self._on_task_completed(task))

        except Exception as e:
            task.status = 'failed'
            error_msg = str(e)

            # 更新UI
            self.window.after(0, lambda: self._on_task_failed(task, error_msg))

    def _save_outline_text(self, task, result_text):
        """保存大纲到文件（纯文本格式）"""
        # 解析返回的文本
        parsed_data = self._parse_outline_response(result_text)

        # 创建输出文件夹
        os.makedirs('outlines', exist_ok=True)

        title = parsed_data.get('title', 'Untitled') or 'Untitled'
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))
        safe_title = safe_title.replace(' ', '_') if safe_title else 'Untitled'

        # 文件夹名：书名_类型
        folder_name = f"{safe_title}_{task.genre}"
        output_folder = os.path.join('outlines', folder_name)

        # 如果文件夹已存在，添加时间戳
        if os.path.exists(output_folder):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            folder_name = f"{safe_title}_{task.genre}_{timestamp}"
            output_folder = os.path.join('outlines', folder_name)

        os.makedirs(output_folder, exist_ok=True)

        # 1. 保存 title.txt
        with open(os.path.join(output_folder, 'title.txt'), 'w', encoding='utf-8') as f:
            f.write(parsed_data.get('title', '') or '')

        # 2. 保存 blurb.txt
        with open(os.path.join(output_folder, 'blurb.txt'), 'w', encoding='utf-8') as f:
            f.write(parsed_data.get('blurb', '') or '')

        # 3. 保存 tags.txt
        with open(os.path.join(output_folder, 'tags.txt'), 'w', encoding='utf-8') as f:
            f.write(parsed_data.get('tags', '') or '')

        # 4. 保存 category.txt
        with open(os.path.join(output_folder, 'category.txt'), 'w', encoding='utf-8') as f:
            f.write(task.genre)

        # 5. 保存章节大纲（每章一个prompt文件：chapter_X_prompt.txt）
        chapters = parsed_data.get('chapters', [])
        for chapter in chapters:
            ch_num = chapter.get('number', 0)
            ch_title = chapter.get('title', f'Chapter {ch_num}') or f'Chapter {ch_num}'
            ch_summary = chapter.get('summary', '') or ''

            # 文件名：chapter_1_prompt.txt, chapter_2_prompt.txt, ...
            filename = f"chapter_{ch_num}_prompt.txt"

            with open(os.path.join(output_folder, filename), 'w', encoding='utf-8') as f:
                f.write(f"Chapter {ch_num}: {ch_title}\n\n")
                f.write(f"Summary:\n{ch_summary}\n\n")
                if 'key_events' in chapter:
                    f.write(f"Key Events:\n{chapter['key_events']}\n\n")
                if 'characters' in chapter:
                    f.write(f"Characters: {chapter['characters']}\n")

        # 6. 保存完整大纲备份
        with open(os.path.join(output_folder, '_full_outline.txt'), 'w', encoding='utf-8') as f:
            f.write(result_text)

        # 7. 保存写作用的精简Prompt（_writing_prompt.txt）
        self._save_writing_prompt(output_folder, result_text, parsed_data)

        return output_folder

    def _save_writing_prompt(self, output_folder, result_text, parsed_data):
        """保存写作工具需要的基础Prompt（只包含世界观和角色，不含章节大纲）

        章节大纲已单独保存在 chapter_X_prompt.txt 文件中
        """
        writing_prompt = ""

        # 1. 提取 WORLD_SETTING
        world_match = re.search(r'={5,}\s*WORLD_SETTING\s*={5,}\s*\n(.+?)(?=\n={5,}|$)', result_text, re.DOTALL)
        if world_match:
            world_setting = world_match.group(1).strip()
            writing_prompt += "===== WORLD_SETTING =====\n"
            writing_prompt += world_setting + "\n\n"

        # 2. 提取 MAIN_CHARACTERS
        chars_match = re.search(r'={5,}\s*MAIN_CHARACTERS\s*={5,}\s*\n(.+?)(?=\n={5,}|$)', result_text, re.DOTALL)
        if chars_match:
            main_characters = chars_match.group(1).strip()
            writing_prompt += "===== MAIN_CHARACTERS =====\n"
            writing_prompt += main_characters + "\n\n"

        # 注：章节大纲不再包含在_writing_prompt.txt中
        # 每章的大纲已单独保存在 chapter_X_prompt.txt 文件中
        # 写作工具会根据需要动态加载相关章节的prompt

        # 保存文件
        with open(os.path.join(output_folder, '_writing_prompt.txt'), 'w', encoding='utf-8') as f:
            f.write(writing_prompt)

    def _parse_outline_response(self, text):
        """解析AI返回的纯文本大纲"""
        data = {
            'title': '',
            'blurb': '',
            'tags': '',
            'category': '',
            'chapters': []
        }

        # 提取title
        title_match = re.search(r'={5,}\s*TITLE\s*={5,}\s*\n(.+?)(?=\n={5,}|$)', text, re.DOTALL)
        if title_match:
            data['title'] = title_match.group(1).strip()

        # 提取blurb
        blurb_match = re.search(r'={5,}\s*BLURB\s*={5,}\s*\n(.+?)(?=\n={5,}|$)', text, re.DOTALL)
        if blurb_match:
            data['blurb'] = blurb_match.group(1).strip()

        # 提取tags
        tags_match = re.search(r'={5,}\s*TAGS\s*={5,}\s*\n(.+?)(?=\n={5,}|$)', text, re.DOTALL)
        if tags_match:
            data['tags'] = tags_match.group(1).strip()

        # 提取category
        category_match = re.search(r'={5,}\s*CATEGORY\s*={5,}\s*\n(.+?)(?=\n={5,}|$)', text, re.DOTALL)
        if category_match:
            data['category'] = category_match.group(1).strip()

        # 提取章节
        chapter_section = re.search(r'={5,}\s*CHAPTER_OUTLINES\s*={5,}\s*\n(.+?)(?=\n={5,}\s*END|$)', text, re.DOTALL)
        if chapter_section:
            chapter_text = chapter_section.group(1)

            # 匹配每个章节
            chapter_pattern = r'Chapter\s+(\d+):\s*(.+?)\n\s*Summary:\s*(.+?)(?=\n\s*(?:Key Events:|Characters:|Chapter\s+\d+:|$))'
            for match in re.finditer(chapter_pattern, chapter_text, re.DOTALL):
                ch_num = int(match.group(1))
                ch_title = match.group(2).strip()
                ch_summary = match.group(3).strip()

                chapter_data = {
                    'number': ch_num,
                    'title': ch_title,
                    'summary': ch_summary
                }

                # 尝试提取Key Events
                events_match = re.search(rf'Chapter\s+{ch_num}:.*?Key Events:\s*(.+?)(?=\n\s*Characters:|Chapter\s+\d+:|$)', chapter_text, re.DOTALL)
                if events_match:
                    chapter_data['key_events'] = events_match.group(1).strip()

                # 尝试提取Characters
                chars_match = re.search(rf'Chapter\s+{ch_num}:.*?Characters:\s*(.+?)(?=\n\s*Chapter\s+\d+:|$)', chapter_text, re.DOTALL)
                if chars_match:
                    chapter_data['characters'] = chars_match.group(1).strip()

                data['chapters'].append(chapter_data)

        return data

    def _on_task_completed(self, task):
        """任务完成回调"""
        frame = self.task_frames[task.task_id]
        frame.status_label.config(text="✅ 完成", fg="green")
        frame.start_btn.config(text="🔄 重新生成", state=tk.NORMAL)
        frame.folder_btn.config(state=tk.NORMAL)

        messagebox.showinfo(
            "任务完成",
            f"任务完成！\n文件: {os.path.basename(task.source_file)}\n输出: {task.output_folder}"
        )

    def _on_task_failed(self, task, error_msg):
        """任务失败回调"""
        frame = self.task_frames[task.task_id]
        frame.status_label.config(text="❌ 失败", fg="red")
        frame.start_btn.config(state=tk.NORMAL)

        messagebox.showerror(
            "任务失败",
            f"任务执行失败\n文件: {os.path.basename(task.source_file)}\n错误: {error_msg}"
        )

    def open_output_folder(self, task):
        """打开输出文件夹"""
        if not task.output_folder or not os.path.exists(task.output_folder):
            messagebox.showwarning("警告", "输出文件夹不存在")
            return

        try:
            if sys.platform == 'win32':
                os.startfile(task.output_folder)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', task.output_folder])
            else:
                subprocess.Popen(['xdg-open', task.output_folder])
        except Exception as e:
            messagebox.showerror("错误", f"打开文件夹失败: {str(e)}")

    def remove_task(self, task):
        """删除单个任务"""
        if task.status == 'running':
            messagebox.showwarning("警告", "无法删除正在运行的任务")
            return

        if messagebox.askyesno("确认", f"确定要删除任务 {os.path.basename(task.source_file)} 吗？"):
            # 从列表中移除
            self.tasks.remove(task)

            # 从UI中移除
            if task.task_id in self.task_frames:
                frame = self.task_frames[task.task_id]
                frame.destroy()
                del self.task_frames[task.task_id]

            # 如果队列为空，显示空提示
            if len(self.tasks) == 0:
                self.empty_label.pack()

    def clear_all_tasks(self):
        """清空所有任务"""
        # 检查是否有运行中的任务
        running_tasks = [t for t in self.tasks if t.status == 'running']
        if running_tasks:
            messagebox.showwarning("警告", "有任务正在运行中，无法清空队列")
            return

        if not self.tasks:
            messagebox.showinfo("提示", "队列已经是空的了")
            return

        if messagebox.askyesno("确认", f"确定要清空所有 {len(self.tasks)} 个任务吗？"):
            # 销毁所有任务UI
            for task in self.tasks[:]:  # 复制列表避免迭代时修改
                if task.task_id in self.task_frames:
                    self.task_frames[task.task_id].destroy()
                    del self.task_frames[task.task_id]

            # 清空任务列表
            self.tasks.clear()

            # 显示空提示
            self.empty_label.pack()

    def test_api_connection(self):
        """测试API连接"""
        api_key = self.api_key_var.get()
        model = self.model_var.get()

        if not api_key:
            self.api_status_label.config(text="❌ 请输入API Key", fg="red")
            return

        # 更新状态
        self.api_status_label.config(text="🔄 测试中...", fg="blue")
        self.window.update()

        # 在新线程中测试，避免阻塞UI
        def _test():
            try:
                client = OpenAI(
                    api_key=api_key,
                    base_url='https://yunwuapi.com/v1/'
                )

                # 发送一个简单的测试请求
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "user", "content": "Hello"}
                    ],
                    max_tokens=10
                )

                # 检查响应
                if response and response.choices and len(response.choices) > 0:
                    # 成功
                    self.window.after(0, lambda: self.api_status_label.config(
                        text="✅ 连接成功", fg="green"
                    ))
                else:
                    raise ValueError("API响应格式异常")

            except Exception as e:
                error_msg = str(e) if e else "未知错误"
                if error_msg and len(error_msg) > 50:
                    error_msg = error_msg[:50] + "..."

                self.window.after(0, lambda: self.api_status_label.config(
                    text=f"❌ {error_msg}", fg="red"
                ))

        thread = threading.Thread(target=_test, daemon=True)
        thread.start()

    def manage_prompts(self):
        """Prompt管理和版本控制"""
        # 创建Prompt管理窗口
        prompt_window = tk.Toplevel(self.window)
        prompt_window.title("Prompt管理")
        prompt_window.geometry("900x700")

        # 标题
        title_label = tk.Label(
            prompt_window,
            text="📝 Prompt模板管理",
            font=("Arial", 16, "bold"),
            bg="#2196F3",
            fg="white",
            pady=15
        )
        title_label.pack(fill=tk.X)

        # 主容器
        main_frame = tk.Frame(prompt_window, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 说明文本和版本选择
        info_frame = tk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            info_frame,
            text="Prompt版本:",
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT)

        # 版本下拉选择
        version_var = tk.StringVar()
        available_versions = self.prompt_mgr.get_outline_versions()
        current_version = self.prompt_mgr.prompts['outline'].get('active_version', 'Default')
        version_var.set(current_version)

        def on_version_change(event=None):
            selected_version = version_var.get()
            prompt_text.config(state=tk.NORMAL)
            prompt_text.delete("1.0", tk.END)
            try:
                version_prompt = self.prompt_mgr.get_outline_prompt(selected_version)
                prompt_text.insert(tk.END, version_prompt)
            except Exception as e:
                prompt_text.insert(tk.END, f"加载版本失败: {str(e)}")
            prompt_text.config(state=tk.DISABLED)
            edit_btn.config(state=tk.NORMAL)
            save_btn.config(state=tk.DISABLED)

        version_combo = ttk.Combobox(
            info_frame,
            textvariable=version_var,
            values=available_versions,
            state="readonly",
            width=30
        )
        version_combo.pack(side=tk.LEFT, padx=10)
        version_combo.bind('<<ComboboxSelected>>', on_version_change)

        # 设为活跃版本按钮
        def set_active():
            selected_version = version_var.get()
            self.prompt_mgr.set_active_outline_version(selected_version)
            messagebox.showinfo("成功", f"已将 '{selected_version}' 设为活跃版本")

        tk.Button(
            info_frame,
            text="设为活跃",
            command=set_active,
            bg="#2196F3",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)

        # Prompt显示区域
        prompt_text = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            font=("Courier", 9),
            height=25
        )
        prompt_text.pack(fill=tk.BOTH, expand=True)

        # 加载当前Prompt
        try:
            current_prompt = self.prompt_mgr.get_default_outline_prompt()
            prompt_text.insert(tk.END, current_prompt)
            prompt_text.config(state=tk.DISABLED)  # 只读
        except Exception as e:
            prompt_text.insert(tk.END, f"加载失败: {str(e)}")

        # 按钮区域
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        # 编辑按钮
        def edit_prompt():
            prompt_text.config(state=tk.NORMAL)
            edit_btn.config(state=tk.DISABLED)
            save_btn.config(state=tk.NORMAL)

        # 保存按钮
        def save_prompt():
            # 创建版本名输入窗口
            version_window = tk.Toplevel(prompt_window)
            version_window.title("保存Prompt版本")
            version_window.geometry("400x180")
            version_window.transient(prompt_window)
            version_window.grab_set()

            tk.Label(
                version_window,
                text="请输入版本名称:",
                font=("Arial", 12)
            ).pack(pady=(20, 10))

            version_entry = tk.Entry(version_window, width=40, font=("Arial", 11))
            version_entry.pack(pady=10)
            version_entry.insert(0, f"Custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            version_entry.select_range(0, tk.END)
            version_entry.focus()

            def do_save():
                version_name = version_entry.get().strip()
                if not version_name:
                    messagebox.showwarning("警告", "版本名称不能为空", parent=version_window)
                    return

                new_prompt = prompt_text.get("1.0", tk.END).strip()
                try:
                    # 保存到prompt_manager
                    self.prompt_mgr.save_custom_outline_prompt(version_name, new_prompt)
                    self.prompt_mgr.set_active_outline_version(version_name)

                    # 更新版本下拉框
                    version_combo['values'] = self.prompt_mgr.get_outline_versions()
                    version_var.set(version_name)

                    messagebox.showinfo("成功", f"Prompt已保存为版本 '{version_name}'！\n将在下次生成任务时使用新的Prompt。", parent=version_window)
                    version_window.destroy()
                    prompt_text.config(state=tk.DISABLED)
                    edit_btn.config(state=tk.NORMAL)
                    save_btn.config(state=tk.DISABLED)
                except Exception as e:
                    messagebox.showerror("保存失败", f"保存Prompt时出错:\n{str(e)}", parent=version_window)

            button_frame_save = tk.Frame(version_window)
            button_frame_save.pack(pady=20)

            tk.Button(
                button_frame_save,
                text="保存",
                command=do_save,
                width=10,
                bg="#4CAF50",
                fg="white"
            ).pack(side=tk.LEFT, padx=5)

            tk.Button(
                button_frame_save,
                text="取消",
                command=version_window.destroy,
                width=10
            ).pack(side=tk.LEFT, padx=5)

            # 绑定回车键
            version_entry.bind('<Return>', lambda e: do_save())

        # 重置为默认
        def reset_to_default():
            if messagebox.askyesno("确认", "确定要重置为默认Prompt吗？"):
                try:
                    self.prompt_mgr.reset_to_default()
                    prompt_text.config(state=tk.NORMAL)
                    prompt_text.delete("1.0", tk.END)
                    prompt_text.insert(tk.END, self.prompt_mgr.get_default_outline_prompt())
                    prompt_text.config(state=tk.DISABLED)
                    messagebox.showinfo("成功", "已重置为默认Prompt")
                except Exception as e:
                    messagebox.showerror("重置失败", f"重置Prompt时出错:\n{str(e)}")

        edit_btn = tk.Button(
            button_frame,
            text="✏️ 编辑",
            command=edit_prompt,
            width=15,
            bg="#FF9800",
            fg="white"
        )
        edit_btn.pack(side=tk.LEFT, padx=5)

        save_btn = tk.Button(
            button_frame,
            text="💾 保存",
            command=save_prompt,
            width=15,
            bg="#4CAF50",
            fg="white",
            state=tk.DISABLED
        )
        save_btn.pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_frame,
            text="🔄 重置为默认",
            command=reset_to_default,
            width=15
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_frame,
            text="关闭",
            command=prompt_window.destroy,
            width=15
        ).pack(side=tk.RIGHT, padx=5)

    def run(self):
        """运行应用"""
        self.window.mainloop()


def main():
    """主函数"""
    app = OutlineGeneratorWithQueue()
    app.run()


if __name__ == '__main__':
    main()
