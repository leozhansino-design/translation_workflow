#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小说生成器 - 主应用（参考工作代码重写）
支持从文件夹自动抓取prompts，断点续写
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


# 固定的SYSTEM_PROMPT（参考用户代码）
SYSTEM_PROMPT = """You are a web novel writer. Write addictive English web fiction.

【RULES】
1. English ONLY - No Chinese names/places
2. Each chapter: 15,000-20,000 words
3. Include 3-5 "爽点" per chapter:
   - Victories, face-slapping, power-ups
   - Romantic moments, revelations
   - Plot twists, justice served

【STYLE: 短平快】
- Short sentences (10-15 words)
- Short paragraphs (1-3 sentences)
- Fast pacing (event every 200-300 words)
- Mobile-friendly

【STRUCTURE】
Opening: Action/tension immediately
Development: 2-3 scenes with 爽点
Climax: Biggest 爽点
Hook: Cliffhanger ending

【LOCALIZATION】
Names: Emma, Lucas, Ethan (Western)
Places: Manhattan, London, Seattle
Culture: Western only

【DIALOGUE】
Short, punchy exchanges:
"You're fired." He grinned.
She smiled. "Check your email."
His face went pale.

Write addictive entertainment. START NOW."""


class WriterTask:
    """写作任务"""

    def __init__(self, task_id, prompt_folder, batch_size, config_params):
        self.task_id = task_id
        self.prompt_folder = prompt_folder
        self.batch_size = batch_size
        self.config = config_params
        self.status = 'pending'
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.output_folder = None
        self.current_chapter = 1
        self.total_chapters = 0
        self.current_batch = 0
        self.total_batches = 0
        self.progress = 0
        self.title = ""
        self.category = ""

    def to_dict(self):
        return {
            'task_id': self.task_id,
            'prompt_folder': self.prompt_folder,
            'batch_size': self.batch_size,
            'config': self.config,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'output_folder': self.output_folder,
            'current_chapter': self.current_chapter,
            'total_chapters': self.total_chapters,
            'progress': self.progress
        }


