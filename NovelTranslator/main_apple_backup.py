"""
小说翻译工具 - 主程序（Apple风格）

现代化的苹果风格GUI界面，支持批量翻译中文小说为英文
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


# ========== Apple风格配色方案 ==========
COLORS = {
    'bg': '#F5F5F7',            # 背景浅灰
    'card_bg': '#FFFFFF',       # 卡片白色
    'primary': '#007AFF',       # 苹果蓝
    'success': '#34C759',       # 成功绿
    'warning': '#FF9500',       # 警告橙
    'danger': '#FF3B30',        # 危险红
    'text_primary': '#1D1D1F',  # 主要文字
    'text_secondary': '#86868B', # 次要文字
    'border': '#E5E5EA',        # 边框
    'hover': '#F0F0F5'          # 悬停背景
}

FONTS = {
    'title': ('SF Pro Display', 20, 'bold'),
    'heading': ('SF Pro Display', 14, 'bold'),
    'body': ('SF Pro Text', 11),
    'small': ('SF Pro Text', 10),
    'mono': ('SF Mono', 10)
}


class RoundedButton(tk.Canvas):
    """圆角按钮"""
    def __init__(self, parent, text, command, bg_color, fg_color='white', width=120, height=40):
        super().__init__(parent, width=width, height=height, bg=COLORS['card_bg'],
                        highlightthickness=0)
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.command = command
        self.text = text

        # 绘制圆角矩形
        self.rounded_rect = self.create_rounded_rectangle(
            2, 2, width-2, height-2, radius=10, fill=bg_color, outline=""
        )

        # 文字
        self.text_obj = self.create_text(
            width/2, height/2, text=text, fill=fg_color,
            font=FONTS['body']
        )

        # 绑定事件
        self.bind('<Button-1>', lambda e: self.command())
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)

    def create_rounded_rectangle(self, x1, y1, x2, y2, radius=10, **kwargs):
        points = [
            x1+radius, y1,
            x1+radius, y1,
            x2-radius, y1,
            x2-radius, y1,
            x2, y1,
            x2, y1+radius,
            x2, y1+radius,
            x2, y2-radius,
            x2, y2-radius,
            x2, y2,
            x2-radius, y2,
            x2-radius, y2,
            x1+radius, y2,
            x1+radius, y2,
            x1, y2,
            x1, y2-radius,
            x1, y2-radius,
            x1, y1+radius,
            x1, y1+radius,
            x1, y1
        ]
        return self.create_polygon(points, **kwargs, smooth=True)

    def on_enter(self, e):
        # 悬停效果：稍微变暗
        self.itemconfig(self.rounded_rect, fill=self._darken_color(self.bg_color))

    def on_leave(self, e):
        self.itemconfig(self.rounded_rect, fill=self.bg_color)

    def _darken_color(self, color):
        """使颜色稍微变暗"""
        if color == COLORS['primary']:
            return '#0051D5'
        elif color == COLORS['success']:
            return '#28A745'
        elif color == COLORS['danger']:
            return '#DC3545'
        return color


class TranslatorApp:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Novel Translator")
        self.window.geometry("800x900")
        self.window.resizable(False, False)
        self.window.configure(bg=COLORS['bg'])

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

        # 创建UI
        self.create_widgets()

        # 加载配置
        self.load_config()

    def create_widgets(self):
        """创建Apple风格UI组件"""

        # ========== 主容器 ==========
        main_container = tk.Frame(self.window, bg=COLORS['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # ========== 标题区 ==========
        title_frame = tk.Frame(main_container, bg=COLORS['bg'])
        title_frame.pack(fill=tk.X, pady=(0, 20))

        title_label = tk.Label(
            title_frame,
            text="📖 Novel Translator",
            font=FONTS['title'],
            bg=COLORS['bg'],
            fg=COLORS['text_primary']
        )
        title_label.pack(side=tk.LEFT)

        subtitle_label = tk.Label(
            title_frame,
            text="AI-Powered Translation Tool",
            font=FONTS['small'],
            bg=COLORS['bg'],
            fg=COLORS['text_secondary']
        )
        subtitle_label.pack(side=tk.LEFT, padx=10)

        # ========== API配置卡片 ==========
        api_card = self.create_card(main_container, "API Configuration")
        api_card.pack(fill=tk.X, pady=(0, 15))

        # API Key
        self.create_input_row(api_card, "API Key", show="•", row=0)

        # API URL
        self.create_input_row(api_card, "API URL", row=1)

        # 测试按钮和状态
        test_frame = tk.Frame(api_card, bg=COLORS['card_bg'])
        test_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0), sticky=tk.W)

        self.test_btn = RoundedButton(
            test_frame, "Test Connection",
            self.test_api,
            COLORS['primary'],
            width=140, height=36
        )
        self.test_btn.pack(side=tk.LEFT)

        self.api_status_label = tk.Label(
            test_frame,
            text="● Not tested",
            font=FONTS['small'],
            bg=COLORS['card_bg'],
            fg=COLORS['text_secondary']
        )
        self.api_status_label.pack(side=tk.LEFT, padx=15)

        # 线程数
        thread_frame = tk.Frame(api_card, bg=COLORS['card_bg'])
        thread_frame.grid(row=3, column=0, columnspan=2, pady=(15, 0), sticky=tk.W)

        tk.Label(
            thread_frame,
            text="Threads:",
            font=FONTS['body'],
            bg=COLORS['card_bg'],
            fg=COLORS['text_primary']
        ).pack(side=tk.LEFT)

        self.workers_spinbox = tk.Spinbox(
            thread_frame,
            from_=1, to=20,
            width=8,
            font=FONTS['body'],
            relief=tk.FLAT,
            bd=1,
            highlightthickness=1,
            highlightbackground=COLORS['border']
        )
        self.workers_spinbox.pack(side=tk.LEFT, padx=10)

        # ========== 文件管理卡片 ==========
        file_card = self.create_card(main_container, "Files")
        file_card.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # 按钮组
        btn_frame = tk.Frame(file_card, bg=COLORS['card_bg'])
        btn_frame.grid(row=0, column=0, pady=(0, 15), sticky=tk.W)

        add_file_btn = RoundedButton(
            btn_frame, "+ Add Files",
            self.add_files,
            COLORS['primary'],
            width=110, height=36
        )
        add_file_btn.pack(side=tk.LEFT, padx=(0, 10))

        add_folder_btn = RoundedButton(
            btn_frame, "+ Add Folder",
            self.add_folder,
            COLORS['primary'],
            width=110, height=36
        )
        add_folder_btn.pack(side=tk.LEFT, padx=(0, 10))

        clear_btn = RoundedButton(
            btn_frame, "Clear",
            self.clear_files,
            COLORS['danger'],
            width=80, height=36
        )
        clear_btn.pack(side=tk.LEFT)

        # 文件列表
        list_container = tk.Frame(file_card, bg=COLORS['card_bg'])
        list_container.grid(row=1, column=0, sticky=tk.NSEW)
        file_card.grid_rowconfigure(1, weight=1)
        file_card.grid_columnconfigure(0, weight=1)

        scrollbar = tk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.file_listbox = tk.Listbox(
            list_container,
            yscrollcommand=scrollbar.set,
            height=8,
            font=FONTS['mono'],
            relief=tk.FLAT,
            bd=0,
            bg=COLORS['bg'],
            fg=COLORS['text_primary'],
            selectbackground=COLORS['primary'],
            selectforeground='white',
            highlightthickness=0
        )
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)

        # 统计信息
        self.stats_label = tk.Label(
            file_card,
            text="0 files | Est. $0.00",
            font=FONTS['small'],
            bg=COLORS['card_bg'],
            fg=COLORS['text_secondary']
        )
        self.stats_label.grid(row=2, column=0, pady=(10, 0))

        # ========== 开始按钮 ==========
        self.start_btn = RoundedButton(
            main_container,
            "🚀 Start Translation",
            self.start_translation,
            COLORS['success'],
            width=760, height=50
        )
        self.start_btn.pack(pady=(0, 15))

        # ========== 状态卡片 ==========
        status_card = self.create_card(main_container, "Translation Status")
        status_card.pack(fill=tk.BOTH, expand=True)

        # 状态文本区
        self.status_text = scrolledtext.ScrolledText(
            status_card,
            height=10,
            font=FONTS['mono'],
            relief=tk.FLAT,
            bd=0,
            bg=COLORS['bg'],
            fg=COLORS['text_primary'],
            state=tk.DISABLED,
            wrap=tk.WORD
        )
        self.status_text.grid(row=0, column=0, sticky=tk.NSEW)
        status_card.grid_rowconfigure(0, weight=1)
        status_card.grid_columnconfigure(0, weight=1)

        # 进度标签
        self.progress_label = tk.Label(
            status_card,
            text="Ready to translate",
            font=FONTS['body'],
            bg=COLORS['card_bg'],
            fg=COLORS['text_secondary']
        )
        self.progress_label.grid(row=1, column=0, pady=(10, 0))

    def create_card(self, parent, title):
        """创建卡片容器"""
        card_frame = tk.Frame(parent, bg=COLORS['card_bg'], relief=tk.FLAT)
        card_frame.configure(highlightbackground=COLORS['border'],
                           highlightthickness=1)

        # 内容区（带padding）
        content = tk.Frame(card_frame, bg=COLORS['card_bg'])
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 标题
        if title:
            title_label = tk.Label(
                content,
                text=title,
                font=FONTS['heading'],
                bg=COLORS['card_bg'],
                fg=COLORS['text_primary']
            )
            title_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 15))
            start_row = 1
        else:
            start_row = 0

        # 配置网格权重
        content.grid_columnconfigure(1, weight=1)

        # 返回内容区供添加控件
        content.start_row = start_row
        return content

    def create_input_row(self, parent, label_text, show=None, row=0):
        """创建输入行"""
        actual_row = parent.start_row + row if hasattr(parent, 'start_row') else row

        # 标签
        label = tk.Label(
            parent,
            text=label_text + ":",
            font=FONTS['body'],
            bg=COLORS['card_bg'],
            fg=COLORS['text_primary'],
            width=10,
            anchor=tk.W
        )
        label.grid(row=actual_row, column=0, sticky=tk.W, pady=8)

        # 输入框
        entry = tk.Entry(
            parent,
            font=FONTS['body'],
            relief=tk.FLAT,
            bd=1,
            highlightthickness=1,
            highlightbackground=COLORS['border'],
            highlightcolor=COLORS['primary']
        )
        if show:
            entry.config(show=show)
        entry.grid(row=actual_row, column=1, sticky=tk.EW, pady=8, padx=(10, 0))

        # 保存引用
        if label_text == "API Key":
            self.api_key_entry = entry
        elif label_text == "API URL":
            self.api_url_entry = entry

        return entry

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

    def test_api(self):
        """测试API连接"""
        api_key = self.api_key_entry.get().strip()
        if not api_key:
            messagebox.showwarning("Warning", "Please enter API Key first")
            return

        # 保存API Key
        self.config_mgr.set_api_key(api_key)
        api_url = self.api_url_entry.get().strip()
        if api_url:
            self.config_mgr.set_api_base_url(api_url)

        # 更新状态
        self.api_status_label.config(text="● Testing...", fg=COLORS['warning'])

        # 在新线程中测试
        def test_thread():
            result = self.translator.test_api_connection(self.call_api)
            self.window.after(0, lambda: self.update_api_status(result))

        threading.Thread(target=test_thread, daemon=True).start()

    def update_api_status(self, result):
        """更新API状态"""
        if result['success']:
            self.api_status_label.config(
                text="● " + result['message'],
                fg=COLORS['success']
            )
        else:
            self.api_status_label.config(
                text="● " + result['message'],
                fg=COLORS['danger']
            )

    def add_files(self):
        """添加文件"""
        files = filedialog.askopenfilenames(
            title="Select Novel Files",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        for file in files:
            if file not in self.files:
                self.files.append(file)
                basename = os.path.basename(file)
                size = os.path.getsize(file)
                word_count = size // 3
                display = f"{basename} ({word_count/10000:.1f}w words)"
                self.file_listbox.insert(tk.END, display)

        self.update_stats()

    def add_folder(self):
        """添加文件夹"""
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            for filename in os.listdir(folder):
                if filename.endswith('.txt'):
                    file_path = os.path.join(folder, filename)
                    if file_path not in self.files:
                        self.files.append(file_path)
                        size = os.path.getsize(file_path)
                        word_count = size // 3
                        display = f"{filename} ({word_count/10000:.1f}w words)"
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
        self.stats_label.config(
            text=f"{count} files | Est. ${estimated_cost:.2f}"
        )

    def start_translation(self):
        """开始翻译"""
        if self.is_translating:
            messagebox.showwarning("Warning", "Translation in progress, please wait")
            return

        if not self.files:
            messagebox.showwarning("Warning", "Please add files to translate first")
            return

        api_key = self.api_key_entry.get().strip()
        if not api_key:
            messagebox.showwarning("Warning", "Please enter API Key first")
            return

        api_url = self.api_url_entry.get().strip()
        if not api_url:
            messagebox.showwarning("Warning", "Please enter API URL first")
            return

        # 保存配置
        self.config_mgr.set_api_key(api_key)
        self.config_mgr.set_api_base_url(api_url)
        workers = int(self.workers_spinbox.get())
        self.config_mgr.set_max_workers(workers)

        # 确认
        if not messagebox.askyesno(
            "Confirm",
            f"Ready to translate {len(self.files)} novels\n"
            f"Using {workers} threads\n\n"
            f"Start now?"
        ):
            return

        # 开始翻译
        self.is_translating = True
        self.start_btn.itemconfig(
            self.start_btn.text_obj,
            text="⏳ Translating..."
        )
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
        """批量翻译"""
        try:
            resources = self.resource_mgr.allocate_resources(self.files)
            workers = self.config_mgr.get_max_workers()
            self.executor = ThreadPoolExecutor(max_workers=workers)

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

            for future in as_completed(futures):
                result = future.result()
                if result['success']:
                    self.completed_count += 1

            self.window.after(0, self.translation_complete)

        except Exception as e:
            self.window.after(0, lambda: messagebox.showerror(
                "Error", f"Translation failed: {str(e)}"
            ))
            self.window.after(0, self.reset_ui)

    def update_status(self, title: str, status: str, elapsed: float, cost: float):
        """更新状态"""
        def _update():
            self.translation_results[title] = {
                'status': status,
                'time': elapsed,
                'cost': cost
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
                text = f"{icon} {title}  {elapsed:.0f}s  ${cost:.2f}\n"
            elif status == "运行中":
                icon = "🔄"
                text = f"{icon} {title}  {status}  {elapsed:.0f}s\n"
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

            self.progress_label.config(
                text=f"Time: {total_elapsed:.0f}s | Completed: {self.completed_count}/{total_count}"
            )

            self.window.after(1000, self.update_progress)

    def translation_complete(self):
        """翻译完成"""
        self.is_translating = False
        total_elapsed = time.time() - self.total_start_time
        total_cost = sum(r['cost'] for r in self.translation_results.values())

        messagebox.showinfo(
            "Complete",
            f"Translation completed!\n\n"
            f"Time: {total_elapsed:.0f}s\n"
            f"Cost: ${total_cost:.2f}\n"
            f"Files: {self.completed_count}/{len(self.files)}"
        )

        self.reset_ui()

    def reset_ui(self):
        """重置UI"""
        self.is_translating = False
        self.start_btn.itemconfig(
            self.start_btn.text_obj,
            text="🚀 Start Translation"
        )

    def call_api(self, prompt: str, content: str) -> tuple:
        """调用API"""
        try:
            from openai import OpenAI

            api_key = self.config_mgr.get_api_key()
            api_base_url = self.config_mgr.get_api_base_url()
            model_config = self.config_mgr.get_model_config()

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
            raise Exception(f"API call failed: {str(e)}")

    def run(self):
        """运行应用"""
        self.window.mainloop()


if __name__ == "__main__":
    app = TranslatorApp()
    app.run()
