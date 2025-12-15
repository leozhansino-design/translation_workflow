"""
短篇小说工具 - Short Novel Tools
独立的短篇小说生成工具，包含大纲生成和写作生成两个功能
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import json
import os
import sys
import uuid
import shutil
from datetime import datetime
from openai import OpenAI

# 修复Mac上的SSL证书验证问题
import ssl
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except AttributeError:
    pass

from resource_mgr import ResourceManager


def get_resource_path(relative_path):
    """获取资源文件的绝对路径（支持PyInstaller打包）"""
    if getattr(sys, 'frozen', False):
        app_name = "ShortNovelTools"
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
                import shutil
                shutil.copy2(bundled_path, user_path)
                return user_path
        except Exception:
            pass
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        return os.path.join(os.getcwd(), relative_path)


# 默认Prompt模板
DEFAULT_OUTLINE_PROMPT = """You are a professional web novel outline writer. Create a detailed outline for a short story.

## Name Suggestions
Male names: {male_names}
Female names: {female_names}

## Requirements
- Create a compelling short story outline
- Include main characters, plot points, and key scenes
- The story should be engaging and have a satisfying arc
- Use Western names and settings

## CRITICAL: Output Format (MUST follow exactly)
You MUST output in this EXACT format with these markers:

===TITLE===
[Your story title here]

===GENRE===
[Genre like: Romance, Fantasy, Urban, Thriller, etc.]

===AGE===
[Target audience: 18-25, 25-35, 35-45, etc.]

===OUTLINE===
[Complete detailed outline including:
- Main Characters (2-4 characters with descriptions)
- Plot Summary (500-1000 words)
- Key Scenes (5-8 scenes with brief descriptions)]

===END===

IMPORTANT: You MUST include all markers (===TITLE===, ===GENRE===, ===AGE===, ===OUTLINE===, ===END===) in your response.

Now create the outline based on the input story concept:"""

DEFAULT_WRITING_PROMPT = """You are a professional web novel writer. Write a complete short story based on the provided outline.

## Requirements
- Write between 25000-50000 characters
- Use engaging, fast-paced narrative style
- Include plenty of dialogue
- Create satisfying moments throughout the story
- Use Western names and settings
- Output ONLY the story content, no explanations or meta-commentary

## CRITICAL: Completion Marker
When you finish the story, you MUST end with this exact marker on its own line:
===END===

This marker indicates the story is complete. DO NOT forget this marker!

## Outline
{outline}

