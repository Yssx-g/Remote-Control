"""
远程控制防护软件 - 独立代理版
作为中间代理运行，拦截所有远程控制请求

使用方法：
1. 先运行原始服务器 (server.py 或 server_gui.py) 在端口 9999
2. 运行此防护软件，它会监听端口 9998
3. 客户端连接到端口 9998（而不是 9999）
4. 所有请求都会经过防护软件的审核

架构：
  控制端(Client:9998) <---> 防护软件(Proxy) <---> 被控端(Server:9999)
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import queue
import socket
import struct
import json
import time
from datetime import datetime

# 配置
LISTEN_PORT = 9998          # 防护软件监听端口（客户端连接这个）
SERVER_PORT = 9999          # 原始服务器端口（防护软件转发到这里）
SERVER_HOST = '127.0.0.1'   # 原始服务器地址


class MessageType:
    """消息类型（从protocol.py复制，保持独立）"""
    AUTH = 'AUTH'
    AUTH_RESPONSE = 'AUTH_RESPONSE'
    SCREENSHOT = 'SCREENSHOT'
    SCREENSHOT_DATA = 'SCREENSHOT_DATA'
    CAMERA = 'CAMERA'
    CAMERA_DATA = 'CAMERA_DATA'
    VIDEO_START = 'VIDEO_START'
    VIDEO_STOP = 'VIDEO_STOP'
    VIDEO_FRAME = 'VIDEO_FRAME'
    RECORD_START = 'RECORD_START'
    RECORD_STOP = 'RECORD_STOP'
    RECORD_STATUS = 'RECORD_STATUS'
    FILE_DOWNLOAD = 'FILE_DOWNLOAD'
    FILE_DATA = 'FILE_DATA'
    FILE_UPLOAD = 'FILE_UPLOAD'
    FILE_UPLOAD_RESPONSE = 'FILE_UPLOAD_RESPONSE'
    FILE_EXECUTE = 'FILE_EXECUTE'
    FILE_EXECUTE_RESPONSE = 'FILE_EXECUTE_RESPONSE'
    REGISTRY_QUERY = 'REGISTRY_QUERY'
    REGISTRY_SET = 'REGISTRY_SET'
    REGISTRY_DELETE = 'REGISTRY_DELETE'
    REGISTRY_RESPONSE = 'REGISTRY_RESPONSE'
    SYSTEM_INFO = 'SYSTEM_INFO'
    SYSTEM_INFO_RESPONSE = 'SYSTEM_INFO_RESPONSE'
    MIC_RECORD = 'MIC_RECORD'
    MIC_RECORD_RESPONSE = 'MIC_RECORD_RESPONSE'
    SCREEN_START = 'SCREEN_START'
    SCREEN_STOP = 'SCREEN_STOP'
    SCREEN_FRAME = 'SCREEN_FRAME'
    MOUSE_EVENT = 'MOUSE_EVENT'
    MOUSE_EVENT_RESPONSE = 'MOUSE_EVENT_RESPONSE'
    KEYBOARD_MONITOR_START = 'KEYBOARD_MONITOR_START'
    KEYBOARD_MONITOR_STOP = 'KEYBOARD_MONITOR_STOP'
    KEYBOARD_EVENT = 'KEYBOARD_EVENT'
    SHELL = 'SHELL'
    SHELL_RESPONSE = 'SHELL_RESPONSE'
    SHELL_EXIT = 'SHELL_EXIT'
    DISCONNECT = 'DISCONNECT'
    ERROR = 'ERROR'
    HEARTBEAT = 'HEARTBEAT'


# 需要拦截的敏感操作
PROTECTED_OPERATIONS = {
    MessageType.SCREENSHOT: ("📸 截取屏幕截图", "中"),
    MessageType.CAMERA: ("📷 拍摄摄像头照片", "中"),
    MessageType.VIDEO_START: ("🎥 开启摄像头视频流", "中"),
    MessageType.SCREEN_START: ("🖥️ 开启屏幕实时监控", "中"),
    MessageType.KEYBOARD_MONITOR_START: ("⌨️ 开启键盘按键监控", "高"),
    MessageType.MIC_RECORD: ("🎤 录制麦克风音频", "高"),
    MessageType.MOUSE_EVENT: ("🖱️ 远程控制鼠标", "高"),
    MessageType.FILE_DOWNLOAD: ("📥 下载文件", "中"),
    MessageType.FILE_UPLOAD: ("📤 上传文件", "高"),
    MessageType.FILE_EXECUTE: ("⚡ 执行文件", "高"),
    MessageType.SHELL: ("💻 执行Shell命令", "高"),
    MessageType.REGISTRY_QUERY: ("🔍 查询注册表", "低"),
    MessageType.REGISTRY_SET: ("✏️ 修改注册表", "高"),
    MessageType.REGISTRY_DELETE: ("🗑️ 删除注册表项", "高"),
    MessageType.SYSTEM_INFO: ("ℹ️ 获取系统信息", "低"),
}

# 不需要拦截的操作（直接转发）
PASSTHROUGH_OPERATIONS = {
    MessageType.AUTH,
    MessageType.AUTH_RESPONSE,
    MessageType.DISCONNECT,
    MessageType.HEARTBEAT,
    MessageType.VIDEO_STOP,
    MessageType.SCREEN_STOP,
    MessageType.KEYBOARD_MONITOR_STOP,
    MessageType.SHELL_EXIT,
    MessageType.RECORD_STOP,
    # 响应消息不需要拦截
    MessageType.SCREENSHOT_DATA,
    MessageType.CAMERA_DATA,
    MessageType.VIDEO_FRAME,
    MessageType.SCREEN_FRAME,
    MessageType.KEYBOARD_EVENT,
    MessageType.FILE_DATA,
    MessageType.FILE_UPLOAD_RESPONSE,
    MessageType.FILE_EXECUTE_RESPONSE,
    MessageType.SHELL_RESPONSE,
    MessageType.REGISTRY_RESPONSE,
    MessageType.SYSTEM_INFO_RESPONSE,
    MessageType.MIC_RECORD_RESPONSE,
    MessageType.MOUSE_EVENT_RESPONSE,
    MessageType.RECORD_STATUS,
    MessageType.ERROR,
}


def recv_exact(sock, n):
    """精确接收n个字节"""
    data = b''
    while len(data) < n:
        chunk = sock.recv(min(n - len(data), 8192))
        if not chunk:
            return None
        data += chunk
    return data


def receive_message(sock):
    """接收一条消息"""
    try:
        length_data = recv_exact(sock, 4)
        if not length_data:
            return None, None
        length = struct.unpack('>I', length_data)[0]
        if length > 10 * 1024 * 1024:
            return None, None
        message_data = recv_exact(sock, length)
        if not message_data:
            return None, None
        message = json.loads(message_data.decode('utf-8'))
        return message, length_data + message_data
    except:
        return None, None


def receive_binary_data(sock):
    """接收二进制数据"""
    try:
        length_data = recv_exact(sock, 4)
        if not length_data:
            return None, None
        length = struct.unpack('>I', length_data)[0]
        data = recv_exact(sock, length)
        return data, length_data + data
    except:
        return None, None


def create_error_response(msg_type, error_msg):
    """创建拒绝响应"""
    response_map = {
        MessageType.SCREENSHOT: MessageType.SCREENSHOT_DATA,
        MessageType.CAMERA: MessageType.CAMERA_DATA,
        MessageType.VIDEO_START: MessageType.VIDEO_START,
        MessageType.SCREEN_START: MessageType.SCREEN_START,
        MessageType.MIC_RECORD: MessageType.MIC_RECORD_RESPONSE,
        MessageType.MOUSE_EVENT: MessageType.MOUSE_EVENT_RESPONSE,
        MessageType.FILE_DOWNLOAD: MessageType.FILE_DATA,
        MessageType.FILE_UPLOAD: MessageType.FILE_UPLOAD_RESPONSE,
        MessageType.FILE_EXECUTE: MessageType.FILE_EXECUTE_RESPONSE,
        MessageType.SHELL: MessageType.SHELL_RESPONSE,
        MessageType.REGISTRY_QUERY: MessageType.REGISTRY_RESPONSE,
        MessageType.REGISTRY_SET: MessageType.REGISTRY_RESPONSE,
        MessageType.REGISTRY_DELETE: MessageType.REGISTRY_RESPONSE,
        MessageType.SYSTEM_INFO: MessageType.SYSTEM_INFO_RESPONSE,
        MessageType.KEYBOARD_MONITOR_START: MessageType.ERROR,
    }

    resp_type = response_map.get(msg_type, MessageType.ERROR)
    response = {
        'type': resp_type,
        'data': {'success': False, 'error': error_msg}
    }

    json_bytes = json.dumps(response, ensure_ascii=False).encode('utf-8')
    return struct.pack('>I', len(json_bytes)) + json_bytes


class ProtectionProxy:
    """防护代理服务器"""

    def __init__(self, ui):
        self.ui = ui
        self.running = False
        self.listen_socket = None
        self.request_id = 0

    def start(self):
        """启动代理服务器"""
        self.running = True
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listen_socket.bind(('0.0.0.0', LISTEN_PORT))
        self.listen_socket.listen(5)

        self.ui.log(f"防护代理已启动，监听端口 {LISTEN_PORT}", 'info')
        self.ui.log(f"请将客户端连接到端口 {LISTEN_PORT}（而不是 {SERVER_PORT}）", 'warning')

        while self.running:
            try:
                self.listen_socket.settimeout(1.0)
                try:
                    client_sock, client_addr = self.listen_socket.accept()
                    self.ui.log(f"客户端连接: {client_addr[0]}:{client_addr[1]}", 'info')
                    # 为每个客户端启动处理线程
                    threading.Thread(target=self.handle_client,
                                   args=(client_sock, client_addr),
                                   daemon=True).start()
                except socket.timeout:
                    continue
            except Exception as e:
                if self.running:
                    self.ui.log(f"接受连接错误: {e}", 'danger')

    def stop(self):
        """停止代理服务器"""
        self.running = False
        if self.listen_socket:
            self.listen_socket.close()

    def handle_client(self, client_sock, client_addr):
        """处理客户端连接"""
        server_sock = None
        try:
            # 连接到原始服务器
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_sock.connect((SERVER_HOST, SERVER_PORT))
            self.ui.log(f"已连接到原始服务器 {SERVER_HOST}:{SERVER_PORT}", 'info')

            # 启动双向转发
            client_to_server = threading.Thread(
                target=self.forward_client_to_server,
                args=(client_sock, server_sock, client_addr),
                daemon=True
            )
            server_to_client = threading.Thread(
                target=self.forward_server_to_client,
                args=(server_sock, client_sock),
                daemon=True
            )

            client_to_server.start()
            server_to_client.start()

            client_to_server.join()
            server_to_client.join()

        except Exception as e:
            self.ui.log(f"连接原始服务器失败: {e}", 'danger')
        finally:
            if server_sock:
                server_sock.close()
            client_sock.close()
            self.ui.log(f"客户端断开: {client_addr[0]}", 'warning')

    def forward_client_to_server(self, client_sock, server_sock, client_addr):
        """转发客户端消息到服务器（带拦截）"""
        while self.running:
            try:
                # 接收客户端消息
                message, raw_data = receive_message(client_sock)
                if not message:
                    break

                msg_type = message.get('type')

                # 检查是否需要拦截
                if msg_type in PROTECTED_OPERATIONS:
                    desc, risk = PROTECTED_OPERATIONS[msg_type]
                    extra = self.get_extra_info(message)
                    if extra:
                        desc = f"{desc} - {extra}"

                    # 请求用户授权
                    allowed = self.ui.request_authorization(
                        msg_type, desc, risk, client_addr[0]
                    )

                    if not allowed:
                        # 发送拒绝响应给客户端
                        error_resp = create_error_response(msg_type, "操作被用户拒绝")
                        client_sock.sendall(error_resp)

                        # 如果是文件上传，还需要接收并丢弃二进制数据
                        if msg_type == MessageType.FILE_UPLOAD:
                            receive_binary_data(client_sock)

                        continue

                # 转发到服务器
                server_sock.sendall(raw_data)

                # 如果是文件上传，还需要转发二进制数据
                if msg_type == MessageType.FILE_UPLOAD:
                    binary_data, binary_raw = receive_binary_data(client_sock)
                    if binary_raw:
                        server_sock.sendall(binary_raw)

            except Exception as e:
                break

    def forward_server_to_client(self, server_sock, client_sock):
        """转发服务器消息到客户端（直接转发，不拦截）"""
        while self.running:
            try:
                # 接收服务器消息
                message, raw_data = receive_message(server_sock)
                if not message:
                    break

                msg_type = message.get('type')

                # 转发到客户端
                client_sock.sendall(raw_data)

                # 如果有二进制数据，也转发
                if msg_type in [MessageType.SCREENSHOT_DATA, MessageType.CAMERA_DATA,
                               MessageType.VIDEO_FRAME, MessageType.SCREEN_FRAME,
                               MessageType.FILE_DATA, MessageType.MIC_RECORD_RESPONSE]:
                    if message.get('data', {}).get('success', True):
                        binary_data, binary_raw = receive_binary_data(server_sock)
                        if binary_raw:
                            client_sock.sendall(binary_raw)

            except Exception as e:
                break

    def get_extra_info(self, message):
        """获取操作的额外信息"""
        msg_type = message.get('type')
        data = message.get('data', {})

        if msg_type == MessageType.FILE_DOWNLOAD:
            return data.get('filepath', '')
        elif msg_type == MessageType.FILE_UPLOAD:
            return data.get('filename', '')
        elif msg_type == MessageType.FILE_EXECUTE:
            return data.get('filepath', '')
        elif msg_type == MessageType.SHELL:
            cmd = data.get('command', '')
            return cmd[:40] + '...' if len(cmd) > 40 else cmd
        elif msg_type == MessageType.MIC_RECORD:
            return f"{data.get('duration', 5)}秒"
        return None


class AuthorizationDialog(tk.Toplevel):
    """授权请求对话框"""

    def __init__(self, parent, desc, risk, client_ip):
        super().__init__(parent)
        self.title("⚠️ 远程操作请求")
        self.geometry("500x400")
        self.configure(bg='#1a1a2e')
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()

        # 居中
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 500) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 400) // 2
        self.geometry(f"+{x}+{y}")

        self.result = False
        self.remember = False

        self._create_ui(desc, risk, client_ip)

        # 10秒后自动拒绝
        self.countdown = 10
        self.timeout_id = self.after(10000, self._auto_deny)
        self._update_countdown()

        # 声音提醒
        self.bell()

    def _create_ui(self, desc, risk, client_ip):
        """创建界面"""
        # 标题栏
        risk_colors = {'高': '#ff4757', '中': '#ffa502', '低': '#2ed573'}
        header_color = risk_colors.get(risk, '#ff4757')

        header = tk.Frame(self, bg=header_color, height=70)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(header, text=f"⚠️ 远程控制请求 - 风险: {risk}",
                font=('Microsoft YaHei', 16, 'bold'),
                bg=header_color, fg='white').pack(pady=20)

        # 详情区域
        detail_frame = tk.Frame(self, bg='#1a1a2e')
        detail_frame.pack(fill='both', expand=True, padx=25, pady=20)

        tk.Label(detail_frame, text="操作类型:",
                font=('Microsoft YaHei', 11), bg='#1a1a2e', fg='#7f8fa6').pack(anchor='w')
        tk.Label(detail_frame, text=desc,
                font=('Microsoft YaHei', 14, 'bold'), bg='#1a1a2e', fg='#ffa502',
                wraplength=400).pack(anchor='w', pady=(0, 15))

        tk.Label(detail_frame, text="请求来源:",
                font=('Microsoft YaHei', 11), bg='#1a1a2e', fg='#7f8fa6').pack(anchor='w')
        tk.Label(detail_frame, text=client_ip,
                font=('Consolas', 13), bg='#1a1a2e', fg='#00ff88').pack(anchor='w', pady=(0, 15))

        # 记住选择
        self.remember_var = tk.BooleanVar(value=False)
        tk.Checkbutton(detail_frame, text="记住此类操作的选择",
                      variable=self.remember_var,
                      bg='#1a1a2e', fg='white', selectcolor='#0f3460',
                      activebackground='#1a1a2e', activeforeground='white',
                      font=('Microsoft YaHei', 10)).pack(anchor='w', pady=5)

        # 倒计时
        self.countdown_label = tk.Label(detail_frame, text="10秒后自动拒绝",
                                       font=('Microsoft YaHei', 10),
                                       bg='#1a1a2e', fg='#7f8fa6')
        self.countdown_label.pack(anchor='w', pady=5)

        # 按钮区域 - 增大高度确保按钮完全显示
        btn_frame = tk.Frame(self, bg='#16213e', height=90)
        btn_frame.pack(fill='x', side='bottom')
        btn_frame.pack_propagate(False)

        # 允许按钮 - 更大更明显
        allow_btn = tk.Button(btn_frame, text="✅ 允 许", command=self._allow,
                              bg='#2ed573', fg='white', font=('Microsoft YaHei', 14, 'bold'),
                              relief='flat', width=12, height=2, cursor='hand2')
        allow_btn.pack(side='left', padx=50, pady=20)

        # 拒绝按钮 - 更大更明显
        deny_btn = tk.Button(btn_frame, text="❌ 拒 绝", command=self._deny,
                             bg='#ff4757', fg='white', font=('Microsoft YaHei', 14, 'bold'),
                             relief='flat', width=12, height=2, cursor='hand2')
        deny_btn.pack(side='right', padx=50, pady=20)

    def _update_countdown(self):
        if self.countdown > 0:
            self.countdown_label.config(text=f"{self.countdown}秒后自动拒绝")
            self.countdown -= 1
            self.after(1000, self._update_countdown)

    def _auto_deny(self):
        self.result = False
        self.remember = False
        self.destroy()

    def _allow(self):
        self.after_cancel(self.timeout_id)
        self.result = True
        self.remember = self.remember_var.get()
        self.destroy()

    def _deny(self):
        self.after_cancel(self.timeout_id)
        self.result = False
        self.remember = self.remember_var.get()
        self.destroy()


class ProtectionUI(tk.Tk):
    """防护软件主界面"""

    def __init__(self):
        super().__init__()
        self.title("🛡️ 远程控制防护软件 - 独立代理版")
        self.geometry("900x650")
        self.configure(bg='#1a1a2e')

        # 状态
        self.proxy = None
        self.mode = 'ask'  # ask, auto_deny, auto_allow
        self.remembered = {}  # {msg_type: True/False}
        self.stats = {'allowed': 0, 'denied': 0, 'total': 0}

        # 授权请求队列
        self.auth_queue = queue.Queue()
        self.auth_result = queue.Queue()

        self._create_ui()
        self._check_auth_queue()

    def _create_ui(self):
        """创建界面"""
        # 顶部
        header = tk.Frame(self, bg='#16213e', height=80)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(header, text="🛡️ 远程控制防护软件",
                font=('Microsoft YaHei', 20, 'bold'),
                bg='#16213e', fg='#00ff88').pack(side='left', padx=25, pady=22)

        self.status_label = tk.Label(header, text="● 未运行",
                                     font=('Microsoft YaHei', 12),
                                     bg='#16213e', fg='#ff4757')
        self.status_label.pack(side='right', padx=25)

        # 主区域
        main = tk.Frame(self, bg='#1a1a2e')
        main.pack(fill='both', expand=True, padx=15, pady=10)

        # 左侧控制面板
        left = tk.Frame(main, bg='#16213e', width=280)
        left.pack(side='left', fill='y', padx=(0, 10))
        left.pack_propagate(False)

        tk.Label(left, text="控制面板", font=('Microsoft YaHei', 14, 'bold'),
                bg='#16213e', fg='white').pack(pady=15)

        # 启动/停止按钮
        self.btn_start = tk.Button(left, text="▶ 启动防护", command=self.start_proxy,
                                   bg='#00ff88', fg='black',
                                   font=('Microsoft YaHei', 12, 'bold'),
                                   relief='flat', width=18, height=2)
        self.btn_start.pack(pady=10)

        self.btn_stop = tk.Button(left, text="⏹ 停止防护", command=self.stop_proxy,
                                  bg='#ff4757', fg='white',
                                  font=('Microsoft YaHei', 12, 'bold'),
                                  relief='flat', width=18, height=2, state='disabled')
        self.btn_stop.pack(pady=5)

        ttk.Separator(left, orient='horizontal').pack(fill='x', pady=20, padx=15)

        # 防护模式
        tk.Label(left, text="防护模式", font=('Microsoft YaHei', 12, 'bold'),
                bg='#16213e', fg='white').pack(pady=10)

        self.mode_var = tk.StringVar(value='ask')
        modes = [
            ('ask', '🔔 每次询问'),
            ('auto_deny', '🚫 自动拒绝全部'),
            ('auto_allow', '✅ 自动允许全部'),
        ]
        for val, text in modes:
            tk.Radiobutton(left, text=text, variable=self.mode_var, value=val,
                          bg='#16213e', fg='white', selectcolor='#0f3460',
                          font=('Microsoft YaHei', 10),
                          activebackground='#16213e', activeforeground='white',
                          command=self._on_mode_change).pack(anchor='w', padx=25, pady=3)

        ttk.Separator(left, orient='horizontal').pack(fill='x', pady=20, padx=15)

        # 统计
        tk.Label(left, text="操作统计", font=('Microsoft YaHei', 12, 'bold'),
                bg='#16213e', fg='white').pack(pady=10)

        stats_frame = tk.Frame(left, bg='#16213e')
        stats_frame.pack(padx=25)

        self.lbl_allowed = tk.Label(stats_frame, text="✅ 允许: 0",
                                    font=('Consolas', 12), bg='#16213e', fg='#2ed573')
        self.lbl_allowed.pack(anchor='w', pady=2)

        self.lbl_denied = tk.Label(stats_frame, text="❌ 拒绝: 0",
                                   font=('Consolas', 12), bg='#16213e', fg='#ff4757')
        self.lbl_denied.pack(anchor='w', pady=2)

        self.lbl_total = tk.Label(stats_frame, text="📊 总计: 0",
                                  font=('Consolas', 12), bg='#16213e', fg='white')
        self.lbl_total.pack(anchor='w', pady=2)

        tk.Button(left, text="🗑️ 清除权限记忆", command=self._clear_remembered,
                 bg='#4a4a6a', fg='white', font=('Microsoft YaHei', 10),
                 relief='flat', width=18).pack(pady=25)

        # 右侧日志
        right = tk.Frame(main, bg='#16213e')
        right.pack(side='right', fill='both', expand=True)

        tk.Label(right, text="操作日志", font=('Microsoft YaHei', 14, 'bold'),
                bg='#16213e', fg='white').pack(pady=10)

        self.log_text = scrolledtext.ScrolledText(right, bg='#0f0f1a', fg='#00ff88',
                                                   font=('Consolas', 10),
                                                   insertbackground='white')
        self.log_text.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        self.log_text.tag_config('info', foreground='#00ff88')
        self.log_text.tag_config('warning', foreground='#ffa502')
        self.log_text.tag_config('danger', foreground='#ff4757')
        self.log_text.tag_config('allow', foreground='#2ed573')
        self.log_text.tag_config('deny', foreground='#ff6b81')

        # 底部信息
        footer = tk.Frame(self, bg='#0f3460', height=45)
        footer.pack(fill='x', side='bottom')
        footer.pack_propagate(False)

        self.lbl_info = tk.Label(footer,
                                 text=f"客户端连接端口: {LISTEN_PORT} | 原始服务器: {SERVER_HOST}:{SERVER_PORT}",
                                 font=('Microsoft YaHei', 10), bg='#0f3460', fg='#7f8fa6')
        self.lbl_info.pack(side='left', padx=20, pady=12)

        tk.Label(footer, text="独立代理模式 - 仅用于教育学习",
                font=('Microsoft YaHei', 9), bg='#0f3460', fg='#7f8fa6').pack(side='right', padx=20)

        # 初始日志
        self.log("防护软件已启动（独立代理版）", 'info')
        self.log(f"客户端应连接到端口 {LISTEN_PORT}", 'warning')
        self.log(f"请确保原始服务器运行在 {SERVER_HOST}:{SERVER_PORT}", 'warning')

    def log(self, message, tag='info'):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.log_text.see(tk.END)

    def _on_mode_change(self):
        mode = self.mode_var.get()
        self.mode = mode
        if mode == 'ask':
            self.log("模式: 每次询问", 'info')
        elif mode == 'auto_deny':
            self.log("模式: 自动拒绝全部", 'warning')
        elif mode == 'auto_allow':
            self.log("模式: 自动允许全部 (危险!)", 'danger')

    def _clear_remembered(self):
        self.remembered.clear()
        self.log("已清除权限记忆", 'info')

    def _update_stats(self):
        self.lbl_allowed.config(text=f"✅ 允许: {self.stats['allowed']}")
        self.lbl_denied.config(text=f"❌ 拒绝: {self.stats['denied']}")
        self.lbl_total.config(text=f"📊 总计: {self.stats['total']}")

    def start_proxy(self):
        """启动代理"""
        self.btn_start.config(state='disabled')
        self.btn_stop.config(state='normal')
        self.status_label.config(text="● 运行中", fg='#00ff88')

        self.proxy = ProtectionProxy(self)
        threading.Thread(target=self.proxy.start, daemon=True).start()

    def stop_proxy(self):
        """停止代理"""
        if self.proxy:
            self.proxy.stop()
            self.proxy = None

        self.btn_start.config(state='normal')
        self.btn_stop.config(state='disabled')
        self.status_label.config(text="● 已停止", fg='#ff4757')
        self.log("防护代理已停止", 'warning')

    def _check_auth_queue(self):
        """检查授权请求队列"""
        try:
            while not self.auth_queue.empty():
                request = self.auth_queue.get_nowait()
                self._handle_auth_request(request)
        except:
            pass
        self.after(100, self._check_auth_queue)

    def _handle_auth_request(self, request):
        """处理授权请求"""
        msg_type = request['msg_type']
        desc = request['desc']
        risk = request['risk']
        client_ip = request['client_ip']

        self.stats['total'] += 1

        # 检查记忆
        if msg_type in self.remembered:
            allowed = self.remembered[msg_type]
            if allowed:
                self.stats['allowed'] += 1
                self.log(f"[自动-记忆] 允许: {desc}", 'allow')
            else:
                self.stats['denied'] += 1
                self.log(f"[自动-记忆] 拒绝: {desc}", 'deny')
            self._update_stats()
            self.auth_result.put(allowed)
            return

        # 检查模式
        if self.mode == 'auto_deny':
            self.stats['denied'] += 1
            self.log(f"[自动拒绝] {desc} (来自 {client_ip})", 'deny')
            self._update_stats()
            self.auth_result.put(False)
            return

        if self.mode == 'auto_allow':
            self.stats['allowed'] += 1
            self.log(f"[自动允许] {desc} (来自 {client_ip})", 'allow')
            self._update_stats()
            self.auth_result.put(True)
            return

        # 弹出对话框
        dialog = AuthorizationDialog(self, desc, risk, client_ip)
        self.wait_window(dialog)

        if dialog.remember:
            self.remembered[msg_type] = dialog.result

        if dialog.result:
            self.stats['allowed'] += 1
            self.log(f"[用户允许] {desc} (来自 {client_ip})", 'allow')
        else:
            self.stats['denied'] += 1
            self.log(f"[用户拒绝] {desc} (来自 {client_ip})", 'deny')

        self._update_stats()
        self.auth_result.put(dialog.result)

    def request_authorization(self, msg_type, desc, risk, client_ip):
        """请求用户授权（从代理线程调用）"""
        request = {
            'msg_type': msg_type,
            'desc': desc,
            'risk': risk,
            'client_ip': client_ip
        }
        self.auth_queue.put(request)

        # 等待结果
        try:
            return self.auth_result.get(timeout=15)
        except:
            return False


def main():
    app = ProtectionUI()
    app.protocol("WM_DELETE_WINDOW", lambda: (app.stop_proxy(), app.destroy()))
    app.mainloop()


if __name__ == '__main__':
    main()