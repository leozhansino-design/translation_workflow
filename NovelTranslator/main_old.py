"""
小说翻译工具 - 主程序

极简GUI界面，支持批量翻译中文小说为英文
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

from config import ConfigManager
from resource_mgr import ResourceManager
from translator import Translator


class TranslatorApp:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("小说翻译工具")
        self.window.geometry("700x800")
        self.window.resizable(False, False)

        # 管理器
        self.config_mgr = ConfigManager()
        self.resource_mgr = ResourceManager()
        self.translator = Translator(self.config_mgr, self.resource_mgr)

        # 数据
        self.files = []  # 待翻译文件列表
        self.executor = None
        self.is_translating = False
        self.translation_results = {}  # {title: {status, time, cost}}
        self.total_start_time = 0
        self.completed_count = 0

        # 创建UI
        self.create_widgets()

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
            text="小说翻译工具",
            font=("Arial", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=10)

        settings_btn = tk.Button(
            title_frame,
            text="设置",
            command=self.open_settings,
            bg="#3498db",
            fg="white",
            font=("Arial", 10),
            relief=tk.FLAT,
            padx=15,
            pady=5
        )
        settings_btn.pack(side=tk.RIGHT, padx=20, pady=10)

        # ========== API配置区 ==========
        api_frame = tk.LabelFrame(self.window, text="API 配置", padx=10, pady=10)
        api_frame.pack(fill=tk.X, padx=20, pady=10)

        # API Key
        tk.Label(api_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W)
        self.api_key_entry = tk.Entry(api_frame, width=40, show="•")
        self.api_key_entry.grid(row=0, column=1, padx=5)

        self.test_btn = tk.Button(
            api_frame,
            text="测试",
            command=self.test_api,
            bg="#27ae60",
            fg="white",
            relief=tk.FLAT,
            padx=10
        )
        self.test_btn.grid(row=0, column=2, padx=5)

        self.api_status_label = tk.Label(api_frame, text="未测试", fg="gray")
        self.api_status_label.grid(row=0, column=3, padx=5)

        # API URL
        tk.Label(api_frame, text="API URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.api_url_entry = tk.Entry(api_frame, width=40)
        self.api_url_entry.grid(row=1, column=1, padx=5, columnspan=3, sticky=tk.W+tk.E)

        # 线程数
        tk.Label(api_frame, text="线程数:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.workers_spinbox = tk.Spinbox(api_frame, from_=1, to=20, width=10)
        self.workers_spinbox.grid(row=2, column=1, sticky=tk.W, padx=5)

        # ========== 文件管理区 ==========
        file_frame = tk.LabelFrame(self.window, text="文件管理", padx=10, pady=10)
        file_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # 按钮区
        btn_frame = tk.Frame(file_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Button(
            btn_frame,
            text="添加文件",
            command=self.add_files,
            bg="#3498db",
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=5
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="添加文件夹",
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

        # 总进度
        self.progress_label = tk.Label(
            status_frame,
            text="总耗时: 0秒 | 完成: 0/0",
            font=("Arial", 10, "bold"),
            fg="#2c3e50"
        )
        self.progress_label.pack(pady=5)

    def load_config(self):
        """加载配置"""
        api_key = self.config_mgr.get_api_key()
        if api_key:
            self.api_key_entry.insert(0, api_key)

        api_url = self.config_mgr.get_api_base_url()
        if api_url:
            self.api_url_entry.insert(0, api_url)

        workers = self.config_mgr.get_max_workers()
        self.workers_spinbox.delete(0, tk.END)
        self.workers_spinbox.insert(0, str(workers))

    def open_settings(self):
        """打开设置窗口"""
        messagebox.showinfo("设置", "设置功能待实现")

    def test_api(self):
        """测试API连接"""
        api_key = self.api_key_entry.get().strip()
        if not api_key:
            messagebox.showwarning("警告", "请先输入 API Key")
            return

        # 保存API Key
        self.config_mgr.set_api_key(api_key)

        # 更新状态
        self.api_status_label.config(text="测试中...", fg="orange")
        self.test_btn.config(state=tk.DISABLED)

        # 在新线程中测试
        def test_thread():
            result = self.translator.test_api_connection(self.call_api)
            self.window.after(0, lambda: self.update_api_status(result))

        threading.Thread(target=test_thread, daemon=True).start()

    def update_api_status(self, result):
        """更新API状态"""
        if result['success']:
            self.api_status_label.config(text=result['message'], fg="green")
        else:
            self.api_status_label.config(text=result['message'], fg="red")
        self.test_btn.config(state=tk.NORMAL)

    def add_files(self):
        """添加文件"""
        files = filedialog.askopenfilenames(
            title="选择小说文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        for file in files:
            if file not in self.files:
                self.files.append(file)
                # 显示文件名和大小
                basename = os.path.basename(file)
                size = os.path.getsize(file)
                word_count = size // 3  # 粗略估计字数
                display = f"{basename} ({word_count/10000:.1f}w字)"
                self.file_listbox.insert(tk.END, display)

        self.update_stats()

    def add_folder(self):
        """添加文件夹"""
        folder = filedialog.askdirectory(title="选择文件夹")
        if folder:
            for filename in os.listdir(folder):
                if filename.endswith('.txt'):
                    file_path = os.path.join(folder, filename)
                    if file_path not in self.files:
                        self.files.append(file_path)
                        # 显示文件名和大小
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
        # 粗略估计成本：每本2万字，约$0.20
        estimated_cost = count * 0.20
        self.stats_label.config(text=f"共 {count} 本 | 预计 ${estimated_cost:.2f}")

    def start_translation(self):
        """开始翻译"""
        if self.is_translating:
            messagebox.showwarning("警告", "正在翻译中，请稍候")
            return

        if not self.files:
            messagebox.showwarning("警告", "请先添加要翻译的文件")
            return

        api_key = self.api_key_entry.get().strip()
        if not api_key:
            messagebox.showwarning("警告", "请先输入 API Key")
            return

        api_url = self.api_url_entry.get().strip()
        if not api_url:
            messagebox.showwarning("警告", "请先输入 API URL")
            return

        # 保存配置
        self.config_mgr.set_api_key(api_key)
        self.config_mgr.set_api_base_url(api_url)
        workers = int(self.workers_spinbox.get())
        self.config_mgr.set_max_workers(workers)

        # 确认
        if not messagebox.askyesno("确认", f"准备翻译 {len(self.files)} 本小说\n使用 {workers} 个线程\n\n是否开始？"):
            return

        # 开始翻译
        self.is_translating = True
        self.start_btn.config(state=tk.DISABLED, text="翻译中...")
        self.completed_count = 0
        self.total_start_time = time.time()
        self.translation_results = {}

        # 清空状态显示
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state=tk.DISABLED)

        # 在新线程中执行翻译
        threading.Thread(target=self.translate_all, daemon=True).start()

        # 启动进度更新
        self.update_progress()

    def translate_all(self):
        """批量翻译（在后台线程中执行）"""
        try:
            # 1. 分配资源
            resources = self.resource_mgr.allocate_resources(self.files)

            # 2. 创建线程池
            workers = self.config_mgr.get_max_workers()
            self.executor = ThreadPoolExecutor(max_workers=workers)

            # 3. 提交任务
            futures = []
            for file, resource in zip(self.files, resources):
                future = self.executor.submit(
                    self.translator.translate_one,
                    file,
                    resource,
                    self.update_status,
                    self.call_api
                )
                futures.append(future)

            # 4. 等待所有任务完成
            for future in as_completed(futures):
                result = future.result()
                if result['success']:
                    self.completed_count += 1

            # 5. 完成
            self.window.after(0, self.translation_complete)

        except Exception as e:
            self.window.after(0, lambda: messagebox.showerror("错误", f"翻译失败: {str(e)}"))
            self.window.after(0, self.reset_ui)

    def update_status(self, title: str, status: str, elapsed: float, cost: float):
        """更新单个文件的状态（线程安全）"""
        def _update():
            # 记录结果
            self.translation_results[title] = {
                'status': status,
                'time': elapsed,
                'cost': cost
            }

            # 更新显示
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
        """更新总进度（定时调用）"""
        if self.is_translating:
            total_elapsed = time.time() - self.total_start_time
            total_count = len(self.files)

            self.progress_label.config(
                text=f"总耗时: {total_elapsed:.0f}秒 | 完成: {self.completed_count}/{total_count}"
            )

            # 每秒更新一次
            self.window.after(1000, self.update_progress)

    def translation_complete(self):
        """翻译完成"""
        self.is_translating = False
        total_elapsed = time.time() - self.total_start_time
        total_cost = sum(r['cost'] for r in self.translation_results.values())

        messagebox.showinfo(
            "完成",
            f"翻译完成！\n\n总耗时: {total_elapsed:.0f}秒\n总成本: ${total_cost:.2f}\n完成: {self.completed_count}/{len(self.files)}"
        )

        self.reset_ui()

    def reset_ui(self):
        """重置UI"""
        self.is_translating = False
        self.start_btn.config(state=tk.NORMAL, text="🚀 开始翻译")

    def call_api(self, prompt: str, content: str) -> tuple:
        """
        调用OpenAI API

        Returns:
            (translated_text, input_tokens, output_tokens)
        """
        try:
            from openai import OpenAI

            api_key = self.config_mgr.get_api_key()
            api_base_url = self.config_mgr.get_api_base_url()
            model_config = self.config_mgr.get_model_config()

            # 创建OpenAI客户端，支持自定义base_url
            client = OpenAI(
                api_key=api_key,
                base_url=api_base_url
            )

            response = client.chat.completions.create(
                model=model_config['model'],
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content}
                ],
                temperature=model_config['temperature'],
                max_tokens=model_config['max_tokens']
            )

            translated = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens

            return (translated, input_tokens, output_tokens)

        except Exception as e:
            raise Exception(f"API调用失败: {str(e)}")

    def run(self):
        """运行应用"""
        self.window.mainloop()


if __name__ == "__main__":
    app = TranslatorApp()
    app.run()
