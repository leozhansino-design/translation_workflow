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

# 修复Mac上的SSL证书验证问题 - 全局设置
import ssl
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except AttributeError:
    pass

from config import config
from resource_mgr import ResourceManager
from prompt_manager import PromptManager
from universal_api import UniversalAPIClient
from utils import (
    extract_genre_from_filename,
    extract_title_from_filename,
    validate_genre,
    parse_json_from_llm_response,
    get_work_directory
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


class CoverTask:
    """封面生成任务"""

    def __init__(self, task_id, outline_folder, title, genre, blurb, config_params):
        self.task_id = task_id
        self.outline_folder = outline_folder
        self.title = title
        self.genre = genre
        self.blurb = blurb
        self.config = config_params
        self.status = 'pending'  # pending, running, completed, failed
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.cover_path = None
        self.prompt_cache = None  # 缓存生成的prompt

    def to_dict(self):
        return {
            'task_id': self.task_id,
            'outline_folder': self.outline_folder,
            'title': self.title,
            'genre': self.genre,
            'blurb': self.blurb,
            'config': self.config,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'cover_path': self.cover_path
        }


class OutlineGeneratorWithQueue:
    """大纲生成器（带任务队列）"""

    def __init__(self):
        self.window = tk.Tk()
        self.window.title("大纲生成器 - 多任务队列")
        self.window.geometry("1400x1000")

        # 初始化管理器
        self.resource_mgr = ResourceManager()
        self.prompt_mgr = PromptManager()

        # 任务队列
        self.tasks = []  # 大纲任务列表
        self.task_frames = {}  # task_id -> frame widget

        # 封面任务队列
        self.cover_tasks = []  # 封面任务列表
        self.cover_task_frames = {}  # cover_task_id -> frame widget

        # 分页设置
        self.outline_current_page = 0  # 大纲当前页
        self.cover_current_page = 0  # 封面当前页
        self.tasks_per_page = 8  # 每页任务数

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

        tk.Button(
            api_frame,
            text="测试Gemini",
            command=self.test_gemini_simple,
            width=12,
            bg="#FF9800",
            fg="black"
        ).grid(row=0, column=3, pady=5, padx=5)

        self.api_status_label = tk.Label(api_frame, text="", fg="gray")
        self.api_status_label.grid(row=0, column=4, pady=5, padx=5)

        # 第二行：模型和Prompt管理
        tk.Label(api_frame, text="模型:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.model_var = tk.StringVar(value="gpt-5.1")
        models = ["gpt-5.1", "gpt-5-mini", "gemini-2.5-pro", "gemini-3-pro-preview"]
        model_combo = ttk.Combobox(
            api_frame,
            textvariable=self.model_var,
            values=models,
            width=20
        )
        model_combo.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)

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
            text="📂 选择文件",
            command=self.select_file
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            file_select_frame,
            text="📁 批量添加",
            command=self.batch_add_files,
            bg="#4CAF50",
            fg="white"
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

        # 批量章节范围（用于批量添加时随机选择）
        tk.Label(task_frame, text="批量章节范围:", fg="#666").grid(row=2, column=2, sticky=tk.W, pady=5, padx=(20, 5))

        range_frame = tk.Frame(task_frame)
        range_frame.grid(row=2, column=3, sticky=tk.W, pady=5, padx=5)

        self.batch_chapter_min_var = tk.IntVar(value=20)
        tk.Spinbox(
            range_frame,
            from_=5,
            to=200,
            increment=5,
            textvariable=self.batch_chapter_min_var,
            width=5
        ).pack(side=tk.LEFT)

        tk.Label(range_frame, text="-").pack(side=tk.LEFT, padx=2)

        self.batch_chapter_max_var = tk.IntVar(value=30)
        tk.Spinbox(
            range_frame,
            from_=5,
            to=200,
            increment=5,
            textvariable=self.batch_chapter_max_var,
            width=5
        ).pack(side=tk.LEFT)

        tk.Label(task_frame, text="Max Tokens:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.max_tokens_var = tk.IntVar(value=100000)
        tk.Spinbox(
            task_frame,
            from_=10000,
            to=200000,
            increment=10000,
            textvariable=self.max_tokens_var,
            width=12
        ).grid(row=3, column=1, sticky=tk.W, pady=5, padx=5)

        # 第四行：添加到队列按钮
        button_frame = tk.Frame(task_frame)
        button_frame.grid(row=4, column=0, columnspan=4, pady=10)

        tk.Button(
            button_frame,
            text="➕ 添加到任务队列",
            command=self.add_to_queue,
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="black",
            height=2,
            width=20
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            button_frame,
            text="📥 导入网页版大纲",
            command=self.import_web_outline,
            font=("Arial", 12, "bold"),
            bg="#2196F3",
            fg="black",
            height=2,
            width=20
        ).pack(side=tk.LEFT, padx=10)

        # === 封面生成区域 ===
        cover_frame = tk.LabelFrame(top_container, text="🎨 封面生成", padx=15, pady=10)
        cover_frame.pack(fill=tk.X, pady=(10, 0))

        # 文件夹选择
        tk.Label(cover_frame, text="Outline文件夹:", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, pady=5
        )

        folder_select_frame = tk.Frame(cover_frame)
        folder_select_frame.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5, columnspan=3)

        self.cover_folders_label = tk.Label(
            folder_select_frame,
            text="未选择（可多选）",
            fg="gray",
            font=("Arial", 9)
        )
        self.cover_folders_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(
            folder_select_frame,
            text="➕ 添加文件夹",
            command=self.add_cover_folder
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            folder_select_frame,
            text="📁 批量添加",
            command=self.add_cover_folder_batch,
            bg="#4CAF50",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            folder_select_frame,
            text="🗑️ 清空",
            command=self.clear_cover_folders
        ).pack(side=tk.LEFT, padx=5)

        # 生成按钮和状态
        button_status_frame = tk.Frame(cover_frame)
        button_status_frame.grid(row=1, column=0, columnspan=4, pady=10)

        tk.Button(
            button_status_frame,
            text="📝 Prompt管理",
            command=self.manage_cover_prompts,
            font=("Arial", 11, "bold"),
            bg="#2196F3",
            fg="black",
            height=2,
            width=15
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_status_frame,
            text="👁️ 预览Prompt",
            command=self.preview_cover_prompt,
            font=("Arial", 11, "bold"),
            bg="#FF9800",
            fg="black",
            height=2,
            width=15
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_status_frame,
            text="🎨 生成封面",
            command=self.generate_covers,
            font=("Arial", 12, "bold"),
            bg="#9C27B0",
            fg="black",
            height=2,
            width=20
        ).pack(side=tk.LEFT, padx=10)

        self.cover_status_label = tk.Label(button_status_frame, text="", fg="gray", font=("Arial", 10))
        self.cover_status_label.pack(side=tk.LEFT, padx=10)

        # 初始化封面生成变量
        self.cover_folders = []

        # === 下半部分：任务队列（双列布局）===
        queue_container = tk.LabelFrame(
            self.window,
            text="📋 任务队列",
            font=("Arial", 12, "bold"),
            padx=10,
            pady=10
        )
        queue_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建双列容器
        columns_frame = tk.Frame(queue_container)
        columns_frame.pack(fill=tk.BOTH, expand=True)

        # === 左列：大纲生成任务 ===
        outline_column = tk.Frame(columns_frame, bg="#f0f0f0", relief=tk.RIDGE, borderwidth=1)
        outline_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # 左列标题和工具栏
        outline_header = tk.Frame(outline_column, bg="#2196F3")
        outline_header.pack(fill=tk.X)

        tk.Label(
            outline_header,
            text="📝 大纲生成",
            font=("Arial", 11, "bold"),
            bg="#2196F3",
            fg="white"
        ).pack(side=tk.LEFT, padx=10, pady=5)

        tk.Button(
            outline_header,
            text="🗑️ 清空",
            command=self.clear_outline_tasks,
            bg="#f44336",
            fg="white",
            width=8,
            font=("Arial", 8)
        ).pack(side=tk.RIGHT, padx=5, pady=5)

        tk.Button(
            outline_header,
            text="▶️ 全部开始",
            command=self.start_all_outline_tasks,
            bg="#4CAF50",
            fg="white",
            width=10,
            font=("Arial", 8)
        ).pack(side=tk.RIGHT, padx=5, pady=5)

        # 大纲分页控制
        outline_pagination = tk.Frame(outline_column, bg="#e0e0e0")
        outline_pagination.pack(fill=tk.X, padx=2, pady=2)

        tk.Button(outline_pagination, text="◀", command=self.outline_previous_page, width=3).pack(side=tk.LEFT, padx=2)
        self.outline_page_label = tk.Label(outline_pagination, text="1/1 页", bg="#e0e0e0", font=("Arial", 8))
        self.outline_page_label.pack(side=tk.LEFT, padx=10, expand=True)
        tk.Button(outline_pagination, text="▶", command=self.outline_next_page, width=3).pack(side=tk.RIGHT, padx=2)

        # 左列滚动区域
        outline_canvas = tk.Canvas(outline_column, bg="white")
        outline_scrollbar = ttk.Scrollbar(outline_column, orient="vertical", command=outline_canvas.yview)

        self.queue_frame = tk.Frame(outline_canvas, bg="white")

        self.queue_frame.bind(
            "<Configure>",
            lambda e: outline_canvas.configure(scrollregion=outline_canvas.bbox("all"))
        )

        outline_canvas.create_window((0, 0), window=self.queue_frame, anchor="nw")
        outline_canvas.configure(yscrollcommand=outline_scrollbar.set)

        outline_canvas.pack(side="left", fill="both", expand=True)
        outline_scrollbar.pack(side="right", fill="y")

        # 左列空队列提示
        self.empty_label = tk.Label(
            self.queue_frame,
            text="暂无大纲任务\n点击上方「添加到任务队列」",
            font=("Arial", 10),
            fg="gray",
            bg="white",
            pady=30
        )
        self.empty_label.pack()

        # === 右列：封面生成任务 ===
        cover_column = tk.Frame(columns_frame, bg="#f0f0f0", relief=tk.RIDGE, borderwidth=1)
        cover_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # 右列标题和工具栏
        cover_header = tk.Frame(cover_column, bg="#9C27B0")
        cover_header.pack(fill=tk.X)

        tk.Label(
            cover_header,
            text="🎨 封面生成",
            font=("Arial", 11, "bold"),
            bg="#9C27B0",
            fg="white"
        ).pack(side=tk.LEFT, padx=10, pady=5)

        tk.Button(
            cover_header,
            text="🗑️ 清空",
            command=self.clear_cover_tasks,
            bg="#f44336",
            fg="white",
            width=8,
            font=("Arial", 8)
        ).pack(side=tk.RIGHT, padx=5, pady=5)

        tk.Button(
            cover_header,
            text="▶️ 全部开始",
            command=self.start_all_cover_tasks,
            bg="#4CAF50",
            fg="white",
            width=10,
            font=("Arial", 8)
        ).pack(side=tk.RIGHT, padx=5, pady=5)

        # 封面分页控制
        cover_pagination = tk.Frame(cover_column, bg="#e0e0e0")
        cover_pagination.pack(fill=tk.X, padx=2, pady=2)

        tk.Button(cover_pagination, text="◀", command=self.cover_previous_page, width=3).pack(side=tk.LEFT, padx=2)
        self.cover_page_label = tk.Label(cover_pagination, text="1/1 页", bg="#e0e0e0", font=("Arial", 8))
        self.cover_page_label.pack(side=tk.LEFT, padx=10, expand=True)
        tk.Button(cover_pagination, text="▶", command=self.cover_next_page, width=3).pack(side=tk.RIGHT, padx=2)

        # 右列滚动区域
        cover_canvas = tk.Canvas(cover_column, bg="white")
        cover_scrollbar = ttk.Scrollbar(cover_column, orient="vertical", command=cover_canvas.yview)

        self.cover_queue_frame = tk.Frame(cover_canvas, bg="white")

        self.cover_queue_frame.bind(
            "<Configure>",
            lambda e: cover_canvas.configure(scrollregion=cover_canvas.bbox("all"))
        )

        cover_canvas.create_window((0, 0), window=self.cover_queue_frame, anchor="nw")
        cover_canvas.configure(yscrollcommand=cover_scrollbar.set)

        cover_canvas.pack(side="left", fill="both", expand=True)
        cover_scrollbar.pack(side="right", fill="y")

        # 右列空队列提示
        self.cover_empty_label = tk.Label(
            self.cover_queue_frame,
            text="暂无封面任务\n从大纲任务中生成",
            font=("Arial", 10),
            fg="gray",
            bg="white",
            pady=30
        )
        self.cover_empty_label.pack()

    def select_file(self):
        """选择源文件"""
        file_path = filedialog.askopenfilename(
            title="选择原文文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if file_path:
            try:
                # 规范化路径 - 确保在Mac/Windows上都正确
                file_path = os.path.abspath(os.path.normpath(file_path))
                print(f"🔍 选择的文件: {file_path}")

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

    def batch_add_files(self):
        """批量添加文件到任务队列"""
        initial_dir = self._get_default_directory()

        folder = filedialog.askdirectory(
            title="选择包含小说文件的文件夹（格式：书名_类型.txt）",
            initialdir=initial_dir
        )

        if not folder:
            return

        folder = os.path.abspath(os.path.normpath(folder))
        print(f"\n📁 批量扫描文件夹: {folder}")

        # 获取章节范围
        min_chapters = self.batch_chapter_min_var.get()
        max_chapters = self.batch_chapter_max_var.get()

        if min_chapters > max_chapters:
            print(f"⚠️  章节范围错误: {min_chapters}-{max_chapters}")
            self.file_label.config(text="❌ 章节范围错误", fg="red")
            return

        # 扫描所有txt文件
        import glob
        import random
        from utils import extract_genre_from_filename, validate_genre

        txt_files = glob.glob(os.path.join(folder, "*.txt"))
        print(f"  扫描到 {len(txt_files)} 个 .txt 文件")

        valid_files = []
        skipped_files = []

        for file_path in txt_files:
            try:
                # 提取并验证类型
                genre = extract_genre_from_filename(file_path)
                available_genres = self.resource_mgr.get_available_genres()
                validate_genre(genre, available_genres)

                valid_files.append({
                    'path': file_path,
                    'genre': genre,
                    'name': os.path.basename(file_path)
                })
                print(f"  ✅ 找到: {os.path.basename(file_path)} ({genre})")

            except ValueError as e:
                print(f"  ⚠️  跳过: {os.path.basename(file_path)} - {e}")
                skipped_files.append(f"{os.path.basename(file_path)}: {str(e)}")

        print(f"\n扫描完成: 找到 {len(valid_files)} 个有效文件")

        if not valid_files:
            # 显示详细的错误信息
            if skipped_files:
                error_details = "\n".join(skipped_files[:5])  # 只显示前5个
                if len(skipped_files) > 5:
                    error_details += f"\n... 还有 {len(skipped_files) - 5} 个文件"
                messagebox.showwarning(
                    "未找到有效文件",
                    f"扫描了 {len(txt_files)} 个文件，都被跳过了\n\n"
                    f"跳过的文件:\n{error_details}\n\n"
                    f"文件格式要求: [书名]_[类型].txt\n"
                    f"可用类型: {', '.join(self.resource_mgr.get_available_genres()[:8])}..."
                )
            else:
                messagebox.showwarning("未找到文件", f"文件夹中没有找到 .txt 文件")
            self.file_label.config(text="❌ 未找到有效文件", fg="red")
            return

        # 为每个文件创建任务，随机分配章节数
        added_count = 0
        failed_tasks = []

        for file_info in valid_files:
            try:
                # 随机选择章节数
                chapter_count = random.randint(min_chapters, max_chapters)

                # 创建任务
                task_id = str(uuid.uuid4())
                config_params = {
                    'api_key': self.api_key_var.get(),
                    'base_url': 'https://yunwuapi.com',
                    'model': self.model_var.get(),
                    'male_count': self.male_count_var.get(),
                    'female_count': self.female_count_var.get(),
                    'chapter_count': chapter_count,  # 随机章节数
                    'max_tokens': self.max_tokens_var.get(),
                }

                task = OutlineTask(task_id, file_info['path'], file_info['genre'], config_params)
                self.tasks.append(task)

                added_count += 1
                print(f"  ✅ 已添加: {file_info['name']} (要求 {chapter_count} 章)")

            except Exception as e:
                error_msg = f"{file_info['name']}: {str(e)}"
                print(f"  ❌ 添加失败: {error_msg}")
                failed_tasks.append(error_msg)

        # 刷新显示
        self.refresh_outline_tasks_display()

        print(f"\n✅ 批量添加完成: 成功添加 {added_count}/{len(valid_files)} 个任务")

        # 显示结果摘要
        if added_count > 0:
            self.file_label.config(
                text=f"✅ 已批量添加 {added_count} 个任务 (章节范围 {min_chapters}-{max_chapters})",
                fg="green"
            )
            if failed_tasks:
                # 有成功也有失败，显示警告
                error_details = "\n".join(failed_tasks[:3])
                if len(failed_tasks) > 3:
                    error_details += f"\n... 还有 {len(failed_tasks) - 3} 个失败"
                messagebox.showwarning(
                    "部分添加成功",
                    f"成功添加: {added_count} 个任务\n"
                    f"添加失败: {len(failed_tasks)} 个任务\n\n"
                    f"失败详情:\n{error_details}"
                )
        else:
            # 全部失败
            self.file_label.config(text="❌ 添加任务失败", fg="red")
            error_details = "\n".join(failed_tasks[:5])
            if len(failed_tasks) > 5:
                error_details += f"\n... 还有 {len(failed_tasks) - 5} 个失败"
            messagebox.showerror(
                "添加任务失败",
                f"找到 {len(valid_files)} 个有效文件，但创建任务全部失败\n\n"
                f"失败详情:\n{error_details}"
            )

    def add_to_queue(self):
        """添加任务到队列"""
        if not self.current_source_file:
            print("⚠️  警告: 请先选择原文文件")
            self.file_label.config(text="❌ 请先选择文件", fg="red")
            return

        if not self.api_key_var.get():
            messagebox.showwarning("警告", "请输入API Key")
            return

        # 创建任务
        task_id = f"outline_{uuid.uuid4().hex[:8]}"

        config_params = {
            'api_key': self.api_key_var.get(),
            'base_url': 'https://yunwuapi.com',
            'model': self.model_var.get(),
            'male_count': self.male_count_var.get(),
            'female_count': self.female_count_var.get(),
            'chapter_count': self.chapter_count_var.get(),
            'max_tokens': self.max_tokens_var.get(),
        }

        task = OutlineTask(task_id, self.current_source_file, self.current_genre, config_params)
        self.tasks.append(task)

        # 刷新显示（支持分页）
        self.refresh_outline_tasks_display()

        print(f"✅ 任务已添加: {os.path.basename(self.current_source_file)}")

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
            # 规范化路径 - 确保在Mac/Windows上都正确
            file_path = os.path.abspath(os.path.normpath(file_path))
            print(f"🔍 导入的文件: {file_path}")

            # 从文件名提取书名和类型
            filename = os.path.basename(file_path)

            # 使用统一的类型提取函数（自动处理大小写）
            try:
                genre = extract_genre_from_filename(file_path)
            except ValueError as e:
                messagebox.showerror("错误", str(e))
                return

            # 提取书名
            match = re.match(r'(.+?)_([A-Za-z+\-]+)\.txt$', filename)
            if match:
                book_title = match.group(1)
            else:
                # 如果正则失败，使用文件名去掉扩展名和类型
                book_title = filename.replace(f'_{genre}.txt', '').replace(f'_{genre.lower()}.txt', '').replace(f'_{genre.upper()}.txt', '')

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
        # 创建任务框架 - 更紧凑
        task_container = tk.Frame(self.queue_frame, relief=tk.RIDGE, borderwidth=1, bg="#f5f5f5")
        task_container.pack(fill=tk.X, padx=5, pady=3)

        self.task_frames[task.task_id] = task_container

        # 左侧：任务信息
        info_frame = tk.Frame(task_container, bg="#f5f5f5")
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=6)

        # 标题行
        title_frame = tk.Frame(info_frame, bg="#f5f5f5")
        title_frame.pack(fill=tk.X)

        tk.Label(
            title_frame,
            text=f"📄 {os.path.basename(task.source_file)}",
            font=("Arial", 10, "bold"),
            bg="#f5f5f5",
            anchor="w"
        ).pack(side=tk.LEFT)

        status_label = tk.Label(
            title_frame,
            text=f"⏸ {task.status}",
            font=("Arial", 9),
            bg="#f5f5f5",
            fg="orange"
        )
        status_label.pack(side=tk.LEFT, padx=8)
        task_container.status_label = status_label  # 保存引用

        # 详情行 - 显示更多信息
        details_frame = tk.Frame(info_frame, bg="#f5f5f5")
        details_frame.pack(fill=tk.X, pady=(3, 0))

        # 动态显示的详情标签
        details_label = tk.Label(
            details_frame,
            text=f"类型: {task.genre}  |  模型: {task.config['model']}",
            font=("Arial", 8),
            bg="#f5f5f5",
            fg="gray"
        )
        details_label.pack(side=tk.LEFT)
        task_container.details_label = details_label  # 保存引用

        # 右侧：操作按钮 - 更紧凑
        button_frame = tk.Frame(task_container, bg="#f5f5f5")
        button_frame.pack(side=tk.RIGHT, padx=8, pady=6)

        # 预览Prompt按钮
        tk.Button(
            button_frame,
            text="👁️ Prompt",
            command=lambda: self.preview_task_prompt(task),
            width=10,
            bg="#FF9800",
            fg="white",
            font=("Arial", 8)
        ).pack(side=tk.LEFT, padx=2)

        # 开始按钮
        start_btn = tk.Button(
            button_frame,
            text="▶️ 开始",
            command=lambda: self.start_task(task),
            width=8,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 8)
        )
        start_btn.pack(side=tk.LEFT, padx=2)
        task_container.start_btn = start_btn  # 保存引用

        # 打开文件夹按钮
        folder_btn = tk.Button(
            button_frame,
            text="📂 文件夹",
            command=lambda: self.open_output_folder(task),
            width=10,
            state=tk.DISABLED,
            font=("Arial", 8)
        )
        folder_btn.pack(side=tk.LEFT, padx=2)
        task_container.folder_btn = folder_btn  # 保存引用

        # 删除按钮
        tk.Button(
            button_frame,
            text="🗑️",
            command=lambda: self.remove_task(task),
            width=4,
            bg="#f44336",
            fg="white",
            font=("Arial", 8)
        ).pack(side=tk.LEFT, padx=2)

    def add_cover_task_to_ui(self, task):
        """添加封面任务到UI"""
        # 隐藏空提示
        if hasattr(self, 'cover_empty_label'):
            self.cover_empty_label.pack_forget()

        # 创建任务框架 - 紧凑设计
        task_container = tk.Frame(self.cover_queue_frame, relief=tk.RIDGE, borderwidth=1, bg="#f5f5f5")
        task_container.pack(fill=tk.X, padx=5, pady=3)

        self.cover_task_frames[task.task_id] = task_container

        # 左侧：任务信息
        info_frame = tk.Frame(task_container, bg="#f5f5f5")
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=6)

        # 标题行
        title_frame = tk.Frame(info_frame, bg="#f5f5f5")
        title_frame.pack(fill=tk.X)

        tk.Label(
            title_frame,
            text=f"🎨 {task.title[:30]}{'...' if len(task.title) > 30 else ''}",
            font=("Arial", 10, "bold"),
            bg="#f5f5f5",
            anchor="w"
        ).pack(side=tk.LEFT)

        status_label = tk.Label(
            title_frame,
            text=f"⏸ {task.status}",
            font=("Arial", 9),
            bg="#f5f5f5",
            fg="orange"
        )
        status_label.pack(side=tk.LEFT, padx=8)
        task_container.status_label = status_label  # 保存引用

        # 详情行 - 显示类型、模型和开始时间
        details_frame = tk.Frame(info_frame, bg="#f5f5f5")
        details_frame.pack(fill=tk.X, pady=(3, 0))

        # 初始详情文本（不显示开始时间）
        details_text = f"类型: {task.genre}  |  模型: {task.config.get('model', 'dall-e-3')}"

        details_label = tk.Label(
            details_frame,
            text=details_text,
            font=("Arial", 8),
            bg="#f5f5f5",
            fg="gray"
        )
        details_label.pack(side=tk.LEFT)
        task_container.details_label = details_label  # 保存引用

        # 右侧：操作按钮 - 紧凑设计
        button_frame = tk.Frame(task_container, bg="#f5f5f5")
        button_frame.pack(side=tk.RIGHT, padx=8, pady=6)

        # 预览Prompt按钮
        tk.Button(
            button_frame,
            text="👁️ Prompt",
            command=lambda: self.preview_cover_task_prompt(task),
            width=10,
            bg="#FF9800",
            fg="white",
            font=("Arial", 8)
        ).pack(side=tk.LEFT, padx=2)

        # 开始按钮
        start_btn = tk.Button(
            button_frame,
            text="▶️ 开始",
            command=lambda: self.start_cover_task(task),
            width=8,
            bg="#9C27B0",
            fg="white",
            font=("Arial", 8)
        )
        start_btn.pack(side=tk.LEFT, padx=2)
        task_container.start_btn = start_btn  # 保存引用

        # 查看封面按钮
        view_btn = tk.Button(
            button_frame,
            text="📷 查看",
            command=lambda: self.view_cover(task),
            width=8,
            state=tk.DISABLED,
            font=("Arial", 8)
        )
        view_btn.pack(side=tk.LEFT, padx=2)
        task_container.view_btn = view_btn  # 保存引用

        # 打开文件夹按钮
        tk.Button(
            button_frame,
            text="📂 文件夹",
            command=lambda: self.open_cover_folder(task),
            width=9,
            font=("Arial", 8)
        ).pack(side=tk.LEFT, padx=2)

        # 删除按钮
        tk.Button(
            button_frame,
            text="🗑️",
            command=lambda: self.remove_cover_task(task),
            width=4,
            bg="#f44336",
            fg="white",
            font=("Arial", 8)
        ).pack(side=tk.LEFT, padx=2)

    def preview_cover_task_prompt(self, task):
        """预览封面任务的Prompt"""
        try:
            # 从outline文件夹读取完整大纲
            outline = ""
            if task.outline_folder and os.path.exists(task.outline_folder):
                full_outline_file = os.path.join(task.outline_folder, '_full_outline.txt')
                if os.path.exists(full_outline_file):
                    with open(full_outline_file, 'r', encoding='utf-8') as f:
                        outline = f.read()
                else:
                    outline = "(未找到_full_outline.txt文件)"
            else:
                outline = "(outline文件夹不存在)"

            # 渲染封面prompt
            prompt_vars = {
                'title': task.title,
                'genre': task.genre,
                'outline': outline
            }
            cover_prompt = self.prompt_mgr.render_cover_prompt(prompt_vars)

            # 创建预览窗口
            preview_win = tk.Toplevel(self.window)
            preview_win.title(f"封面Prompt预览 - {task.title}")
            preview_win.geometry("800x600")

            # 显示prompt
            text_widget = scrolledtext.ScrolledText(preview_win, wrap=tk.WORD, font=("Arial", 10))
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_widget.insert(1.0, cover_prompt)
            text_widget.config(state=tk.DISABLED)

        except Exception as e:
            messagebox.showerror("错误", f"预览Prompt失败: {str(e)}")

    def start_cover_task(self, task):
        """开始封面生成任务"""
        if task.status == 'running':
            messagebox.showinfo("提示", "任务正在运行中")
            return

        if task.status == 'completed':
            if not messagebox.askyesno("确认", "任务已完成，是否重新生成？"):
                return

        # 更新任务状态
        task.status = 'running'
        task.started_at = datetime.now()

        # 更新UI
        if task.task_id in self.cover_task_frames:
            container = self.cover_task_frames[task.task_id]

            # 更新状态标签
            if hasattr(container, 'status_label'):
                container.status_label.config(text="🔄 running", fg="blue")

            # 更新详情标签（添加开始时间）
            if hasattr(container, 'details_label'):
                start_time_str = task.started_at.strftime('%H:%M:%S')
                details_text = f"类型: {task.genre}  |  模型: {task.config.get('model', 'dall-e-3')}  |  开始: {start_time_str}"
                container.details_label.config(text=details_text)

            # 禁用开始按钮
            if hasattr(container, 'start_btn'):
                container.start_btn.config(state=tk.DISABLED)

        # 在后台线程中生成封面
        def generate_thread():
            try:
                # 读取outline信息
                outline_info = self._read_outline_info(task.outline_folder)

                # 调用实际的封面生成逻辑
                success, error_msg = self._generate_single_cover(task.outline_folder, outline_info)

                if success:
                    # 标记为完成
                    task.status = 'completed'
                    task.completed_at = datetime.now()

                    # 保存封面路径
                    cover_path = os.path.join(task.outline_folder, 'cover.png')
                    task.cover_path = cover_path

                    # 更新UI（线程安全）
                    def update_ui_success():
                        if task.task_id in self.cover_task_frames:
                            container = self.cover_task_frames[task.task_id]
                            if hasattr(container, 'status_label'):
                                container.status_label.config(text="✅ completed", fg="green")
                            if hasattr(container, 'view_btn'):
                                container.view_btn.config(state=tk.NORMAL)
                            if hasattr(container, 'start_btn'):
                                container.start_btn.config(state=tk.NORMAL)
                        messagebox.showinfo("成功", f"封面生成成功！\n{task.title}")

                    self.window.after(0, update_ui_success)

                else:
                    # 标记为失败
                    task.status = 'failed'

                    # 更新UI（线程安全）
                    def update_ui_failed():
                        if task.task_id in self.cover_task_frames:
                            container = self.cover_task_frames[task.task_id]
                            if hasattr(container, 'status_label'):
                                container.status_label.config(text="❌ failed", fg="red")
                            if hasattr(container, 'start_btn'):
                                container.start_btn.config(state=tk.NORMAL)
                        messagebox.showerror("失败", f"封面生成失败:\n{error_msg}")

                    self.window.after(0, update_ui_failed)

            except Exception as e:
                task.status = 'failed'

                # 更新UI（线程安全）
                def update_ui_error():
                    if task.task_id in self.cover_task_frames:
                        container = self.cover_task_frames[task.task_id]
                        if hasattr(container, 'status_label'):
                            container.status_label.config(text="❌ failed", fg="red")
                        if hasattr(container, 'start_btn'):
                            container.start_btn.config(state=tk.NORMAL)
                    messagebox.showerror("错误", f"封面生成失败:\n{str(e)}")

                self.window.after(0, update_ui_error)

        threading.Thread(target=generate_thread, daemon=True).start()

    def view_cover(self, task):
        """查看生成的封面"""
        if not task.cover_path or not os.path.exists(task.cover_path):
            messagebox.showwarning("警告", "封面文件不存在")
            return

        try:
            # 在系统默认查看器中打开图片 - 使用subprocess.Popen()更安全
            if sys.platform == 'win32':
                os.startfile(task.cover_path)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', task.cover_path])
            else:
                subprocess.Popen(['xdg-open', task.cover_path])
        except Exception as e:
            messagebox.showerror("错误", f"打开封面失败: {str(e)}")

    def open_cover_folder(self, task):
        """打开封面任务的outline文件夹"""
        if not task.outline_folder or not os.path.exists(task.outline_folder):
            messagebox.showwarning("警告", "文件夹不存在")
            return

        try:
            if sys.platform == 'win32':
                os.startfile(task.outline_folder)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', task.outline_folder])
            else:
                subprocess.Popen(['xdg-open', task.outline_folder])
        except Exception as e:
            messagebox.showerror("错误", f"打开文件夹失败: {str(e)}")

    def remove_cover_task(self, task):
        """删除封面任务"""
        if task.status == 'running':
            messagebox.showwarning("警告", "任务正在运行中，无法删除")
            return

        if messagebox.askyesno("确认", f"确定要删除封面任务「{task.title}」吗？"):
            # 从UI中移除
            if task.task_id in self.cover_task_frames:
                self.cover_task_frames[task.task_id].destroy()
                del self.cover_task_frames[task.task_id]

            # 从列表中移除
            self.cover_tasks = [t for t in self.cover_tasks if t.task_id != task.task_id]

            # 如果队列空了，显示空提示
            if not self.cover_tasks and hasattr(self, 'cover_empty_label'):
                self.cover_empty_label.pack()

    def preview_task_prompt(self, task):
        """预览任务的Prompt"""
        try:
            # 清空缓存，确保使用最新配置重新生成
            task.prompt_cache = None

            # 生成Prompt - 自动检测编码
            content = None
            encodings_to_try = ['utf-8', 'gbk', 'gb2312', 'latin1', 'cp1252']
            for encoding in encodings_to_try:
                try:
                    with open(task.source_file, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue

            if content is None:
                raise ValueError(f"无法读取文件，尝试了以下编码均失败: {', '.join(encodings_to_try)}")

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
                'genre_focus': selected_style['genre_focus'],
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

类型重点 ({task.genre}):
{selected_style['genre_focus'][:200]}...
"""

            # 缓存Prompt
            task.prompt_cache = full_prompt

            # 显示Prompt预览（简化版）
            preview = full_prompt[:1000] + "..." if len(full_prompt) > 1000 else full_prompt
            messagebox.showinfo(
                f"Prompt预览 - {os.path.basename(task.source_file)}",
                f"Prompt已生成（共{len(full_prompt)}字符）\n\n前1000字符预览：\n\n{preview}"
            )

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
            # 读取原文 - 自动检测编码
            content = None
            encodings_to_try = ['utf-8', 'gbk', 'gb2312', 'latin1', 'cp1252']
            for encoding in encodings_to_try:
                try:
                    with open(task.source_file, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue

            if content is None:
                raise ValueError(f"无法读取文件，尝试了以下编码均失败: {', '.join(encodings_to_try)}")

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
                'genre_focus': selected_style['genre_focus'],
                'male_names': names_formatted['male_names'],
                'female_names': names_formatted['female_names'],
                'end_chapter': task.config.get('chapter_count', 15),
            }

            system_prompt = self.prompt_mgr.render_outline_prompt(prompt_vars)

            # 更新UI显示正在调用API
            self.window.after(0, lambda: self._update_task_status(task, "🌐 正在调用API..."))

            # 检测模型类型，决定使用哪种API调用方式
            model = task.config['model']
            use_http_client = 'gemini' in model.lower() or 'gpt-5' in model.lower()

            if use_http_client:
                # 使用http.client方式（适合Gemini等模型）
                from utils import call_api_with_http_client

                result = call_api_with_http_client(
                    api_key=task.config['api_key'],
                    base_url=task.config.get('base_url', 'https://yunwuapi.com'),
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": content}
                    ],
                    temperature=0.8,
                    max_tokens=task.config['max_tokens']
                )

                if not result['success']:
                    raise Exception(f"API调用失败: {result['error']}\n详情: {result.get('details', 'N/A')}")

                result_text = result['content']
            else:
                # 使用UniversalAPIClient（兼容Gemini和GPT）
                base_url = task.config.get('base_url', 'https://yunwuapi.com')
                client = UniversalAPIClient(
                    api_key=task.config['api_key'],
                    base_url=base_url
                )

                response = client.chat_completion(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": content}
                    ],
                    temperature=0.8,
                    max_tokens=task.config['max_tokens']
                )

                result_text = client.get_message_content(response)

            # 检查返回内容是否为空
            if not result_text:
                raise ValueError("API返回内容为空，请检查API配置或稍后重试")

            # 更新UI显示正在处理
            self.window.after(0, lambda: self._update_task_status(task, "📝 正在保存结果..."))

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

        # 创建基础文件夹（打包环境会在用户文档目录下创建）
        work_dir = get_work_directory()
        base_folder = os.path.join(work_dir, 'novels_for_translation')
        os.makedirs(base_folder, exist_ok=True)

        title = parsed_data.get('title', 'Untitled') or 'Untitled'
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))
        safe_title = safe_title.replace(' ', '_') if safe_title else 'Untitled'

        # 文件夹名：书名_translation（新格式）
        folder_name = f"{safe_title}_translation"
        output_folder = os.path.join(base_folder, folder_name)

        # 如果文件夹已存在，添加时间戳
        if os.path.exists(output_folder):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            folder_name = f"{safe_title}_translation_{timestamp}"
            output_folder = os.path.join(base_folder, folder_name)

        os.makedirs(output_folder, exist_ok=True)

        # 复制源文件到项目文件夹
        if task.source_file and os.path.exists(task.source_file):
            import shutil
            source_filename = os.path.basename(task.source_file)
            shutil.copy2(task.source_file, os.path.join(output_folder, source_filename))
            print(f"  ✓ 源文件已复制: {source_filename}")

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

        # 5. 保存 age.txt
        with open(os.path.join(output_folder, 'age.txt'), 'w', encoding='utf-8') as f:
            f.write(parsed_data.get('age_category', '') or '')

        # 6. 保存章节大纲（每章一个prompt文件：chapter_X_prompt.txt）
        chapters = parsed_data.get('chapters', [])
        for chapter in chapters:
            ch_num = chapter.get('number', 0)
            ch_title = chapter.get('title', f'Chapter {ch_num}') or f'Chapter {ch_num}'

            # 文件名：chapter_1_prompt.txt, chapter_2_prompt.txt, ...
            filename = f"chapter_{ch_num}_prompt.txt"

            with open(os.path.join(output_folder, filename), 'w', encoding='utf-8') as f:
                f.write(f"Chapter {ch_num}: {ch_title}\n\n")

                # 保存新格式的字段（如果有的话）
                if 'opening' in chapter:
                    f.write(f"Opening: {chapter['opening']}\n\n")
                if 'development' in chapter:
                    f.write(f"Development: {chapter['development']}\n\n")
                if 'conflict' in chapter:
                    f.write(f"Conflict: {chapter['conflict']}\n\n")
                if 'climax' in chapter:
                    f.write(f"Climax: {chapter['climax']}\n\n")
                if 'hook' in chapter:
                    f.write(f"Hook: {chapter['hook']}\n\n")
                if 'key_scenes' in chapter:
                    f.write(f"Key Scenes:\n{chapter['key_scenes']}\n\n")

                # 兼容旧格式
                if 'summary' in chapter and not any(k in chapter for k in ['opening', 'development', 'conflict']):
                    f.write(f"Summary:\n{chapter['summary']}\n\n")
                if 'key_events' in chapter:
                    f.write(f"Key Events:\n{chapter['key_events']}\n\n")
                if 'characters' in chapter:
                    f.write(f"Characters: {chapter['characters']}\n")

        # 7. 保存完整大纲备份
        with open(os.path.join(output_folder, '_full_outline.txt'), 'w', encoding='utf-8') as f:
            f.write(result_text)

        # 8. 保存写作用的精简Prompt（_writing_prompt.txt）
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
            'age_category': '',
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

        # 提取age_category
        age_match = re.search(r'={5,}\s*AGE_RATING\s*={5,}\s*\n(.+?)(?=\n={5,}|$)', text, re.DOTALL)
        if age_match:
            data['age_category'] = age_match.group(1).strip()

        # 提取章节
        chapter_section = re.search(r'={5,}\s*CHAPTER_OUTLINES\s*={5,}\s*\n(.+?)(?=\n={5,}\s*END|$)', text, re.DOTALL)
        if chapter_section:
            chapter_text = chapter_section.group(1)

            # 匹配每个章节 - 支持新格式（Opening/Development/Conflict/Climax/Hook/Key Scenes）
            # 使用更灵活的模式匹配
            chapter_pattern = r'Chapter\s+(\d+):\s*(.+?)(?=\nChapter\s+\d+:|$)'
            for match in re.finditer(chapter_pattern, chapter_text, re.DOTALL):
                ch_num = int(match.group(1))
                chapter_content = match.group(2).strip()

                # 提取标题（第一行）
                lines = chapter_content.split('\n', 1)
                ch_title = lines[0].strip()
                remaining_content = lines[1] if len(lines) > 1 else ""

                # 构建章节数据，包含完整内容
                chapter_data = {
                    'number': ch_num,
                    'title': ch_title,
                    'summary': remaining_content.strip()  # 保存完整的章节大纲内容
                }

                # 尝试提取特定字段（新格式）
                opening_match = re.search(r'Opening:\s*(.+?)(?=\n(?:Development:|Conflict:|$))', remaining_content, re.DOTALL)
                if opening_match:
                    chapter_data['opening'] = opening_match.group(1).strip()

                development_match = re.search(r'Development:\s*(.+?)(?=\n(?:Conflict:|Climax:|$))', remaining_content, re.DOTALL)
                if development_match:
                    chapter_data['development'] = development_match.group(1).strip()

                conflict_match = re.search(r'Conflict:\s*(.+?)(?=\n(?:Climax:|Hook:|$))', remaining_content, re.DOTALL)
                if conflict_match:
                    chapter_data['conflict'] = conflict_match.group(1).strip()

                climax_match = re.search(r'Climax:\s*(.+?)(?=\n(?:Hook:|Key Scenes:|$))', remaining_content, re.DOTALL)
                if climax_match:
                    chapter_data['climax'] = climax_match.group(1).strip()

                hook_match = re.search(r'Hook:\s*(.+?)(?=\n(?:Key Scenes:|Chapter\s+\d+:|$))', remaining_content, re.DOTALL)
                if hook_match:
                    chapter_data['hook'] = hook_match.group(1).strip()

                key_scenes_match = re.search(r'Key Scenes.*?:\s*(.+?)(?=\nChapter\s+\d+:|$)', remaining_content, re.DOTALL)
                if key_scenes_match:
                    chapter_data['key_scenes'] = key_scenes_match.group(1).strip()

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

    def _update_task_status(self, task, status_text):
        """更新任务状态显示"""
        if task.task_id in self.task_frames:
            frame = self.task_frames[task.task_id]
            frame.status_label.config(text=status_text, fg="blue")

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

    def start_all_outline_tasks(self):
        """一键开始所有大纲任务"""
        if not self.tasks:
            print("⚠️  没有大纲任务")
            return

        pending_tasks = [t for t in self.tasks if t.status == 'pending']
        if not pending_tasks:
            print("⚠️  所有大纲任务都已开始或完成")
            return

        print(f"🚀 开始 {len(pending_tasks)} 个大纲任务")
        for task in pending_tasks:
            try:
                self.start_task(task)
            except Exception as e:
                print(f"❌ 启动失败: {task.genre}, 错误: {e}")

    def clear_outline_tasks(self):
        """清空大纲任务"""
        running_tasks = [t for t in self.tasks if t.status == 'running']
        if running_tasks:
            print("⚠️  有大纲任务正在运行中")
            return

        if not self.tasks:
            print("⚠️  大纲队列已经是空的")
            return

        print(f"🗑️ 清空 {len(self.tasks)} 个大纲任务")
        for task in self.tasks[:]:
            if task.task_id in self.task_frames:
                self.task_frames[task.task_id].destroy()
                del self.task_frames[task.task_id]
        self.tasks.clear()
        self.empty_label.pack()

    def start_all_cover_tasks(self):
        """一键开始所有封面任务"""
        if not self.cover_tasks:
            print("⚠️  没有封面任务")
            return

        pending_tasks = [t for t in self.cover_tasks if t.get('status') == 'pending']
        if not pending_tasks:
            print("⚠️  所有封面任务都已开始或完成")
            return

        print(f"🚀 开始 {len(pending_tasks)} 个封面任务")
        for task in pending_tasks:
            try:
                self.start_cover_task(task)
            except Exception as e:
                print(f"❌ 启动失败: {task.get('outline_info', {}).get('title', 'Unknown')}, 错误: {e}")

    def clear_cover_tasks(self):
        """清空封面任务"""
        if not self.cover_tasks:
            print("⚠️  封面队列已经是空的")
            return

        print(f"🗑️ 清空 {len(self.cover_tasks)} 个封面任务")
        for task in self.cover_tasks[:]:
            if task['task_id'] in self.cover_task_frames:
                self.cover_task_frames[task['task_id']].destroy()
                del self.cover_task_frames[task['task_id']]

        self.cover_tasks.clear()
        self.cover_empty_label.pack()

    def test_api_connection(self):
        """测试API连接 - 使用UniversalAPIClient（兼容Gemini和GPT）"""
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
                # 使用UniversalAPIClient（兼容Gemini和GPT）
                client = UniversalAPIClient(api_key=api_key, base_url="https://yunwuapi.com")

                # 测试调用
                response = client.chat_completion(
                    model=model,
                    messages=[
                        {"role": "user", "content": "你好"}
                    ],
                    temperature=0.7,
                    max_tokens=25000  # Gemini需要较大的max_tokens
                )

                # 检查响应
                if response.get('choices') and len(response['choices']) > 0:
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

    def test_gemini_simple(self):
        """测试Gemini连接 - 使用UniversalAPIClient（兼容Gemini和GPT）"""
        api_key = self.api_key_var.get()

        if not api_key:
            messagebox.showerror("错误", "请输入API Key")
            return

        # 更新状态
        self.api_status_label.config(text="🔄 测试Gemini...", fg="blue")
        self.window.update()

        # 在新线程中测试
        def _test():
            try:
                # 使用UniversalAPIClient（兼容Gemini和GPT）
                client = UniversalAPIClient(api_key=api_key, base_url="https://yunwuapi.com")

                # 测试调用
                response = client.chat_completion(
                    model="gemini-3-pro-preview",
                    messages=[
                        {"role": "user", "content": "你好，你是谁。"}
                    ],
                    temperature=0.7,
                    max_tokens=100
                )

                # 获取回复
                assistant_reply = client.get_message_content(response)

                # 成功
                self.window.after(0, lambda: messagebox.showinfo(
                    "Gemini测试成功",
                    f"模型回复：{assistant_reply}"
                ))
                self.window.after(0, lambda: self.api_status_label.config(
                    text="✅ Gemini连接成功", fg="green"
                ))

            except Exception as e:
                error_msg = f"发生错误：{e}"
                self.window.after(0, lambda: messagebox.showerror("Gemini测试失败", error_msg))
                self.window.after(0, lambda: self.api_status_label.config(
                    text=f"❌ {str(e)[:30]}", fg="red"
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

    def manage_cover_prompts(self):
        """封面Prompt管理和版本控制"""
        # 创建Prompt管理窗口
        prompt_window = tk.Toplevel(self.window)
        prompt_window.title("封面Prompt管理")
        prompt_window.geometry("900x700")

        # 标题
        title_label = tk.Label(
            prompt_window,
            text="📝 封面生成Prompt模板管理",
            font=("Arial", 16, "bold"),
            bg="#9C27B0",
            fg="white",
            pady=15
        )
        title_label.pack(fill=tk.X)

        # 主容器
        main_frame = tk.Frame(prompt_window, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 说明
        info_text = tk.Label(
            main_frame,
            text="支持变量: {title}, {genre}, {outline}",
            font=("Arial", 9),
            fg="gray",
            anchor="w"
        )
        info_text.pack(fill=tk.X, pady=(0, 10))

        # 版本选择
        info_frame = tk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            info_frame,
            text="Prompt版本:",
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT)

        version_var = tk.StringVar()
        available_versions = self.prompt_mgr.get_cover_versions()
        current_version = self.prompt_mgr.prompts.get('cover', {}).get('active_version', 'Default')
        version_var.set(current_version)

        def on_version_change(event=None):
            selected_version = version_var.get()
            prompt_text.config(state=tk.NORMAL)
            prompt_text.delete("1.0", tk.END)
            try:
                version_prompt = self.prompt_mgr.get_cover_prompt(selected_version)
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

        def set_active():
            selected_version = version_var.get()
            self.prompt_mgr.set_active_cover_version(selected_version)
            messagebox.showinfo("成功", f"已将 '{selected_version}' 设为活跃版本")

        tk.Button(
            info_frame,
            text="设为活跃",
            command=set_active,
            bg="#9C27B0",
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
            current_prompt = self.prompt_mgr.get_cover_prompt()
            prompt_text.insert(tk.END, current_prompt)
            prompt_text.config(state=tk.DISABLED)
        except Exception as e:
            prompt_text.insert(tk.END, f"加载失败: {str(e)}")

        # 按钮区域
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        def edit_prompt():
            prompt_text.config(state=tk.NORMAL)
            edit_btn.config(state=tk.DISABLED)
            save_btn.config(state=tk.NORMAL)

        def save_prompt():
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
                    self.prompt_mgr.save_custom_cover_prompt(version_name, new_prompt)
                    self.prompt_mgr.set_active_cover_version(version_name)

                    version_combo['values'] = self.prompt_mgr.get_cover_versions()
                    version_var.set(version_name)

                    messagebox.showinfo("成功", f"Prompt已保存为版本 '{version_name}'！", parent=version_window)
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

            version_entry.bind('<Return>', lambda e: do_save())

        def reset_to_default():
            if messagebox.askyesno("确认", "确定要重置为默认Prompt吗？"):
                try:
                    self.prompt_mgr.restore_default_cover()
                    prompt_text.config(state=tk.NORMAL)
                    prompt_text.delete("1.0", tk.END)
                    prompt_text.insert(tk.END, self.prompt_mgr.get_cover_prompt())
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

    # === 封面生成相关方法 ===
    def preview_cover_prompt(self):
        """预览封面生成Prompt"""
        if not self.cover_folders:
            messagebox.showwarning("警告", "请先选择Outline文件夹")
            return

        # 如果选择了多个文件夹，预览第一个
        folder = self.cover_folders[0]
        folder_name = os.path.basename(folder)

        try:
            # 读取outline信息
            outline_info = self._read_outline_info(folder)

            # 构建prompt
            prompt = self._create_cover_prompt(outline_info)

            # 创建预览窗口
            preview_window = tk.Toplevel(self.window)
            preview_window.title(f"封面Prompt预览 - {folder_name}")
            preview_window.geometry("900x700")

            # 标题
            title_label = tk.Label(
                preview_window,
                text=f"📝 封面生成Prompt预览\n{outline_info['title']} ({outline_info['genre']})",
                font=("Arial", 14, "bold"),
                bg="#9C27B0",
                fg="white",
                pady=15
            )
            title_label.pack(fill=tk.X)

            # 提示信息
            info_frame = tk.Frame(preview_window, bg="#f5f5f5", padx=10, pady=10)
            info_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

            tk.Label(
                info_frame,
                text=f"文件夹: {folder_name}",
                font=("Arial", 10),
                bg="#f5f5f5",
                anchor="w"
            ).pack(fill=tk.X)

            tk.Label(
                info_frame,
                text=f"Prompt长度: {len(prompt)} 字符",
                font=("Arial", 10),
                bg="#f5f5f5",
                fg="gray",
                anchor="w"
            ).pack(fill=tk.X)

            if len(self.cover_folders) > 1:
                tk.Label(
                    info_frame,
                    text=f"注: 已选择 {len(self.cover_folders)} 个文件夹，当前预览第一个",
                    font=("Arial", 9),
                    bg="#f5f5f5",
                    fg="orange",
                    anchor="w"
                ).pack(fill=tk.X)

            # Prompt显示区域
            prompt_frame = tk.Frame(preview_window, padx=10, pady=5)
            prompt_frame.pack(fill=tk.BOTH, expand=True)

            prompt_text = scrolledtext.ScrolledText(
                prompt_frame,
                wrap=tk.WORD,
                font=("Courier", 9),
                height=25
            )
            prompt_text.pack(fill=tk.BOTH, expand=True)
            prompt_text.insert(tk.END, prompt)
            prompt_text.config(state=tk.DISABLED)

            # 按钮区域
            button_frame = tk.Frame(preview_window, pady=10)
            button_frame.pack(fill=tk.X)

            tk.Button(
                button_frame,
                text="关闭",
                command=preview_window.destroy,
                width=15,
                font=("Arial", 11)
            ).pack(pady=5)

        except Exception as e:
            messagebox.showerror("错误", f"预览Prompt失败:\n{str(e)}")

    def _get_default_directory(self):
        """获取默认目录 - 优先使用用户文档目录"""
        # Windows: C:\Users\用户名\Documents\OutlineGenerator
        # Mac/Linux: ~/Documents/OutlineGenerator
        if sys.platform == 'win32':
            docs_dir = os.path.join(os.path.expanduser('~'), 'Documents', 'OutlineGenerator')
        else:
            docs_dir = os.path.expanduser('~/Documents/OutlineGenerator')

        # 检查多个可能的目录
        possible_dirs = [
            docs_dir,
            os.path.abspath("novels_for_translation"),
            os.getcwd()
        ]

        for directory in possible_dirs:
            if os.path.exists(directory):
                return directory

        # 如果都不存在，返回用户文档目录（即使不存在也返回，方便创建）
        return docs_dir

    def add_cover_folder(self):
        """添加outline文件夹"""
        initial_dir = self._get_default_directory()

        folder = filedialog.askdirectory(title="选择Outline文件夹", initialdir=initial_dir)
        if folder:
            # 规范化路径 - 重要！确保路径在Mac/Windows上都正确
            folder = os.path.abspath(os.path.normpath(folder))
            print(f"🔍 选择的文件夹: {folder}")

            # 验证文件夹包含必要文件（_full_outline.txt 或 _writing_prompt.txt）
            full_outline = os.path.join(folder, '_full_outline.txt')
            writing_prompt = os.path.join(folder, '_writing_prompt.txt')

            print(f"  检查 _full_outline.txt: {os.path.exists(full_outline)}")
            print(f"  检查 _writing_prompt.txt: {os.path.exists(writing_prompt)}")

            if not os.path.exists(full_outline) and not os.path.exists(writing_prompt):
                messagebox.showwarning("警告", "所选文件夹不包含 _full_outline.txt 或 _writing_prompt.txt 文件")
                print(f"  ❌ 验证失败：缺少必要文件")
                return

            if folder not in self.cover_folders:
                self.cover_folders.append(folder)
                print(f"  ✅ 文件夹已添加，当前列表: {self.cover_folders}")
                self._update_cover_folders_label()
            else:
                print(f"  ⚠️ 文件夹已存在于列表中")

    def add_cover_folder_batch(self):
        """批量添加outline文件夹（扫描父文件夹下的所有子文件夹）"""
        initial_dir = self._get_default_directory()

        parent_folder = filedialog.askdirectory(
            title="选择父文件夹（将自动扫描所有子文件夹）",
            initialdir=initial_dir
        )

        if not parent_folder:
            return

        # 规范化路径
        parent_folder = os.path.abspath(os.path.normpath(parent_folder))
        print(f"\n📁 批量扫描文件夹: {parent_folder}")

        # 扫描所有子文件夹
        valid_folders = []
        total_scanned = 0

        for root, dirs, files in os.walk(parent_folder):
            total_scanned += 1

            # 检查是否包含必要文件
            has_full_outline = '_full_outline.txt' in files
            has_writing_prompt = '_writing_prompt.txt' in files

            if has_full_outline or has_writing_prompt:
                folder_path = os.path.abspath(os.path.normpath(root))

                # 避免重复添加
                if folder_path not in self.cover_folders and folder_path not in valid_folders:
                    valid_folders.append(folder_path)
                    print(f"  ✅ 找到: {os.path.basename(folder_path)}")

        print(f"\n扫描完成: 共扫描 {total_scanned} 个文件夹，找到 {len(valid_folders)} 个有效的outline文件夹")

        if valid_folders:
            # 添加到列表
            added_count = 0
            for folder in valid_folders:
                if folder not in self.cover_folders:
                    self.cover_folders.append(folder)
                    added_count += 1

            self._update_cover_folders_label()

            messagebox.showinfo(
                "批量添加完成",
                f"扫描文件夹: {os.path.basename(parent_folder)}\n"
                f"扫描总数: {total_scanned} 个文件夹\n"
                f"找到有效: {len(valid_folders)} 个\n"
                f"新增添加: {added_count} 个\n"
                f"当前总数: {len(self.cover_folders)} 个"
            )
        else:
            messagebox.showwarning(
                "未找到有效文件夹",
                f"在 {os.path.basename(parent_folder)} 中未找到包含\n"
                f"_full_outline.txt 或 _writing_prompt.txt 的子文件夹"
            )

    def clear_cover_folders(self):
        """清空选择的文件夹"""
        self.cover_folders.clear()
        self._update_cover_folders_label()

    def _update_cover_folders_label(self):
        """更新文件夹显示标签"""
        if not self.cover_folders:
            self.cover_folders_label.config(text="未选择（可多选）", fg="gray")
        else:
            folder_names = [os.path.basename(f) for f in self.cover_folders]
            display_text = f"已选择 {len(self.cover_folders)} 个: {', '.join(folder_names[:3])}"
            if len(folder_names) > 3:
                display_text += f"... (共{len(folder_names)}个)"
            self.cover_folders_label.config(text=display_text, fg="blue")

    def generate_covers(self):
        """创建封面生成任务（支持批量）"""
        print(f"\n🎨 开始生成封面流程")
        print(f"  当前 cover_folders 列表: {self.cover_folders}")
        print(f"  列表长度: {len(self.cover_folders)}")

        if not self.cover_folders:
            print(f"  ❌ cover_folders 为空，显示警告")
            messagebox.showwarning("警告", "请先选择Outline文件夹")
            return

        if not self.api_key_var.get():
            print(f"  ❌ API Key 未配置")
            messagebox.showwarning("警告", "请先配置API Key")
            return

        # 确认创建任务
        if not messagebox.askyesno("确认", f"将为 {len(self.cover_folders)} 个文件夹创建封面生成任务，确认继续？"):
            print(f"  ⚠️ 用户取消创建任务")
            return

        # 创建任务
        created_count = 0
        skipped_count = 0

        print(f"  开始循环创建任务...")
        for folder in self.cover_folders:
            try:
                # 读取outline信息
                outline_info = self._read_outline_info(folder)

                # 检查是否已存在相同任务
                folder_basename = os.path.basename(folder)
                existing = any(t.outline_folder == folder for t in self.cover_tasks)
                if existing:
                    print(f"⚠️ 跳过重复任务: {folder_basename}")
                    skipped_count += 1
                    continue

                # 创建任务
                task_id = str(uuid.uuid4())
                task = CoverTask(
                    task_id=task_id,
                    outline_folder=folder,
                    title=outline_info['title'],
                    genre=outline_info['genre'],
                    blurb='',  # 不再使用blurb
                    config_params={
                        'model': 'gpt-4o-image-vip',
                        'api_key': self.api_key_var.get(),
                        'base_url': 'https://yunwuapi.com/v1/'
                    }
                )

                # 添加到任务列表
                self.cover_tasks.append(task)

                created_count += 1
                print(f"✅ 创建封面任务: {folder_basename}")

            except Exception as e:
                print(f"❌ 创建任务失败 [{os.path.basename(folder)}]: {e}")
                import traceback
                traceback.print_exc()

        # 刷新显示（支持分页）
        self.refresh_cover_tasks_display()

        # 显示结果
        result_msg = f"已创建 {created_count} 个封面任务"
        if skipped_count > 0:
            result_msg += f"，跳过 {skipped_count} 个重复任务"

        self.cover_status_label.config(text=f"✅ {result_msg}", fg="green")
        print(f"📋 {result_msg}")

    def _read_outline_info(self, folder):
        """读取outline文件夹信息"""
        print(f"    📖 读取文件夹信息: {os.path.basename(folder)}")

        info = {
            'title': 'Untitled',
            'genre': 'Unknown',
            'outline': '',
            'tags': []
        }

        # 读取title
        title_file = os.path.join(folder, 'title.txt')
        if os.path.exists(title_file):
            with open(title_file, 'r', encoding='utf-8') as f:
                info['title'] = f.read().strip()
                print(f"      Title: {info['title']}")

        # 读取genre
        category_file = os.path.join(folder, 'category.txt')
        if os.path.exists(category_file):
            with open(category_file, 'r', encoding='utf-8') as f:
                info['genre'] = f.read().strip()
                print(f"      Genre: {info['genre']}")

        # 读取完整outline（优先读取_full_outline.txt）
        full_outline_file = os.path.join(folder, '_full_outline.txt')
        writing_prompt_file = os.path.join(folder, '_writing_prompt.txt')

        if os.path.exists(full_outline_file):
            with open(full_outline_file, 'r', encoding='utf-8') as f:
                info['outline'] = f.read()
                print(f"      使用 _full_outline.txt ({len(info['outline'])} 字符)")
        elif os.path.exists(writing_prompt_file):
            with open(writing_prompt_file, 'r', encoding='utf-8') as f:
                info['outline'] = f.read()
                print(f"      使用 _writing_prompt.txt ({len(info['outline'])} 字符)")
        else:
            print(f"      ⚠️ 未找到 outline 文件")

        # 读取tags
        tags_file = os.path.join(folder, 'tags.txt')
        if os.path.exists(tags_file):
            with open(tags_file, 'r', encoding='utf-8') as f:
                tags_text = f.read().strip()
                info['tags'] = [tag.strip() for tag in tags_text.split(',') if tag.strip()]

        return info

    def _create_cover_prompt(self, outline_info):
        """构建封面生成prompt（从prompt_mgr获取模板）"""
        title = outline_info['title']
        genre = outline_info['genre']
        outline = outline_info['outline']  # 使用完整outline

        # 从prompt_mgr获取模板
        template = self.prompt_mgr.get_cover_prompt()

        # 渲染变量 - 让AI自己决定风格
        prompt = template.format(
            title=title,
            genre=genre,
            outline=outline
        )

        return prompt

    def _generate_single_cover(self, folder, outline_info):
        """生成单个封面

        Returns:
            (success: bool, error_msg: str): 成功返回(True, ""), 失败返回(False, 错误信息)
        """
        try:
            # 构建prompt
            prompt = self._create_cover_prompt(outline_info)

            print(f"\n🎨 为 {outline_info['title']} 生成封面...")
            print(f"📝 Prompt前100字符: {prompt[:100]}...")

            # 调用API生成图片
            from openai import OpenAI
            client = OpenAI(
                api_key=self.api_key_var.get(),
                base_url="https://yunwuapi.com/v1/"
            )

            print(f"🌐 调用API生成图片...")
            response = client.images.generate(
                model="gpt-4o-image-vip",
                prompt=prompt,
                size="1024x1792",
                quality="hd",
                n=1
            )

            image_url = response.data[0].url
            print(f"✅ 图片生成成功！URL: {image_url}")

            # 下载并保存封面
            import urllib.request
            import ssl
            from PIL import Image

            # 下载原图
            cover_path = os.path.join(folder, 'cover.png')
            print(f"⬇️  下载图片到: {cover_path}")

            # 修复Mac上的SSL证书验证问题 - 使用urlopen而不是urlretrieve
            ssl_context = ssl._create_unverified_context()

            try:
                # 使用urlopen + SSL上下文下载
                with urllib.request.urlopen(image_url, context=ssl_context) as response:
                    image_data = response.read()

                # 写入文件
                with open(cover_path, 'wb') as f:
                    f.write(image_data)

                print(f"💾 封面已保存: {cover_path}")

            except Exception as download_error:
                print(f"❌ 下载失败: {download_error}")
                # 尝试不使用SSL上下文（作为后备）
                try:
                    print(f"🔄 尝试不验证SSL...")
                    import urllib.request
                    req = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, context=ssl_context) as response:
                        image_data = response.read()
                    with open(cover_path, 'wb') as f:
                        f.write(image_data)
                    print(f"💾 封面已保存（使用后备方法）: {cover_path}")
                except Exception as e2:
                    raise Exception(f"图片下载失败: {e2}")

            # 可选：生成缩略图 (300x400)
            try:
                img = Image.open(cover_path)
                # 兼容新旧版本的Pillow (10.0+ vs <10.0)
                try:
                    # Pillow 10.0+ 使用 Image.Resampling.LANCZOS
                    resample_filter = Image.Resampling.LANCZOS
                except AttributeError:
                    # 旧版本 Pillow 使用 Image.LANCZOS
                    resample_filter = Image.LANCZOS
                img_resized = img.resize((300, 400), resample_filter)
                thumbnail_path = os.path.join(folder, 'cover_300x400.jpg')
                img_resized.save(thumbnail_path, quality=95)
                print(f"📐 缩略图已保存: {thumbnail_path}")
            except Exception as thumb_err:
                print(f"⚠️  缩略图生成失败（不影响主流程）: {thumb_err}")

            return (True, "")

        except Exception as e:
            error_msg = str(e)
            print(f"❌ 生成封面错误: {error_msg}")
            import traceback
            full_trace = traceback.format_exc()
            print(full_trace)

            # 返回更详细的错误信息
            if "API" in error_msg or "api" in error_msg.lower():
                return (False, f"API调用失败: {error_msg}")
            elif "url" in error_msg.lower() or "urlretrieve" in error_msg.lower():
                return (False, f"图片下载失败: {error_msg}")
            elif "PIL" in error_msg or "Image" in error_msg:
                return (False, f"图片处理失败: {error_msg}")
            else:
                return (False, error_msg)

    def refresh_outline_tasks_display(self):
        """刷新大纲任务显示 - 支持分页"""
        # 清空当前显示
        for task_id, frame in list(self.task_frames.items()):
            frame.destroy()
        self.task_frames.clear()

        if not self.tasks:
            self.empty_label.pack()
            self._update_outline_pagination_label()
            return

        # 计算分页
        total_tasks = len(self.tasks)
        total_pages = (total_tasks + self.tasks_per_page - 1) // self.tasks_per_page

        if self.outline_current_page >= total_pages:
            self.outline_current_page = max(0, total_pages - 1)

        start_idx = self.outline_current_page * self.tasks_per_page
        end_idx = min(start_idx + self.tasks_per_page, total_tasks)

        # 只显示当前页的任务
        for i in range(start_idx, end_idx):
            task = self.tasks[i]
            self.add_task_to_ui(task)

        self._update_outline_pagination_label()

    def outline_previous_page(self):
        if self.outline_current_page > 0:
            self.outline_current_page -= 1
            self.refresh_outline_tasks_display()

    def outline_next_page(self):
        total_pages = (len(self.tasks) + self.tasks_per_page - 1) // self.tasks_per_page
        if self.outline_current_page < total_pages - 1:
            self.outline_current_page += 1
            self.refresh_outline_tasks_display()

    def _update_outline_pagination_label(self):
        total = len(self.tasks)
        if total == 0:
            self.outline_page_label.config(text="1/1 页")
            return
        pages = (total + self.tasks_per_page - 1) // self.tasks_per_page
        self.outline_page_label.config(text=f"{self.outline_current_page + 1}/{pages} 页 ({total}个)")

    def refresh_cover_tasks_display(self):
        """刷新封面任务显示 - 支持分页"""
        for task_id, frame in list(self.cover_task_frames.items()):
            frame.destroy()
        self.cover_task_frames.clear()

        if not self.cover_tasks:
            self.cover_empty_label.pack()
            self._update_cover_pagination_label()
            return

        total_tasks = len(self.cover_tasks)
        total_pages = (total_tasks + self.tasks_per_page - 1) // self.tasks_per_page

        if self.cover_current_page >= total_pages:
            self.cover_current_page = max(0, total_pages - 1)

        start_idx = self.cover_current_page * self.tasks_per_page
        end_idx = min(start_idx + self.tasks_per_page, total_tasks)

        for i in range(start_idx, end_idx):
            task = self.cover_tasks[i]
            self.add_cover_task_to_ui(task)

        self._update_cover_pagination_label()

    def cover_previous_page(self):
        if self.cover_current_page > 0:
            self.cover_current_page -= 1
            self.refresh_cover_tasks_display()

    def cover_next_page(self):
        total_pages = (len(self.cover_tasks) + self.tasks_per_page - 1) // self.tasks_per_page
        if self.cover_current_page < total_pages - 1:
            self.cover_current_page += 1
            self.refresh_cover_tasks_display()

    def _update_cover_pagination_label(self):
        total = len(self.cover_tasks)
        if total == 0:
            self.cover_page_label.config(text="1/1 页")
            return
        pages = (total + self.tasks_per_page - 1) // self.tasks_per_page
        self.cover_page_label.config(text=f"{self.cover_current_page + 1}/{pages} 页 ({total}个)")

    def run(self):
        """运行应用"""
        self.window.mainloop()


def main():
    """主函数"""
    app = OutlineGeneratorWithQueue()
    app.run()


if __name__ == '__main__':
    main()