Now write the complete story (remember to end with ===END===):"""


class ShortNovelPromptManager:
    """短篇小说Prompt管理器"""

    def __init__(self):
        self.prompts_file = get_resource_path('data/shortnovel_prompts.json')
        self.prompts = self.load_prompts()

    def load_prompts(self):
        """加载Prompt配置"""
        try:
            if os.path.exists(self.prompts_file):
                with open(self.prompts_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载Prompt配置失败: {e}")

        # 返回默认配置
        return {
            'outline': {
                'default': DEFAULT_OUTLINE_PROMPT,
                'versions': {},
                'active': 'default'  # 活跃版本
            },
            'writing': {
                'default': DEFAULT_WRITING_PROMPT,
                'versions': {},
                'active': 'default'  # 活跃版本
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

    def get_outline_prompt(self, version=None):
        """获取大纲Prompt（默认使用活跃版本）"""
        if version is None:
            version = self.prompts['outline'].get('active', 'default')
        if version != 'default' and version in self.prompts['outline'].get('versions', {}):
            return self.prompts['outline']['versions'][version]
        return self.prompts['outline']['default']

    def get_writing_prompt(self, version=None):
        """获取写作Prompt（默认使用活跃版本）"""
        if version is None:
            version = self.prompts['writing'].get('active', 'default')
        if version != 'default' and version in self.prompts['writing'].get('versions', {}):
            return self.prompts['writing']['versions'][version]
        return self.prompts['writing']['default']

    def get_active_outline_version(self):
        """获取大纲活跃版本名称"""
        return self.prompts['outline'].get('active', 'default')

    def get_active_writing_version(self):
        """获取写作活跃版本名称"""
        return self.prompts['writing'].get('active', 'default')

    def set_active_outline_version(self, version):
        """设置大纲活跃版本"""
        self.prompts['outline']['active'] = version
        self.save_prompts()

    def set_active_writing_version(self, version):
        """设置写作活跃版本"""
        self.prompts['writing']['active'] = version
        self.save_prompts()

    def save_outline_prompt(self, name, content):
        """保存大纲Prompt版本"""
        if 'versions' not in self.prompts['outline']:
            self.prompts['outline']['versions'] = {}
        self.prompts['outline']['versions'][name] = content
        self.save_prompts()

    def save_writing_prompt(self, name, content):
        """保存写作Prompt版本"""
        if 'versions' not in self.prompts['writing']:
            self.prompts['writing']['versions'] = {}
        self.prompts['writing']['versions'][name] = content
        self.save_prompts()

    def get_outline_versions(self):
        """获取大纲Prompt版本列表"""
        return ['default'] + list(self.prompts['outline'].get('versions', {}).keys())

    def get_writing_versions(self):
        """获取写作Prompt版本列表"""
        return ['default'] + list(self.prompts['writing'].get('versions', {}).keys())


class OutlineTask:
    """大纲生成任务"""
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
        self.error_msg = None


class WritingTask:
    """写作生成任务"""
    def __init__(self, task_id, source_file, config_params, title=None, outline_folder=None):
        self.task_id = task_id
        self.source_file = source_file  # outline.txt 或 full_outline.txt 的路径
        self.config = config_params
        self.title = title  # 从 title.txt 读取的标题
        self.outline_folder = outline_folder  # 大纲文件夹路径
        self.status = 'pending'
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.output_file = None
        self.output_folder = None
        self.char_count = 0
        self.error_msg = None


class ShortNovelTools:
    """短篇小说工具主界面"""

    MAX_TASKS = 1000  # 最大任务数

    def __init__(self):
        self.window = tk.Tk()
        self.window.title("短篇小说工具 - Short Novel Tools")
        self.window.geometry("1400x900")

        # 初始化管理器
        self.resource_mgr = ResourceManager()
        self.prompt_mgr = ShortNovelPromptManager()

        # 任务列表
        self.outline_tasks = []
        self.outline_task_frames = {}
        self.writing_tasks = []
        self.writing_task_frames = {}

        # 分页设置 - 多列网格布局
        self.outline_current_page = 0
        self.writing_current_page = 0
        self.cards_per_row = 5  # 每行卡片数
        self.rows_per_page = 10  # 每页行数
        self.tasks_per_page = self.cards_per_row * self.rows_per_page  # 50个/页

        # 运行状态
        self.outline_running = False
        self.writing_running = False

        # 设置界面
        self.setup_ui()

    def setup_ui(self):
        """设置界面"""
        # 标题栏
        title_frame = tk.Frame(self.window, bg="#673AB7", height=50)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        tk.Label(
            title_frame,
            text="📚 短篇小说工具 - Short Novel Tools",
            font=("Arial", 18, "bold"),
            bg="#673AB7",
            fg="white"
        ).pack(side=tk.LEFT, padx=20, pady=10)

        # API配置区域
        self.setup_api_config()

        # 创建Notebook（标签页）
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 大纲生成标签页
        self.outline_tab = tk.Frame(self.notebook)
        self.notebook.add(self.outline_tab, text="📝 大纲生成")
        self.setup_outline_tab()

        # 写作生成标签页
        self.writing_tab = tk.Frame(self.notebook)
        self.notebook.add(self.writing_tab, text="✍️ 写作生成")
        self.setup_writing_tab()

    def setup_api_config(self):
        """设置API配置区域"""
        api_frame = tk.LabelFrame(self.window, text="API 配置", padx=10, pady=5)
        api_frame.pack(fill=tk.X, padx=10, pady=5)

        # API预设
        self.api_presets = {
            "BLTCY API (api.bltcy.ai)": {
                "api_key": "sk-z4a6qvhXCbfboOyBwL33BR66mJdHTKj5NO4pfIUSkLBm2jGF",
                "base_url": "https://api.bltcy.ai"
            },
            "云雾API (yunwuapi.com)": {
                "api_key": "sk-4FqZoOFgSYHP6Vfk9HGqhGyrPJjNTVwnaB6zVAbLp8UdlCln",
                "base_url": "https://yunwuapi.com"
            },
            "自定义配置": {
                "api_key": "",
                "base_url": ""
            }
        }

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
        """API预设改变时更新输入框"""
        preset = self.api_preset_var.get()
        if preset in self.api_presets:
            self.api_key_var.set(self.api_presets[preset]['api_key'])
            self.base_url_var.set(self.api_presets[preset]['base_url'])

    def test_api(self):
        """测试API连接"""
        self.api_status.config(text="测试中...", fg="blue")
        self.window.update()

        try:
            base_url = self._normalize_base_url(self.base_url_var.get())
            client = OpenAI(
                api_key=self.api_key_var.get(),
                base_url=base_url
            )
            response = client.chat.completions.create(
                model=self.model_var.get(),
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=100,
                temperature=0.85
            )
            self.api_status.config(text="✅ 连接成功", fg="green")
        except Exception as e:
            error_msg = str(e)
            print(f"API测试失败详情: {error_msg}")  # 打印完整错误到控制台
            self.api_status.config(text=f"❌ 失败: {error_msg[:50]}", fg="red")

    def _normalize_base_url(self, url):
        """规范化Base URL，确保正确的格式"""
        url = url.strip().rstrip('/')
        # 如果已经以 /v1 结尾，不再添加
        if url.endswith('/v1'):
            return url
        # 否则添加 /v1
        return url + '/v1'

    def setup_outline_tab(self):
        """设置大纲生成标签页"""
        # 控制面板
        control_frame = tk.Frame(self.outline_tab)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        # 左侧：文件选择和人名配置
        left_frame = tk.Frame(control_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 文件选择
        file_row = tk.Frame(left_frame)
        file_row.pack(fill=tk.X, pady=2)

        tk.Button(file_row, text="选择文件", command=self.select_outline_file, width=10).pack(side=tk.LEFT)
        tk.Button(file_row, text="选择文件夹", command=self.select_outline_folder, width=10).pack(side=tk.LEFT, padx=5)
        self.outline_file_label = tk.Label(file_row, text="未选择文件", fg="gray")
        self.outline_file_label.pack(side=tk.LEFT, padx=10)

        # 人名配置
        names_row = tk.Frame(left_frame)
        names_row.pack(fill=tk.X, pady=2)

        tk.Label(names_row, text="人名数量 - 男:").pack(side=tk.LEFT)
        self.outline_male_count = tk.IntVar(value=10)
        tk.Spinbox(names_row, from_=1, to=20, textvariable=self.outline_male_count, width=5).pack(side=tk.LEFT, padx=2)

        tk.Label(names_row, text="女:").pack(side=tk.LEFT, padx=(10, 0))
        self.outline_female_count = tk.IntVar(value=10)
        tk.Spinbox(names_row, from_=1, to=20, textvariable=self.outline_female_count, width=5).pack(side=tk.LEFT, padx=2)

        # 输出路径配置
        output_row = tk.Frame(left_frame)
        output_row.pack(fill=tk.X, pady=2)

        tk.Label(output_row, text="输出路径:").pack(side=tk.LEFT)
        self.outline_output_var = tk.StringVar(value="D:\\shortnovels_outline")
        tk.Entry(output_row, textvariable=self.outline_output_var, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(output_row, text="浏览", command=self.select_outline_output_folder, width=6).pack(side=tk.LEFT)

        # 右侧：操作按钮
        right_frame = tk.Frame(control_frame)
        right_frame.pack(side=tk.RIGHT)

        tk.Button(
            right_frame, text="添加任务", command=self.add_outline_tasks,
            bg="#4CAF50", fg="white", width=12
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            right_frame, text="▶ 全部开始", command=self.start_all_outline_tasks,
            bg="#2196F3", fg="white", width=12
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            right_frame, text="🗑 清空", command=self.clear_outline_tasks,
            bg="#f44336", fg="white", width=8
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            right_frame, text="⚙ Prompt管理", command=self.manage_outline_prompts,
            width=12
        ).pack(side=tk.LEFT, padx=2)

        # 进度条
        progress_frame = tk.Frame(self.outline_tab)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)

        self.outline_progress_label = tk.Label(progress_frame, text="进度: 0/0 (0%)")
        self.outline_progress_label.pack(side=tk.LEFT)

        self.outline_progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=400)
        self.outline_progress_bar.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        # 分页控制
        pagination_frame = tk.Frame(self.outline_tab)
        pagination_frame.pack(fill=tk.X, padx=10)

        tk.Button(pagination_frame, text="◀ 上一页", command=self.outline_prev_page, width=10).pack(side=tk.LEFT)
        self.outline_page_label = tk.Label(pagination_frame, text="1/1 页")
        self.outline_page_label.pack(side=tk.LEFT, padx=20)
        tk.Button(pagination_frame, text="下一页 ▶", command=self.outline_next_page, width=10).pack(side=tk.LEFT)

        # 任务列表区域
        task_container = tk.Frame(self.outline_tab)
        task_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        canvas = tk.Canvas(task_container, bg="white")
        scrollbar = ttk.Scrollbar(task_container, orient="vertical", command=canvas.yview)

        self.outline_queue_frame = tk.Frame(canvas, bg="white")
        self.outline_queue_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.outline_queue_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 空队列提示
        self.outline_empty_label = tk.Label(
            self.outline_queue_frame,
            text="暂无任务\n点击「选择文件」或「选择文件夹」添加任务",
            font=("Arial", 10),
            fg="gray",
            bg="white",
            pady=50
        )
        self.outline_empty_label.pack()

    def setup_writing_tab(self):
        """设置写作生成标签页"""
        # 控制面板
        control_frame = tk.Frame(self.writing_tab)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        # 左侧：文件选择
        left_frame = tk.Frame(control_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        file_row = tk.Frame(left_frame)
        file_row.pack(fill=tk.X, pady=2)

        tk.Button(file_row, text="选择单个大纲", command=self.select_writing_file, width=12).pack(side=tk.LEFT)
        tk.Button(file_row, text="批量选择", command=self.select_writing_folder, width=10).pack(side=tk.LEFT, padx=5)
        self.writing_file_label = tk.Label(file_row, text="未选择文件夹", fg="gray")
        self.writing_file_label.pack(side=tk.LEFT, padx=10)

        # 字符数配置
        char_row = tk.Frame(left_frame)
        char_row.pack(fill=tk.X, pady=2)

        tk.Label(char_row, text="目标字符数:").pack(side=tk.LEFT)
        self.min_chars = tk.IntVar(value=25000)
        tk.Entry(char_row, textvariable=self.min_chars, width=8).pack(side=tk.LEFT, padx=2)
        tk.Label(char_row, text="-").pack(side=tk.LEFT)
        self.max_chars = tk.IntVar(value=50000)
        tk.Entry(char_row, textvariable=self.max_chars, width=8).pack(side=tk.LEFT, padx=2)
        tk.Label(char_row, text="字符").pack(side=tk.LEFT)

        # 输出路径配置
        output_row = tk.Frame(left_frame)
        output_row.pack(fill=tk.X, pady=2)

        tk.Label(output_row, text="输出路径:").pack(side=tk.LEFT)
        self.writing_output_var = tk.StringVar(value="D:\\shortnovels_translation_readytoupload")
        tk.Entry(output_row, textvariable=self.writing_output_var, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(output_row, text="浏览", command=self.select_writing_output_folder, width=6).pack(side=tk.LEFT)

        # 右侧：操作按钮
        right_frame = tk.Frame(control_frame)
        right_frame.pack(side=tk.RIGHT)

        tk.Button(
            right_frame, text="添加任务", command=self.add_writing_tasks,
            bg="#4CAF50", fg="white", width=12
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            right_frame, text="▶ 全部开始", command=self.start_all_writing_tasks,
            bg="#2196F3", fg="white", width=12
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            right_frame, text="🗑 清空", command=self.clear_writing_tasks,
            bg="#f44336", fg="white", width=8
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            right_frame, text="⚙ Prompt管理", command=self.manage_writing_prompts,
            width=12
        ).pack(side=tk.LEFT, padx=2)

        # 进度条
        progress_frame = tk.Frame(self.writing_tab)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)

        self.writing_progress_label = tk.Label(progress_frame, text="进度: 0/0 (0%)")
        self.writing_progress_label.pack(side=tk.LEFT)

        self.writing_progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=400)
        self.writing_progress_bar.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        # 分页控制
        pagination_frame = tk.Frame(self.writing_tab)
        pagination_frame.pack(fill=tk.X, padx=10)

        tk.Button(pagination_frame, text="◀ 上一页", command=self.writing_prev_page, width=10).pack(side=tk.LEFT)
        self.writing_page_label = tk.Label(pagination_frame, text="1/1 页")
        self.writing_page_label.pack(side=tk.LEFT, padx=20)
        tk.Button(pagination_frame, text="下一页 ▶", command=self.writing_next_page, width=10).pack(side=tk.LEFT)

        # 任务列表区域
        task_container = tk.Frame(self.writing_tab)
        task_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        canvas = tk.Canvas(task_container, bg="white")
        scrollbar = ttk.Scrollbar(task_container, orient="vertical", command=canvas.yview)

        self.writing_queue_frame = tk.Frame(canvas, bg="white")
        self.writing_queue_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.writing_queue_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 空队列提示
        self.writing_empty_label = tk.Label(
            self.writing_queue_frame,
            text="暂无任务\n点击「选择大纲文件」或「选择大纲文件夹」添加任务",
            font=("Arial", 10),
            fg="gray",
            bg="white",
            pady=50
        )
        self.writing_empty_label.pack()

    # ===== 大纲生成功能 =====

    def select_outline_file(self):
        """选择单个文件添加大纲任务"""
        files = filedialog.askopenfilenames(
            title="选择原文文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if files:
            self.outline_selected_files = list(files)
            self.outline_file_label.config(
                text=f"已选择 {len(files)} 个文件",
                fg="black"
            )

    def select_outline_folder(self):
        """选择文件夹批量添加大纲任务"""
        folder = filedialog.askdirectory(title="选择包含原文的文件夹")
        if folder:
            import glob
            files = glob.glob(os.path.join(folder, "*.txt"))
            if files:
                self.outline_selected_files = files
                self.outline_file_label.config(
                    text=f"已选择 {len(files)} 个文件",
                    fg="black"
                )
            else:
                messagebox.showwarning("警告", "文件夹中没有找到.txt文件")

    def select_outline_output_folder(self):
        """选择大纲输出文件夹"""
        folder = filedialog.askdirectory(title="选择大纲输出文件夹")
        if folder:
            self.outline_output_var.set(folder)

    def select_writing_output_folder(self):
        """选择写作输出文件夹"""
        folder = filedialog.askdirectory(title="选择写作输出文件夹")
        if folder:
            self.writing_output_var.set(folder)

    def add_outline_tasks(self):
        """添加大纲任务到队列"""
        if not hasattr(self, 'outline_selected_files') or not self.outline_selected_files:
            messagebox.showwarning("警告", "请先选择文件")
            return

        # 检查任务数量限制
        if len(self.outline_tasks) + len(self.outline_selected_files) > self.MAX_TASKS:
            messagebox.showwarning("警告", f"任务数量超过上限 {self.MAX_TASKS}")
            return

        added = 0
        for file_path in self.outline_selected_files:
            # 检查是否已存在
            if any(t.source_file == file_path for t in self.outline_tasks):
                continue

            task = OutlineTask(
                task_id=str(uuid.uuid4()),
                source_file=file_path,
                config_params={
                    'model': self.model_var.get(),
                    'api_key': self.api_key_var.get(),
                    'base_url': self.base_url_var.get(),
                    'male_count': self.outline_male_count.get(),
                    'female_count': self.outline_female_count.get(),
                    'max_tokens': 16000,
                    'output_path': self.outline_output_var.get()
                }
            )
            self.outline_tasks.append(task)
            added += 1

        self.outline_selected_files = []
        self.outline_file_label.config(text="未选择文件", fg="gray")
        self.refresh_outline_display()
        self.update_outline_progress()

        if added > 0:
            messagebox.showinfo("成功", f"已添加 {added} 个任务")

    def refresh_outline_display(self):
        """刷新大纲任务显示 - 网格布局"""
        # 清空现有显示
        for widget in self.outline_queue_frame.winfo_children():
            widget.destroy()
        self.outline_task_frames.clear()

        if not self.outline_tasks:
            self.outline_empty_label = tk.Label(
                self.outline_queue_frame,
                text="暂无任务",
                font=("Arial", 10),
                fg="gray",
                bg="white",
                pady=50
            )
            self.outline_empty_label.pack()
            return

        # 计算分页
        total_pages = max(1, (len(self.outline_tasks) - 1) // self.tasks_per_page + 1)
        self.outline_current_page = min(self.outline_current_page, total_pages - 1)

        start_idx = self.outline_current_page * self.tasks_per_page
        end_idx = min(start_idx + self.tasks_per_page, len(self.outline_tasks))

        self.outline_page_label.config(text=f"{self.outline_current_page + 1}/{total_pages} 页 (共{len(self.outline_tasks)}个)")

        # 网格布局显示
        current_tasks = self.outline_tasks[start_idx:end_idx]
        for idx, task in enumerate(current_tasks):
            row = idx // self.cards_per_row
            col = idx % self.cards_per_row
            self.create_outline_task_card(task, row, col)

    def create_outline_task_card(self, task, row, col):
        """创建大纲任务卡片 - 紧凑网格样式"""
        card = tk.Frame(
            self.outline_queue_frame,
            bg="#ffffff",
            relief=tk.RAISED,
            borderwidth=2,
            width=260,
            height=90
        )
        card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
        card.grid_propagate(False)

        # 顶部色条（状态指示）
        status_colors = {
            'pending': '#9E9E9E',
            'running': '#2196F3',
            'completed': '#4CAF50',
            'failed': '#f44336'
        }
        top_bar = tk.Frame(card, bg=status_colors.get(task.status, '#9E9E9E'), height=4)
        top_bar.place(x=0, y=0, width=260)

        # 文件名（截断显示）
        filename = os.path.basename(task.source_file)
        display_name = filename[:22] + "..." if len(filename) > 22 else filename
        tk.Label(
            card, text=display_name,
            font=("Arial", 9), bg="#ffffff", anchor="w"
        ).place(x=8, y=8, width=200)

        # 状态图标
        status_info = {
            'pending': ('⏳', '#9E9E9E'),
            'running': ('🔄', '#2196F3'),
            'completed': ('✅', '#4CAF50'),
            'failed': ('❌', '#f44336')
        }
        icon, color = status_info.get(task.status, ('?', 'black'))
        status_label = tk.Label(card, text=icon, fg=color, bg="#ffffff", font=("Arial", 12))
        status_label.place(x=220, y=6)
        card.status_label = status_label

        # 第二行：启动时间或字符数
        info_text = "等待开始"
        info_color = "#757575"
        if task.status == 'running' and task.started_at:
            info_text = f"⏱ 开始于 {task.started_at.strftime('%H:%M:%S')}"
            info_color = "#2196F3"
        elif task.status == 'completed':
            info_text = f"📊 {task.char_count:,} 字符"
            info_color = "#7B1FA2"
        elif task.status == 'failed':
            info_text = f"⚠️ 生成失败"
            info_color = "#f44336"

        info_label = tk.Label(card, text=info_text, fg=info_color, bg="#ffffff", font=("Arial", 9))
        info_label.place(x=8, y=32)
        card.info_label = info_label

        # 底部按钮区域（带背景）
        btn_frame = tk.Frame(card, bg="#f5f5f5", height=30)
        btn_frame.place(x=0, y=60, width=260, height=30)

        start_btn = tk.Button(
            btn_frame, text="▶ 开始", command=lambda t=task: self.start_outline_task(t),
            width=6, font=("Arial", 8), bg="#4CAF50", fg="white",
            state=tk.NORMAL if task.status != 'running' else tk.DISABLED
        )
        start_btn.place(x=8, y=3)
        card.start_btn = start_btn

        tk.Button(
            btn_frame, text="🗑 删除", command=lambda t=task: self.remove_outline_task(t),
            width=6, font=("Arial", 8), bg="#f44336", fg="white"
        ).place(x=80, y=3)

        tk.Button(
            btn_frame, text="📋 预览", command=lambda t=task: self.preview_outline_prompt(t),
            width=6, font=("Arial", 8), bg="#2196F3", fg="white"
        ).place(x=152, y=3)

        self.outline_task_frames[task.task_id] = card

    def start_outline_task(self, task):
        """开始单个大纲任务"""
        if task.status == 'running':
            return

        task.status = 'running'
        task.started_at = datetime.now()
        self.refresh_outline_display()

        thread = threading.Thread(target=self._execute_outline_task, args=(task,), daemon=True)
        thread.start()

    def preview_outline_prompt(self, task):
        """预览大纲任务的Prompt"""
        try:
            # 读取原文
            with open(task.source_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 获取当前人名配置
            male_count = task.config.get('male_count', 10)
            female_count = task.config.get('female_count', 10)

            # 预览人名（不实际消耗，只是查看将要使用的名字）
            try:
                # 先加载最新的名字数据
                names_data = self.resource_mgr.load_names()
                print(f"[DEBUG] names_data loaded, male count: {len(names_data.get('male', []))}, female count: {len(names_data.get('female', []))}")

                # 按使用次数排序，获取将要被选中的名字
                male_sorted = sorted(names_data.get('male', []), key=lambda x: x.get('used', 0))
                female_sorted = sorted(names_data.get('female', []), key=lambda x: x.get('used', 0))

                print(f"[DEBUG] First male entry: {male_sorted[0] if male_sorted else 'EMPTY'}")

                # 使用 fullname 字段（和 format_names_for_prompt 一致）
                preview_male = [n['fullname'] for n in male_sorted[:male_count]]
                preview_female = [n['fullname'] for n in female_sorted[:female_count]]

                print(f"[DEBUG] preview_male: {preview_male}")

                male_names_str = ", ".join(preview_male) if preview_male else "(无可用男名)"
                female_names_str = ", ".join(preview_female) if preview_female else "(无可用女名)"
            except Exception as e:
                import traceback
                print(f"预览人名失败: {e}")
                traceback.print_exc()  # 打印完整错误堆栈
                male_names_str = f"(将随机选择{male_count}个男名)"
                female_names_str = f"(将随机选择{female_count}个女名)"

            # 构建Prompt
            prompt_template = self.prompt_mgr.get_outline_prompt()
            system_prompt = prompt_template.format(
                male_names=male_names_str,
                female_names=female_names_str
            )

            # 显示预览窗口
            self._show_prompt_preview(
                title=f"大纲Prompt预览 - {os.path.basename(task.source_file)}",
                system_prompt=system_prompt,
                user_content=content,
                config_info=f"模型: {task.config.get('model', 'N/A')}\n"
                           f"API: {task.config.get('base_url', 'N/A')}\n"
                           f"人名: 男{male_count}个, 女{female_count}个\n"
                           f"⚠️ 预览的人名为当前将被选中的名字（实际执行时会标记为已使用）"
            )
        except Exception as e:
            messagebox.showerror("错误", f"预览失败: {e}")

    def _show_prompt_preview(self, title, system_prompt, user_content, config_info=""):
        """显示Prompt预览窗口"""
        preview_window = tk.Toplevel(self.window)
        preview_window.title(title)
        preview_window.geometry("900x700")

        # 配置信息
        if config_info:
            config_frame = tk.Frame(preview_window, bg="#e3f2fd")
            config_frame.pack(fill=tk.X, padx=10, pady=5)
            tk.Label(config_frame, text=config_info, bg="#e3f2fd", justify=tk.LEFT,
                    font=("Arial", 9)).pack(padx=10, pady=5, anchor="w")

        # System Prompt
        tk.Label(preview_window, text="📋 System Prompt:", font=("Arial", 10, "bold"),
                anchor="w").pack(fill=tk.X, padx=10, pady=(10, 0))
        system_text = scrolledtext.ScrolledText(preview_window, height=12, wrap=tk.WORD)
        system_text.pack(fill=tk.X, padx=10, pady=5)
        system_text.insert(tk.END, system_prompt)
        system_text.config(state=tk.DISABLED)

        # User Content
        tk.Label(preview_window, text="📄 User Content (输入内容):", font=("Arial", 10, "bold"),
                anchor="w").pack(fill=tk.X, padx=10, pady=(10, 0))
        user_text = scrolledtext.ScrolledText(preview_window, height=15, wrap=tk.WORD)
        user_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        user_text.insert(tk.END, user_content)
        user_text.config(state=tk.DISABLED)

        # 关闭按钮
        tk.Button(preview_window, text="关闭", command=preview_window.destroy,
                 width=10).pack(pady=10)

    def _execute_outline_task(self, task):
        """执行大纲任务"""
        try:
            # 读取原文
            with open(task.source_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 获取人名
            selected_names = self.resource_mgr.select_names(
                task.config['male_count'],
                task.config['female_count']
            )
            names_formatted = self.resource_mgr.format_names_for_prompt(selected_names)

            # 构建Prompt
            prompt_template = self.prompt_mgr.get_outline_prompt()
            system_prompt = prompt_template.format(
                male_names=names_formatted['male_names'],
                female_names=names_formatted['female_names']
            )

            # 调用API
            client = OpenAI(
                api_key=task.config['api_key'],
                base_url=self._normalize_base_url(task.config['base_url'])
            )

            response = client.chat.completions.create(
                model=task.config['model'],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                max_tokens=task.config['max_tokens'],
                temperature=0.8
            )

            result = response.choices[0].message.content
            task.char_count = len(result)

            # 保存结果到配置的输出路径
            output_base = task.config.get('output_path', '')
            if output_base and os.path.isdir(output_base):
                # 使用配置的输出路径
                output_folder = os.path.join(
                    output_base,
                    os.path.splitext(os.path.basename(task.source_file))[0]
                )
            else:
                # 默认输出到源文件同目录
                output_folder = os.path.join(
                    os.path.dirname(task.source_file),
                    'outlines',
                    os.path.splitext(os.path.basename(task.source_file))[0]
                )
            os.makedirs(output_folder, exist_ok=True)

            # 保存完整结果
            output_file = os.path.join(output_folder, 'full_outline.txt')
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result)

            # 解析并保存各部分到单独文件
            self._parse_and_save_outline(result, output_folder, task)

            task.output_folder = output_folder
            task.status = 'completed'
            task.completed_at = datetime.now()

        except Exception as e:
            task.status = 'failed'
            task.error_msg = str(e)
            print(f"大纲任务失败: {e}")

        # 更新UI
        self.window.after(0, self.refresh_outline_display)
        self.window.after(0, self.update_outline_progress)

    def _parse_and_save_outline(self, result, output_folder, task):
        """解析大纲内容并保存为单独文件"""
        import re

        # 解析各部分
        sections = {
            'title': '',
            'genre': '',
            'age': '',
            'outline': ''
        }

        # 使用正则表达式提取各部分
        title_match = re.search(r'===TITLE===\s*(.*?)\s*(?====|$)', result, re.DOTALL)
        if title_match:
            sections['title'] = title_match.group(1).strip()

        genre_match = re.search(r'===GENRE===\s*(.*?)\s*(?====|$)', result, re.DOTALL)
        if genre_match:
            sections['genre'] = genre_match.group(1).strip()

        age_match = re.search(r'===AGE===\s*(.*?)\s*(?====|$)', result, re.DOTALL)
        if age_match:
            sections['age'] = age_match.group(1).strip()

        outline_match = re.search(r'===OUTLINE===\s*(.*?)\s*(?====END===|$)', result, re.DOTALL)
        if outline_match:
            sections['outline'] = outline_match.group(1).strip()

        # 检查是否有END标记（用于判断是否完整）
        has_end = '===END===' in result
        task.outline_complete = has_end

        # 保存各部分到单独文件
        for key, content in sections.items():
            if content:
                file_path = os.path.join(output_folder, f'{key}.txt')
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

        # 如果缺少关键部分，记录警告
        missing_parts = [k for k, v in sections.items() if not v]
        if missing_parts:
            task.warning_msg = f"缺少部分: {', '.join(missing_parts)}"
            print(f"警告: 大纲缺少部分 - {missing_parts}")

    def start_all_outline_tasks(self):
        """开始所有等待中的大纲任务"""
        pending_tasks = [t for t in self.outline_tasks if t.status == 'pending']
        if not pending_tasks:
            messagebox.showinfo("提示", "没有等待中的任务")
            return

        for task in pending_tasks:
            task.status = 'running'
            task.started_at = datetime.now()
            thread = threading.Thread(target=self._execute_outline_task, args=(task,), daemon=True)
            thread.start()

        self.refresh_outline_display()

    def remove_outline_task(self, task):
        """移除大纲任务"""
        if task.status == 'running':
            messagebox.showwarning("警告", "无法移除运行中的任务")
            return
        self.outline_tasks.remove(task)
        self.refresh_outline_display()
        self.update_outline_progress()

    def clear_outline_tasks(self):
        """清空大纲任务"""
        running = [t for t in self.outline_tasks if t.status == 'running']
        if running:
            messagebox.showwarning("警告", f"有 {len(running)} 个任务正在运行")
            return

        if messagebox.askyesno("确认", "确定要清空所有任务吗？"):
            self.outline_tasks.clear()
            self.refresh_outline_display()
            self.update_outline_progress()

    def update_outline_progress(self):
        """更新大纲进度条"""
        total = len(self.outline_tasks)
        completed = len([t for t in self.outline_tasks if t.status == 'completed'])

        if total > 0:
            percent = int(completed / total * 100)
            self.outline_progress_bar['value'] = percent
            self.outline_progress_label.config(text=f"进度: {completed}/{total} ({percent}%)")
        else:
            self.outline_progress_bar['value'] = 0
            self.outline_progress_label.config(text="进度: 0/0 (0%)")

    def outline_prev_page(self):
        """大纲上一页"""
        if self.outline_current_page > 0:
            self.outline_current_page -= 1
            self.refresh_outline_display()

    def outline_next_page(self):
        """大纲下一页"""
        total_pages = (len(self.outline_tasks) - 1) // self.tasks_per_page + 1
        if self.outline_current_page < total_pages - 1:
            self.outline_current_page += 1
            self.refresh_outline_display()

    def manage_outline_prompts(self):
        """管理大纲Prompt"""
        self._open_prompt_manager('outline')

    # ===== 写作生成功能 =====

    def select_writing_file(self):
        """选择单个大纲文件夹（包含title.txt, outline.txt等）"""
        folder = filedialog.askdirectory(title="选择大纲文件夹（包含title.txt和outline.txt）")
        if folder:
            # 检查是否是有效的大纲文件夹
            outline_info = self._parse_outline_folder(folder)
            if outline_info:
                self.writing_selected_folders = [outline_info]
                title_display = outline_info['title'][:30] + "..." if len(outline_info['title']) > 30 else outline_info['title']
                self.writing_file_label.config(
                    text=f"已选择: {title_display}",
                    fg="black"
                )
            else:
                messagebox.showwarning("警告", "所选文件夹不是有效的大纲文件夹\n需要包含 outline.txt 或 full_outline.txt")

    def select_writing_folder(self):
        """选择父文件夹，批量添加所有子文件夹中的大纲"""
        parent_folder = filedialog.askdirectory(title="选择包含多个大纲文件夹的父目录")
        if parent_folder:
            # 扫描所有子文件夹
            valid_folders = []
            for item in os.listdir(parent_folder):
                subfolder = os.path.join(parent_folder, item)
                if os.path.isdir(subfolder):
                    outline_info = self._parse_outline_folder(subfolder)
                    if outline_info:
                        valid_folders.append(outline_info)

            if valid_folders:
                self.writing_selected_folders = valid_folders
                self.writing_file_label.config(
                    text=f"已找到 {len(valid_folders)} 个大纲文件夹",
                    fg="black"
                )
            else:
                messagebox.showwarning("警告", "未找到有效的大纲文件夹\n每个子文件夹需要包含 outline.txt 或 full_outline.txt")

    def _parse_outline_folder(self, folder):
        """解析大纲文件夹，返回信息字典或None"""
        # 查找大纲文件（优先 outline.txt，其次 full_outline.txt）
        outline_file = None
        for filename in ['outline.txt', 'full_outline.txt']:
            path = os.path.join(folder, filename)
            if os.path.exists(path):
                outline_file = path
                break

        if not outline_file:
            return None

        # 读取标题（从title.txt，如果没有则用文件夹名）
        title = os.path.basename(folder)  # 默认用文件夹名
        title_file = os.path.join(folder, 'title.txt')
        if os.path.exists(title_file):
            try:
                with open(title_file, 'r', encoding='utf-8') as f:
                    title = f.read().strip()
            except:
                pass

        return {
            'folder': folder,
            'outline_file': outline_file,
            'title': title
        }

    def add_writing_tasks(self):
        """添加写作任务到队列"""
        if not hasattr(self, 'writing_selected_folders') or not self.writing_selected_folders:
            messagebox.showwarning("警告", "请先选择大纲文件夹")
            return

        if len(self.writing_tasks) + len(self.writing_selected_folders) > self.MAX_TASKS:
            messagebox.showwarning("警告", f"任务数量超过上限 {self.MAX_TASKS}")
            return

        added = 0
        for folder_info in self.writing_selected_folders:
            # 检查是否已存在相同的任务（按文件夹路径判断）
            if any(t.outline_folder == folder_info['folder'] for t in self.writing_tasks):
                continue

            task = WritingTask(
                task_id=str(uuid.uuid4()),
                source_file=folder_info['outline_file'],
                config_params={
                    'model': self.model_var.get(),
                    'api_key': self.api_key_var.get(),
                    'base_url': self.base_url_var.get(),
                    'min_chars': self.min_chars.get(),
                    'max_chars': self.max_chars.get(),
                    'max_tokens': 60000,
                    'output_path': self.writing_output_var.get()
                },
                title=folder_info['title'],
                outline_folder=folder_info['folder']
            )
            self.writing_tasks.append(task)
            added += 1

        self.writing_selected_folders = []
        self.writing_file_label.config(text="未选择文件夹", fg="gray")
        self.refresh_writing_display()
        self.update_writing_progress()

        if added > 0:
            messagebox.showinfo("成功", f"已添加 {added} 个写作任务")

    def refresh_writing_display(self):
        """刷新写作任务显示 - 网格布局"""
        for widget in self.writing_queue_frame.winfo_children():
            widget.destroy()
        self.writing_task_frames.clear()

        if not self.writing_tasks:
            self.writing_empty_label = tk.Label(
                self.writing_queue_frame,
                text="暂无任务",
                font=("Arial", 10),
                fg="gray",
                bg="white",
                pady=50
            )
            self.writing_empty_label.pack()
            return

        total_pages = max(1, (len(self.writing_tasks) - 1) // self.tasks_per_page + 1)
        self.writing_current_page = min(self.writing_current_page, total_pages - 1)

        start_idx = self.writing_current_page * self.tasks_per_page
        end_idx = min(start_idx + self.tasks_per_page, len(self.writing_tasks))

        self.writing_page_label.config(text=f"{self.writing_current_page + 1}/{total_pages} 页 (共{len(self.writing_tasks)}个)")

        # 网格布局显示
        current_tasks = self.writing_tasks[start_idx:end_idx]
        for idx, task in enumerate(current_tasks):
            row = idx // self.cards_per_row
            col = idx % self.cards_per_row
            self.create_writing_task_card(task, row, col)

    def create_writing_task_card(self, task, row, col):
        """创建写作任务卡片 - 紧凑网格样式"""
        card = tk.Frame(
            self.writing_queue_frame,
            bg="#ffffff",
            relief=tk.RAISED,
            borderwidth=2,
            width=260,
            height=90
        )
        card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
        card.grid_propagate(False)

        # 顶部色条（状态指示）- 写作用蓝紫色系
        status_colors = {
            'pending': '#9E9E9E',
            'running': '#673AB7',
            'completed': '#4CAF50',
            'incomplete': '#FF9800',  # 橙色表示未完成
            'failed': '#f44336'
        }
        top_bar = tk.Frame(card, bg=status_colors.get(task.status, '#9E9E9E'), height=4)
        top_bar.place(x=0, y=0, width=260)

        # 标题显示（优先用title，否则用文件夹名）
        display_name = task.title if task.title else os.path.basename(task.outline_folder or task.source_file)
        display_name = display_name[:25] + "..." if len(display_name) > 25 else display_name
        tk.Label(
            card, text=display_name,
            font=("Arial", 9), bg="#ffffff", anchor="w"
        ).place(x=8, y=8, width=200)

        # 状态图标
        status_info = {
            'pending': ('⏳', '#9E9E9E'),
            'running': ('🔄', '#673AB7'),
            'completed': ('✅', '#4CAF50'),
            'incomplete': ('⚠️', '#FF9800'),  # 橙色警告表示未完成
            'failed': ('❌', '#f44336')
        }
        icon, color = status_info.get(task.status, ('?', 'black'))
        status_label = tk.Label(card, text=icon, fg=color, bg="#ffffff", font=("Arial", 12))
        status_label.place(x=220, y=6)
        card.status_label = status_label

        # 第二行：启动时间或字符数
        info_text = "等待开始"
        info_color = "#757575"
        if task.status == 'running' and task.started_at:
            info_text = f"⏱ 开始于 {task.started_at.strftime('%H:%M:%S')}"
            info_color = "#673AB7"
        elif task.status == 'completed':
            info_text = f"✓ {task.char_count:,} 字符"
            info_color = "#4CAF50"
        elif task.status == 'incomplete':
            # 显示未完成原因
            warning = getattr(task, 'warning_msg', '未完成')
            info_text = f"⚠️ {task.char_count:,}字符 - {warning}"
            info_color = "#FF9800"
        elif task.status == 'failed':
            info_text = f"❌ 生成失败"
            info_color = "#f44336"

        info_label = tk.Label(card, text=info_text, fg=info_color, bg="#ffffff", font=("Arial", 9))
        info_label.place(x=8, y=32)
        card.info_label = info_label

        # 底部按钮区域（带背景）
        btn_frame = tk.Frame(card, bg="#f5f5f5", height=30)
        btn_frame.place(x=0, y=60, width=260, height=30)

        start_btn = tk.Button(
            btn_frame, text="▶ 开始", command=lambda t=task: self.start_writing_task(t),
            width=6, font=("Arial", 8), bg="#673AB7", fg="white",
            state=tk.NORMAL if task.status != 'running' else tk.DISABLED
        )
        start_btn.place(x=8, y=3)
        card.start_btn = start_btn

        tk.Button(
            btn_frame, text="🗑 删除", command=lambda t=task: self.remove_writing_task(t),
            width=6, font=("Arial", 8), bg="#f44336", fg="white"
        ).place(x=80, y=3)

        tk.Button(
            btn_frame, text="📋 预览", command=lambda t=task: self.preview_writing_prompt(t),
            width=6, font=("Arial", 8), bg="#673AB7", fg="white"
        ).place(x=152, y=3)

        self.writing_task_frames[task.task_id] = card

    def start_writing_task(self, task):
        """开始单个写作任务"""
        if task.status == 'running':
            return

        task.status = 'running'
        task.started_at = datetime.now()
        self.refresh_writing_display()

        thread = threading.Thread(target=self._execute_writing_task, args=(task,), daemon=True)
        thread.start()

    def preview_writing_prompt(self, task):
        """预览写作任务的Prompt"""
        try:
            # 读取大纲
            with open(task.source_file, 'r', encoding='utf-8') as f:
                outline = f.read()

            # 构建Prompt
            prompt_template = self.prompt_mgr.get_writing_prompt()
            prompt = prompt_template.format(outline=outline)

            # 添加字符数要求
            min_chars = task.config.get('min_chars', 25000)
            max_chars = task.config.get('max_chars', 50000)

            full_prompt = f"""{prompt}

