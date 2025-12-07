"""
远程控制服务端 - GUI版本（被控端）
在控制端请求时弹出授权确认窗口
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import socket
import sys
import os
from datetime import datetime

# 导入原有逻辑和配置
try:
    from server import RemoteControlServer
    from config import SERVER_HOST, SERVER_PORT, Colors, SAFE_DIRECTORY
    from utils import get_local_ip
    from gui_theme import COLORS, FONTS, PADDING
except ImportError as e:
    print(f"缺少依赖文件: {e}")
    sys.exit(1)

class GeekServerUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Remote Control - Host [Passive]")
        self.geometry("600x450")
        self.configure(bg=COLORS['bg_dark'])
        self.resizable(False, False)

        self.server_thread = None
        self.server_instance = None
        self.is_running = False

        # === 界面布局 ===
        self._init_ui()

    def _init_ui(self):
        # 1. 顶部状态栏
        self.header_frame = tk.Frame(self, bg=COLORS['bg_lighter'], pady=10)
        self.header_frame.pack(fill='x', padx=PADDING, pady=PADDING)

        self.lbl_title = tk.Label(self.header_frame, text="HOST STATUS: STANDBY",
                                font=FONTS['h1'], bg=COLORS['bg_lighter'], fg=COLORS['fg_secondary'])
        self.lbl_title.pack()

        # 2. 信息面板 (IP/Port)
        self.info_frame = tk.Frame(self, bg=COLORS['bg_dark'])
        self.info_frame.pack(fill='x', padx=PADDING)

        # 本机信息表格
        self._create_info_row(self.info_frame, "Local IP:", get_local_ip(), 0)
        self._create_info_row(self.info_frame, "Listen Port:", str(SERVER_PORT), 1)
        self._create_info_row(self.info_frame, "Safe Dir:", SAFE_DIRECTORY, 2)

        # 3. 连接状态面板
        self.status_frame = tk.Frame(self, bg=COLORS['bg_lighter'], bd=1, relief='solid')
        self.status_frame.pack(fill='x', padx=PADDING, pady=20)

        tk.Label(self.status_frame, text="[ Connection Status ]", font=FONTS['h2'],
                bg=COLORS['bg_lighter'], fg=COLORS['fg_white']).pack(anchor='w', padx=5, pady=5)

        self.lbl_conn_status = tk.Label(self.status_frame, text="Waiting for connection...",
                                      font=FONTS['body'], bg=COLORS['bg_lighter'], fg=COLORS['fg_white'])
        self.lbl_conn_status.pack(pady=10)

        self.lbl_remote_info = tk.Label(self.status_frame, text="",
                                      font=FONTS['mono'], bg=COLORS['bg_lighter'], fg=COLORS['fg_primary'])
        self.lbl_remote_info.pack(pady=5)

        # 4. 日志区域
        self.log_area = scrolledtext.ScrolledText(self, height=8, bg='black', fg=COLORS['fg_white'],
                                                font=FONTS['mono'], insertbackground='white')
        self.log_area.pack(fill='both', expand=True, padx=PADDING, pady=(0, PADDING))
        self.log("System initialized. Ready to start.")

        # 5. 底部控制按钮
        self.btn_frame = tk.Frame(self, bg=COLORS['bg_dark'])
        self.btn_frame.pack(fill='x', padx=PADDING, pady=(0, PADDING))

        self.btn_start = tk.Button(self.btn_frame, text="START SERVICE", command=self.start_server,
                                 bg=COLORS['btn_bg'], fg=COLORS['fg_primary'], font=FONTS['h2'], relief='flat')
        self.btn_start.pack(side='left', fill='x', expand=True, padx=5)

        self.btn_stop = tk.Button(self.btn_frame, text="STOP", command=self.stop_server,
                                bg=COLORS['btn_bg'], fg=COLORS['fg_danger'], font=FONTS['h2'], relief='flat', state='disabled')
        self.btn_stop.pack(side='right', fill='x', expand=True, padx=5)

    def _create_info_row(self, parent, label, value, row):
        tk.Label(parent, text=label, font=FONTS['body'], bg=COLORS['bg_dark'], fg=COLORS['fg_white']).grid(row=row, column=0, sticky='e', padx=5)
        tk.Label(parent, text=value, font=FONTS['mono'], bg=COLORS['bg_dark'], fg=COLORS['fg_secondary']).grid(row=row, column=1, sticky='w', padx=5)

    def log(self, message):
        """线程安全的日志输出"""
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        self.log_area.insert(tk.END, f"{timestamp} {message}\n")
        self.log_area.see(tk.END)

    def start_server(self):
        self.server_instance = GuiRemoteServer(self)
        self.server_thread = threading.Thread(target=self.server_instance.start, daemon=True)
        self.server_thread.start()

        self.is_running = True
        self.btn_start.config(state='disabled', bg=COLORS['bg_dark'])
        self.btn_stop.config(state='normal', bg=COLORS['btn_bg'])
        self.lbl_title.config(text="HOST STATUS: RUNNING", fg=COLORS['fg_primary'])
        self.log("Server started listening.")

    def stop_server(self):
        if self.server_instance:
            self.server_instance.stop()
        self.is_running = False
        self.btn_start.config(state='normal', bg=COLORS['btn_bg'])
        self.btn_stop.config(state='disabled', bg=COLORS['bg_dark'])
        self.lbl_title.config(text="HOST STATUS: STOPPED", fg=COLORS['fg_danger'])
        self.update_connection_status(False)
        self.log("Server stopped.")

    def request_permission(self, client_addr):
        """核心需求：弹出窗口请求允许"""
        response = messagebox.askyesno(
            "Security Alert - Connection Request",
            f"Incoming remote control request from:\n\nIP: {client_addr[0]}\nPort: {client_addr[1]}\n\nDo you allow this connection?",
            parent=self
        )
        if response:
            self.log(f"Connection ACCEPTED from {client_addr}")
            self.update_connection_status(True, client_addr)
        else:
            self.log(f"Connection DENIED from {client_addr}")
        return response

    def update_connection_status(self, connected, client_addr=None):
        if connected and client_addr:
            self.status_frame.config(bg=COLORS['fg_danger'])
            self.lbl_conn_status.config(text="⚠️ SYSTEM UNDER REMOTE CONTROL", bg=COLORS['fg_danger'], fg='white')

            info_text = f"Controller IP: {client_addr[0]} | Port: {client_addr[1]}\nLocal Service Port: {SERVER_PORT}"
            self.lbl_remote_info.config(text=info_text, bg=COLORS['fg_danger'], fg='white')
        else:
            self.status_frame.config(bg=COLORS['bg_lighter'])
            self.lbl_conn_status.config(text="Waiting for connection...", bg=COLORS['bg_lighter'], fg=COLORS['fg_white'])
            self.lbl_remote_info.config(text="", bg=COLORS['bg_lighter'])

# 继承原有 Server 类以注入 GUI 逻辑
class GuiRemoteServer(RemoteControlServer):
    def __init__(self, ui_app):
        super().__init__()
        self.ui = ui_app

    def handle_client(self, client_socket, client_address):
        """重写处理客户端连接的方法，加入GUI交互"""
        self.client_socket = client_socket
        self.client_address = client_address

        # 1. 在主线程中请求权限
        allow = self.ui.request_permission(client_address)

        if not allow:
            client_socket.close()
            return

        # 2. 调用父类逻辑
        try:
            super().handle_client(client_socket, client_address)
        except Exception as e:
            self.ui.log(f"Error handling client: {e}")
        finally:
            # 连接结束后更新 UI
            self.ui.update_connection_status(False)

if __name__ == "__main__":
    app = GeekServerUI()
    app.mainloop()
