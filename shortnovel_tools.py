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

## Output Format
Please provide:
1. Title
2. Genre
3. Main Characters (2-4 characters)
4. Plot Summary (500-1000 words)
5. Key Scenes (5-8 scenes with brief descriptions)

Now create the outline based on the input story concept:"""

DEFAULT_WRITING_PROMPT = """You are a professional web novel writer. Write a complete short story based on the provided outline.

## Requirements
- Write between 25000-50000 characters
- Use engaging, fast-paced narrative style
- Include plenty of dialogue
- Create satisfying moments throughout the story
- Use Western names and settings
- Output ONLY the story content, no explanations or meta-commentary

## Outline
{outline}

Now write the complete story:"""


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
                'versions': {}
            },
            'writing': {
                'default': DEFAULT_WRITING_PROMPT,
                'versions': {}
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
        """获取大纲Prompt"""
        if version and version in self.prompts['outline'].get('versions', {}):
            return self.prompts['outline']['versions'][version]
        return self.prompts['outline']['default']

    def get_writing_prompt(self, version=None):
        """获取写作Prompt"""
        if version and version in self.prompts['writing'].get('versions', {}):
            return self.prompts['writing']['versions'][version]
        return self.prompts['writing']['default']

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
    def __init__(self, task_id, source_file, config_params):
        self.task_id = task_id
        self.source_file = source_file
        self.config = config_params
        self.status = 'pending'
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.output_file = None
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

        # 分页设置
        self.outline_current_page = 0
        self.writing_current_page = 0
        self.tasks_per_page = 10

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
        self.model_var = tk.StringVar(value="gpt-4.1-mini")
        model_combo = ttk.Combobox(row1, textvariable=self.model_var, width=20)
        model_combo['values'] = ["gpt-4.1-mini", "gpt-4.1", "gpt-4o", "gpt-4o-mini", "gpt-5-mini", "claude-sonnet-4-20250514"]
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
            client = OpenAI(
                api_key=self.api_key_var.get(),
                base_url=self.base_url_var.get().rstrip('/') + '/v1'
            )
            response = client.chat.completions.create(
                model=self.model_var.get(),
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=10
            )
            self.api_status.config(text="✅ 连接成功", fg="green")
        except Exception as e:
            self.api_status.config(text=f"❌ 失败: {str(e)[:30]}", fg="red")

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
        self.outline_male_count = tk.IntVar(value=5)
        tk.Spinbox(names_row, from_=1, to=20, textvariable=self.outline_male_count, width=5).pack(side=tk.LEFT, padx=2)

        tk.Label(names_row, text="女:").pack(side=tk.LEFT, padx=(10, 0))
        self.outline_female_count = tk.IntVar(value=5)
        tk.Spinbox(names_row, from_=1, to=20, textvariable=self.outline_female_count, width=5).pack(side=tk.LEFT, padx=2)

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

        tk.Button(file_row, text="选择大纲文件", command=self.select_writing_file, width=12).pack(side=tk.LEFT)
        tk.Button(file_row, text="选择大纲文件夹", command=self.select_writing_folder, width=14).pack(side=tk.LEFT, padx=5)
        self.writing_file_label = tk.Label(file_row, text="未选择文件", fg="gray")
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
                    'max_tokens': 16000
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
        """刷新大纲任务显示"""
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
        total_pages = (len(self.outline_tasks) - 1) // self.tasks_per_page + 1
        self.outline_current_page = min(self.outline_current_page, total_pages - 1)

        start_idx = self.outline_current_page * self.tasks_per_page
        end_idx = min(start_idx + self.tasks_per_page, len(self.outline_tasks))

        self.outline_page_label.config(text=f"{self.outline_current_page + 1}/{total_pages} 页")

        # 显示当前页的任务
        for task in self.outline_tasks[start_idx:end_idx]:
            self.create_outline_task_card(task)

    def create_outline_task_card(self, task):
        """创建大纲任务卡片"""
        card = tk.Frame(self.outline_queue_frame, bg="#f5f5f5", relief=tk.RIDGE, borderwidth=1)
        card.pack(fill=tk.X, padx=5, pady=3)

        # 文件名
        filename = os.path.basename(task.source_file)
        tk.Label(
            card, text=filename[:40] + "..." if len(filename) > 40 else filename,
            font=("Arial", 10, "bold"), bg="#f5f5f5", anchor="w"
        ).pack(side=tk.LEFT, padx=10, pady=8)

        # 状态标签
        status_text = {
            'pending': '⏳ 等待中',
            'running': '🔄 运行中',
            'completed': '✅ 完成',
            'failed': '❌ 失败'
        }
        status_color = {
            'pending': 'gray',
            'running': 'blue',
            'completed': 'green',
            'failed': 'red'
        }

        status_label = tk.Label(
            card, text=status_text.get(task.status, task.status),
            fg=status_color.get(task.status, 'black'), bg="#f5f5f5"
        )
        status_label.pack(side=tk.LEFT, padx=10)
        card.status_label = status_label

        # 字符数显示
        char_label = tk.Label(card, text="", fg="purple", bg="#f5f5f5")
        char_label.pack(side=tk.LEFT, padx=10)
        card.char_label = char_label

        if task.status == 'completed' and task.char_count > 0:
            char_label.config(text=f"📊 {task.char_count:,} 字符")
        elif task.status == 'failed' and task.error_msg:
            char_label.config(text=f"⚠️ {task.error_msg[:20]}...", fg="red")

        # 操作按钮
        btn_frame = tk.Frame(card, bg="#f5f5f5")
        btn_frame.pack(side=tk.RIGHT, padx=5)

        start_btn = tk.Button(
            btn_frame, text="▶", command=lambda t=task: self.start_outline_task(t),
            width=3, state=tk.NORMAL if task.status != 'running' else tk.DISABLED
        )
        start_btn.pack(side=tk.LEFT, padx=2)
        card.start_btn = start_btn

        tk.Button(
            btn_frame, text="🗑", command=lambda t=task: self.remove_outline_task(t),
            width=3
        ).pack(side=tk.LEFT, padx=2)

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
                base_url=task.config['base_url'].rstrip('/') + '/v1'
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

            # 保存结果
            output_folder = os.path.join(
                os.path.dirname(task.source_file),
                'outlines',
                os.path.splitext(os.path.basename(task.source_file))[0]
            )
            os.makedirs(output_folder, exist_ok=True)

            output_file = os.path.join(output_folder, '_full_outline.txt')
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result)

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
        """选择大纲文件添加写作任务"""
        files = filedialog.askopenfilenames(
            title="选择大纲文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if files:
            self.writing_selected_files = list(files)
            self.writing_file_label.config(
                text=f"已选择 {len(files)} 个文件",
                fg="black"
            )

    def select_writing_folder(self):
        """选择文件夹批量添加写作任务"""
        folder = filedialog.askdirectory(title="选择包含大纲的文件夹")
        if folder:
            import glob
            # 搜索所有大纲文件
            files = []
            for pattern in ['**/outline*.txt', '**/*_outline*.txt', '**/full_outline*.txt', '**/_full_outline.txt']:
                files.extend(glob.glob(os.path.join(folder, pattern), recursive=True))

            # 也直接搜索.txt文件
            if not files:
                files = glob.glob(os.path.join(folder, "*.txt"))

            if files:
                self.writing_selected_files = list(set(files))  # 去重
                self.writing_file_label.config(
                    text=f"已选择 {len(self.writing_selected_files)} 个文件",
                    fg="black"
                )
            else:
                messagebox.showwarning("警告", "文件夹中没有找到大纲文件")

    def add_writing_tasks(self):
        """添加写作任务到队列"""
        if not hasattr(self, 'writing_selected_files') or not self.writing_selected_files:
            messagebox.showwarning("警告", "请先选择文件")
            return

        if len(self.writing_tasks) + len(self.writing_selected_files) > self.MAX_TASKS:
            messagebox.showwarning("警告", f"任务数量超过上限 {self.MAX_TASKS}")
            return

        added = 0
        for file_path in self.writing_selected_files:
            if any(t.source_file == file_path for t in self.writing_tasks):
                continue

            task = WritingTask(
                task_id=str(uuid.uuid4()),
                source_file=file_path,
                config_params={
                    'model': self.model_var.get(),
                    'api_key': self.api_key_var.get(),
                    'base_url': self.base_url_var.get(),
                    'min_chars': self.min_chars.get(),
                    'max_chars': self.max_chars.get(),
                    'max_tokens': 60000
                }
            )
            self.writing_tasks.append(task)
            added += 1

        self.writing_selected_files = []
        self.writing_file_label.config(text="未选择文件", fg="gray")
        self.refresh_writing_display()
        self.update_writing_progress()

        if added > 0:
            messagebox.showinfo("成功", f"已添加 {added} 个任务")

    def refresh_writing_display(self):
        """刷新写作任务显示"""
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

        total_pages = (len(self.writing_tasks) - 1) // self.tasks_per_page + 1
        self.writing_current_page = min(self.writing_current_page, total_pages - 1)

        start_idx = self.writing_current_page * self.tasks_per_page
        end_idx = min(start_idx + self.tasks_per_page, len(self.writing_tasks))

        self.writing_page_label.config(text=f"{self.writing_current_page + 1}/{total_pages} 页")

        for task in self.writing_tasks[start_idx:end_idx]:
            self.create_writing_task_card(task)

    def create_writing_task_card(self, task):
        """创建写作任务卡片"""
        card = tk.Frame(self.writing_queue_frame, bg="#f5f5f5", relief=tk.RIDGE, borderwidth=1)
        card.pack(fill=tk.X, padx=5, pady=3)

        filename = os.path.basename(task.source_file)
        tk.Label(
            card, text=filename[:40] + "..." if len(filename) > 40 else filename,
            font=("Arial", 10, "bold"), bg="#f5f5f5", anchor="w"
        ).pack(side=tk.LEFT, padx=10, pady=8)

        status_text = {
            'pending': '⏳ 等待中',
            'running': '🔄 运行中',
            'completed': '✅ 完成',
            'failed': '❌ 失败'
        }
        status_color = {
            'pending': 'gray',
            'running': 'blue',
            'completed': 'green',
            'failed': 'red'
        }

        status_label = tk.Label(
            card, text=status_text.get(task.status, task.status),
            fg=status_color.get(task.status, 'black'), bg="#f5f5f5"
        )
        status_label.pack(side=tk.LEFT, padx=10)
        card.status_label = status_label

        # 字符数显示
        char_label = tk.Label(card, text="", fg="purple", bg="#f5f5f5")
        char_label.pack(side=tk.LEFT, padx=10)
        card.char_label = char_label

        if task.status == 'completed' and task.char_count > 0:
            char_label.config(text=f"📊 {task.char_count:,} 字符")
        elif task.status == 'failed' and task.error_msg:
            char_label.config(text=f"⚠️ {task.error_msg[:20]}...", fg="red")

        btn_frame = tk.Frame(card, bg="#f5f5f5")
        btn_frame.pack(side=tk.RIGHT, padx=5)

        start_btn = tk.Button(
            btn_frame, text="▶", command=lambda t=task: self.start_writing_task(t),
            width=3, state=tk.NORMAL if task.status != 'running' else tk.DISABLED
        )
        start_btn.pack(side=tk.LEFT, padx=2)
        card.start_btn = start_btn

        tk.Button(
            btn_frame, text="🗑", command=lambda t=task: self.remove_writing_task(t),
            width=3
        ).pack(side=tk.LEFT, padx=2)

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
Write the complete story now:"""

            # 调用API
            client = OpenAI(
                api_key=task.config['api_key'],
                base_url=task.config['base_url'].rstrip('/') + '/v1'
            )

            response = client.chat.completions.create(
                model=task.config['model'],
                messages=[{"role": "user", "content": full_prompt}],
                max_tokens=task.config['max_tokens'],
                temperature=0.85
            )

            result = response.choices[0].message.content
            task.char_count = len(result)

            # 保存结果
            output_dir = os.path.dirname(task.source_file)
            base_name = os.path.splitext(os.path.basename(task.source_file))[0]
            output_file = os.path.join(output_dir, f"{base_name}_story.txt")

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result)

            task.output_file = output_file
            task.status = 'completed'
            task.completed_at = datetime.now()

        except Exception as e:
            task.status = 'failed'
            task.error_msg = str(e)
            print(f"写作任务失败: {e}")

        self.window.after(0, self.refresh_writing_display)
        self.window.after(0, self.update_writing_progress)

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

        if total > 0:
            percent = int(completed / total * 100)
            self.writing_progress_bar['value'] = percent
            self.writing_progress_label.config(text=f"进度: {completed}/{total} ({percent}%)")
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
        manager_window.geometry("800x600")

        # 版本选择
        version_frame = tk.Frame(manager_window)
        version_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(version_frame, text="版本:").pack(side=tk.LEFT)
        version_var = tk.StringVar(value='default')

        if prompt_type == 'outline':
            versions = self.prompt_mgr.get_outline_versions()
        else:
            versions = self.prompt_mgr.get_writing_versions()

        version_combo = ttk.Combobox(version_frame, textvariable=version_var, width=20)
        version_combo['values'] = versions
        version_combo.pack(side=tk.LEFT, padx=5)

        # 文本编辑区域
        text_widget = scrolledtext.ScrolledText(manager_window, wrap=tk.WORD, font=("Courier", 10))
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 加载当前版本内容
        def load_version(*args):
            version = version_var.get()
            version = None if version == 'default' else version
            if prompt_type == 'outline':
                content = self.prompt_mgr.get_outline_prompt(version)
            else:
                content = self.prompt_mgr.get_writing_prompt(version)
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
                else:
                    self.prompt_mgr.save_writing_prompt(name, content)
                version_combo['values'] = self.prompt_mgr.get_outline_versions() if prompt_type == 'outline' else self.prompt_mgr.get_writing_versions()
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

        tk.Button(btn_frame, text="保存当前版本", command=save_current, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="另存为新版本", command=save_as_new, width=15).pack(side=tk.LEFT, padx=5)
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