class NovelWriterApp:
    """小说生成器主应用"""

    def __init__(self):
        self.window = tk.Tk()
        self.window.title("小说生成器 - 自动批次生成")
        self.window.geometry("1200x900")

        # 任务队列
        self.tasks = []
        self.task_frames = {}
        self.running_processes = {}

        # 当前选择
        self.current_prompt_folder = None
        self.current_prompt_data = None

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
            text="✍️ 小说生成器 - 自动批次生成",
            font=("Arial", 20, "bold"),
            bg="#FF6B6B",
            fg="white"
        ).pack(side=tk.LEFT, padx=20, pady=10)

        # === 配置区域 ===
        config_container = tk.Frame(self.window)
        config_container.pack(fill=tk.X, padx=10, pady=10)

        # API配置
        api_frame = tk.LabelFrame(config_container, text="API 配置", padx=15, pady=10)
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
        models = ["gpt-5-mini", "gpt-5.1", "gemini-2.5-pro", "gpt-5", "claude-3.5-sonnet"]
        model_combo = ttk.Combobox(
            api_frame,
            textvariable=self.model_var,
            values=models,
            width=20
        )
        model_combo.grid(row=1, column=3, sticky=tk.W, pady=5, padx=5)

        # 任务配置
        task_frame = tk.LabelFrame(config_container, text="新建任务", padx=15, pady=10)
        task_frame.pack(fill=tk.X)

        # 第一行：文件夹选择
        tk.Label(task_frame, text="Prompt文件夹:", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, pady=5
        )

        file_select_frame = tk.Frame(task_frame)
        file_select_frame.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5, columnspan=3)

        self.folder_label = tk.Label(
            file_select_frame,
            text="未选择文件夹（需包含_writing_prompt.txt和chapter_X_prompt.txt）",
            fg="gray",
            font=("Arial", 9)
        )
        self.folder_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(
            file_select_frame,
            text="选择文件夹",
            command=self.select_prompt_folder
        ).pack(side=tk.LEFT, padx=5)

        self.folder_info_label = tk.Label(file_select_frame, text="", fg="blue", font=("Arial", 9, "bold"))
        self.folder_info_label.pack(side=tk.LEFT, padx=10)

        # 第二行：批次大小和参数
        tk.Label(task_frame, text="每批章节数:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.batch_size_var = tk.IntVar(value=3)
        tk.Spinbox(
            task_frame,
            from_=1,
            to=5,
            textvariable=self.batch_size_var,
            width=10
        ).grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)

        tk.Label(task_frame, text="Temperature:").grid(row=1, column=2, sticky=tk.W, pady=5, padx=(20, 5))
        self.temperature_var = tk.DoubleVar(value=0.85)
        tk.Scale(
            task_frame,
            from_=0,
            to=1,
            resolution=0.05,
            orient=tk.HORIZONTAL,
            variable=self.temperature_var,
            length=150
        ).grid(row=1, column=3, sticky=tk.W, pady=5, padx=5)

        tk.Label(task_frame, text="Max Tokens:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.max_tokens_var = tk.IntVar(value=120000)
        tk.Spinbox(
            task_frame,
            from_=32000,
            to=200000,
            increment=16000,
            textvariable=self.max_tokens_var,
            width=10
        ).grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)

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

        # === 任务队列 ===
        queue_frame = tk.LabelFrame(self.window, text="任务队列", padx=10, pady=10)
        queue_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 工具栏
        toolbar = tk.Frame(queue_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))

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
                if "/v1" in host:
                    path = "/chat/completions"
                    host = host.split("/v1")[0]
                else:
                    path = "/v1/chat/completions"
            else:
                host = base_url.replace("http://", "").rstrip("/")
                if "/v1" in host:
                    path = "/chat/completions"
                    host = host.split("/v1")[0]
                else:
                    path = "/v1/chat/completions"

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
                conn = http.client.HTTPSConnection(host)
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

    def select_prompt_folder(self):
        """选择prompt文件夹"""
        folder_path = filedialog.askdirectory(title="选择Prompt文件夹")

        if folder_path:
            self.load_prompt_folder(folder_path)

    def load_prompt_folder(self, folder_path):
        """加载prompt文件夹（参考用户代码）"""
        try:
            folder = Path(folder_path)

            if not folder.exists():
                messagebox.showerror("错误", f"文件夹不存在: {folder_path}")
                return

            data = {
                'writing_prompt': '',
                'title': '',
                'category': '',
                'chapters': {}
            }

            # 读取_writing_prompt.txt（必需）
            writing_prompt_file = folder / '_writing_prompt.txt'
            if not writing_prompt_file.exists():
                messagebox.showerror("错误", "找不到 _writing_prompt.txt（必需文件）")
                return

            with open(writing_prompt_file, 'r', encoding='utf-8') as f:
                data['writing_prompt'] = f.read().strip()

            # 读取可选文件
            title_file = folder / 'title.txt'
            if title_file.exists():
                with open(title_file, 'r', encoding='utf-8') as f:
                    data['title'] = f.read().strip()

            category_file = folder / 'category.txt'
            if category_file.exists():
                with open(category_file, 'r', encoding='utf-8') as f:
                    data['category'] = f.read().strip()

            # 读取所有章节prompts
            chapter_files = sorted(folder.glob('chapter_*_prompt.txt'))
            for chapter_file in chapter_files:
                filename = chapter_file.name
                try:
                    chapter_num = int(filename.split('_')[1])
                    with open(chapter_file, 'r', encoding='utf-8') as f:
                        data['chapters'][chapter_num] = f.read().strip()
                except (IndexError, ValueError):
                    continue

            if not data['chapters']:
                messagebox.showerror("错误", "没有找到章节prompt文件 (chapter_X_prompt.txt)")
                return

            # 保存数据
            self.current_prompt_folder = folder_path
            self.current_prompt_data = data

            # 显示信息
            total_chapters = len(data['chapters'])
            self.folder_label.config(
                text=os.path.basename(folder_path),
                fg="black"
            )

            info_text = f"📖 {total_chapters}章"
            if data['title']:
                info_text = f"📖 {data['title'][:30]}... | {total_chapters}章"
            if data['category']:
                info_text += f" | {data['category']}"

            self.folder_info_label.config(text=info_text)

            messagebox.showinfo(
                "成功",
                f"已加载Prompt文件夹：\n"
                f"书名: {data['title'] or '未知'}\n"
                f"类型: {data['category'] or '未知'}\n"
                f"章节: {total_chapters}章"
            )

        except Exception as e:
            messagebox.showerror("错误", f"加载文件夹失败：\n{str(e)}")

    def add_task_to_queue(self):
        """添加任务到队列"""
        if not self.current_prompt_folder:
            messagebox.showwarning("警告", "请先选择Prompt文件夹")
            return

        # 生成任务ID
        task_id = str(uuid.uuid4())[:8]

        # 创建任务配置
        config_params = {
            'api_key': self.api_key_var.get(),
            'base_url': self.base_url_var.get(),
            'model': self.model_var.get(),
            'temperature': self.temperature_var.get(),
            'max_tokens': self.max_tokens_var.get()
        }

        # 创建任务
        task = WriterTask(
            task_id=task_id,
            prompt_folder=self.current_prompt_folder,
            batch_size=self.batch_size_var.get(),
            config_params=config_params
        )

        task.total_chapters = len(self.current_prompt_data['chapters'])
        task.total_batches = (task.total_chapters + task.batch_size - 1) // task.batch_size
        task.title = self.current_prompt_data.get('title', '未知')
        task.category = self.current_prompt_data.get('category', '未知')

        self.tasks.append(task)
        self.create_task_widget(task)
        self.update_queue_count()

        messagebox.showinfo("成功", f"任务已添加到队列\nID: {task_id}\n预计{task.total_batches}批次")

    def create_task_widget(self, task):
        """创建任务显示组件"""
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

        info_text = f"📖 {task.title} | {task.category} | {task.total_chapters}章 | 每批{task.batch_size}章"

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

        # 进度信息
        progress_info_label = tk.Label(
            task_frame,
            text=f"批次: 0/{task.total_batches} | 章节: 0/{task.total_chapters}",
            font=("Arial", 9),
            bg="#f0f0f0",
            anchor=tk.W
        )
        progress_info_label.pack(fill=tk.X, padx=10, pady=2)

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

        start_btn = tk.Button(
            btn_frame,
            text="▶️ 开始",
            command=lambda: self.start_task(task),
            bg="#4CAF50",
            fg="white",
            width=10
        )
        start_btn.pack(side=tk.LEFT, padx=2)

        tk.Button(
            btn_frame,
            text="👁️ 预览Prompt",
            command=lambda: self.preview_prompt(task),
            width=12
        ).pack(side=tk.LEFT, padx=2)

        open_dir_btn = tk.Button(
            btn_frame,
            text="📂 打开目录",
            command=lambda: self.open_output_directory(task),
            width=10,
            state=tk.DISABLED
        )
        open_dir_btn.pack(side=tk.LEFT, padx=2)

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
            'progress_info_label': progress_info_label,
            'start_btn': start_btn,
            'open_dir_btn': open_dir_btn
        }

    def preview_prompt(self, task):
        """预览任务的Prompt（第一批次）"""
        try:
            # 加载prompt数据
            folder = Path(task.prompt_folder)

            # 读取_writing_prompt.txt
            with open(folder / '_writing_prompt.txt', 'r', encoding='utf-8') as f:
                writing_prompt = f.read().strip()

            # 读取第一批章节prompts
            chapter_nums = sorted([int(f.stem.split('_')[1]) for f in folder.glob('chapter_*_prompt.txt')])
            first_batch_nums = chapter_nums[:task.batch_size]

            chapter_prompts = []
            for num in first_batch_nums:
                with open(folder / f'chapter_{num}_prompt.txt', 'r', encoding='utf-8') as f:
                    chapter_prompts.append((num, f.read().strip()))

            # 构建完整prompt（参考用户代码）
            prompt_parts = []

            prompt_parts.append("="*70)
            prompt_parts.append("SYSTEM PROMPT（固定）")
            prompt_parts.append("="*70)
            prompt_parts.append(SYSTEM_PROMPT)
            prompt_parts.append("\n" + "="*70)
            prompt_parts.append("USER PROMPT")
            prompt_parts.append("="*70)

            prompt_parts.append("\n【写作要求】")
            prompt_parts.append(writing_prompt)
            prompt_parts.append("\n" + "="*60)

            prompt_parts.append("\n【本批次章节大纲】")
            for ch_num, prompt in chapter_prompts:
                prompt_parts.append(f"\n===== 第{ch_num}章 =====")
                prompt_parts.append(prompt)

            prompt_parts.append("\n" + "="*60)
            prompt_parts.append(f"\n现在写第{first_batch_nums[0]}-{first_batch_nums[-1]}章。")
            prompt_parts.append(f"要求：每章15,000-20,000英文单词，只输出小说正文。")
            prompt_parts.append("\n开始写作：")

            full_prompt = "\n".join(prompt_parts)

            # 显示预览窗口
            preview_window = tk.Toplevel(self.window)
            preview_window.title(f"Prompt预览（第一批次） - 任务 {task.task_id}")
            preview_window.geometry("900x700")

            text_area = scrolledtext.ScrolledText(
                preview_window,
                wrap=tk.WORD,
                font=("Courier", 9)
            )
            text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_area.insert(tk.END, full_prompt)
            text_area.config(state=tk.DISABLED)

        except Exception as e:
            messagebox.showerror("错误", f"生成Prompt预览失败：\n{str(e)}")

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

            if task.task_id in self.running_processes:
                process = self.running_processes[task.task_id]
                process.terminate()
                del self.running_processes[task.task_id]

        if task.task_id in self.task_frames:
            self.task_frames[task.task_id]['frame'].destroy()
            del self.task_frames[task.task_id]

        self.tasks.remove(task)
        self.update_queue_count()

    def clear_queue(self):
        """清空队列"""
        if not self.tasks:
            return

        if messagebox.askyesno("确认", f"确定要清空所有 {len(self.tasks)} 个任务吗？"):
            for task in self.tasks:
                if task.task_id in self.running_processes:
                    process = self.running_processes[task.task_id]
                    process.terminate()

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
            'prompt_folder': task.prompt_folder,
            'batch_size': task.batch_size,
            'api_key': task.config['api_key'],
            'base_url': task.config['base_url'],
            'model': task.config['model'],
            'temperature': task.config['temperature'],
            'max_tokens': task.config['max_tokens']
        }

        config_file = f'{task_dir}/config.json'
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        # 创建初始进度文件
        progress = {
            'task_id': task.task_id,
            'status': 'initializing',
            'message': '初始化中...',
            'current_chapter': 1,
            'current_batch': 0,
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
                time.sleep(0.5)

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
            current_batch = progress.get('current_batch', 0)
            current_chapter = progress.get('current_chapter', 1)
            progress_pct = progress.get('progress', 0)
            output_folder = progress.get('output_folder', '')

            task.current_batch = current_batch
            task.current_chapter = current_chapter
            task.progress = progress_pct
            if output_folder:
                task.output_folder = output_folder

            widgets = self.task_frames.get(task.task_id)
            if not widgets:
                return

            if status == 'completed':
                task.status = 'completed'
                task.completed_at = datetime.now()
                widgets['status_label'].config(text="✅ 完成", fg="green")
                widgets['progress_bar']['value'] = 100
                widgets['progress_info_label'].config(
                    text=f"批次: {task.total_batches}/{task.total_batches} | 章节: {task.total_chapters}/{task.total_chapters} | ✅ 完成"
                )
                widgets['start_btn'].config(state=tk.NORMAL, text="✅ 完成")
                widgets['open_dir_btn'].config(state=tk.NORMAL)

            elif status == 'failed':
                task.status = 'failed'
                widgets['status_label'].config(text=f"❌ 失败", fg="red")
                widgets['start_btn'].config(state=tk.NORMAL, text="❌ 失败")

            elif status == 'generating':
                widgets['status_label'].config(
                    text=f"🔄 批次{current_batch}/{task.total_batches}",
                    fg="blue"
                )
                widgets['progress_bar']['value'] = progress_pct
                widgets['progress_info_label'].config(
                    text=f"批次: {current_batch}/{task.total_batches} | 章节: {current_chapter}/{task.total_chapters} | {progress_pct}%"
                )
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