IMPORTANT: The story must be between {min_chars} and {max_chars} characters. This is MANDATORY.
Write the complete story now (remember to end with ===END===):"""

            # 显示预览窗口
            self._show_prompt_preview(
                title=f"写作Prompt预览 - {os.path.basename(task.source_file)}",
                system_prompt="(无System Prompt，仅User Prompt)",
                user_content=full_prompt,
                config_info=f"模型: {task.config.get('model', 'N/A')}\n"
                           f"API: {task.config.get('base_url', 'N/A')}\n"
                           f"字符要求: {min_chars:,} - {max_chars:,}"
            )
        except Exception as e:
            messagebox.showerror("错误", f"预览失败: {e}")

    def _execute_writing_task(self, task):
        """执行写作任务"""
        try:
            # 读取大纲
            with open(task.source_file, 'r', encoding='utf-8') as f:
                outline = f.read()

            # 构建Prompt
            prompt_template = self.prompt_mgr.get_writing_prompt()
            prompt = prompt_template.format(outline=outline)

            # 添加字符数要求
            min_chars = task.config['min_chars']
            max_chars = task.config['max_chars']

            full_prompt = f"""{prompt}

IMPORTANT: The story must be between {min_chars} and {max_chars} characters. This is MANDATORY.
Write the complete story now (remember to end with ===END===):"""

            # 调用API
            client = OpenAI(
                api_key=task.config['api_key'],
                base_url=self._normalize_base_url(task.config['base_url'])
            )

            response = client.chat.completions.create(
                model=task.config['model'],
                messages=[{"role": "user", "content": full_prompt}],
                max_tokens=task.config['max_tokens'],
                temperature=0.85
            )

            result = response.choices[0].message.content
            task.char_count = len(result)

            # 检测是否有END标记（判断是否完整）
            has_end = '===END===' in result
            task.has_end_marker = has_end

            # 判断是否完成：需要有END标记且字符数达到最小要求
            is_complete = has_end and task.char_count >= min_chars
            task.story_complete = is_complete

            # 获取大纲文件夹路径（优先用task.outline_folder，否则用source_file的父目录）
            source_outline_folder = task.outline_folder or os.path.dirname(task.source_file)

            # 获取文件夹名（优先用task.title，否则用文件夹名）
            if task.title:
                folder_name = self._sanitize_folder_name(task.title)
            else:
                folder_name = os.path.basename(source_outline_folder)

            # 确定输出路径
            output_base = task.config.get('output_path', '')
            if output_base and os.path.isdir(output_base):
                # 使用配置的输出路径，以title为文件夹名
                output_folder = os.path.join(output_base, folder_name)
            else:
                # 默认输出到源文件同目录
                output_folder = os.path.join(os.path.dirname(source_outline_folder), folder_name + '_ready')

            os.makedirs(output_folder, exist_ok=True)

            # 复制大纲文件夹中的所有文件到输出文件夹
            self._copy_outline_files(source_outline_folder, output_folder)

            # 保存生成的正文到输出文件夹
            story_file = os.path.join(output_folder, 'story.txt')
            with open(story_file, 'w', encoding='utf-8') as f:
                f.write(result)

            task.output_file = story_file
            task.output_folder = output_folder

            # 根据完成状态设置不同状态
            if is_complete:
                task.status = 'completed'
            else:
                task.status = 'incomplete'  # 新增状态：未完成
                if not has_end:
                    task.warning_msg = "缺少END标记"
                elif task.char_count < min_chars:
                    task.warning_msg = f"字符数不足({task.char_count}<{min_chars})"

            task.completed_at = datetime.now()

        except Exception as e:
            task.status = 'failed'
            task.error_msg = str(e)
            print(f"写作任务失败: {e}")

        self.window.after(0, self.refresh_writing_display)
        self.window.after(0, self.update_writing_progress)

    def _sanitize_folder_name(self, name):
        """清理文件夹名称，移除不能用于文件夹名的字符"""
        import re
        # 移除Windows不允许的字符: \ / : * ? " < > |
        sanitized = re.sub(r'[\\/:*?"<>|]', '', name)
        # 移除前后空白
        sanitized = sanitized.strip()
        # 移除前后的点（Windows不允许）
        sanitized = sanitized.strip('.')
        # 限制长度（Windows最大255字符）
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        # 如果为空，返回默认名
        if not sanitized:
            sanitized = 'untitled'
        return sanitized

    def _copy_outline_files(self, source_folder, dest_folder):
        """复制大纲文件夹中的所有文件到目标文件夹"""
        # 需要复制的文件列表
        files_to_copy = ['title.txt', 'genre.txt', 'age.txt', 'outline.txt', 'full_outline.txt']

        for filename in files_to_copy:
            source_path = os.path.join(source_folder, filename)
            if os.path.exists(source_path):
                dest_path = os.path.join(dest_folder, filename)
                try:
                    shutil.copy2(source_path, dest_path)
                except Exception as e:
                    print(f"复制文件失败 {filename}: {e}")

        # 同时复制其他可能存在的文件（如原始输入文件等）
        for item in os.listdir(source_folder):
            if item not in files_to_copy:
                source_path = os.path.join(source_folder, item)
                dest_path = os.path.join(dest_folder, item)
                if os.path.isfile(source_path) and not os.path.exists(dest_path):
                    try:
                        shutil.copy2(source_path, dest_path)
                    except Exception as e:
                        print(f"复制文件失败 {item}: {e}")

    def start_all_writing_tasks(self):
        """开始所有等待中的写作任务"""
        pending_tasks = [t for t in self.writing_tasks if t.status == 'pending']
        if not pending_tasks:
            messagebox.showinfo("提示", "没有等待中的任务")
            return

        for task in pending_tasks:
            task.status = 'running'
            task.started_at = datetime.now()
            thread = threading.Thread(target=self._execute_writing_task, args=(task,), daemon=True)
            thread.start()

        self.refresh_writing_display()

    def remove_writing_task(self, task):
        """移除写作任务"""
        if task.status == 'running':
            messagebox.showwarning("警告", "无法移除运行中的任务")
            return
        self.writing_tasks.remove(task)
        self.refresh_writing_display()
        self.update_writing_progress()

    def clear_writing_tasks(self):
        """清空写作任务"""
        running = [t for t in self.writing_tasks if t.status == 'running']
        if running:
            messagebox.showwarning("警告", f"有 {len(running)} 个任务正在运行")
            return

        if messagebox.askyesno("确认", "确定要清空所有任务吗？"):
            self.writing_tasks.clear()
            self.refresh_writing_display()
            self.update_writing_progress()

    def update_writing_progress(self):
        """更新写作进度条"""
        total = len(self.writing_tasks)
        completed = len([t for t in self.writing_tasks if t.status == 'completed'])
        incomplete = len([t for t in self.writing_tasks if t.status == 'incomplete'])
        failed = len([t for t in self.writing_tasks if t.status == 'failed'])
        done = completed + incomplete + failed  # 所有已处理的任务

        if total > 0:
            percent = int(done / total * 100)
            self.writing_progress_bar['value'] = percent
            # 显示详细统计：完成/未完成/失败
            status_text = f"进度: {done}/{total} ({percent}%) - ✓{completed}"
            if incomplete > 0:
                status_text += f" ⚠{incomplete}"
            if failed > 0:
                status_text += f" ✗{failed}"
            self.writing_progress_label.config(text=status_text)
        else:
            self.writing_progress_bar['value'] = 0
            self.writing_progress_label.config(text="进度: 0/0 (0%)")

    def writing_prev_page(self):
        """写作上一页"""
        if self.writing_current_page > 0:
            self.writing_current_page -= 1
            self.refresh_writing_display()

    def writing_next_page(self):
        """写作下一页"""
        total_pages = (len(self.writing_tasks) - 1) // self.tasks_per_page + 1
        if self.writing_current_page < total_pages - 1:
            self.writing_current_page += 1
            self.refresh_writing_display()

    def manage_writing_prompts(self):
        """管理写作Prompt"""
        self._open_prompt_manager('writing')

    # ===== Prompt管理 =====

    def _open_prompt_manager(self, prompt_type):
        """打开Prompt管理窗口"""
        manager_window = tk.Toplevel(self.window)
        manager_window.title(f"Prompt管理 - {'大纲' if prompt_type == 'outline' else '写作'}")
        manager_window.geometry("900x650")

        # 顶部信息栏
        info_frame = tk.Frame(manager_window, bg="#e3f2fd", height=40)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        info_frame.pack_propagate(False)

        # 获取当前活跃版本
        if prompt_type == 'outline':
            active_version = self.prompt_mgr.get_active_outline_version()
        else:
            active_version = self.prompt_mgr.get_active_writing_version()

        active_label = tk.Label(
            info_frame,
            text=f"🔹 当前活跃版本: {active_version}",
            font=("Arial", 10, "bold"),
            bg="#e3f2fd",
            fg="#1565C0"
        )
        active_label.pack(side=tk.LEFT, padx=10, pady=8)

        # 版本选择
        version_frame = tk.Frame(manager_window)
        version_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(version_frame, text="选择版本:").pack(side=tk.LEFT)

        if prompt_type == 'outline':
            versions = self.prompt_mgr.get_outline_versions()
        else:
            versions = self.prompt_mgr.get_writing_versions()

        version_var = tk.StringVar(value=active_version)
        version_combo = ttk.Combobox(version_frame, textvariable=version_var, width=25)
        version_combo['values'] = versions
        version_combo.pack(side=tk.LEFT, padx=5)

        # 设为活跃按钮
        def set_active():
            version = version_var.get()
            if prompt_type == 'outline':
                self.prompt_mgr.set_active_outline_version(version)
            else:
                self.prompt_mgr.set_active_writing_version(version)
            active_label.config(text=f"🔹 当前活跃版本: {version}")
            messagebox.showinfo("成功", f"已将 '{version}' 设为活跃版本\n下次启动任务将使用此版本")

        tk.Button(
            version_frame, text="⭐ 设为活跃", command=set_active,
            bg="#FFC107", fg="black", width=12
        ).pack(side=tk.LEFT, padx=10)

        # 文本编辑区域
        text_widget = scrolledtext.ScrolledText(manager_window, wrap=tk.WORD, font=("Courier", 10))
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 加载当前版本内容
        def load_version(*args):
            version = version_var.get()
            version_to_load = None if version == 'default' else version
            if prompt_type == 'outline':
                content = self.prompt_mgr.get_outline_prompt(version_to_load)
            else:
                content = self.prompt_mgr.get_writing_prompt(version_to_load)
            text_widget.delete(1.0, tk.END)
            text_widget.insert(1.0, content)

        version_combo.bind('<<ComboboxSelected>>', load_version)
        load_version()

        # 按钮区域
        btn_frame = tk.Frame(manager_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        def save_as_new():
            name = tk.simpledialog.askstring("保存", "请输入版本名称:")
            if name:
                content = text_widget.get(1.0, tk.END).strip()
                if prompt_type == 'outline':
                    self.prompt_mgr.save_outline_prompt(name, content)
                    versions = self.prompt_mgr.get_outline_versions()
                else:
                    self.prompt_mgr.save_writing_prompt(name, content)
                    versions = self.prompt_mgr.get_writing_versions()
                version_combo['values'] = versions
                version_var.set(name)
                messagebox.showinfo("成功", f"已保存为 '{name}'")

        def save_current():
            version = version_var.get()
            if version == 'default':
                messagebox.showwarning("警告", "无法覆盖默认版本，请另存为新版本")
                return
            content = text_widget.get(1.0, tk.END).strip()
            if prompt_type == 'outline':
                self.prompt_mgr.save_outline_prompt(version, content)
            else:
                self.prompt_mgr.save_writing_prompt(version, content)
            messagebox.showinfo("成功", "已保存")

        def delete_version():
            version = version_var.get()
            if version == 'default':
                messagebox.showwarning("警告", "无法删除默认版本")
                return
            if messagebox.askyesno("确认", f"确定要删除版本 '{version}' 吗？"):
                if prompt_type == 'outline':
                    if version in self.prompt_mgr.prompts['outline']['versions']:
                        del self.prompt_mgr.prompts['outline']['versions'][version]
                        if self.prompt_mgr.get_active_outline_version() == version:
                            self.prompt_mgr.set_active_outline_version('default')
                            active_label.config(text="🔹 当前活跃版本: default")
                    versions = self.prompt_mgr.get_outline_versions()
                else:
                    if version in self.prompt_mgr.prompts['writing']['versions']:
                        del self.prompt_mgr.prompts['writing']['versions'][version]
                        if self.prompt_mgr.get_active_writing_version() == version:
                            self.prompt_mgr.set_active_writing_version('default')
                            active_label.config(text="🔹 当前活跃版本: default")
                    versions = self.prompt_mgr.get_writing_versions()
                self.prompt_mgr.save_prompts()
                version_combo['values'] = versions
                version_var.set('default')
                load_version()
                messagebox.showinfo("成功", f"已删除版本 '{version}'")

        tk.Button(btn_frame, text="保存当前版本", command=save_current, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="另存为新版本", command=save_as_new, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="删除版本", command=delete_version, width=10, bg="#f44336", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="关闭", command=manager_window.destroy, width=10).pack(side=tk.RIGHT, padx=5)

    def run(self):
        """运行主窗口"""
        self.window.mainloop()


# 添加simpledialog支持
import tkinter.simpledialog


def main():
    app = ShortNovelTools()
    app.run()


if __name__ == "__main__":
    main()
