"""
小说写作工具 - 主窗口
批量生成小说章节，支持断点续写
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import json
import time
import traceback
from datetime import datetime

from writer_worker import WriterWorker
from utils import scan_chapter_files


class WritingTask:
    """写作任务对象"""
    def __init__(self, outline_folder, config):
        self.outline_folder = outline_folder
        self.config = config
        self.status = 'pending'
        self.progress = 0
        self.current_chapter = 0
        self.total_chapters = config.get('end_chapter', 50)
        self.cost = 0.0
        self.started_at = None
        self.worker_thread = None
        self.title = os.path.basename(outline_folder)

        # 扫描已有章节（断点续写）
        self.existing_chapters = self._scan_existing_chapters()
        if self.existing_chapters:
            self.current_chapter = max(self.existing_chapters)
            # 计算进度
            self.progress = (len(self.existing_chapters) / self.total_chapters) * 100

    def _scan_existing_chapters(self):
        """扫描项目文件夹中已有的章节"""
        project_folder = self.config.get('project_folder', self.outline_folder)
        if not os.path.exists(project_folder):
            return []

        chapters = []
        for file in os.listdir(project_folder):
            if file.startswith('chapter_') and file.endswith('.txt'):
                try:
                    ch_num = int(file.replace('chapter_', '').replace('.txt', ''))
                    chapters.append(ch_num)
                except:
                    pass

        return sorted(chapters)


class WritingToolWindow:
    """写作工具主窗口"""

    def __init__(self):
        self.window = tk.Tk()
        self.window.title("小说写作工具")
        self.window.geometry("1200x800")

        self.tasks = []  # 任务列表
        self.task_containers = {}  # 任务卡片引用

        self.setup_ui()

    def setup_ui(self):
        """设置界面"""
        # 标题栏
        title_frame = tk.Frame(self.window, bg="#4CAF50", height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        tk.Label(
            title_frame,
            text="📝 小说写作工具",
            font=("Arial", 20, "bold"),
            bg="#4CAF50",
            fg="white"
        ).pack(side=tk.LEFT, padx=20, pady=10)

        tk.Label(
            title_frame,
            text="批量生成小说章节 | 支持断点续写",
            font=("Arial", 11),
            bg="#4CAF50",
            fg="white"
        ).pack(side=tk.LEFT, padx=10)

        # API配置区
        config_frame = tk.LabelFrame(self.window, text="⚙️ API配置", padx=15, pady=10)
        config_frame.pack(fill=tk.X, padx=10, pady=10)

        # API Key
        tk.Label(config_frame, text="API Key:", width=12, anchor='w').grid(row=0, column=0, sticky=tk.W, pady=5)
        self.api_key_var = tk.StringVar(value="sk-4FqZoOFgSYHP6Vfk9HGqhGyrPJjNTVwnaB6zVAbLp8UdlCln")
        tk.Entry(config_frame, textvariable=self.api_key_var, show="*", width=50).grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)

        # Base URL
        tk.Label(config_frame, text="Base URL:", width=12, anchor='w').grid(row=1, column=0, sticky=tk.W, pady=5)
        self.base_url_var = tk.StringVar(value="https://yunwuapi.com")
        tk.Entry(config_frame, textvariable=self.base_url_var, width=50).grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)

        # Model
        tk.Label(config_frame, text="Model:", width=12, anchor='w').grid(row=2, column=0, sticky=tk.W, pady=5)
        self.model_var = tk.StringVar(value="gpt-5.1")
        model_combo = ttk.Combobox(config_frame, textvariable=self.model_var, width=47)
        model_combo['values'] = ["gpt-5.1", "gpt-5-mini", "gemini-2.5-pro", "gpt-5", "gemini-3-pro-preview"]
        model_combo.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        model_combo['state'] = 'normal'  # 允许手动输入

        # Temperature
        tk.Label(config_frame, text="Temperature:", width=12, anchor='w').grid(row=3, column=0, sticky=tk.W, pady=5)
        self.temperature_var = tk.DoubleVar(value=0.8)
        tk.Scale(config_frame, from_=0, to=1, resolution=0.1, orient=tk.HORIZONTAL,
                 variable=self.temperature_var, length=300).grid(row=3, column=1, sticky=tk.W, pady=5, padx=5)

        # Max Tokens
        tk.Label(config_frame, text="Max Tokens:", width=12, anchor='w').grid(row=4, column=0, sticky=tk.W, pady=5)
        self.max_tokens_var = tk.IntVar(value=20000)
        tk.Spinbox(config_frame, from_=5000, to=200000, increment=1000,
                   textvariable=self.max_tokens_var, width=15).grid(row=4, column=1, sticky=tk.W, pady=5, padx=5)

        # 测试API按钮
        test_frame = tk.Frame(config_frame)
        test_frame.grid(row=5, column=0, columnspan=2, pady=10)

        tk.Button(
            test_frame,
            text="测试API连接",
            command=self.test_api_connection,
            bg="#2196F3",
            fg="white",
            width=12
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            test_frame,
            text="测试Gemini",
            command=self.test_gemini_simple,
            bg="#FF9800",
            fg="white",
            width=12
        ).pack(side=tk.LEFT, padx=5)

        self.api_status_label = tk.Label(test_frame, text="", fg="gray")
        self.api_status_label.pack(side=tk.LEFT, padx=10)

        # 添加任务区
        add_task_frame = tk.LabelFrame(self.window, text="➕ 添加任务", padx=15, pady=10)
        add_task_frame.pack(fill=tk.X, padx=10, pady=10)

        # 选择大纲文件夹
        folder_frame = tk.Frame(add_task_frame)
        folder_frame.pack(fill=tk.X, pady=5)

        tk.Label(folder_frame, text="大纲文件夹:", width=12, anchor='w').pack(side=tk.LEFT)
        self.outline_folder_var = tk.StringVar(value="未选择")
        tk.Label(folder_frame, textvariable=self.outline_folder_var, fg="gray").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Button(folder_frame, text="📂 选择", command=self.select_outline_folder, width=10).pack(side=tk.RIGHT, padx=5)

        # 章节范围和批次
        range_frame = tk.Frame(add_task_frame)
        range_frame.pack(fill=tk.X, pady=5)

        tk.Label(range_frame, text="章节范围:", width=12, anchor='w').pack(side=tk.LEFT)
        tk.Label(range_frame, text="从").pack(side=tk.LEFT, padx=(0, 5))
        self.start_chapter_var = tk.IntVar(value=1)
        tk.Spinbox(range_frame, from_=1, to=500, textvariable=self.start_chapter_var, width=8).pack(side=tk.LEFT)
        tk.Label(range_frame, text="到").pack(side=tk.LEFT, padx=(10, 5))
        self.end_chapter_var = tk.IntVar(value=50)
        tk.Spinbox(range_frame, from_=1, to=500, textvariable=self.end_chapter_var, width=8).pack(side=tk.LEFT)

        tk.Label(range_frame, text="每批章节数:", width=12, anchor='w').pack(side=tk.LEFT, padx=(20, 5))
        self.batch_size_var = tk.IntVar(value=3)
        tk.Spinbox(range_frame, from_=1, to=10, textvariable=self.batch_size_var, width=8).pack(side=tk.LEFT)

        tk.Button(range_frame, text="✚ 添加到队列", command=self.add_task,
                  bg="#2196F3", fg="white", width=15).pack(side=tk.RIGHT, padx=5)

        # 任务队列
        queue_frame = tk.LabelFrame(self.window, text="📋 任务队列", padx=5, pady=5)
        queue_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Canvas + Scrollbar
        self.canvas = tk.Canvas(queue_frame, bg="white")
        scrollbar = ttk.Scrollbar(queue_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.tasks_frame = tk.Frame(self.canvas, bg="white")

        self.canvas_window = self.canvas.create_window((0, 0), window=self.tasks_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tasks_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))

        # 显示空状态
        self.show_empty_state()

    def show_empty_state(self):
        """显示空状态提示"""
        for widget in self.tasks_frame.winfo_children():
            widget.destroy()

        empty_label = tk.Label(
            self.tasks_frame,
            text="📭 暂无任务，请选择大纲文件夹后添加任务",
            font=("Arial", 12),
            fg="gray",
            bg="white"
        )
        empty_label.pack(pady=50)

    def test_api_connection(self):
        """测试API连接"""
        api_key = self.api_key_var.get()
        base_url = self.base_url_var.get()
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
                # 使用 http.client 方式（完全按照成功脚本的方式）
                import http.client
                import json

                # 准备请求数据
                payload = json.dumps({
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": "Hello"
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 10,
                    "stream": False
                })

                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {api_key}'
                }

                # 简单解析URL - 去掉协议头（和成功的Gemini测试代码一样）
                host = base_url.replace("https://", "").replace("http://", "").rstrip('/')
                # 如果URL中包含路径，只取主机名
                if '/' in host:
                    host = host.split('/')[0]

                # 连接（不设置timeout，和成功的Gemini测试代码一样）
                conn = http.client.HTTPSConnection(host)

                # 发送请求
                conn.request("POST", "/v1/chat/completions", payload, headers)
                response = conn.getresponse()
                data = response.read().decode('utf-8')

                conn.close()

                # 检查响应
                if response.status == 200:
                    response_data = json.loads(data)
                    if response_data.get('choices') and len(response_data['choices']) > 0:
                        # 成功
                        self.window.after(0, lambda: self.api_status_label.config(
                            text="✅ 连接成功", fg="green"
                        ))
                    else:
                        raise ValueError("API响应格式异常")
                else:
                    raise ValueError(f"API返回状态码 {response.status}: {data[:100]}")

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
        """使用用户提供的完全相同的代码测试Gemini连接"""
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
                # === 完全按照用户提供的代码 ===
                import http.client
                import json

                # 配置信息
                API_BASE_URL = "https://yunwuapi.com"
                API_KEY = api_key
                MODEL_NAME = "gemini-2.5-pro"

                # 设置连接
                conn = http.client.HTTPSConnection(API_BASE_URL.replace("https://", ""))  # 去掉协议头

                # 准备请求数据
                payload = json.dumps({
                    "model": MODEL_NAME,
                    "messages": [
                        {
                            "role": "user",
                            "content": "你好，你是谁。"
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 25000,
                    "stream": False
                })

                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {API_KEY}'
                }

                # 发送请求
                conn.request("POST", "/v1/chat/completions", payload, headers)
                response = conn.getresponse()
                data = response.read().decode('utf-8')

                # 解析并显示结果
                if response.status == 200:
                    response_data = json.loads(data)
                    assistant_reply = response_data['choices'][0]['message']['content']

                    # 成功
                    self.window.after(0, lambda: messagebox.showinfo(
                        "Gemini测试成功",
                        f"模型回复：{assistant_reply}"
                    ))
                    self.window.after(0, lambda: self.api_status_label.config(
                        text="✅ Gemini连接成功", fg="green"
                    ))
                else:
                    error_msg = f"请求失败，状态码：{response.status}\n错误信息：{data[:200]}"
                    self.window.after(0, lambda: messagebox.showerror("Gemini测试失败", error_msg))
                    self.window.after(0, lambda: self.api_status_label.config(
                        text=f"❌ 状态码{response.status}", fg="red"
                    ))

                conn.close()

            except Exception as e:
                error_msg = f"发生错误：{e}"
                self.window.after(0, lambda: messagebox.showerror("Gemini测试失败", error_msg))
                self.window.after(0, lambda: self.api_status_label.config(
                    text=f"❌ {str(e)[:30]}", fg="red"
                ))

        thread = threading.Thread(target=_test, daemon=True)
        thread.start()

    def select_outline_folder(self):
        """选择大纲文件夹"""
        folder = filedialog.askdirectory(title="选择大纲文件夹", initialdir="outlines")
        if folder:
            # 验证文件夹包含_writing_prompt.txt
            if not os.path.exists(os.path.join(folder, '_writing_prompt.txt')):
                messagebox.showwarning("警告", "所选文件夹不包含 _writing_prompt.txt 文件")
                return

            self.outline_folder_var.set(os.path.basename(folder))
            self.selected_outline_folder = folder

    def add_task(self):
        """添加任务到队列"""
        if not hasattr(self, 'selected_outline_folder'):
            messagebox.showwarning("警告", "请先选择大纲文件夹")
            return

        if not self.api_key_var.get():
            messagebox.showwarning("警告", "请输入API Key")
            return

        # 构建配置
        config = {
            'api_key': self.api_key_var.get(),
            'base_url': self.base_url_var.get(),
            'model': self.model_var.get(),
            'temperature': self.temperature_var.get(),
            'max_tokens': self.max_tokens_var.get(),
            'start_chapter': self.start_chapter_var.get(),
            'end_chapter': self.end_chapter_var.get(),
            'batch_size': self.batch_size_var.get(),
            'outline_file': self.selected_outline_folder,  # 大纲文件夹
            'project_folder': self.selected_outline_folder  # 写作到大纲文件夹
        }

        # 创建任务
        task = WritingTask(self.selected_outline_folder, config)
        self.tasks.append(task)

        # 刷新界面
        self.refresh_task_list()

        messagebox.showinfo("成功", f"任务已添加：{task.title}")

    def refresh_task_list(self):
        """刷新任务列表"""
        # 清空
        for widget in self.tasks_frame.winfo_children():
            widget.destroy()
        self.task_containers.clear()

        if not self.tasks:
            self.show_empty_state()
            return

        # 创建任务卡片
        for i, task in enumerate(self.tasks):
            self._create_task_card(task, i)

    def _create_task_card(self, task, index):
        """创建任务卡片"""
        # 任务容器
        container = tk.Frame(self.tasks_frame, bg="#f5f5f5", relief=tk.RAISED, borderwidth=1)
        container.pack(fill=tk.X, padx=5, pady=5)

        # 左侧信息
        info_frame = tk.Frame(container, bg="#f5f5f5")
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 标题
        tk.Label(
            info_frame,
            text=f"📖 {task.title}",
            font=("Arial", 12, "bold"),
            bg="#f5f5f5"
        ).pack(anchor="w")

        # 详情
        status_map = {'pending': ('⏸️', 'orange'), 'in_progress': ('🔄', 'blue'),
                      'completed': ('✅', 'green'), 'failed': ('❌', 'red')}
        icon, color = status_map.get(task.status, ('❓', 'gray'))

        details_text = f"{icon} {task.status}  |  章节: {task.current_chapter}/{task.total_chapters}  |  模型: {task.config['model']}"
        if task.started_at:
            details_text += f"  |  启动: {task.started_at}"

        tk.Label(
            info_frame,
            text=details_text,
            font=("Arial", 9),
            bg="#f5f5f5",
            fg="gray"
        ).pack(anchor="w", pady=(5, 5))

        # 进度条
        progress_frame = tk.Frame(info_frame, bg="#f5f5f5")
        progress_frame.pack(fill=tk.X, pady=(5, 0))

        progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, mode='determinate', value=task.progress)
        progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        progress_text = tk.Label(progress_frame, text=f"{task.progress:.1f}% | ${task.cost:.2f}",
                                font=("Arial", 9), bg="#f5f5f5", fg="gray")
        progress_text.pack(side=tk.LEFT, padx=(10, 0))

        # 右侧按钮
        button_frame = tk.Frame(container, bg="#f5f5f5")
        button_frame.pack(side=tk.RIGHT, padx=10, pady=10)

        tk.Button(button_frame, text="👁️ 预览", command=lambda: self.preview_prompt(task),
                  width=10, bg="#FF9800", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="▶️ 开始", command=lambda: self.start_task(task),
                  width=10, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="🔄 重新生成", command=lambda: self.restart_task(task),
                  width=12).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="📂 文件夹", command=lambda: self.open_folder(task),
                  width=10).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="🗑️ 删除", command=lambda: self.delete_task(index),
                  width=8, bg="#f44336", fg="white").pack(side=tk.LEFT, padx=2)

        # 保存引用
        self.task_containers[index] = {
            'container': container,
            'progress_bar': progress_bar,
            'progress_text': progress_text
        }

    def preview_prompt(self, task):
        """预览Prompt - 显示实际会发送给API的完整prompt"""
        try:
            # 读取outline文件夹
            outline_folder = task.outline_folder

            # 1. 读取 _writing_prompt.txt（基础prompt）
            writing_prompt_file = os.path.join(outline_folder, '_writing_prompt.txt')
            if not os.path.exists(writing_prompt_file):
                messagebox.showerror("错误", "找不到 _writing_prompt.txt 文件")
                return

            with open(writing_prompt_file, 'r', encoding='utf-8') as f:
                base_prompt = f.read()

            # 2. 确定当前要生成的章节范围
            # 扫描已生成的章节
            project_folder = task.config.get('project_folder', outline_folder)
            if os.path.exists(project_folder):
                scan_result = scan_chapter_files(project_folder)
                max_chapter = scan_result['max_chapter']
            else:
                max_chapter = 0

            # 计算下一批次
            config_start = task.config.get('start_chapter', 1)
            batch_size = task.config.get('batch_size', 3)

            next_start = max(max_chapter + 1, config_start)
            next_end = min(next_start + batch_size - 1, task.config.get('end_chapter', 100))

            # 3. 读取相关章节的prompts
            chapter_prompts = ""

            # 如果不是从第1章开始，添加上一章的prompt
            if next_start > 1:
                prev_chapter_prompt_file = os.path.join(outline_folder, f'chapter_{next_start - 1}_prompt.txt')
                if os.path.exists(prev_chapter_prompt_file):
                    with open(prev_chapter_prompt_file, 'r', encoding='utf-8') as f:
                        chapter_prompts += f"===== 上一章 (Chapter {next_start - 1}) =====\n"
                        chapter_prompts += f.read() + "\n\n"

            # 添加当前批次所有章节的prompts
            for ch_num in range(next_start, next_end + 1):
                chapter_prompt_file = os.path.join(outline_folder, f'chapter_{ch_num}_prompt.txt')
                if os.path.exists(chapter_prompt_file):
                    with open(chapter_prompt_file, 'r', encoding='utf-8') as f:
                        chapter_prompts += f.read() + "\n\n"

            # 4. 组合完整的prompt
            full_prompt = base_prompt + "\n\n===== CHAPTER_OUTLINES =====\n" + chapter_prompts

            # 5. 检查是否有前文（上一章的最后2000字符）
            previous_context = ""
            if next_start > 1:
                prev_chapter_file = os.path.join(project_folder, f'chapter_{next_start - 1}.txt')
                if os.path.exists(prev_chapter_file):
                    try:
                        with open(prev_chapter_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # 提取正文（去掉元数据）
                            if '---' in content:
                                content = content.split('---')[0]
                            previous_context = content[-2000:] if len(content) > 2000 else content
                    except:
                        pass

            if previous_context:
                full_prompt += f"\n\n===== PREVIOUS_CONTEXT =====\n{previous_context}\n"

            # User prompt
            user_prompt = f"请写作 Chapter {next_start} - {next_end}"

            # 6. 显示在窗口中
            self._show_prompt_window(task, full_prompt, user_prompt, next_start, next_end, max_chapter)

        except Exception as e:
            messagebox.showerror("错误", f"预览Prompt失败: {str(e)}\n{traceback.format_exc()}")

    def _show_prompt_window(self, task, system_prompt, user_prompt, next_start, next_end, max_chapter):
        """显示Prompt预览窗口"""
        # 创建窗口
        prompt_window = tk.Toplevel(self.window)
        prompt_window.title(f"Prompt预览 - {task.title}")
        prompt_window.geometry("900x700")

        # 顶部信息
        info_frame = tk.Frame(prompt_window, bg="#f0f0f0", padx=10, pady=10)
        info_frame.pack(fill=tk.X)

        tk.Label(
            info_frame,
            text=f"📖 {task.title}",
            font=("Arial", 14, "bold"),
            bg="#f0f0f0"
        ).pack(anchor=tk.W)

        tk.Label(
            info_frame,
            text=f"已完成: {max_chapter} 章  |  下一批次: Chapter {next_start}-{next_end}",
            font=("Arial", 10),
            bg="#f0f0f0",
            fg="blue"
        ).pack(anchor=tk.W, pady=5)

        tk.Label(
            info_frame,
            text=f"模型: {task.config.get('model', 'N/A')}  |  Temperature: {task.config.get('temperature', 0.8)}  |  Max Tokens: {task.config.get('max_tokens', 20000)}",
            font=("Arial", 9),
            bg="#f0f0f0",
            fg="gray"
        ).pack(anchor=tk.W)

        # 统计信息
        system_chars = len(system_prompt)
        user_chars = len(user_prompt)
        total_chars = system_chars + user_chars

        tk.Label(
            info_frame,
            text=f"System Prompt: {system_chars:,} 字符  |  User Prompt: {user_chars:,} 字符  |  总计: {total_chars:,} 字符",
            font=("Arial", 9, "bold"),
            bg="#f0f0f0",
            fg="#d32f2f"
        ).pack(anchor=tk.W, pady=5)

        # Notebook (标签页)
        notebook = ttk.Notebook(prompt_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab 1: System Prompt
        system_frame = tk.Frame(notebook)
        notebook.add(system_frame, text="System Prompt")

        system_text = scrolledtext.ScrolledText(
            system_frame,
            wrap=tk.WORD,
            font=("Courier", 10),
            bg="#f5f5f5"
        )
        system_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        system_text.insert('1.0', system_prompt)
        system_text.config(state=tk.DISABLED)

        # Tab 2: User Prompt
        user_frame = tk.Frame(notebook)
        notebook.add(user_frame, text="User Prompt")

        user_text = scrolledtext.ScrolledText(
            user_frame,
            wrap=tk.WORD,
            font=("Courier", 10),
            bg="#f5f5f5"
        )
        user_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        user_text.insert('1.0', user_prompt)
        user_text.config(state=tk.DISABLED)

        # Tab 3: 完整Prompt（合并后的）
        combined_frame = tk.Frame(notebook)
        notebook.add(combined_frame, text="完整Prompt（发送给API）")

        combined_text = scrolledtext.ScrolledText(
            combined_frame,
            wrap=tk.WORD,
            font=("Courier", 10),
            bg="#fff3cd"
        )
        combined_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 按照实际API调用的方式合并（system + user）
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        combined_text.insert('1.0', combined_prompt)
        combined_text.config(state=tk.DISABLED)

        # 底部按钮
        button_frame = tk.Frame(prompt_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(
            button_frame,
            text="🔄 刷新",
            command=lambda: [prompt_window.destroy(), self.preview_prompt(task)],
            width=15,
            bg="#2196F3",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_frame,
            text="📋 复制System Prompt",
            command=lambda: self._copy_to_clipboard(system_prompt),
            width=20
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_frame,
            text="📋 复制完整Prompt",
            command=lambda: self._copy_to_clipboard(combined_prompt),
            width=20
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_frame,
            text="关闭",
            command=prompt_window.destroy,
            width=10
        ).pack(side=tk.RIGHT, padx=5)

    def _copy_to_clipboard(self, text):
        """复制到剪贴板"""
        self.window.clipboard_clear()
        self.window.clipboard_append(text)
        messagebox.showinfo("成功", f"已复制 {len(text):,} 字符到剪贴板")

    def start_task(self, task):
        """启动任务"""
        if task.status == 'in_progress':
            messagebox.showinfo("提示", "任务正在运行中")
            return

        task.status = 'in_progress'
        task.started_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 启动WriterWorker子进程
        def _run_task():
            try:
                # 创建任务配置文件
                task_id = f"writing_{int(time.time()*1000)}"
                task_dir = f"tasks/{task_id}"
                os.makedirs(task_dir, exist_ok=True)

                config_file = os.path.join(task_dir, 'config.json')

                print(f"\n{'='*70}")
                print(f"🚀 启动任务: {task.title}")
                print(f"{'='*70}")
                print(f"  任务ID: {task_id}")
                print(f"  配置文件: {config_file}")
                print(f"\n📝 配置内容:")
                for key, value in task.config.items():
                    if key == 'api_key':
                        print(f"  {key}: {value[:10]}...{value[-5:]}")
                    else:
                        print(f"  {key}: {value}")

                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(task.config, f, indent=2, ensure_ascii=False)

                print(f"\n✅ 配置文件已创建")

                # 启动writer_worker_v2.py作为子进程
                import subprocess
                import sys

                cmd = [
                    sys.executable,
                    'writer_worker_v2.py',
                    '--config', config_file,
                    '--task-id', task_id
                ]

                print(f"\n🔧 执行命令: {' '.join(cmd)}\n")
                print(f"{'='*70}\n")

                # 运行子进程
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )

                # 实时读取输出
                for line in process.stdout:
                    print(line.rstrip())

                # 等待完成
                process.wait()

                print(f"\n{'='*70}")
                if process.returncode == 0:
                    print(f"✅ 任务完成: {task.title}")
                    task.status = 'completed'
                else:
                    print(f"❌ 任务失败: {task.title} (返回码: {process.returncode})")
                    task.status = 'failed'
                print(f"{'='*70}\n")

                # 更新UI
                self.window.after(0, self.refresh_task_list)

            except Exception as e:
                print(f"\n{'='*70}")
                print(f"❌ 任务异常: {e}")
                print(f"{'='*70}")
                import traceback
                traceback.print_exc()
                task.status = 'failed'
                self.window.after(0, self.refresh_task_list)

        # 在新线程中运行
        import threading
        thread = threading.Thread(target=_run_task, daemon=True)
        thread.start()

        messagebox.showinfo("成功", f"任务已启动：{task.title}\n查看控制台输出了解进度")
        self.refresh_task_list()

    def restart_task(self, task):
        """重新生成（从头开始）"""
        if messagebox.askyesno("确认", "确定要从头重新生成吗？\n已生成的章节将被覆盖"):
            task.current_chapter = 0
            task.progress = 0
            task.cost = 0.0
            task.status = 'pending'
            self.refresh_task_list()

    def open_folder(self, task):
        """打开文件夹"""
        import platform
        folder = task.config.get('project_folder', task.outline_folder)

        if not os.path.exists(folder):
            messagebox.showwarning("警告", "项目文件夹不存在")
            return

        system = platform.system()
        if system == 'Darwin':
            os.system(f'open "{folder}"')
        elif system == 'Windows':
            os.system(f'explorer "{folder}"')
        else:
            os.system(f'xdg-open "{folder}"')

    def delete_task(self, index):
        """删除任务"""
        if messagebox.askyesno("确认", "确定要删除这个任务吗？\n注意：不会删除已生成的文件"):
            del self.tasks[index]
            self.refresh_task_list()

    def run(self):
        """运行应用"""
        self.window.mainloop()


def main():
    app = WritingToolWindow()
    app.run()


if __name__ == '__main__':
    main()
