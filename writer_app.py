#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小说生成器 - 主应用（完全重写版本）
参考outline_generator架构
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import json
import os
import subprocess
import sys
import uuid
import time
from datetime import datetime
from pathlib import Path

from prompt_manager import PromptManager
from prompt_preview import PromptPreviewWindow
from utils import extract_genre_from_filename


class WriterTask:
    """写作任务"""

    def __init__(self, task_id, outline_file, start_chapter, end_chapter, config_params):
        self.task_id = task_id
        self.outline_file = outline_file
        self.start_chapter = start_chapter
        self.end_chapter = end_chapter
        self.config = config_params
        self.status = 'pending'  # pending, running, completed, failed
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.output_folder = None
        self.prompt_cache = None  # 缓存生成的prompt
        self.current_chapter = start_chapter
        self.total_chapters = end_chapter - start_chapter + 1
        self.progress = 0  # 0-100

    def to_dict(self):
        return {
            'task_id': self.task_id,
            'outline_file': self.outline_file,
            'start_chapter': self.start_chapter,
            'end_chapter': self.end_chapter,
            'config': self.config,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'output_folder': self.output_folder,
            'current_chapter': self.current_chapter,
            'progress': self.progress
        }


class NovelWriterApp:
    """小说生成器主应用"""

    def __init__(self):
        self.window = tk.Tk()
        self.window.title("小说生成器 - 多任务队列")
        self.window.geometry("1200x900")

        # 初始化管理器
        self.prompt_mgr = PromptManager()

        # 任务队列
        self.tasks = []  # 任务列表
        self.task_frames = {}  # task_id -> frame widget
        self.running_processes = {}  # task_id -> subprocess

        # 当前选择
        self.current_outline_file = None
        self.current_outline_data = None

        # 初始化界面
        self.setup_ui()

        # 开始轮询任务状态
        self.start_polling()

    def setup_ui(self):
        """设置界面"""
        # === 标题栏 ===
        title_frame = tk.Frame(self.window, bg="#FF6B6B", height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        tk.Label(
            title_frame,
            text="✍️ 小说生成器 - 多任务队列",
            font=("Arial", 20, "bold"),
            bg="#FF6B6B",
            fg="white"
        ).pack(side=tk.LEFT, padx=20, pady=10)

        # === 上半部分：配置和添加任务 ===
        top_container = tk.Frame(self.window)
        top_container.pack(fill=tk.X, padx=10, pady=10)

        # API配置区域
        api_frame = tk.LabelFrame(top_container, text="API 配置", padx=15, pady=10)
        api_frame.pack(fill=tk.X, pady=(0, 10))

        # 第一行：API Key和Base URL
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

        # 第二行：Base URL和模型
        tk.Label(api_frame, text="Base URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.base_url_var = tk.StringVar(value="https://yunwuapi.com/v1/")
        tk.Entry(
            api_frame,
            textvariable=self.base_url_var,
            width=50
        ).grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)

        tk.Label(api_frame, text="模型:").grid(row=1, column=2, sticky=tk.W, pady=5, padx=(20, 5))
        self.model_var = tk.StringVar(value="gpt-5-mini")
        models = ["gpt-5-mini", "gpt-5.1", "gemini-2.5-pro", "gpt-5", "gemini-3-pro-preview"]
        model_combo = ttk.Combobox(
            api_frame,
            textvariable=self.model_var,
            values=models,
            width=20
        )
        model_combo.grid(row=1, column=3, sticky=tk.W, pady=5, padx=5)

        # 第三行：并发数和Prompt管理
        tk.Label(api_frame, text="并发章节数:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.parallel_count_var = tk.IntVar(value=3)
        tk.Spinbox(
            api_frame,
            from_=1,
            to=10,
            textvariable=self.parallel_count_var,
            width=10
        ).grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)

        tk.Button(
            api_frame,
            text="📝 Prompt管理",
            command=self.manage_prompts,
            width=12
        ).grid(row=2, column=2, pady=5, padx=(20, 5))

        # 任务配置区域
        task_frame = tk.LabelFrame(top_container, text="新建任务", padx=15, pady=10)
        task_frame.pack(fill=tk.X)

        # 第一行：大纲文件选择
        tk.Label(task_frame, text="大纲文件:", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, pady=5
        )

        file_select_frame = tk.Frame(task_frame)
        file_select_frame.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5, columnspan=3)

        self.file_label = tk.Label(
            file_select_frame,
            text="未选择大纲文件（需要.json文件）",
            fg="gray",
            font=("Arial", 9)
        )
        self.file_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(
            file_select_frame,
            text="选择大纲",
            command=self.select_outline_file
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            file_select_frame,
            text="选择文件夹",
            command=self.select_outline_folder
        ).pack(side=tk.LEFT, padx=5)

        self.outline_info_label = tk.Label(file_select_frame, text="", fg="blue", font=("Arial", 9, "bold"))
        self.outline_info_label.pack(side=tk.LEFT, padx=10)

        # 第二行：章节范围和每次章节数
        tk.Label(task_frame, text="章节范围:").grid(row=1, column=0, sticky=tk.W, pady=5)

        chapter_range_frame = tk.Frame(task_frame)
        chapter_range_frame.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)

        tk.Label(chapter_range_frame, text="从第").pack(side=tk.LEFT)
        self.start_chapter_var = tk.IntVar(value=1)
        tk.Spinbox(
            chapter_range_frame,
            from_=1,
            to=500,
            textvariable=self.start_chapter_var,
            width=8
        ).pack(side=tk.LEFT, padx=5)

        tk.Label(chapter_range_frame, text="章到第").pack(side=tk.LEFT)
        self.end_chapter_var = tk.IntVar(value=10)
        tk.Spinbox(
            chapter_range_frame,
            from_=1,
            to=500,
            textvariable=self.end_chapter_var,
            width=8
        ).pack(side=tk.LEFT, padx=5)
        tk.Label(chapter_range_frame, text="章").pack(side=tk.LEFT)

        tk.Label(task_frame, text="每次生成:").grid(row=1, column=2, sticky=tk.W, pady=5, padx=(20, 5))
        self.chapters_per_batch_var = tk.IntVar(value=1)
        tk.Spinbox(
            task_frame,
            from_=1,
            to=5,
            textvariable=self.chapters_per_batch_var,
            width=8
        ).grid(row=1, column=3, sticky=tk.W, pady=5, padx=5)

        # 第三行：Temperature和Max Tokens
        tk.Label(task_frame, text="Temperature:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.temperature_var = tk.DoubleVar(value=0.85)
        tk.Scale(
            task_frame,
            from_=0,
            to=1,
            resolution=0.05,
            orient=tk.HORIZONTAL,
            variable=self.temperature_var,
            length=150
        ).grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)

        tk.Label(task_frame, text="Max Tokens:").grid(row=2, column=2, sticky=tk.W, pady=5, padx=(20, 5))
        self.max_tokens_var = tk.IntVar(value=32000)
        tk.Spinbox(
            task_frame,
            from_=8000,
            to=128000,
            increment=4000,
            textvariable=self.max_tokens_var,
            width=10
        ).grid(row=2, column=3, sticky=tk.W, pady=5, padx=5)

        # 添加任务按钮
        add_btn_frame = tk.Frame(task_frame)
        add_btn_frame.grid(row=3, column=0, columnspan=4, pady=10)

        tk.Button(
            add_btn_frame,
            text="➕ 添加到队列",
            command=self.add_task_to_queue,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 11, "bold"),
            width=20,
            height=2
        ).pack()

        # === 下半部分：任务队列 ===
        queue_frame = tk.LabelFrame(self.window, text="任务队列", padx=10, pady=10)
        queue_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 工具栏
        toolbar = tk.Frame(queue_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            toolbar,
            text="0 个任务",
            font=("Arial", 10)
        ).pack(side=tk.LEFT)

        self.queue_count_label = tk.Label(
            toolbar,
            text="0 个任务",
            font=("Arial", 10)
        )
        self.queue_count_label.pack(side=tk.LEFT, padx=10)

        tk.Button(
            toolbar,
            text="🗑️ 清空队列",
            command=self.clear_queue,
            width=12
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(
            toolbar,
            text="🚀 启动所有任务",
            command=self.start_all_tasks,
            bg="#2196F3",
            fg="white",
            width=15
        ).pack(side=tk.RIGHT, padx=5)

        # 任务列表容器（可滚动）
        canvas = tk.Canvas(queue_frame, bg="white")
        scrollbar = ttk.Scrollbar(queue_frame, orient="vertical", command=canvas.yview)
        self.tasks_container = tk.Frame(canvas, bg="white")

        self.tasks_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.tasks_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def test_api_connection(self):
        """测试API连接"""
        def test():
            self.api_status_label.config(text="测试中...", fg="orange")

            import http.client
            api_key = self.api_key_var.get()
            base_url = self.base_url_var.get()
            model = self.model_var.get()

            if not api_key:
                self.api_status_label.config(text="❌ 请输入API Key", fg="red")
                return

            # 解析base_url
            if base_url.startswith("https://"):
                host = base_url.replace("https://", "").rstrip("/")
                path = "/v1/chat/completions" if "/v1" in base_url else "/chat/completions"
            else:
                host = base_url.replace("http://", "").rstrip("/")
                path = "/v1/chat/completions" if "/v1" in base_url else "/chat/completions"

            payload = json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            })

            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }

            try:
                conn = http.client.HTTPSConnection(host.split("/")[0])
                conn.request("POST", path, payload, headers)
                response = conn.getresponse()
                data = response.read().decode('utf-8')

                if response.status == 200:
                    self.api_status_label.config(text="✅ 连接成功", fg="green")
                else:
                    self.api_status_label.config(text=f"❌ HTTP {response.status}", fg="red")

                conn.close()
            except Exception as e:
                self.api_status_label.config(text=f"❌ {str(e)[:30]}", fg="red")

        threading.Thread(target=test, daemon=True).start()

    def manage_prompts(self):
        """打开Prompt管理窗口"""
        PromptPreviewWindow(self.window, self.prompt_mgr, prompt_type='writer')

    def select_outline_file(self):
        """选择单个大纲文件"""
        file_path = filedialog.askopenfilename(
            title="选择大纲JSON文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )

        if file_path:
            self.load_outline_file(file_path)

    def select_outline_folder(self):
        """选择文件夹（自动查找大纲JSON）"""
        folder_path = filedialog.askdirectory(title="选择大纲文件夹")

        if folder_path:
            # 查找文件夹中的JSON文件
            json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]

            if not json_files:
                messagebox.showwarning("警告", "文件夹中没有找到JSON文件")
                return

            if len(json_files) == 1:
                # 只有一个JSON文件，直接加载
                file_path = os.path.join(folder_path, json_files[0])
                self.load_outline_file(file_path)
            else:
                # 多个JSON文件，让用户选择
                choice = messagebox.askquestion(
                    "选择文件",
                    f"找到{len(json_files)}个JSON文件，选择第一个吗？\n{json_files[0]}"
                )
                if choice == 'yes':
                    file_path = os.path.join(folder_path, json_files[0])
                    self.load_outline_file(file_path)

    def load_outline_file(self, file_path):
        """加载大纲文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.current_outline_data = json.load(f)

            self.current_outline_file = file_path

            # 显示信息
            outline = self.current_outline_data.get('outline', {})
            title = outline.get('title', '未知')
            genre = outline.get('genre', '未知')
            chapters = len(outline.get('chapter_outlines', []))

            self.file_label.config(
                text=os.path.basename(file_path),
                fg="black"
            )

            self.outline_info_label.config(
                text=f"📖 {title} | {genre} | {chapters}章"
            )

            # 自动设置章节范围
            self.start_chapter_var.set(1)
            self.end_chapter_var.set(chapters)

            messagebox.showinfo("成功", f"已加载大纲：\n书名: {title}\n类型: {genre}\n章节: {chapters}章")

        except Exception as e:
            messagebox.showerror("错误", f"加载大纲文件失败：\n{str(e)}")

    def add_task_to_queue(self):
        """添加任务到队列"""
        if not self.current_outline_file:
            messagebox.showwarning("警告", "请先选择大纲文件")
            return

        # 生成任务ID
        task_id = str(uuid.uuid4())[:8]

        # 创建任务配置
        config_params = {
            'api_key': self.api_key_var.get(),
            'base_url': self.base_url_var.get(),
            'model': self.model_var.get(),
            'temperature': self.temperature_var.get(),
            'max_tokens': self.max_tokens_var.get(),
            'parallel_count': self.parallel_count_var.get(),
            'chapters_per_batch': self.chapters_per_batch_var.get()
        }

        # 创建任务
        task = WriterTask(
            task_id=task_id,
            outline_file=self.current_outline_file,
            start_chapter=self.start_chapter_var.get(),
            end_chapter=self.end_chapter_var.get(),
            config_params=config_params
        )

        self.tasks.append(task)
        self.create_task_widget(task)
        self.update_queue_count()

        messagebox.showinfo("成功", f"任务已添加到队列\nID: {task_id}")

    def create_task_widget(self, task):
        """创建任务显示组件"""
        # 任务框架
        task_frame = tk.Frame(
            self.tasks_container,
            relief=tk.RAISED,
            borderwidth=2,
            bg="#f0f0f0"
        )
        task_frame.pack(fill=tk.X, padx=5, pady=5)

        # 头部
        header_frame = tk.Frame(task_frame, bg="#e0e0e0")
        header_frame.pack(fill=tk.X)

        # 任务信息
        outline = self.current_outline_data.get('outline', {})
        title = outline.get('title', '未知')
        genre = outline.get('genre', '未知')

        info_text = f"📖 {title} | {genre} | 第{task.start_chapter}-{task.end_chapter}章"

        tk.Label(
            header_frame,
            text=info_text,
            font=("Arial", 10, "bold"),
            bg="#e0e0e0",
            anchor=tk.W
        ).pack(side=tk.LEFT, padx=10, pady=5)

        # 状态标签
        status_label = tk.Label(
            header_frame,
            text="⏸️ 等待中",
            font=("Arial", 9),
            bg="#e0e0e0",
            fg="gray"
        )
        status_label.pack(side=tk.RIGHT, padx=10, pady=5)

        # 进度条
        progress_bar = ttk.Progressbar(
            task_frame,
            orient="horizontal",
            length=300,
            mode="determinate"
        )
        progress_bar.pack(fill=tk.X, padx=10, pady=5)

        # 按钮区域
        btn_frame = tk.Frame(task_frame, bg="#f0f0f0")
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        # 开始按钮
        start_btn = tk.Button(
            btn_frame,
            text="▶️ 开始",
            command=lambda: self.start_task(task),
            bg="#4CAF50",
            fg="white",
            width=10
        )
        start_btn.pack(side=tk.LEFT, padx=2)

        # 预览Prompt按钮
        tk.Button(
            btn_frame,
            text="👁️ 预览Prompt",
            command=lambda: self.preview_prompt(task),
            width=12
        ).pack(side=tk.LEFT, padx=2)

        # 打开输出目录按钮
        open_dir_btn = tk.Button(
            btn_frame,
            text="📂 打开目录",
            command=lambda: self.open_output_directory(task),
            width=10,
            state=tk.DISABLED
        )
        open_dir_btn.pack(side=tk.LEFT, padx=2)

        # 删除按钮
        tk.Button(
            btn_frame,
            text="🗑️ 删除",
            command=lambda: self.remove_task(task),
            width=8
        ).pack(side=tk.RIGHT, padx=2)

        # 保存widget引用
        self.task_frames[task.task_id] = {
            'frame': task_frame,
            'status_label': status_label,
            'progress_bar': progress_bar,
            'start_btn': start_btn,
            'open_dir_btn': open_dir_btn
        }

    def preview_prompt(self, task):
        """预览任务的Prompt"""
        try:
            # 加载大纲数据
            with open(task.outline_file, 'r', encoding='utf-8') as f:
                outline_data = json.load(f)

            outline = outline_data.get('outline', {})

            # 构建prompt变量
            prompt_vars = {
                'genre': outline.get('genre', 'Fiction'),
                'style': outline_data.get('style', ''),
                'world_setting': outline.get('world_setting', ''),
                'characters': self.format_characters(outline.get('main_characters', [])),
                'start_chapter': task.start_chapter,
                'end_chapter': task.end_chapter,
                'chapter_outlines': self.format_chapter_outlines(
                    outline.get('chapter_outlines', []),
                    task.start_chapter,
                    task.end_chapter
                ),
                'previous_context': ''
            }

            # 渲染prompt
            prompt = self.prompt_mgr.render_writer_prompt(prompt_vars)

            # 显示预览窗口
            preview_window = tk.Toplevel(self.window)
            preview_window.title(f"Prompt预览 - 任务 {task.task_id}")
            preview_window.geometry("800x600")

            text_area = scrolledtext.ScrolledText(
                preview_window,
                wrap=tk.WORD,
                font=("Courier", 9)
            )
            text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_area.insert(tk.END, prompt)
            text_area.config(state=tk.DISABLED)

        except Exception as e:
            messagebox.showerror("错误", f"生成Prompt预览失败：\n{str(e)}")

    def format_characters(self, characters):
        """格式化角色信息"""
        result = []
        for char in characters:
            result.append(f"- {char.get('name', '')} ({char.get('gender', '')})")
            result.append(f"  Role: {char.get('role', '')}")
            result.append(f"  Personality: {char.get('personality', '')}")
            result.append(f"  Background: {char.get('background', '')}")
        return '\n'.join(result)

    def format_chapter_outlines(self, chapter_outlines, start, end):
        """格式化章节大纲"""
        result = []
        for ch in chapter_outlines:
            ch_num = ch.get('chapter_number', 0)
            if start <= ch_num <= end:
                result.append(f"Chapter {ch_num}: {ch.get('title', '')}")
                result.append(f"Summary: {ch.get('summary', '')}")
                if ch.get('key_events'):
                    result.append(f"Key Events: {', '.join(ch['key_events'])}")
                if ch.get('characters_involved'):
                    result.append(f"Characters: {', '.join(ch['characters_involved'])}")
                result.append("")
        return '\n'.join(result)

    def open_output_directory(self, task):
        """打开输出目录"""
        if task.output_folder and os.path.exists(task.output_folder):
            if sys.platform == 'win32':
                os.startfile(task.output_folder)
            elif sys.platform == 'darwin':
                subprocess.run(['open', task.output_folder])
            else:
                subprocess.run(['xdg-open', task.output_folder])
        else:
            messagebox.showinfo("提示", "输出目录尚未生成")

    def remove_task(self, task):
        """删除任务"""
        if task.status == 'running':
            if not messagebox.askyesno("确认", "任务正在运行，确定要删除吗？"):
                return

            # 停止进程
            if task.task_id in self.running_processes:
                process = self.running_processes[task.task_id]
                process.terminate()
                del self.running_processes[task.task_id]

        # 删除widget
        if task.task_id in self.task_frames:
            self.task_frames[task.task_id]['frame'].destroy()
            del self.task_frames[task.task_id]

        # 删除任务
        self.tasks.remove(task)
        self.update_queue_count()

    def clear_queue(self):
        """清空队列"""
        if not self.tasks:
            return

        if messagebox.askyesno("确认", f"确定要清空所有 {len(self.tasks)} 个任务吗？"):
            # 停止所有运行中的任务
            for task in self.tasks:
                if task.task_id in self.running_processes:
                    process = self.running_processes[task.task_id]
                    process.terminate()

            # 清空
            for task_id in list(self.task_frames.keys()):
                self.task_frames[task_id]['frame'].destroy()

            self.tasks = []
            self.task_frames = {}
            self.running_processes = {}
            self.update_queue_count()

    def start_task(self, task):
        """启动单个任务"""
        if task.status == 'running':
            messagebox.showinfo("提示", "任务已在运行中")
            return

        # 更新状态
        task.status = 'running'
        task.started_at = datetime.now()

        widgets = self.task_frames[task.task_id]
        widgets['status_label'].config(text="🔄 运行中", fg="blue")
        widgets['start_btn'].config(state=tk.DISABLED)

        # 创建任务配置文件
        self.create_task_config(task)

        # 启动独立进程
        self.launch_writer_worker(task)

    def create_task_config(self, task):
        """创建任务配置文件"""
        task_dir = f'tasks/{task.task_id}'
        os.makedirs(task_dir, exist_ok=True)

        config = {
            'task_type': 'writer',
            'task_id': task.task_id,
            'outline_file': task.outline_file,
            'start_chapter': task.start_chapter,
            'end_chapter': task.end_chapter,
            'api_key': task.config['api_key'],
            'base_url': task.config['base_url'],
            'model': task.config['model'],
            'temperature': task.config['temperature'],
            'max_tokens': task.config['max_tokens'],
            'parallel_count': task.config['parallel_count'],
            'chapters_per_batch': task.config['chapters_per_batch']
        }

        config_file = f'{task_dir}/config.json'
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        # 创建初始进度文件
        progress = {
            'task_id': task.task_id,
            'status': 'initializing',
            'message': '初始化中...',
            'current_chapter': task.start_chapter,
            'progress': 0,
            'updated_at': datetime.now().isoformat()
        }

        progress_file = f'{task_dir}/progress.json'
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, indent=2, ensure_ascii=False)

    def launch_writer_worker(self, task):
        """启动writer worker进程"""
        task_dir = f'tasks/{task.task_id}'
        config_file = f'{task_dir}/config.json'

        # 启动独立进程
        cmd = [
            sys.executable,
            'writer_worker.py',
            '--config', config_file,
            '--task-id', task.task_id
        ]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        self.running_processes[task.task_id] = process

    def start_all_tasks(self):
        """启动所有待处理的任务"""
        pending_tasks = [t for t in self.tasks if t.status == 'pending']

        if not pending_tasks:
            messagebox.showinfo("提示", "没有待处理的任务")
            return

        if messagebox.askyesno("确认", f"确定要启动 {len(pending_tasks)} 个任务吗？"):
            for task in pending_tasks:
                self.start_task(task)
                time.sleep(0.5)  # 避免同时启动太多

    def update_queue_count(self):
        """更新队列计数"""
        self.queue_count_label.config(text=f"{len(self.tasks)} 个任务")

    def start_polling(self):
        """开始轮询任务状态"""
        self.poll_task_status()

    def poll_task_status(self):
        """轮询任务状态"""
        for task in self.tasks:
            if task.status == 'running':
                self.update_task_status(task)

        # 每2秒轮询一次
        self.window.after(2000, self.poll_task_status)

    def update_task_status(self, task):
        """更新任务状态"""
        progress_file = f'tasks/{task.task_id}/progress.json'

        if not os.path.exists(progress_file):
            return

        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)

            status = progress.get('status', 'unknown')
            current_chapter = progress.get('current_chapter', task.start_chapter)
            progress_pct = progress.get('progress', 0)
            message = progress.get('message', '')
            output_folder = progress.get('output_folder', '')

            # 更新任务对象
            task.current_chapter = current_chapter
            task.progress = progress_pct
            if output_folder:
                task.output_folder = output_folder

            # 更新UI
            widgets = self.task_frames.get(task.task_id)
            if not widgets:
                return

            if status == 'completed':
                task.status = 'completed'
                task.completed_at = datetime.now()
                widgets['status_label'].config(text="✅ 完成", fg="green")
                widgets['progress_bar']['value'] = 100
                widgets['start_btn'].config(state=tk.NORMAL, text="✅ 完成")
                widgets['open_dir_btn'].config(state=tk.NORMAL)

            elif status == 'failed':
                task.status = 'failed'
                widgets['status_label'].config(text=f"❌ 失败", fg="red")
                widgets['start_btn'].config(state=tk.NORMAL, text="❌ 失败")

            elif status == 'generating':
                widgets['status_label'].config(
                    text=f"🔄 第{current_chapter}章 ({progress_pct}%)",
                    fg="blue"
                )
                widgets['progress_bar']['value'] = progress_pct
                if output_folder:
                    widgets['open_dir_btn'].config(state=tk.NORMAL)

        except Exception as e:
            print(f"更新任务状态失败: {str(e)}")

    def run(self):
        """运行应用"""
        self.window.mainloop()


def main():
    """主函数"""
    app = NovelWriterApp()
    app.run()


if __name__ == '__main__':
    main()
