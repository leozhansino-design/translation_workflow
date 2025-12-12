"""
小说写作工具 - 主窗口
批量生成小说章节，支持断点续写
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import sys
import subprocess
import json
import time
import traceback
from datetime import datetime

from writer_worker import WriterWorker
from utils import scan_chapter_files
from prompt_manager import PromptManager
from universal_api import UniversalAPIClient


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
        import re
        project_folder = self.config.get('project_folder', self.outline_folder)
        if not os.path.exists(project_folder):
            return []

        chapters = []
        for file in os.listdir(project_folder):
            # 排除大纲文件 chapter_X_prompt.txt
            if '_prompt.txt' in file:
                continue

            # 支持 chapter_1.txt 和 chapter_1_Title.txt 两种格式
            match = re.match(r'chapter_(\d+)(?:_.*)?\.txt$', file)
            if match:
                chapters.append(int(match.group(1)))

        return sorted(chapters)


class WritingToolWindow:
    """写作工具主窗口"""

    def __init__(self):
        self.window = tk.Tk()
        self.window.title("小说写作工具")
        self.window.geometry("1400x1000")

        self.tasks = []  # 任务列表
        self.task_containers = {}  # 任务卡片引用
        self.prompt_mgr = PromptManager()  # Prompt管理器

        # 分页设置
        self.current_page = 0  # 当前页码（从0开始）
        self.tasks_per_page = 8  # 每页任务数

        # 全局进度监控
        self.progress_monitor_running = False  # 监控是否正在运行
        self.progress_update_interval = 5000  # 5秒更新一次（毫秒）

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

        # 预设API配置列表
        self.api_presets = {
            "云雾API (yunwuapi.com)": {
                "api_key": "sk-4FqZoOFgSYHP6Vfk9HGqhGyrPJjNTVwnaB6zVAbLp8UdlCln",
                "base_url": "https://yunwuapi.com"
            },
            "BLTCY API (api.bltcy.ai)": {
                "api_key": "sk-z4a6qvhXCbfboOyBwL33BR66mJdHTKj5NO4pfIUSkLBm2jGF",
                "base_url": "https://api.bltcy.ai"
            },
            "自定义配置": {
                "api_key": "",
                "base_url": ""
            }
        }

        # API配置选择
        tk.Label(config_frame, text="API配置:", width=12, anchor='w').grid(row=0, column=0, sticky=tk.W, pady=5)
        self.api_preset_var = tk.StringVar(value="云雾API (yunwuapi.com)")
        api_preset_combo = ttk.Combobox(config_frame, textvariable=self.api_preset_var, width=30)
        api_preset_combo['values'] = list(self.api_presets.keys())
        api_preset_combo.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        api_preset_combo.bind('<<ComboboxSelected>>', self.on_api_preset_change)

        # API Key
        tk.Label(config_frame, text="API Key:", width=12, anchor='w').grid(row=1, column=0, sticky=tk.W, pady=5)
        self.api_key_var = tk.StringVar(value="sk-4FqZoOFgSYHP6Vfk9HGqhGyrPJjNTVwnaB6zVAbLp8UdlCln")
        tk.Entry(config_frame, textvariable=self.api_key_var, show="*", width=50).grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)

        # Base URL选择框
        tk.Label(config_frame, text="Base URL:", width=12, anchor='w').grid(row=2, column=0, sticky=tk.W, pady=5)
        self.base_url_var = tk.StringVar(value="https://yunwuapi.com")
        base_url_combo = ttk.Combobox(config_frame, textvariable=self.base_url_var, width=47)
        base_url_combo['values'] = ["https://yunwuapi.com", "https://api.bltcy.ai"]
        base_url_combo.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        base_url_combo['state'] = 'normal'  # 允许手动输入

        # Model
        tk.Label(config_frame, text="Model:", width=12, anchor='w').grid(row=3, column=0, sticky=tk.W, pady=5)
        self.model_var = tk.StringVar(value="gpt-5-mini")
        model_combo = ttk.Combobox(config_frame, textvariable=self.model_var, width=47)
        model_combo['values'] = ["gpt-5.1", "gpt-5-mini", "gemini-2.5-pro", "gemini-3-pro-preview"]
        model_combo.grid(row=3, column=1, sticky=tk.W, pady=5, padx=5)
        model_combo['state'] = 'normal'  # 允许手动输入

        # Temperature
        tk.Label(config_frame, text="Temperature:", width=12, anchor='w').grid(row=4, column=0, sticky=tk.W, pady=5)
        self.temperature_var = tk.DoubleVar(value=0.8)
        tk.Scale(config_frame, from_=0, to=1, resolution=0.1, orient=tk.HORIZONTAL,
                 variable=self.temperature_var, length=300).grid(row=4, column=1, sticky=tk.W, pady=5, padx=5)

        # Max Tokens
        tk.Label(config_frame, text="Max Tokens:", width=12, anchor='w').grid(row=5, column=0, sticky=tk.W, pady=5)
        self.max_tokens_var = tk.IntVar(value=20000)
        tk.Spinbox(config_frame, from_=5000, to=200000, increment=1000,
                   textvariable=self.max_tokens_var, width=15).grid(row=5, column=1, sticky=tk.W, pady=5, padx=5)

        # 测试API按钮
        test_frame = tk.Frame(config_frame)
        test_frame.grid(row=6, column=0, columnspan=2, pady=10)

        tk.Button(
            test_frame,
            text="测试API连接",
            command=self.test_api_connection,
            bg="#2196F3",
            fg="black",
            width=12
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            test_frame,
            text="测试Gemini",
            command=self.test_gemini_simple,
            bg="#FF9800",
            fg="black",
            width=12
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            test_frame,
            text="📝 Prompt管理",
            command=self.manage_writer_prompts,
            bg="#9C27B0",
            fg="black",
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
        tk.Button(folder_frame, text="📁 批量", command=self.select_outline_folder_batch, width=10, bg="#4CAF50", fg="white").pack(side=tk.RIGHT, padx=5)

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
                  bg="#2196F3", fg="black", width=15).pack(side=tk.RIGHT, padx=5)

        # 任务队列
        queue_frame = tk.LabelFrame(self.window, text="📋 任务队列", padx=5, pady=5)
        queue_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 分页控制栏
        pagination_frame = tk.Frame(queue_frame, bg="#f0f0f0")
        pagination_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(
            pagination_frame,
            text="◀ 上一页",
            command=self.previous_page,
            width=10
        ).pack(side=tk.LEFT, padx=5)

        self.page_label = tk.Label(
            pagination_frame,
            text="第 1/1 页 (0 个任务)",
            font=("Arial", 10, "bold"),
            bg="#f0f0f0"
        )
        self.page_label.pack(side=tk.LEFT, padx=20, expand=True)

        # 添加全部开始和清空按钮
        tk.Button(
            pagination_frame,
            text="🗑️ 清空",
            command=self.clear_all_tasks,
            bg="#f44336",
            fg="white",
            width=10,
            font=("Arial", 9, "bold")
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(
            pagination_frame,
            text="▶️ 全部开始",
            command=self.start_all_tasks,
            bg="#4CAF50",
            fg="white",
            width=12,
            font=("Arial", 9, "bold")
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(
            pagination_frame,
            text="下一页 ▶",
            command=self.next_page,
            width=10
        ).pack(side=tk.RIGHT, padx=5)

        # 进度条
        progress_frame = tk.Frame(queue_frame, bg="#f0f0f0", height=30)
        progress_frame.pack(fill=tk.X, padx=5, pady=5)
        progress_frame.pack_propagate(False)

        self.progress_label = tk.Label(
            progress_frame,
            text="进度: 0/0 (0%)",
            font=("Arial", 9, "bold"),
            bg="#f0f0f0"
        )
        self.progress_label.pack(side=tk.LEFT, padx=10)

        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode='determinate',
            length=200
        )
        self.progress_bar.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

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

    def on_api_preset_change(self, event=None):
        """当选择预设API配置时，自动填充API Key和Base URL"""
        preset_name = self.api_preset_var.get()
        if preset_name in self.api_presets:
            preset = self.api_presets[preset_name]
            if preset["api_key"]:  # 如果预设有API Key
                self.api_key_var.set(preset["api_key"])
            if preset["base_url"]:  # 如果预设有Base URL
                self.base_url_var.set(preset["base_url"])

    def test_api_connection(self):
        """测试API连接 - 使用UniversalAPIClient（兼容Gemini和GPT）"""
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
                # 使用UniversalAPIClient（兼容Gemini和GPT）
                client = UniversalAPIClient(api_key=api_key, base_url=base_url)

                # 测试调用
                response = client.chat_completion(
                    model=model,
                    messages=[
                        {"role": "user", "content": "你好"}
                    ],
                    temperature=0.7,
                    max_tokens=25000  # Gemini需要较大的max_tokens
                )

                # 成功
                if response.get('choices') and len(response['choices']) > 0:
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
                    max_tokens=25000  # Gemini需要较大的max_tokens
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

    def manage_writer_prompts(self):
        """Prompt管理和版本控制"""
        # 创建Prompt管理窗口
        prompt_window = tk.Toplevel(self.window)
        prompt_window.title("写作Prompt管理")
        prompt_window.geometry("900x700")

        # 标题
        title_label = tk.Label(
            prompt_window,
            text="📝 写作Prompt模板管理",
            font=("Arial", 16, "bold"),
            bg="#4CAF50",
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
        available_versions = self.prompt_mgr.get_writer_versions()
        current_version = self.prompt_mgr.prompts['writer'].get('active_version', 'Default')
        version_var.set(current_version)

        def on_version_change(event=None):
            selected_version = version_var.get()
            prompt_text.config(state=tk.NORMAL)
            prompt_text.delete("1.0", tk.END)
            try:
                version_prompt = self.prompt_mgr.get_writer_prompt(selected_version)
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
            self.prompt_mgr.set_active_writer_version(selected_version)
            messagebox.showinfo("成功", f"已将 '{selected_version}' 设为活跃版本")

        tk.Button(
            info_frame,
            text="设为活跃",
            command=set_active,
            bg="#4CAF50",
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
            current_prompt = self.prompt_mgr.get_writer_prompt()
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
                    self.prompt_mgr.save_custom_writer_prompt(version_name, new_prompt)
                    self.prompt_mgr.set_active_writer_version(version_name)

                    # 更新版本下拉框
                    version_combo['values'] = self.prompt_mgr.get_writer_versions()
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
                    self.prompt_mgr.restore_default_writer()
                    prompt_text.config(state=tk.NORMAL)
                    prompt_text.delete("1.0", tk.END)
                    prompt_text.insert(tk.END, self.prompt_mgr.get_writer_prompt())
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

        # 如果都不存在，返回用户文档目录
        return docs_dir

    def select_outline_folder(self):
        """选择大纲文件夹 - 自动检测章节数"""
        initial_dir = self._get_default_directory()

        folder = filedialog.askdirectory(title="选择大纲文件夹", initialdir=initial_dir)
        if folder:
            # 规范化路径 - 重要！确保路径在Mac/Windows上都正确
            folder = os.path.abspath(os.path.normpath(folder))
            print(f"🔍 选择的文件夹: {folder}")

            # 验证文件夹包含_writing_prompt.txt
            writing_prompt_path = os.path.join(folder, '_writing_prompt.txt')
            print(f"🔍 检查文件: {writing_prompt_path}")

            if not os.path.exists(writing_prompt_path):
                print(f"⚠️  警告: 所选文件夹不包含 _writing_prompt.txt 文件")
                self.outline_folder_var.set("❌ 无效文件夹")
                return

            # 自动检测章节数（扫描chapter_*_prompt.txt文件）
            import glob
            chapter_files = glob.glob(os.path.join(folder, 'chapter_*_prompt.txt'))

            if chapter_files:
                # 提取章节号
                chapter_nums = []
                for file in chapter_files:
                    filename = os.path.basename(file)
                    try:
                        # 提取章节号: chapter_1_prompt.txt -> 1
                        num = int(filename.split('_')[1])
                        chapter_nums.append(num)
                    except (IndexError, ValueError):
                        continue

                if chapter_nums:
                    max_chapter = max(chapter_nums)
                    total_chapters = len(chapter_nums)

                    # 自动设置章节范围
                    self.start_chapter_var.set(1)
                    self.end_chapter_var.set(max_chapter)

                    print(f"✅ 自动检测到 {total_chapters} 个章节 (1-{max_chapter})")
                    self.outline_folder_var.set(f"{os.path.basename(folder)} ({total_chapters}章)")
                else:
                    print(f"⚠️  警告: 未找到有效的章节大纲文件")
                    self.outline_folder_var.set("❌ 无章节文件")
                    return
            else:
                print(f"⚠️  警告: 文件夹中没有chapter_*_prompt.txt文件")
                self.outline_folder_var.set("❌ 无章节文件")
                return

            self.selected_outline_folder = folder

    def select_outline_folder_batch(self):
        """批量选择大纲文件夹 - 扫描父文件夹下所有子文件夹并自动添加任务"""
        initial_dir = self._get_default_directory()

        parent_folder = filedialog.askdirectory(
            title="选择父文件夹（将自动扫描所有子文件夹并添加任务）",
            initialdir=initial_dir
        )

        if not parent_folder:
            return

        if not self.api_key_var.get():
            print("⚠️  警告: 请先输入API Key")
            return

        # 规范化路径
        parent_folder = os.path.abspath(os.path.normpath(parent_folder))
        print(f"\n📁 批量扫描文件夹: {parent_folder}")

        # 扫描所有子文件夹
        valid_folders = []
        total_scanned = 0

        for root, dirs, files in os.walk(parent_folder):
            total_scanned += 1

            # 检查是否包含_writing_prompt.txt
            if '_writing_prompt.txt' in files:
                # 检查是否有章节文件
                import glob
                chapter_files = glob.glob(os.path.join(root, 'chapter_*_prompt.txt'))

                if chapter_files:
                    folder_path = os.path.abspath(os.path.normpath(root))

                    # 提取章节信息
                    chapter_nums = []
                    for file in chapter_files:
                        filename = os.path.basename(file)
                        try:
                            num = int(filename.split('_')[1])
                            chapter_nums.append(num)
                        except (IndexError, ValueError):
                            continue

                    if chapter_nums:
                        max_chapter = max(chapter_nums)
                        total_chapters = len(chapter_nums)

                        valid_folders.append({
                            'path': folder_path,
                            'name': os.path.basename(folder_path),
                            'chapters': total_chapters,
                            'max_chapter': max_chapter
                        })
                        print(f"  ✅ 找到: {os.path.basename(folder_path)} ({total_chapters}章)")

        print(f"\n扫描完成: 共扫描 {total_scanned} 个文件夹，找到 {len(valid_folders)} 个有效的大纲文件夹")

        if valid_folders:
            # 自动添加所有任务
            added_count = 0
            for folder_info in valid_folders:
                try:
                    # 构建配置
                    config = {
                        'api_key': self.api_key_var.get(),
                        'base_url': self.base_url_var.get(),
                        'model': self.model_var.get(),
                        'temperature': self.temperature_var.get(),
                        'max_tokens': self.max_tokens_var.get(),
                        'start_chapter': 1,
                        'end_chapter': folder_info['max_chapter'],
                        'batch_size': self.batch_size_var.get(),
                        'outline_file': folder_info['path'],  # 大纲文件夹路径
                        'project_folder': folder_info['path']  # 写作到大纲文件夹（和outline在一起）
                    }

                    # 创建任务
                    task = WritingTask(folder_info['path'], config)
                    self.tasks.append(task)
                    added_count += 1
                    print(f"  ✅ 已添加任务: {task.title} (1-{folder_info['max_chapter']}章)")
                except Exception as e:
                    print(f"  ❌ 添加失败: {folder_info['name']}, 错误: {e}")

            # 刷新界面
            self.refresh_task_list()

            print(f"\n✅ 批量添加完成: 成功添加 {added_count}/{len(valid_folders)} 个任务")
            self.outline_folder_var.set(f"✅ 已添加 {added_count} 个任务")
        else:
            print(f"⚠️  未找到有效文件夹")
            self.outline_folder_var.set("❌ 未找到有效文件夹")

    def add_task(self):
        """添加任务到队列"""
        if not hasattr(self, 'selected_outline_folder'):
            print("⚠️  警告: 请先选择大纲文件夹")
            self.outline_folder_var.set("❌ 请先选择文件夹")
            return

        if not self.api_key_var.get():
            print("⚠️  警告: 请输入API Key")
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
            'project_folder': self.selected_outline_folder  # 写作到大纲文件夹（和outline在一起）
        }

        # 创建任务
        task = WritingTask(self.selected_outline_folder, config)
        self.tasks.append(task)

        # 刷新界面
        self.refresh_task_list()

        print(f"✅ 任务已添加：{task.title}")

    def refresh_task_list(self):
        """刷新任务列表 - 支持分页"""
        # 清空
        for widget in self.tasks_frame.winfo_children():
            widget.destroy()
        self.task_containers.clear()

        if not self.tasks:
            self.show_empty_state()
            self._update_pagination_label()
            return

        # 计算分页
        total_tasks = len(self.tasks)
        total_pages = (total_tasks + self.tasks_per_page - 1) // self.tasks_per_page

        # 确保当前页在有效范围内
        if self.current_page >= total_pages:
            self.current_page = max(0, total_pages - 1)

        # 计算当前页的任务范围
        start_idx = self.current_page * self.tasks_per_page
        end_idx = min(start_idx + self.tasks_per_page, total_tasks)

        # 只显示当前页的任务
        for i in range(start_idx, end_idx):
            task = self.tasks[i]
            self._create_task_card(task, i)

        # 更新分页标签
        self._update_pagination_label()

    def _create_task_card(self, task, index):
        """创建任务卡片"""
        # 任务容器 - 更紧凑
        container = tk.Frame(self.tasks_frame, bg="#f5f5f5", relief=tk.RAISED, borderwidth=1)
        container.pack(fill=tk.X, padx=5, pady=3)

        # 左侧信息
        info_frame = tk.Frame(container, bg="#f5f5f5")
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=6)

        # 标题
        tk.Label(
            info_frame,
            text=f"📖 {task.title}",
            font=("Arial", 10, "bold"),
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
            font=("Arial", 8),
            bg="#f5f5f5",
            fg=color  # 使用状态对应的颜色
        ).pack(anchor="w", pady=(3, 3))

        # 进度条
        progress_frame = tk.Frame(info_frame, bg="#f5f5f5")
        progress_frame.pack(fill=tk.X, pady=(3, 0))

        progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, mode='determinate', value=task.progress)
        progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        progress_text = tk.Label(progress_frame, text=f"{task.progress:.1f}% | ${task.cost:.2f}",
                                font=("Arial", 8), bg="#f5f5f5", fg="gray")
        progress_text.pack(side=tk.LEFT, padx=(8, 0))

        # 右侧按钮 - 更紧凑
        button_frame = tk.Frame(container, bg="#f5f5f5")
        button_frame.pack(side=tk.RIGHT, padx=8, pady=6)

        tk.Button(button_frame, text="👁️ Prompt", command=lambda: self.preview_prompt(task),
                  width=9, bg="#FF9800", fg="white", font=("Arial", 8)).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="▶️ 开始", command=lambda: self.start_task(task),
                  width=8, bg="#4CAF50", fg="white", font=("Arial", 8)).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="🔄 重启", command=lambda: self.restart_task(task),
                  width=8, font=("Arial", 8)).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="📂 文件夹", command=lambda: self.open_folder(task),
                  width=9, font=("Arial", 8)).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="🗑️", command=lambda: self.delete_task(index),
                  width=4, bg="#f44336", fg="white", font=("Arial", 8)).pack(side=tk.LEFT, padx=2)

        # 保存引用
        self.task_containers[index] = {
            'container': container,
            'progress_bar': progress_bar,
            'progress_text': progress_text
        }

    def preview_prompt(self, task):
        """预览Prompt - 显示实际会发送给API的完整prompt（新逻辑：单章节）"""
        try:
            # 读取outline文件夹
            outline_folder = task.outline_folder

            # 1. 确定下一章节号
            project_folder = task.config.get('project_folder', outline_folder)
            if os.path.exists(project_folder):
                scan_result = scan_chapter_files(project_folder)
                max_chapter = scan_result['max_chapter']
            else:
                max_chapter = 0

            config_start = task.config.get('start_chapter', 1)
            next_chapter = max(max_chapter + 1, config_start)

            # 2. 从prompt_mgr获取system prompt（固定的写作规则）
            system_prompt = self.prompt_mgr.get_writer_prompt()

            # 3. 读取_writing_prompt.txt（世界观+角色）
            writing_prompt_file = os.path.join(outline_folder, '_writing_prompt.txt')
            base_info = ""
            if os.path.exists(writing_prompt_file):
                with open(writing_prompt_file, 'r', encoding='utf-8') as f:
                    base_info = f.read()

            # 4. 读取当前章节的summary（只读取单个章节）
            chapter_summary = ""

            # 添加上一章summary（如果有）
            if next_chapter > 1:
                prev_file = os.path.join(outline_folder, f'chapter_{next_chapter - 1}_prompt.txt')
                if os.path.exists(prev_file):
                    with open(prev_file, 'r', encoding='utf-8') as f:
                        chapter_summary += f"===== Previous Chapter Summary =====\n"
                        chapter_summary += f.read() + "\n\n"

            # 添加当前章节summary
            current_file = os.path.join(outline_folder, f'chapter_{next_chapter}_prompt.txt')
            if os.path.exists(current_file):
                with open(current_file, 'r', encoding='utf-8') as f:
                    chapter_summary += f"===== Current Chapter Outline =====\n"
                    chapter_summary += f.read() + "\n\n"

            # 5. 构建user prompt
            user_prompt = f"""【Book Information】
