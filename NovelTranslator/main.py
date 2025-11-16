"""
小说翻译工具 - 完整增强版 v1.1

功能列表:
✅ API Key和Base URL配置  
✅ Model自定义输入
✅ 全名格式支持
✅ 任务开始时间和计时器
✅ Preview功能（查看Prompt、风格、人名）
✅ 历史任务记录
✅ Excel保存和导出
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import threading
import time
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import pandas as pd

from config import ConfigManager
from resource_mgr import ResourceManager
from translator import Translator


class TranslatorApp:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("小说翻译工具 v1.1")
        self.window.geometry("900x900")
        self.window.resizable(True, True)

        # 管理器
        self.config_mgr = ConfigManager()
        self.resource_mgr = ResourceManager()
        self.translator = Translator(self.config_mgr, self.resource_mgr)

        # 数据
        self.files = []
        self.executor = None
        self.is_translating = False
        self.translation_results = {}
        self.total_start_time = 0
        self.completed_count = 0
        self.current_resources = []

        # 创建UI
        self.create_widgets()

        # 启动日志
        self.log("="*60, "INFO")
        self.log("小说翻译工具 v1.1 启动", "SUCCESS")
        self.log("="*60, "INFO")

        # 加载配置
        self.load_config()

    def create_widgets(self):
        """创建UI组件"""

        # ========== 标题栏 ==========
        title_frame = tk.Frame(self.window, bg="#2c3e50", height=50)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        title_label = tk.Label(
            title_frame,
            text="📖 小说翻译工具 v1.1",
            font=("Arial", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=10)

        # 历史记录按钮
        history_btn = tk.Button(
            title_frame,
            text="📋 历史记录",
            command=self.show_history,
            bg="#9b59b6",
            fg="white",
            font=("Arial", 10),
            relief=tk.FLAT,
            padx=15,
            pady=5
        )
        history_btn.pack(side=tk.RIGHT, padx=10, pady=10)

        # Excel导出按钮  
        excel_btn = tk.Button(
            title_frame,
            text="📊 导出Excel",
            command=self.export_to_excel,
            bg="#e67e22",
            fg="white",
            font=("Arial", 10),
            relief=tk.FLAT,
            padx=15,
            pady=5
        )
        excel_btn.pack(side=tk.RIGHT, padx=10, pady=10)

        # ========== API配置区 ==========
        api_frame = tk.LabelFrame(self.window, text="API 配置", padx=10, pady=10)
        api_frame.pack(fill=tk.X, padx=20, pady=10)

        # API Key
        tk.Label(api_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W)
        self.api_key_entry = tk.Entry(api_frame, width=50, show="•")
        self.api_key_entry.grid(row=0, column=1, padx=5, columnspan=2)

        self.test_btn = tk.Button(
            api_frame,
            text="测试连接",
            command=self.test_api,
            bg="#27ae60",
            fg="white",
            relief=tk.FLAT,
            padx=10
        )
        self.test_btn.grid(row=0, column=3, padx=5)

        self.api_status_label = tk.Label(api_frame, text="● 未测试", fg="gray")
        self.api_status_label.grid(row=0, column=4, padx=5)

        # Base URL
        tk.Label(api_frame, text="Base URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.api_url_entry = tk.Entry(api_frame, width=50)
        self.api_url_entry.grid(row=1, column=1, padx=5, pady=5, columnspan=2)

        tk.Label(api_frame, text="(如: https://yunwuapi.com/v1/)", fg="gray", font=("Arial", 8)).grid(
            row=1, column=3, columnspan=2, sticky=tk.W
        )

        # Model
        tk.Label(api_frame, text="Model:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.model_entry = tk.Entry(api_frame, width=30)
        self.model_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)

        # Model快捷选择按钮
        tk.Button(
            api_frame,
            text="gpt-5.1",
            command=lambda: self.set_model("gpt-5.1"),
            bg="#3498db",
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=3,
            font=("Arial", 9)
        ).grid(row=2, column=2, padx=5)

        tk.Button(
            api_frame,
            text="gemini-2.5-pro",
            command=lambda: self.set_model("gemini-2.5-pro"),
            bg="#16a085",
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=3,
            font=("Arial", 9)
        ).grid(row=2, column=3, padx=5)

        # 线程数
        tk.Label(api_frame, text="线程数:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.workers_spinbox = tk.Spinbox(api_frame, from_=1, to=20, width=10)
        self.workers_spinbox.grid(row=3, column=1, sticky=tk.W, padx=5)

        # ========== 文件管理区 ==========
        file_frame = tk.LabelFrame(self.window, text="文件管理", padx=10, pady=10)
        file_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # 按钮区
        btn_frame = tk.Frame(file_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Button(
            btn_frame,
            text="+ 添加文件",
            command=self.add_files,
            bg="#3498db",
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=5
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="+ 添加文件夹",
            command=self.add_folder,
            bg="#3498db",
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=5
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="清空列表",
            command=self.clear_files,
            bg="#e74c3c",
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=5
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="🔍 Preview",
            command=self.show_preview,
            bg="#9b59b6",
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=5
        ).pack(side=tk.LEFT, padx=5)

        # 文件列表
        tk.Label(file_frame, text="待翻译列表:", font=("Arial", 10, "bold")).pack(anchor=tk.W)

        list_frame = tk.Frame(file_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.file_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            height=8,
            font=("Consolas", 9)
        )
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)

        # 统计信息
        self.stats_label = tk.Label(
            file_frame,
            text="共 0 本 | 预计 $0.00",
            font=("Arial", 10),
            fg="#2c3e50"
        )
        self.stats_label.pack(pady=5)

        # ========== 开始翻译按钮 ==========
        self.start_btn = tk.Button(
            self.window,
            text="🚀 开始翻译",
            command=self.start_translation,
            bg="#27ae60",
            fg="white",
            font=("Arial", 14, "bold"),
            relief=tk.FLAT,
            pady=10
        )
        self.start_btn.pack(fill=tk.X, padx=20, pady=10)

        # ========== 翻译状态区 ==========
        status_frame = tk.LabelFrame(self.window, text="翻译状态", padx=10, pady=10)
        status_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.status_text = scrolledtext.ScrolledText(
            status_frame,
            height=10,
            font=("Consolas", 9),
            state=tk.DISABLED
        )
        self.status_text.pack(fill=tk.BOTH, expand=True)

        # 任务时间显示
        time_frame = tk.Frame(status_frame)
        time_frame.pack(fill=tk.X, pady=5)

        tk.Label(time_frame, text="任务开始时间:", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        self.start_time_label = tk.Label(time_frame, text="-", font=("Arial", 9, "bold"), fg="#3498db")
        self.start_time_label.pack(side=tk.LEFT, padx=5)

        tk.Label(time_frame, text="|", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

        tk.Label(time_frame, text="已用时:", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        self.elapsed_time_label = tk.Label(time_frame, text="0秒", font=("Arial", 9, "bold"), fg="#e74c3c")
        self.elapsed_time_label.pack(side=tk.LEFT, padx=5)

        # 总进度
        self.progress_label = tk.Label(
            status_frame,
            text="总耗时: 0秒 | 完成: 0/0",
            font=("Arial", 10, "bold"),
            fg="#2c3e50"
        )
        self.progress_label.pack(pady=5)

        # 查看Prompts按钮
        tk.Button(
            status_frame,
            text="🔍 查看Prompts",
            command=self.show_prompts,
            bg="#3498db",
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=5,
            font=("Arial", 9)
        ).pack(pady=5)

        # ========== 日志区 ==========
        log_frame = tk.LabelFrame(self.window, text="实时日志", padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=8,
            font=("Consolas", 8),
            state=tk.DISABLED,
            bg="#f8f9fa",
            fg="#2c3e50"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def log(self, message: str, level: str = "INFO"):
        """写入日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # 颜色标记
        if level == "ERROR":
            prefix = "❌"
            color = "red"
        elif level == "SUCCESS":
            prefix = "✅"
            color = "green"
        elif level == "WARNING":
            prefix = "⚠️"
            color = "orange"
        else:
            prefix = "ℹ️"
            color = "#2c3e50"

        log_entry = f"[{timestamp}] {prefix} {message}\n"

        def _update():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, log_entry)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)

        # 如果在主线程，直接更新；否则调度到主线程
        try:
            self.window.after(0, _update)
        except:
            _update()

    def load_config(self):
        """加载配置"""
        self.log("正在加载配置...")

        api_key = self.config_mgr.get_api_key()
        if api_key:
            self.api_key_entry.insert(0, api_key)
            self.log(f"API Key已加载 (长度: {len(api_key)})")

        api_url = self.config_mgr.get_api_base_url()
        if api_url:
            self.api_url_entry.insert(0, api_url)
            self.log(f"Base URL已加载: {api_url}")

        # 加载model
        config = self.config_mgr.load_config()
        model = config.get('model', 'gpt-5.1')
        self.model_entry.insert(0, model)
        self.log(f"Model已加载: {model}")

        workers = self.config_mgr.get_max_workers()
        self.workers_spinbox.delete(0, tk.END)
        self.workers_spinbox.insert(0, str(workers))
        self.log(f"线程数已设置: {workers}")

        self.log("配置加载完成", "SUCCESS")

    def set_model(self, model_name: str):
        """快捷设置Model"""
        self.log(f"设置Model为: {model_name}")
        try:
            self.model_entry.delete(0, tk.END)
            self.model_entry.insert(0, model_name)
            # 自动保存
            config = self.config_mgr.load_config()
            config['model'] = model_name
            self.config_mgr.save_config(config)
            self.log(f"Model设置成功: {model_name}", "SUCCESS")
            messagebox.showinfo("成功", f"Model已设置为: {model_name}")
        except Exception as e:
            self.log(f"设置Model失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"设置Model失败: {str(e)}")

    def test_api(self):
        """测试API连接"""
        self.log("开始测试API连接...")
        try:
            api_key = self.api_key_entry.get().strip()
            if not api_key:
                self.log("API Key为空", "WARNING")
                messagebox.showwarning("警告", "请先输入 API Key")
                return

            api_url = self.api_url_entry.get().strip()
            if not api_url:
                self.log("Base URL为空", "WARNING")
                messagebox.showwarning("警告", "请先输入 Base URL")
                return

            model = self.model_entry.get().strip()
            if not model:
                self.log("Model为空", "WARNING")
                messagebox.showwarning("警告", "请先输入 Model")
                return

            self.log(f"API配置 - URL: {api_url}, Model: {model}")

            # 保存配置
            self.config_mgr.set_api_key(api_key)
            self.config_mgr.set_api_base_url(api_url)

            config = self.config_mgr.load_config()
            config['model'] = model
            self.config_mgr.save_config(config)

            self.log("配置已保存，正在测试连接...")

            # 更新状态
            self.api_status_label.config(text="● 测试中...", fg="orange")
            self.test_btn.config(state=tk.DISABLED)

            # 在新线程中测试
            def test_thread():
                try:
                    self.log("测试线程已启动")
                    result = self.translator.test_api_connection(self.call_api)
                    self.log(f"测试结果: {result}")
                    self.window.after(0, lambda: self.update_api_status(result))
                except Exception as e:
                    self.log(f"测试线程异常: {str(e)}", "ERROR")
                    error_result = {'success': False, 'message': f"测试失败: {str(e)}"}
                    self.window.after(0, lambda: self.update_api_status(error_result))

            threading.Thread(target=test_thread, daemon=True).start()
            self.log("测试线程已创建")

        except Exception as e:
            self.log(f"测试API异常: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"测试失败: {str(e)}")

    def update_api_status(self, result):
        """更新API状态"""
        self.log(f"更新API状态: {result}")
        try:
            if result['success']:
                self.api_status_label.config(text="● " + result['message'], fg="green")
                self.log("API连接测试成功", "SUCCESS")
            else:
                self.api_status_label.config(text="● " + result['message'], fg="red")
                self.log(f"API连接测试失败: {result['message']}", "ERROR")
            self.test_btn.config(state=tk.NORMAL)
        except Exception as e:
            self.log(f"更新API状态异常: {str(e)}", "ERROR")

    def add_files(self):
        """添加文件"""
        self.log("打开文件选择对话框...")
        try:
            files = filedialog.askopenfilenames(
                title="选择小说文件",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
            )
            if files:
                self.log(f"选中 {len(files)} 个文件")
                for file in files:
                    if file not in self.files:
                        self.files.append(file)
                        basename = os.path.basename(file)
                        size = os.path.getsize(file)
                        word_count = size // 3
                        display = f"{basename} ({word_count/10000:.1f}w字)"
                        self.file_listbox.insert(tk.END, display)
                        self.log(f"添加文件: {basename}")

                self.update_stats()
                self.log(f"文件添加完成，当前共 {len(self.files)} 个文件", "SUCCESS")
            else:
                self.log("未选择文件")
        except Exception as e:
            self.log(f"添加文件失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"添加文件失败: {str(e)}")

    def add_folder(self):
        """添加文件夹"""
        folder = filedialog.askdirectory(title="选择文件夹")
        if folder:
            for filename in os.listdir(folder):
                if filename.endswith('.txt'):
                    file_path = os.path.join(folder, filename)
                    if file_path not in self.files:
                        self.files.append(file_path)
                        size = os.path.getsize(file_path)
                        word_count = size // 3
                        display = f"{filename} ({word_count/10000:.1f}w字)"
                        self.file_listbox.insert(tk.END, display)

            self.update_stats()

    def clear_files(self):
        """清空文件列表"""
        self.files = []
        self.file_listbox.delete(0, tk.END)
        self.update_stats()

    def update_stats(self):
        """更新统计信息"""
        count = len(self.files)
        estimated_cost = count * 0.20
        self.stats_label.config(text=f"共 {count} 本 | 预计 ${estimated_cost:.2f}")

    def show_preview(self):
        """显示Preview窗口"""
        self.log("打开Preview窗口...")
        try:
            if not self.files:
                self.log("文件列表为空，无法Preview", "WARNING")
                messagebox.showwarning("警告", "请先添加文件")
                return

            # 分配资源
            self.log("正在分配资源用于Preview...")
            resources = self.resource_mgr.allocate_resources(self.files)
            self.log(f"资源分配完成，准备显示 {len(resources)} 本书的Preview")

            # 创建Preview窗口
            preview_window = tk.Toplevel(self.window)
            preview_window.title("🔍 Preview - Prompt & Resources")
            preview_window.geometry("850x750")

            # Notebook
            notebook = ttk.Notebook(preview_window)
            notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # 遍历每个文件
            for i, (file, resource) in enumerate(zip(self.files[:5], resources[:5])):
                title = self.resource_mgr.extract_title(file)
                genre = resource['genre']

                # 创建标签页
                tab = tk.Frame(notebook)
                notebook.add(tab, text=f"{title} ({genre})")

                # 内容区
                content_text = scrolledtext.ScrolledText(
                    tab,
                    font=("Consolas", 9),
                    wrap=tk.WORD
                )
                content_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

                # 构建显示内容
                preview_content = f"""{'='*70}
📖 文件: {os.path.basename(file)}
📂 类型: {genre}
✍️  风格作者: {resource['author']}
{'='*70}

【写作风格】
{resource['style']}

{'='*70}
【可用角色名（Full Name格式）】

男性角色 (前10个):
"""
                names_data = self.resource_mgr.load_names()
                male_names = [n for n in resource['names'] if n in names_data['male']][:10]
                for name in male_names:
                    preview_content += f"  • {name['fullname']} (first: {name['firstname']}, last: {name['lastname']})\n"

                preview_content += "\n女性角色 (前10个):\n"
                female_names = [n for n in resource['names'] if n in names_data['female']][:10]
                for name in female_names:
                    preview_content += f"  • {name['fullname']} (first: {name['firstname']}, last: {name['lastname']})\n"

                preview_content += f"\n{'='*70}\n"
                preview_content += "【完整Prompt（前2000字符）】\n\n"

                # 构建完整Prompt
                full_prompt = self.translator.build_prompt(resource['style'], resource['names'])
                preview_content += full_prompt[:2000] + "\n\n... (省略部分内容)"

                content_text.insert(1.0, preview_content)
                content_text.config(state=tk.DISABLED)

            # 关闭按钮
            tk.Button(
                preview_window,
                text="关闭",
                command=preview_window.destroy,
                bg="#95a5a6",
                fg="white",
                relief=tk.FLAT,
                padx=20,
                pady=5
            ).pack(pady=10)

            self.log("Preview窗口已打开", "SUCCESS")

        except Exception as e:
            self.log(f"打开Preview失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"打开Preview失败: {str(e)}")

    def start_translation(self):
        """开始翻译"""
        self.log("=== 开始翻译流程 ===")
        try:
            if self.is_translating:
                self.log("已有翻译任务在运行", "WARNING")
                messagebox.showwarning("警告", "正在翻译中，请稍候")
                return

            if not self.files:
                self.log("文件列表为空", "WARNING")
                messagebox.showwarning("警告", "请先添加要翻译的文件")
                return

            api_key = self.api_key_entry.get().strip()
            if not api_key:
                self.log("API Key为空", "WARNING")
                messagebox.showwarning("警告", "请先输入 API Key")
                return

            api_url = self.api_url_entry.get().strip()
            if not api_url:
                self.log("Base URL为空", "WARNING")
                messagebox.showwarning("警告", "请先输入 Base URL")
                return

            model = self.model_entry.get().strip()
            if not model:
                self.log("Model为空", "WARNING")
                messagebox.showwarning("警告", "请先输入 Model")
                return

            self.log(f"配置检查通过 - 文件数: {len(self.files)}, Model: {model}")

            # 保存配置
            self.config_mgr.set_api_key(api_key)
            self.config_mgr.set_api_base_url(api_url)

            config = self.config_mgr.load_config()
            config['model'] = model
            self.config_mgr.save_config(config)

            workers = int(self.workers_spinbox.get())
            self.config_mgr.set_max_workers(workers)

            self.log(f"配置已保存 - 线程数: {workers}")

            # 确认
            if not messagebox.askyesno("确认", f"准备翻译 {len(self.files)} 本小说\n使用模型: {model}\n使用 {workers} 个线程\n\n是否开始？"):
                self.log("用户取消翻译")
                return

            self.log("用户确认开始翻译")

            # 开始翻译
            self.is_translating = True
            self.start_btn.config(state=tk.DISABLED, text="⏳ 翻译中...")
            self.completed_count = 0
            self.total_start_time = time.time()
            self.translation_results = {}

            # 显示开始时间
            start_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.start_time_label.config(text=start_time_str)

            self.log(f"翻译任务启动 - 开始时间: {start_time_str}", "SUCCESS")

            # 清空状态显示
            self.status_text.config(state=tk.NORMAL)
            self.status_text.delete(1.0, tk.END)
            self.status_text.config(state=tk.DISABLED)

            # 在新线程中执行翻译
            threading.Thread(target=self.translate_all, daemon=True).start()

            self.log("翻译线程已创建")

            # 启动进度更新
            self.update_progress()

        except Exception as e:
            self.log(f"开始翻译异常: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"启动翻译失败: {str(e)}")

    async def translate_all_async(self):
        """异步批量翻译 - 真正的并发"""
        self.log("异步翻译开始...")
        try:
            self.log("正在分配资源（风格和人名）...")
            resources = self.resource_mgr.allocate_resources(self.files)
            self.current_resources = resources
            self.log(f"资源分配完成 - 共 {len(resources)} 个任务")

            # 创建异步任务列表
            tasks = []
            for i, (file, resource) in enumerate(zip(self.files, resources)):
                title = os.path.basename(file)
                self.log(f"创建异步任务 {i+1}/{len(self.files)}: {title}")
                task = self.translate_one_async(file, resource)
                tasks.append(task)

            self.log(f"所有异步任务已创建，开始并发执行...")

            # 并发执行所有任务
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理结果
            for result in results:
                if isinstance(result, Exception):
                    self.log(f"任务执行异常: {str(result)}", "ERROR")
                elif result and result.get('success'):
                    self.completed_count += 1
                    # 保存prompt和tags到translation_results
                    if result['title'] in self.translation_results:
                        self.translation_results[result['title']]['prompt'] = result.get('prompt', '')
                        self.translation_results[result['title']]['tags'] = result.get('tags', [])
                    self.log(f"任务完成 ({self.completed_count}/{len(self.files)})")

            self.log("所有异步任务已完成，准备收尾...", "SUCCESS")
            self.window.after(0, self.translation_complete)

        except Exception as e:
            self.log(f"异步翻译异常: {str(e)}", "ERROR")
            self.window.after(0, lambda: messagebox.showerror("错误", f"翻译失败: {str(e)}"))
            self.window.after(0, self.reset_ui)

    async def translate_one_async(self, file_path: str, resource: dict):
        """异步翻译单个文件"""
        try:
            title = self.resource_mgr.extract_title(file_path)

            # 读取文件
            content = self.translator.read_file(file_path)

            # 构建Prompt
            prompt = self.translator.build_prompt(resource['style'], resource['names'])

            # 更新状态：运行中
            self.window.after(0, lambda: self.update_status(title, "运行中", 0, 0, prompt))

            # 异步调用API
            start_time = time.time()
            translated, input_tokens, output_tokens = await self.call_api_async(prompt, content)

            # 计算成本和耗时
            duration = time.time() - start_time
            cost = self.config_mgr.calculate_cost(input_tokens, output_tokens)

            # 保存结果
            output_file = self.translator.save_result(title, translated)

            # 提取tags
            tags = self.translator.extract_tags(translated)

            # 提取使用的人名并更新使用次数
            used_names = self.translator.extract_used_names(translated, resource['names'])
            self.resource_mgr.update_name_usage(used_names)

            # 记录到summary
            record = {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "original": title,
                "translated": output_file,
                "genre": resource['genre'],
                "author_style": resource['author'],
                "names": used_names,
                "tags": tags,
                "word_count": self.translator.count_words(content),
                "time": round(duration, 2),
                "cost": round(cost, 2),
                "prompt": prompt
            }
            self.config_mgr.add_record(record)

            # 更新状态：完成
            self.window.after(0, lambda: self.update_status(title, "完成", duration, cost, prompt))

            return {
                'success': True,
                'title': title,
                'prompt': prompt,
                'tags': tags
            }

        except Exception as e:
            self.log(f"翻译 {title} 失败: {str(e)}", "ERROR")
            return {
                'success': False,
                'title': title,
                'error': str(e)
            }

    def translate_all(self):
        """批量翻译 - 使用异步并发"""
        self.log("translate_all 线程开始执行")
        try:
            # 在新的事件循环中运行异步任务
            asyncio.run(self.translate_all_async())

        except Exception as e:
            self.log(f"translate_all 异常: {str(e)}", "ERROR")
            self.window.after(0, lambda: messagebox.showerror("错误", f"翻译失败: {str(e)}"))
            self.window.after(0, self.reset_ui)

    def update_status(self, title: str, status: str, elapsed: float, cost: float, prompt: str = ""):
        """更新状态"""
        def _update():
            self.translation_results[title] = {
                'status': status,
                'time': elapsed,
                'cost': cost,
                'prompt': prompt
            }
            self.refresh_status_display()

        self.window.after(0, _update)

    def refresh_status_display(self):
        """刷新状态显示"""
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)

        for title, info in self.translation_results.items():
            status = info['status']
            elapsed = info['time']
            cost = info['cost']

            if status == "完成":
                icon = "✅"
                text = f"{icon} {title}  {elapsed:.0f}秒  ${cost:.2f}\n"
            elif status == "运行中":
                icon = "🔄"
                text = f"{icon} {title}  {status}  {elapsed:.0f}秒\n"
            else:
                icon = "❌"
                text = f"{icon} {title}  {status}\n"

            self.status_text.insert(tk.END, text)

        self.status_text.config(state=tk.DISABLED)
        self.status_text.see(tk.END)

    def update_progress(self):
        """更新进度"""
        if self.is_translating:
            total_elapsed = time.time() - self.total_start_time
            total_count = len(self.files)

            # 更新已用时
            self.elapsed_time_label.config(text=f"{total_elapsed:.0f}秒")

            self.progress_label.config(
                text=f"总耗时: {total_elapsed:.0f}秒 | 完成: {self.completed_count}/{total_count}"
            )

            self.window.after(1000, self.update_progress)

    def translation_complete(self):
        """翻译完成"""
        self.log("=== 翻译任务全部完成 ===", "SUCCESS")
        try:
            self.is_translating = False
            total_elapsed = time.time() - self.total_start_time
            total_cost = sum(r['cost'] for r in self.translation_results.values())

            self.log(f"总耗时: {total_elapsed:.0f}秒")
            self.log(f"总成本: ${total_cost:.2f}")
            self.log(f"完成数量: {self.completed_count}/{len(self.files)}")

            # 自动保存到Excel
            self.log("正在保存到Excel...")
            self.save_to_excel()

            messagebox.showinfo(
                "完成",
                f"翻译完成！\n\n总耗时: {total_elapsed:.0f}秒\n总成本: ${total_cost:.2f}\n完成: {self.completed_count}/{len(self.files)}"
            )

            self.reset_ui()

        except Exception as e:
            self.log(f"翻译完成处理异常: {str(e)}", "ERROR")

    def reset_ui(self):
        """重置UI"""
        self.is_translating = False
        self.start_btn.config(state=tk.NORMAL, text="🚀 开始翻译")

    def call_api(self, prompt: str, content: str) -> tuple:
        """调用API - 同步版本（用于测试连接）"""
        try:
            from openai import OpenAI

            api_key = self.config_mgr.get_api_key()
            api_base_url = self.config_mgr.get_api_base_url()

            # 从配置读取model（界面输入的）
            config = self.config_mgr.load_config()
            model = config.get('model', 'gpt-5.1')
            temperature = config.get('temperature', 0.8)
            max_tokens = config.get('max_tokens', 100000)

            self.log(f"调用API - Model: {model}, URL: {api_base_url}")

            client = OpenAI(
                api_key=api_key,
                base_url=api_base_url
            )

            response = client.chat.completions.create(
                model=model,  # 使用界面输入的model
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            translated = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens

            self.log(f"API调用成功 - 输入tokens: {input_tokens}, 输出tokens: {output_tokens}")

            return (translated, input_tokens, output_tokens)

        except Exception as e:
            self.log(f"API调用异常: {str(e)}", "ERROR")
            raise Exception(f"API调用失败: {str(e)}")

    async def call_api_async(self, prompt: str, content: str) -> tuple:
        """调用API - 异步版本（用于并发翻译）"""
        try:
            from openai import AsyncOpenAI

            api_key = self.config_mgr.get_api_key()
            api_base_url = self.config_mgr.get_api_base_url()

            # 从配置读取model
            config = self.config_mgr.load_config()
            model = config.get('model', 'gpt-5.1')
            temperature = config.get('temperature', 0.8)
            max_tokens = config.get('max_tokens', 100000)

            self.log(f"异步调用API - Model: {model}")

            client = AsyncOpenAI(
                api_key=api_key,
                base_url=api_base_url
            )

            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            translated = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens

            self.log(f"异步API调用成功 - 输入tokens: {input_tokens}, 输出tokens: {output_tokens}")

            return (translated, input_tokens, output_tokens)

        except Exception as e:
            self.log(f"异步API调用异常: {str(e)}", "ERROR")
            raise Exception(f"API调用失败: {str(e)}")

    def save_to_excel(self):
        """自动保存到Excel"""
        try:
            summary = self.config_mgr.load_summary()
            if not summary['records']:
                return

            df = pd.DataFrame(summary['records'])

            # 确保data目录存在
            os.makedirs("data", exist_ok=True)

            excel_file = os.path.join("data", "translation_history.xlsx")
            df.to_excel(excel_file, index=False, engine='openpyxl')

            print(f"✅ 记录已保存到: {excel_file}")

        except Exception as e:
            print(f"❌ Excel保存失败: {str(e)}")

    def export_to_excel(self):
        """手动导出Excel"""
        try:
            summary = self.config_mgr.load_summary()
            if not summary['records']:
                messagebox.showinfo("提示", "暂无翻译记录")
                return

            filename = filedialog.asksaveasfilename(
                title="导出Excel",
                defaultextension=".xlsx",
                filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")],
                initialfile=f"translation_history_{datetime.now().strftime('%Y%m%d')}.xlsx"
            )

            if filename:
                df = pd.DataFrame(summary['records'])
                df.to_excel(filename, index=False, engine='openpyxl')
                messagebox.showinfo("成功", f"已导出到:\n{filename}")

        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")

    def show_prompts(self):
        """显示当前翻译任务的Prompts"""
        self.log("打开Prompts查看窗口...")
        try:
            if not self.translation_results:
                messagebox.showinfo("提示", "暂无翻译任务")
                return

            # 创建Prompts窗口
            prompts_window = tk.Toplevel(self.window)
            prompts_window.title("🔍 Translation Prompts")
            prompts_window.geometry("900x700")

            tk.Label(
                prompts_window,
                text="翻译任务Prompts",
                font=("Arial", 14, "bold")
            ).pack(pady=10)

            # Notebook
            notebook = ttk.Notebook(prompts_window)
            notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # 为每个任务创建标签页
            for title, info in self.translation_results.items():
                prompt = info.get('prompt', 'No prompt available')
                status = info.get('status', 'Unknown')

                # 创建标签页
                tab = tk.Frame(notebook)
                notebook.add(tab, text=f"{title[:30]}...")

                # 标题和状态
                header_frame = tk.Frame(tab)
                header_frame.pack(fill=tk.X, padx=10, pady=10)

                tk.Label(
                    header_frame,
                    text=f"📖 {title}",
                    font=("Arial", 11, "bold")
                ).pack(anchor=tk.W)

                tk.Label(
                    header_frame,
                    text=f"状态: {status}",
                    font=("Arial", 9),
                    fg="green" if status == "完成" else "orange"
                ).pack(anchor=tk.W)

                # Prompt内容
                prompt_text = scrolledtext.ScrolledText(
                    tab,
                    font=("Consolas", 9),
                    wrap=tk.WORD,
                    bg="#f8f9fa"
                )
                prompt_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                prompt_text.insert(1.0, prompt)
                prompt_text.config(state=tk.DISABLED)

            # 关闭按钮
            tk.Button(
                prompts_window,
                text="关闭",
                command=prompts_window.destroy,
                bg="#95a5a6",
                fg="white",
                relief=tk.FLAT,
                padx=20,
                pady=5
            ).pack(pady=10)

            self.log("Prompts窗口已打开", "SUCCESS")

        except Exception as e:
            self.log(f"打开Prompts窗口失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"打开Prompts失败: {str(e)}")

    def show_history(self):
        """显示历史记录"""
        summary = self.config_mgr.load_summary()

        if not summary['records']:
            messagebox.showinfo("提示", "暂无历史记录")
            return

        history_window = tk.Toplevel(self.window)
        history_window.title("📋 历史翻译记录")
        history_window.geometry("950x650")

        tk.Label(
            history_window,
            text="历史翻译记录",
            font=("Arial", 14, "bold")
        ).pack(pady=10)

        # Treeview
        tree_frame = tk.Frame(history_window)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        columns = ('日期', '原书名', '类型', '风格', 'Tags', '字数', '耗时(秒)', '成本($)', 'Prompt')
        tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='headings',
            yscrollcommand=scrollbar.set
        )

        for col in columns:
            tree.heading(col, text=col)
            if col == '原书名':
                tree.column(col, width=150)
            elif col == 'Tags':
                tree.column(col, width=250)
            elif col == 'Prompt':
                tree.column(col, width=150)
            elif col == '类型':
                tree.column(col, width=80)
            elif col == '风格':
                tree.column(col, width=130)
            else:
                tree.column(col, width=100)

        # 插入数据
        for record in summary['records']:
            prompt = record.get('prompt', '')
            prompt_preview = (prompt[:30] + '...') if len(prompt) > 30 else prompt

            tags = record.get('tags', [])
            tags_str = ' '.join([f"#{tag}" for tag in tags]) if tags else '-'

            tree.insert('', tk.END, values=(
                record.get('date', '-'),
                record.get('original', '-'),
                record.get('genre', '-'),
                record.get('author_style', '-'),
                tags_str,
                record.get('word_count', 0),
                record.get('time', 0),
                f"${record.get('cost', 0):.2f}",
                prompt_preview
            ))

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=tree.yview)

        # 统计
        total_count = len(summary['records'])
        total_cost = sum(r.get('cost', 0) for r in summary['records'])
        total_time = sum(r.get('time', 0) for r in summary['records'])

        stats_label = tk.Label(
            history_window,
            text=f"总计: {total_count} 本 | 总成本: ${total_cost:.2f} | 总耗时: {total_time:.0f}秒",
            font=("Arial", 10, "bold")
        )
        stats_label.pack(pady=10)

        tk.Button(
            history_window,
            text="关闭",
            command=history_window.destroy,
            bg="#95a5a6",
            fg="white",
            relief=tk.FLAT,
            padx=20,
            pady=5
        ).pack(pady=10)

    def run(self):
        """运行应用"""
        self.window.mainloop()


if __name__ == "__main__":
    app = TranslatorApp()
    app.run()
