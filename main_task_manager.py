"""
任务管理器主窗口
显示所有写作任务，支持创建、监控、管理任务
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import time
import os
from datetime import datetime

from task_manager import TaskManager
from utils import format_time_elapsed, scan_chapter_files


class TaskManagerWindow:
    """任务管理器主窗口"""

    def __init__(self):
        self.window = tk.Tk()
        self.window.title("任务管理器 - 小说写作工具")
        self.window.geometry("1100x750")

        self.task_mgr = TaskManager()
        self.task_containers = {}  # 存储任务容器的引用

        # 轮询线程
        self.polling = False

        # 初始化界面
        self.setup_ui()
        self.refresh_tasks()

        # 启动轮询
        self.start_polling()

    def setup_ui(self):
        """设置界面"""
        # === 标题栏 ===
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
            text="批量生成小说章节",
            font=("Arial", 11),
            bg="#4CAF50",
            fg="white"
        ).pack(side=tk.LEFT, padx=10)

        # === 工具栏 ===
        toolbar = tk.Frame(self.window)
        toolbar.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(
            toolbar,
            text="➕ 新建任务",
            command=self.create_new_task,
            bg="#2196F3",
            fg="white",
            width=12
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            toolbar,
            text="🔄 刷新",
            command=self.refresh_tasks,
            width=12
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            toolbar,
            text="🗑️ 清空队列",
            command=self.clear_all_tasks,
            width=12,
            bg="#f44336",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)

        # === 任务队列（滚动区域）===
        queue_frame = tk.LabelFrame(self.window, text="📋 任务队列", padx=5, pady=5)
        queue_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建Canvas和Scrollbar
        self.canvas = tk.Canvas(queue_frame, bg="white")
        scrollbar = ttk.Scrollbar(queue_frame, orient=tk.VERTICAL, command=self.canvas.yview)

        # 创建内部Frame（用于放置任务卡片）
        self.tasks_frame = tk.Frame(self.canvas, bg="white")

        # 创建canvas窗口
        self.canvas_window = self.canvas.create_window((0, 0), window=self.tasks_frame, anchor="nw")

        # 配置Canvas
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # 布局
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定配置事件（自动调整canvas窗口宽度）
        self.tasks_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_frame_configure(self, event=None):
        """更新Canvas的滚动区域"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """调整内部Frame的宽度以匹配Canvas"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def refresh_tasks(self):
        """刷新任务列表"""
        # 清空现有任务卡片
        for widget in self.tasks_frame.winfo_children():
            widget.destroy()
        self.task_containers.clear()

        # 获取所有任务
        tasks = self.task_mgr.list_all_tasks()

        if not tasks:
            # 显示空状态提示
            empty_label = tk.Label(
                self.tasks_frame,
                text="📭 暂无任务，点击「新建任务」开始",
                font=("Arial", 12),
                fg="gray",
                bg="white"
            )
            empty_label.pack(pady=50)
            return

        # 为每个任务创建卡片
        for task_data in tasks:
            task_id = task_data['task_id']
            self._create_task_card(task_id)

    def _create_task_card(self, task_id):
        """创建任务卡片"""
        summary = self.task_mgr.get_task_summary(task_id)
        if not summary:
            return

        # 创建任务容器（卡片）
        task_container = tk.Frame(self.tasks_frame, bg="#f5f5f5", relief=tk.RAISED, borderwidth=1)
        task_container.pack(fill=tk.X, padx=5, pady=5)

        # 左侧：信息区域
        info_frame = tk.Frame(task_container, bg="#f5f5f5")
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 标题行
        title_frame = tk.Frame(info_frame, bg="#f5f5f5")
        title_frame.pack(fill=tk.X)

        tk.Label(
            title_frame,
            text=f"📖 {summary['title']}",
            font=("Arial", 12, "bold"),
            bg="#f5f5f5",
            anchor="w"
        ).pack(side=tk.LEFT)

        # 状态标签
        status_icon, status_color = self._get_status_display(summary['status'])
        status_label = tk.Label(
            title_frame,
            text=f"{status_icon} {summary['status']}",
            font=("Arial", 10),
            bg="#f5f5f5",
            fg=status_color
        )
        status_label.pack(side=tk.LEFT, padx=10)

        # 详情行
        details_frame = tk.Frame(info_frame, bg="#f5f5f5")
        details_frame.pack(fill=tk.X, pady=(5, 0))

        details_text = f"模型: {summary.get('model', 'N/A')}  |  章节: {summary['current_chapter']}/{summary['target_chapters']}"

        # 如果有启动时间，显示启动时间
        if summary.get('started_at'):
            started_time = summary['started_at'][:19] if len(summary.get('started_at', '')) > 19 else summary.get('started_at', '')
            details_text += f"  |  启动: {started_time}"

        details_label = tk.Label(
            details_frame,
            text=details_text,
            font=("Arial", 9),
            bg="#f5f5f5",
            fg="gray"
        )
        details_label.pack(side=tk.LEFT)

        # 进度条
        progress_frame = tk.Frame(info_frame, bg="#f5f5f5")
        progress_frame.pack(fill=tk.X, pady=(8, 0))

        progress_bar = ttk.Progressbar(
            progress_frame,
            orient=tk.HORIZONTAL,
            length=300,
            mode='determinate',
            value=summary['progress_percent']
        )
        progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        progress_text = tk.Label(
            progress_frame,
            text=f"{summary['progress_percent']:.1f}% | ${summary['total_cost']:.2f}",
            font=("Arial", 9),
            bg="#f5f5f5",
            fg="gray"
        )
        progress_text.pack(side=tk.LEFT, padx=(10, 0))

        # 右侧：按钮区域
        button_frame = tk.Frame(task_container, bg="#f5f5f5")
        button_frame.pack(side=tk.RIGHT, padx=10, pady=10)

        # 开始按钮
        start_btn = tk.Button(
            button_frame,
            text="▶️ 开始",
            command=lambda: self.start_task(task_id),
            width=12,
            bg="#4CAF50",
            fg="white"
        )
        start_btn.pack(side=tk.LEFT, padx=3)

        # 停止按钮
        stop_btn = tk.Button(
            button_frame,
            text="⏸️ 停止",
            command=lambda: self.stop_task(task_id),
            width=12,
            bg="#FF9800",
            fg="white",
            state=tk.DISABLED
        )
        stop_btn.pack(side=tk.LEFT, padx=3)

        # 打开文件夹按钮
        tk.Button(
            button_frame,
            text="📂 文件夹",
            command=lambda: self.open_project_folder(task_id),
            width=12
        ).pack(side=tk.LEFT, padx=3)

        # 删除按钮
        tk.Button(
            button_frame,
            text="🗑️ 删除",
            command=lambda: self.delete_task(task_id),
            width=10,
            bg="#f44336",
            fg="white"
        ).pack(side=tk.LEFT, padx=3)

        # 保存引用以便后续更新
        self.task_containers[task_id] = {
            'container': task_container,
            'status_label': status_label,
            'details_label': details_label,
            'progress_bar': progress_bar,
            'progress_text': progress_text,
            'start_btn': start_btn,
            'stop_btn': stop_btn
        }

        # 根据当前状态调整按钮
        self._update_task_buttons(task_id, summary['status'], summary['is_running'])

    def _get_status_display(self, status):
        """获取状态显示（图标和颜色）"""
        status_map = {
            'pending': ('⏸️', 'orange'),
            'initializing': ('🔄', 'blue'),
            'in_progress': ('🔄', 'blue'),
            'completed': ('✅', 'green'),
            'failed': ('❌', 'red')
        }
        return status_map.get(status, ('❓', 'gray'))

    def _update_task_buttons(self, task_id, status, is_running):
        """更新任务按钮状态"""
        if task_id not in self.task_containers:
            return

        refs = self.task_containers[task_id]
        start_btn = refs['start_btn']
        stop_btn = refs['stop_btn']

        if status == 'completed':
            start_btn.config(state=tk.DISABLED)
            stop_btn.config(state=tk.DISABLED)
        elif is_running:
            start_btn.config(state=tk.DISABLED)
            stop_btn.config(state=tk.NORMAL)
        else:
            start_btn.config(state=tk.NORMAL)
            stop_btn.config(state=tk.DISABLED)

    def _update_task_display(self, task_id):
        """更新单个任务的显示信息"""
        if task_id not in self.task_containers:
            return

        summary = self.task_mgr.get_task_summary(task_id)
        if not summary:
            return

        refs = self.task_containers[task_id]

        # 更新状态
        status_icon, status_color = self._get_status_display(summary['status'])
        refs['status_label'].config(text=f"{status_icon} {summary['status']}", fg=status_color)

        # 更新详情
        details_text = f"模型: {summary.get('model', 'N/A')}  |  章节: {summary['current_chapter']}/{summary['target_chapters']}"
        if summary.get('started_at'):
            started_time = summary['started_at'][:19] if len(summary.get('started_at', '')) > 19 else summary.get('started_at', '')
            details_text += f"  |  启动: {started_time}"
        refs['details_label'].config(text=details_text)

        # 更新进度条
        refs['progress_bar']['value'] = summary['progress_percent']
        refs['progress_text'].config(text=f"{summary['progress_percent']:.1f}% | ${summary['total_cost']:.2f}")

        # 更新按钮
        self._update_task_buttons(task_id, summary['status'], summary['is_running'])

    def create_new_task(self):
        """创建新任务"""
        NewTaskWindow(self.window, self.task_mgr, callback=self.refresh_tasks)

    def start_task(self, task_id):
        """启动任务"""
        try:
            # 记录启动时间
            progress = self.task_mgr.get_task_progress(task_id)
            if progress:
                progress['started_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                # 直接保存progress.json
                import json
                progress_file = os.path.join('tasks', task_id, 'progress.json')
                with open(progress_file, 'w', encoding='utf-8') as f:
                    json.dump(progress, f, indent=2, ensure_ascii=False)

            # 启动任务
            self.task_mgr.start_task(task_id)
            messagebox.showinfo("成功", f"任务 {task_id} 已启动")

            # 刷新显示
            self.window.after(500, lambda: self._update_task_display(task_id))

        except Exception as e:
            messagebox.showerror("错误", f"启动任务失败: {str(e)}")

    def stop_task(self, task_id):
        """停止任务"""
        if messagebox.askyesno("确认", "确定要停止这个任务吗？"):
            success = self.task_mgr.stop_task(task_id)
            if success:
                messagebox.showinfo("成功", "任务已停止")
                self._update_task_display(task_id)
            else:
                messagebox.showwarning("警告", "任务可能未运行或已停止")

    def delete_task(self, task_id):
        """删除任务"""
        if messagebox.askyesno("确认", "确定要删除这个任务吗？\n注意：这不会删除生成的项目文件。"):
            self.task_mgr.delete_task(task_id)
            self.refresh_tasks()

    def clear_all_tasks(self):
        """清空所有任务"""
        tasks = self.task_mgr.list_all_tasks()
        if not tasks:
            messagebox.showinfo("提示", "任务队列已经是空的")
            return

        if messagebox.askyesno("确认", f"确定要清空所有 {len(tasks)} 个任务吗？\n注意：这不会删除生成的项目文件。"):
            for task_data in tasks:
                self.task_mgr.delete_task(task_data['task_id'])
            self.refresh_tasks()
            messagebox.showinfo("成功", "已清空所有任务")

    def open_project_folder(self, task_id):
        """打开项目文件夹"""
        config = self.task_mgr.get_task_config(task_id)
        project_folder = config.get('project_folder')

        if project_folder and os.path.exists(project_folder):
            import platform
            system = platform.system()

            if system == 'Darwin':  # Mac
                os.system(f'open "{project_folder}"')
            elif system == 'Windows':
                os.system(f'explorer "{project_folder}"')
            else:  # Linux
                os.system(f'xdg-open "{project_folder}"')
        else:
            messagebox.showwarning("警告", "项目文件夹不存在")

    def start_polling(self):
        """启动轮询"""
        self.polling = True

        def poll():
            while self.polling:
                time.sleep(2)  # 每2秒刷新一次
                # 只更新现有任务的显示，不完全刷新
                tasks = self.task_mgr.list_all_tasks()
                task_ids = [t['task_id'] for t in tasks]

                # 检查是否有新任务或任务被删除
                current_ids = set(self.task_containers.keys())
                new_ids = set(task_ids)

                if current_ids != new_ids:
                    # 有变化，完全刷新
                    self.window.after(0, self.refresh_tasks)
                else:
                    # 只更新每个任务的显示
                    for task_id in task_ids:
                        self.window.after(0, lambda tid=task_id: self._update_task_display(tid))

        threading.Thread(target=poll, daemon=True).start()

    def run(self):
        """运行应用"""
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.window.mainloop()

    def on_close(self):
        """关闭窗口"""
        self.polling = False
        self.window.destroy()


class NewTaskWindow:
    """新建任务窗口"""

    def __init__(self, parent, task_mgr, callback=None):
        self.task_mgr = task_mgr
        self.callback = callback

        self.window = tk.Toplevel(parent)
        self.window.title("新建任务")
        self.window.geometry("600x450")

        self.outline_file = None

        self.setup_ui()

    def setup_ui(self):
        """设置界面"""
        # 大纲选择
        tk.Label(self.window, text="选择大纲文件夹:", font=("Arial", 11, "bold")).pack(
            anchor=tk.W, padx=10, pady=(10, 5)
        )

        file_frame = tk.Frame(self.window)
        file_frame.pack(fill=tk.X, padx=10, pady=5)

        self.file_label = tk.Label(file_frame, text="未选择文件夹（需包含 _writing_prompt.txt）", fg="gray")
        self.file_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(
            file_frame,
            text="选择文件夹",
            command=self.select_outline
        ).pack(side=tk.RIGHT)

        # 配置参数
        config_frame = tk.LabelFrame(self.window, text="配置参数", padx=15, pady=10)
        config_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # API Key
        tk.Label(config_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.api_key_var = tk.StringVar(value="sk-4FqZoOFgSYHP6Vfk9HGqhGyrPJjNTVwnaB6zVAbLp8UdlCln")
        tk.Entry(
            config_frame,
            textvariable=self.api_key_var,
            show="*",
            width=40
        ).grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)

        # Base URL
        tk.Label(config_frame, text="Base URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.base_url_var = tk.StringVar(value="https://yunwuapi.com/v1/")
        tk.Entry(
            config_frame,
            textvariable=self.base_url_var,
            width=40
        ).grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)

        # 模型
        tk.Label(config_frame, text="模型:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.model_var = tk.StringVar(value="gpt-5.1")
        model_combo = ttk.Combobox(
            config_frame,
            textvariable=self.model_var,
            values=["gpt-5.1", "gemini-2.5-pro", "gpt-5", "gemini-3-pro-preview", "gpt-4-turbo-preview"],
            width=37
        )
        model_combo.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)

        # 章节范围
        tk.Label(config_frame, text="章节范围:").grid(row=3, column=0, sticky=tk.W, pady=5)
        chapter_range_frame = tk.Frame(config_frame)
        chapter_range_frame.grid(row=3, column=1, sticky=tk.W, pady=5, padx=5)

        self.start_chapter_var = tk.IntVar(value=1)
        tk.Label(chapter_range_frame, text="从").pack(side=tk.LEFT)
        tk.Spinbox(
            chapter_range_frame,
            from_=1,
            to=500,
            textvariable=self.start_chapter_var,
            width=8
        ).pack(side=tk.LEFT, padx=5)

        self.end_chapter_var = tk.IntVar(value=50)
        tk.Label(chapter_range_frame, text="到").pack(side=tk.LEFT, padx=5)
        tk.Spinbox(
            chapter_range_frame,
            from_=1,
            to=500,
            textvariable=self.end_chapter_var,
            width=8
        ).pack(side=tk.LEFT, padx=5)

        # 批次大小
        tk.Label(config_frame, text="每批章节数:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.batch_size_var = tk.IntVar(value=5)
        tk.Spinbox(
            config_frame,
            from_=1,
            to=10,
            textvariable=self.batch_size_var,
            width=15
        ).grid(row=4, column=1, sticky=tk.W, pady=5, padx=5)

        # Temperature
        tk.Label(config_frame, text="Temperature:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.temperature_var = tk.DoubleVar(value=0.8)
        tk.Scale(
            config_frame,
            from_=0,
            to=1,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=self.temperature_var,
            length=200
        ).grid(row=5, column=1, sticky=tk.W, pady=5, padx=5)

        # Max Tokens
        tk.Label(config_frame, text="Max Tokens:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.max_tokens_var = tk.IntVar(value=20000)
        tk.Spinbox(
            config_frame,
            from_=5000,
            to=200000,
            increment=1000,
            textvariable=self.max_tokens_var,
            width=15
        ).grid(row=6, column=1, sticky=tk.W, pady=5, padx=5)

        # 按钮
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(
            btn_frame,
            text="创建任务",
            command=self.create_task,
            bg="#4CAF50",
            fg="white",
            width=15
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(
            btn_frame,
            text="取消",
            command=self.window.destroy,
            width=15
        ).pack(side=tk.RIGHT, padx=5)

    def select_outline(self):
        """选择大纲文件夹"""
        folder_path = filedialog.askdirectory(
            title="选择大纲文件夹（需包含 _writing_prompt.txt）",
            initialdir="outlines"
        )

        if folder_path:
            # 检查是否包含 _writing_prompt.txt
            prompt_file = os.path.join(folder_path, '_writing_prompt.txt')
            if not os.path.exists(prompt_file):
                messagebox.showwarning("警告", "所选文件夹不包含 _writing_prompt.txt 文件")
                return

            self.outline_file = folder_path
            self.file_label.config(text=os.path.basename(folder_path), fg="black")

    def create_task(self):
        """创建任务（不自动启动）"""
        if not self.outline_file:
            messagebox.showwarning("警告", "请先选择大纲文件夹")
            return

        if not self.api_key_var.get():
            messagebox.showwarning("警告", "请输入API Key")
            return

        # 验证章节范围
        start_ch = self.start_chapter_var.get()
        end_ch = self.end_chapter_var.get()
        if start_ch > end_ch:
            messagebox.showwarning("警告", "起始章节不能大于结束章节")
            return

        # 构建配置
        config = {
            'api_key': self.api_key_var.get(),
            'base_url': self.base_url_var.get(),
            'model': self.model_var.get(),
            'start_chapter': start_ch,
            'end_chapter': end_ch,
            'target_chapters': end_ch,  # 保持兼容性
            'batch_size': self.batch_size_var.get(),
            'temperature': self.temperature_var.get(),
            'max_tokens': self.max_tokens_var.get()
        }

        try:
            # 只创建任务，不启动
            task_id = self.task_mgr.create_task(self.outline_file, config)

            messagebox.showinfo("成功", f"任务已创建！\n任务ID: {task_id}\n\n点击「开始」按钮启动任务")

            # 刷新父窗口
            if self.callback:
                self.callback()

            # 关闭窗口
            self.window.destroy()

        except Exception as e:
            messagebox.showerror("错误", f"创建任务失败: {str(e)}")


class TaskDetailWindow:
    """任务详情窗口"""

    def __init__(self, parent, task_id, task_mgr):
        self.task_id = task_id
        self.task_mgr = task_mgr

        self.window = tk.Toplevel(parent)
        self.window.title(f"任务详情 - {task_id}")
        self.window.geometry("700x600")

        self.setup_ui()
        self.load_detail()

    def setup_ui(self):
        """设置界面"""
        # 详情文本
        self.detail_text = scrolledtext.ScrolledText(
            self.window,
            height=30,
            wrap=tk.WORD,
            font=("Courier", 9)
        )
        self.detail_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 按钮
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(
            btn_frame,
            text="刷新",
            command=self.load_detail,
            width=12
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="停止任务",
            command=self.stop_task,
            width=12
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="打开项目文件夹",
            command=self.open_project_folder,
            width=15
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="关闭",
            command=self.window.destroy,
            width=12
        ).pack(side=tk.RIGHT, padx=5)

    def load_detail(self):
        """加载详情"""
        config = self.task_mgr.get_task_config(self.task_id)
        progress = self.task_mgr.get_task_progress(self.task_id)

        if not config or not progress:
            return

        detail = f"""
{'='*70}
任务ID: {self.task_id}
{'='*70}

配置信息:
- 大纲文件: {config.get('outline_file', 'N/A')}
- 模型: {config.get('model', 'N/A')}
- Base URL: {config.get('base_url', 'N/A')}
- 批次大小: {config.get('batch_size', 'N/A')} 章/批
- 目标章节数: {config.get('target_chapters', 'N/A')}
- Temperature: {config.get('temperature', 'N/A')}
- Max Tokens: {config.get('max_tokens', 'N/A')}

进度信息:
- 状态: {progress.get('status', 'N/A')}
- 当前章节: {progress.get('current_chapter', 0)} / {progress.get('target_chapters', 0)}
- 已完成章节: {progress.get('chapters_completed', 0)}
- Token使用: {progress.get('total_tokens', 0):,}
- 预计费用: ${progress.get('total_cost', 0):.2f}

时间信息:
- 创建时间: {progress.get('created_at', 'N/A')}
- 更新时间: {progress.get('updated_at', 'N/A')}

消息:
{progress.get('message', 'N/A')}

{'='*70}
"""

        self.detail_text.delete(1.0, tk.END)
        self.detail_text.insert(1.0, detail)

    def stop_task(self):
        """停止任务"""
        if messagebox.askyesno("确认", "确定要停止这个任务吗？"):
            success = self.task_mgr.stop_task(self.task_id)
            if success:
                messagebox.showinfo("成功", "任务已停止")
            else:
                messagebox.showwarning("警告", "任务可能未运行或已停止")

    def open_project_folder(self):
        """打开项目文件夹"""
        config = self.task_mgr.get_task_config(self.task_id)
        project_folder = config.get('project_folder')

        if project_folder and os.path.exists(project_folder):
            import platform
            system = platform.system()

            if system == 'Darwin':  # Mac
                os.system(f'open "{project_folder}"')
            elif system == 'Windows':
                os.system(f'explorer "{project_folder}"')
            else:  # Linux
                os.system(f'xdg-open "{project_folder}"')
        else:
            messagebox.showwarning("警告", "项目文件夹不存在")


def main():
    """主函数"""
    app = TaskManagerWindow()
    app.run()


if __name__ == '__main__':
    main()