Title: {task.title}
Genre: {task.config.get('genre', 'Novel')}

【World & Characters】
{base_info}

【Chapter Outline】
{chapter_summary}"""

            # 6. 读取上一章最后1500字符
            previous_context = ""
            if next_chapter > 1:
                prev_chapter_file = os.path.join(project_folder, f'chapter_{next_chapter - 1}.txt')
                if os.path.exists(prev_chapter_file):
                    try:
                        with open(prev_chapter_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if '---' in content:
                                content = content.split('---')[0]
                            previous_context = content[-1500:] if len(content) > 1500 else content
                    except:
                        pass

            if previous_context:
                user_prompt += f"""

【Previous Chapter Ending (Last 1500 characters)】
{previous_context}
"""
            else:
                if next_chapter == 1:
                    user_prompt += """

【Note】
This is the first chapter - establish the world and hook readers immediately.
"""

            user_prompt += f"""

Now write Chapter {next_chapter} based on the outline above."""

            # 7. 显示在窗口中
            self._show_prompt_window(task, system_prompt, user_prompt, next_chapter, next_chapter, max_chapter)

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
            text=f"已完成: {max_chapter} 章  |  下一章节: Chapter {next_start}",
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

    def start_all_tasks(self):
        """一键开始所有待处理的任务"""
        if not self.tasks:
            messagebox.showinfo("提示", "没有任务")
            return

        pending_tasks = [t for t in self.tasks if t.status == 'pending']
        if not pending_tasks:
            messagebox.showinfo("提示", "所有任务都已开始或完成")
            return

        print(f"\n🚀 全部开始: 共 {len(pending_tasks)} 个待处理任务")
        started_count = 0
        skipped_count = 0
        for task in pending_tasks:
            try:
                # silent_on_conflict=True 避免批量启动时弹出多个冲突窗口
                success = self.start_task(task, silent_on_conflict=True)
                if success:
                    started_count += 1
                    time.sleep(0.5)  # 稍微延迟避免同时启动太多
                else:
                    skipped_count += 1
            except Exception as e:
                print(f"❌ 启动失败: {task.title}, 错误: {e}")
                import traceback
                traceback.print_exc()

        print(f"✅ 已启动 {started_count} 个任务" + (f"，跳过 {skipped_count} 个冲突任务" if skipped_count > 0 else ""))

    def update_progress(self):
        """更新任务进度条"""
        total = len(self.tasks)
        if total == 0:
            self.progress_label.config(text="进度: 0/0 (0%)")
            self.progress_bar['value'] = 0
            return

        completed = len([t for t in self.tasks if t.status == 'completed'])
        percentage = int((completed / total) * 100)

        self.progress_label.config(text=f"进度: {completed}/{total} ({percentage}%)")
        self.progress_bar['maximum'] = total
        self.progress_bar['value'] = completed

    def clear_all_tasks(self):
        """清空所有任务"""
        if not self.tasks:
            messagebox.showinfo("提示", "任务队列已经是空的")
            return

        # 检查是否有运行中的任务
        running_tasks = [t for t in self.tasks if t.status == 'in_progress']
        if running_tasks:
            messagebox.showwarning("无法清空", f"有 {len(running_tasks)} 个任务正在运行中，请先等待完成或停止")
            return

        # 确认对话框
        if not messagebox.askyesno("确认清空", f"确定要清空 {len(self.tasks)} 个写作任务吗？\n\n注意：已完成的章节文件不会被删除"):
            return

        print(f"🗑️ 清空 {len(self.tasks)} 个写作任务")

        # 清空任务列表
        self.tasks.clear()

        # 重置分页
        self.current_page = 0

        # 刷新显示和进度条
        self.refresh_task_list()
        self.update_progress()
        print("✅ 写作任务已清空")

    def start_task(self, task, silent_on_conflict=False):
        """启动任务 - 直接运行worker（不用subprocess，避免exe打包问题）

        Args:
            task: 要启动的任务
            silent_on_conflict: 如果为True，遇到冲突时不弹窗，只打印日志

        Returns:
            True: 成功启动
            False: 启动失败或冲突
        """
        print(f"\n{'='*70}")
        print(f"🎬 start_task() 被调用")
        print(f"  任务: {task.title}")
        print(f"  当前状态: {task.status}")
        print(f"  当前进度: {task.current_chapter}/{task.total_chapters}")
        print(f"  配置检查:")
        print(f"    - api_key: {'存在' if task.config.get('api_key') else '❌ 缺失'}")
        print(f"    - base_url: {task.config.get('base_url', '❌ 缺失')}")
        print(f"    - model: {task.config.get('model', '❌ 缺失')}")
        print(f"    - outline_file: {task.config.get('outline_file', '❌ 缺失')}")
        print(f"{'='*70}\n")

        if task.status == 'in_progress':
            if not silent_on_conflict:
                messagebox.showinfo("提示", "任务正在运行中")
            print("  ⏸️ 任务已在运行，返回")
            return False

        # 检查是否有其他任务正在使用相同的文件夹（防止并行冲突）
        task_outline_folder = task.config.get('project_folder', task.outline_folder)
        for other_task in self.tasks:
            if other_task != task and other_task.status == 'in_progress':
                other_folder = other_task.config.get('project_folder', other_task.outline_folder)
                if task_outline_folder == other_folder:
                    if not silent_on_conflict:
                        messagebox.showwarning("冲突", f"该文件夹已有任务正在运行中！\n\n文件夹: {os.path.basename(task_outline_folder)}\n\n请等待其完成后再启动。")
                    print(f"  ⚠️ 冲突: 文件夹 {task_outline_folder} 已有任务在运行，跳过")
                    return False

        # 如果是completed或failed状态，询问是否重新开始
        if task.status in ['completed', 'failed']:
            print(f"  ⚠️ 任务状态为 {task.status}，重新开始")
            # 直接重新开始，不再弹出确认对话框
            # 重置状态
            print("  ✅ 用户确认，重置任务状态")
            task.progress = 0
            task.current_chapter = 0
            # 清理旧的进度文件
            if hasattr(task, 'task_id'):
                old_progress = os.path.join('tasks', task.task_id, 'progress.json')
                if os.path.exists(old_progress):
                    os.remove(old_progress)
                    print(f"  🗑️ 已删除旧进度文件: {old_progress}")

        task.status = 'in_progress'
        task.started_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"  ✅ 任务状态更新为: in_progress")
        print(f"  ⏰ 启动时间: {task.started_at}\n")

        # 直接运行WriterWorker（不用subprocess，就像Jupyter代码一样）
        def _run_task():
            try:
                print(f"\n{'='*70}")
                print(f"🚀 启动任务: {task.title}")
                print(f"{'='*70}")

                # 直接导入并运行worker（不用subprocess！）
                from writer_worker_v2 import WriterWorkerV2

                # 创建临时配置（不需要文件）
                task_id = f"writing_{int(time.time()*1000)}"
                task.task_id = task_id  # 保存task_id用于进度跟踪

                print(f"  任务ID: {task_id}")
                print(f"\n📝 配置内容:")
                for key, value in task.config.items():
                    if key == 'api_key':
                        print(f"  {key}: {value[:10]}...{value[-5:]}")
                    else:
                        print(f"  {key}: {value}")

                # 创建任务目录
                task_dir = os.path.join('tasks', task_id)
                os.makedirs(task_dir, exist_ok=True)

                # 创建临时config文件（worker需要读取）
                config_file = os.path.join(task_dir, 'config.json')
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(task.config, f, indent=2, ensure_ascii=False)

                print(f"\n✅ 配置文件已创建: {config_file}")
                print(f"\n🔧 直接运行 WriterWorkerV2（不用subprocess）...")
                print(f"{'='*70}\n")

                # 直接创建并运行worker（就像Jupyter一样！）
                worker = WriterWorkerV2(config_file, task_id)
                worker.run()

                print(f"\n{'='*70}")
                print(f"✅ 任务完成: {task.title}")
                print(f"{'='*70}\n")

                # 读取最终进度文件，确保current_chapter是最新的
                if hasattr(task, 'task_id'):
                    progress_file = os.path.join('tasks', task.task_id, 'progress.json')
                    if os.path.exists(progress_file):
                        try:
                            with open(progress_file, 'r', encoding='utf-8') as f:
                                final_progress = json.load(f)
                            task.current_chapter = final_progress.get('current_chapter', task.current_chapter)
                            task.progress = (task.current_chapter / task.total_chapters) * 100 if task.total_chapters > 0 else 100
                            print(f"  📊 最终进度: {task.current_chapter}/{task.total_chapters}")
                        except Exception as e:
                            print(f"  ⚠️ 读取最终进度失败: {e}")

                task.status = 'completed'
                self.window.after(0, lambda: (self.refresh_task_list(), self.update_progress()))

            except Exception as e:
                print(f"\n{'='*70}")
                print(f"❌ 任务异常: {e}")
                print(f"{'='*70}")
                import traceback
                traceback.print_exc()

                # 读取最终进度文件，获取失败时的current_chapter
                if hasattr(task, 'task_id'):
                    progress_file = os.path.join('tasks', task.task_id, 'progress.json')
                    if os.path.exists(progress_file):
                        try:
                            with open(progress_file, 'r', encoding='utf-8') as f:
                                final_progress = json.load(f)
                            task.current_chapter = final_progress.get('current_chapter', task.current_chapter)
                            task.progress = (task.current_chapter / task.total_chapters) * 100 if task.total_chapters > 0 else 0
                            print(f"  📊 失败时进度: {task.current_chapter}/{task.total_chapters}")
                        except Exception as read_error:
                            print(f"  ⚠️ 读取最终进度失败: {read_error}")

                task.status = 'failed'
                self.window.after(0, lambda: (self.refresh_task_list(), self.update_progress()))

        # 在新线程中运行
        import threading
        thread = threading.Thread(target=_run_task, daemon=True)
        thread.start()

        # 启动全局进度监控（如果还未启动）
        if not self.progress_monitor_running:
            self._start_global_progress_monitor()

        print(f"✅ 任务已启动：{task.title}")
        self.refresh_task_list()
        return True

    def _start_global_progress_monitor(self):
        """启动全局进度监控 - 所有任务统一每5秒更新一次"""
        if self.progress_monitor_running:
            return

        self.progress_monitor_running = True
        print(f"🔄 启动全局进度监控（每{self.progress_update_interval/1000}秒更新）")

        def _update_all_progress():
            if not self.progress_monitor_running:
                return

            # 检查是否有运行中的任务
            has_running_tasks = any(t.status == 'in_progress' for t in self.tasks)

            if has_running_tasks:
                # 批量更新所有任务进度
                updated = False
                for task in self.tasks:
                    if task.status == 'in_progress' and hasattr(task, 'task_id'):
                        progress_file = os.path.join('tasks', task.task_id, 'progress.json')
                        if os.path.exists(progress_file):
                            try:
                                with open(progress_file, 'r', encoding='utf-8') as f:
                                    progress = json.load(f)

                                # 更新task对象
                                old_chapter = task.current_chapter
                                task.current_chapter = progress.get('current_chapter', 0)
                                task.progress = (task.current_chapter / task.total_chapters) * 100 if task.total_chapters > 0 else 0

                                # 检查状态变化
                                progress_status = progress.get('status', 'in_progress')
                                if progress_status in ['completed', 'failed']:
                                    task.status = progress_status
                                    updated = True
                                elif old_chapter != task.current_chapter:
                                    updated = True

                            except:
                                pass

                # 只有当有变化时才刷新UI（减少不必要的刷新）
                if updated:
                    self.window.after(0, self.refresh_task_list)

                # 继续监控
                self.window.after(self.progress_update_interval, _update_all_progress)
            else:
                # 没有运行中的任务，停止监控
                print("⏸️ 无运行中任务，停止全局进度监控")
                self.progress_monitor_running = False

        # 1秒后开始第一次检查
        self.window.after(1000, _update_all_progress)

    def _start_progress_monitoring(self, task):
        """监控任务进度并更新UI - 已弃用，使用全局监控代替"""
        # 这个方法保留但不再使用，由 _start_global_progress_monitor 代替
        pass

    def restart_task(self, task):
        """重启任务（清除状态和进度，相当于重新开始）"""
        print(f"🔄 重启任务: {task.title}")

        # 清理进度文件
        if hasattr(task, 'task_id') and task.task_id:
            progress_file = os.path.join('tasks', task.task_id, 'progress.json')
            if os.path.exists(progress_file):
                try:
                    os.remove(progress_file)
                    print(f"  🗑️ 已删除进度文件: {progress_file}")
                except Exception as e:
                    print(f"  ⚠️ 删除进度文件失败: {e}")

            # 清理task_id
            delattr(task, 'task_id')

        # 重置任务状态
        task.current_chapter = 0
        task.progress = 0
        task.cost = 0.0
        task.status = 'pending'
        task.started_at = None
        task.worker_thread = None

        print(f"  ✅ 任务已重置为初始状态")
        self.refresh_task_list()

    def open_folder(self, task):
        """打开文件夹"""
        folder = task.outline_folder

        if not folder or not os.path.exists(folder):
            messagebox.showwarning("警告", "项目文件夹不存在")
            return

        try:
            if sys.platform == 'win32':
                os.startfile(folder)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', folder])
            else:
                subprocess.Popen(['xdg-open', folder])
        except Exception as e:
            messagebox.showerror("错误", f"打开文件夹失败: {str(e)}")

    def delete_task(self, index):
        """删除任务"""
        print(f"🗑️ 删除任务 #{index + 1}")
        del self.tasks[index]
        self.refresh_task_list()

    def previous_page(self):
        """上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_task_list()

    def next_page(self):
        """下一页"""
        total_pages = (len(self.tasks) + self.tasks_per_page - 1) // self.tasks_per_page
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.refresh_task_list()

    def _update_pagination_label(self):
        """更新分页标签"""
        total_tasks = len(self.tasks)
        if total_tasks == 0:
            self.page_label.config(text="第 1/1 页 (0 个任务)")
            return

        total_pages = (total_tasks + self.tasks_per_page - 1) // self.tasks_per_page
        current_page_display = self.current_page + 1

        start_idx = self.current_page * self.tasks_per_page
        end_idx = min(start_idx + self.tasks_per_page, total_tasks)

        self.page_label.config(
            text=f"第 {current_page_display}/{total_pages} 页 "
                 f"(共 {total_tasks} 个任务，显示 {start_idx + 1}-{end_idx})"
        )

    def run(self):
        """运行应用"""
        self.window.mainloop()


def main():
    app = WritingToolWindow()
    app.run()


if __name__ == '__main__':
    main()
