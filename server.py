"""
服务器端主程序 - 远程控制系统（被控主机B）
实现服务器端的所有功能
"""

import socket
import threading
import os
import sys
import subprocess
import io
import time
from datetime import datetime

# 导入截图库
try:
    import mss
    from PIL import Image
except ImportError:
    print("错误: 请先安装依赖库")
    print("运行: pip install -r requirements.txt")
    exit(1)

# 导入自定义模块
from config import *
from protocol import *
from utils import *
from screen_stream import ScreenStream


class RemoteControlServer:
    """远程控制服务器类"""
    
    def __init__(self, host=SERVER_HOST, port=SERVER_PORT):
        """
        初始化服务器
        
        Args:
            host: 服务器监听地址
            port: 服务器监听端口
        """
        self.host = host
        self.port = port
        self.server_socket = None
        self. is_running = False
        self. client_socket = None
        self.client_address = None
        self.is_authenticated = False
        self.is_controlled = False  # 是否处于受控状态
        self.shell_mode = False  # 是否处于Shell模式
        self.shell_root_dir = os.path.abspath(SAFE_DIRECTORY)  # Shell根目录（沙箱）
        self.shell_working_dir = os.path.abspath(SAFE_DIRECTORY)  # Shell当前工作目录
        self.video_stream = None  # 视频流对象
        self.video_streaming = False  # 是否正在视频流传输
        
        print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}{'  远程控制系统 - 服务器端 (被控主机B)':^60}{Colors.RESET}")
        print(f"{Colors. CYAN}{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"{Colors.YELLOW}⚠️  注意: 本程序仅用于教育学习目的{Colors.RESET}")
        print(f"{Colors.YELLOW}⚠️  仅在本地网络或虚拟机环境中运行{Colors.RESET}")
        print(f"{Colors. CYAN}{'='*60}{Colors. RESET}\n")
    
    def start(self):
        """启动服务器"""
        try:
            # 创建服务器套接字
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket. setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self. server_socket.listen(MAX_CONNECTIONS)
            
            self.is_running = True
            
            # 显示服务器信息
            local_ip = get_local_ip()
            print(f"{Colors.GREEN}✓ 服务器启动成功! {Colors.RESET}")
            print(f"  监听地址: {Colors.BOLD}{local_ip}:{self.port}{Colors.RESET}")
            print(f"  安全目录: {Colors.BOLD}{SAFE_DIRECTORY}{Colors.RESET}")
            print(f"  Shell类型: {Colors.BOLD}{SHELL_TYPE}{Colors.RESET} ({CURRENT_OS})")
            print(f"  允许命令: {Colors.BOLD}{len(ALLOWED_COMMANDS)}个{Colors.RESET}")
            print(f"\n{Colors.CYAN}等待客户端连接...{Colors.RESET}\n")
            
            # 接受连接循环
            while self.is_running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    print(f"\n{Colors. BLUE}► 收到连接请求: {client_address[0]}:{client_address[1]}{Colors.RESET}")
                    
                    # 启动客户端处理线程
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except KeyboardInterrupt:
                    print(f"\n{Colors. YELLOW}接收到中断信号, 正在关闭服务器...{Colors.RESET}")
                    break
                except Exception as e:
                    print(f"{Colors.RED}✗ 接受连接失败: {e}{Colors. RESET}")
        
        except Exception as e:
            print(f"{Colors.RED}✗ 服务器启动失败: {e}{Colors.RESET}")
        
        finally:
            self.stop()
    
    def stop(self):
        """停止服务器"""
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()
        print(f"\n{Colors.GREEN}✓ 服务器已关闭{Colors.RESET}")
    
    def handle_client(self, client_socket, client_address):
        """
        处理客户端连接
        
        Args:
            client_socket: 客户端套接字
            client_address: 客户端地址
        """
        self.client_socket = client_socket
        self.client_address = client_address
        self.is_authenticated = False
        
        try:
            # 等待身份验证
            if not self.authenticate_client():
                print(f"{Colors.RED}✗ 身份验证失败, 断开连接: {client_address[0]}{Colors.RESET}")
                client_socket.close()
                return
            
            print(f"{Colors.GREEN}✓ 身份验证成功: {client_address[0]}{Colors.RESET}")
            self.is_authenticated = True
            self.is_controlled = True
            self.display_controlled_status(True)
            
            # 消息处理循环
            while self.is_running and self.is_authenticated:
                message = receive_message(client_socket)
                
                if message is None:
                    print(f"{Colors. YELLOW}► 客户端断开连接: {client_address[0]}{Colors.RESET}")
                    break
                
                # 处理不同类型的消息
                self.handle_message(message)
        
        except Exception as e:
            print(f"{Colors.RED}✗ 处理客户端时发生错误: {e}{Colors.RESET}")
        
        finally:
            self.is_controlled = False
            self.display_controlled_status(False)
            client_socket.close()
            print(f"{Colors. CYAN}► 连接已关闭: {client_address[0]}{Colors.RESET}\n")
    
    def authenticate_client(self):
        """
        验证客户端身份
        
        Returns:
            bool: 验证是否成功
        """
        try:
            # 接收身份验证消息
            message = receive_message(self.client_socket)
            
            if message is None or message['type'] != MessageType.AUTH:
                response = create_auth_response(False, "无效的验证请求")
                send_message(self.client_socket, response)
                return False
            
            # 验证密码哈希
            password_hash = message['data']. get('password_hash', '')
            
            if password_hash == AUTH_PASSWORD_HASH:
                response = create_auth_response(True, "验证成功")
                send_message(self.client_socket, response)
                return True
            else:
                response = create_auth_response(False, "密码错误")
                send_message(self.client_socket, response)
                return False
        
        except Exception as e:
            print(f"{Colors.RED}✗ 身份验证错误: {e}{Colors. RESET}")
            return False
    
    def handle_message(self, message):
        """
        处理接收到的消息
        
        Args:
            message: 消息字典
        """
        msg_type = message['type']
        data = message['data']
        
        print(f"{Colors.MAGENTA}◄ 收到请求: {msg_type}{Colors.RESET}")
        
        # 根据消息类型调用相应的处理函数
        if msg_type == MessageType.SCREENSHOT:
            self.handle_screenshot()
        
        elif msg_type == MessageType.CAMERA:
            self.handle_camera()
        
        elif msg_type == MessageType.VIDEO_START:
            width = data.get('width', 640)
            height = data.get('height', 480)
            fps = data.get('fps', 30)
            quality = data.get('quality', 85)
            self.handle_video_start(width, height, fps, quality)

        elif msg_type == MessageType.SCREEN_START:
            region = data.get('region', None)
            fps = data.get('fps', 10)
            quality = data.get('quality', 70)
            self.handle_screen_start(region, fps, quality)

        elif msg_type == MessageType.SCREEN_STOP:
            self.handle_screen_stop()
        
        elif msg_type == MessageType.VIDEO_STOP:
            self.handle_video_stop()
        
        elif msg_type == MessageType.RECORD_START:
            filename = data.get('filename', None)
            self.handle_record_start(filename)
        
        elif msg_type == MessageType.RECORD_STOP:
            self.handle_record_stop()
        
        elif msg_type == MessageType.FILE_DOWNLOAD:
            filepath = data.get('filepath', '')
            self.handle_file_download(filepath)
        
        elif msg_type == MessageType.FILE_UPLOAD:
            filepath = data.get('filepath', '')
            filename = data.get('filename', '')
            self.handle_file_upload(filepath, filename)
        
        elif msg_type == MessageType.FILE_EXECUTE:
            filepath = data.get('filepath', '')
            args = data.get('args', '')
            self.handle_file_execute(filepath, args)
        
        elif msg_type == MessageType.MIC_RECORD:
            # 录制来自服务器主机的麦克风并返回 WAV 音频数据
            duration = data.get('duration', 5)
            samplerate = data.get('samplerate', 44100)
            channels = data.get('channels', 1)
            self.handle_mic_record(duration, samplerate, channels)
        
        elif msg_type == MessageType.REGISTRY_QUERY:
            hive = data.get('hive', '')
            key_path = data.get('key_path', '')
            name = data.get('name', None)
            self.handle_registry_query(hive, key_path, name)
        
        elif msg_type == MessageType.REGISTRY_SET:
            hive = data.get('hive', '')
            key_path = data.get('key_path', '')
            name = data.get('name', '')
            value = data.get('value', '')
            value_type = data.get('value_type', 'REG_SZ')
            self.handle_registry_set(hive, key_path, name, value, value_type)
        
        elif msg_type == MessageType.REGISTRY_DELETE:
            hive = data.get('hive', '')
            key_path = data.get('key_path', '')
            name = data.get('name', None)
            self.handle_registry_delete(hive, key_path, name)
        
        elif msg_type == MessageType.SYSTEM_INFO:
            self.handle_system_info()
        
        elif msg_type == MessageType.SHELL:
            command = data.get('command', '')
            working_dir = data.get('working_dir', None)
            self.handle_shell(command, working_dir)

        elif msg_type == MessageType.MOUSE_EVENT:
            # 处理鼠标事件
            event = data.get('event')
            x = data.get('x')
            y = data.get('y')
            button = data.get('button', 'left')
            clicks = data.get('clicks', 1)
            dx = data.get('dx', 0)
            dy = data.get('dy', 0)
            self.handle_mouse_event(event, x, y, button, clicks, dx, dy)
        
        elif msg_type == MessageType.KEYBOARD_MONITOR_START:
            # 开始键盘监控
            self.handle_keyboard_monitor_start()
        
        elif msg_type == MessageType.KEYBOARD_MONITOR_STOP:
            # 停止键盘监控
            self.handle_keyboard_monitor_stop()
        
        elif msg_type == MessageType.SHELL_EXIT:
            print(f"{Colors.YELLOW}► 客户端退出Shell模式{Colors.RESET}")
            self.shell_mode = False
            self.shell_working_dir = self.shell_root_dir  # 重置到根目录
        
        elif msg_type == MessageType.DISCONNECT:
            print(f"{Colors.YELLOW}► 客户端请求断开连接{Colors.RESET}")
            self.is_authenticated = False
        
        else:
            error_msg = create_error_message(f"未知的消息类型: {msg_type}")
            send_message(self.client_socket, error_msg)
    
    def handle_screenshot(self):
        """处理截图请求"""
        try:
            print(f"  {Colors.CYAN}正在截取屏幕... {Colors.RESET}")
            
            # 使用 mss 截取屏幕
            with mss.mss() as sct:
                # 截取主显示器
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                
                # 转换为 PIL Image
                img = Image.frombytes('RGB', screenshot.size, screenshot. rgb)
                
                # 压缩图片
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=85, optimize=True)
                img_data = output.getvalue()
            
            print(f"  {Colors.GREEN}✓ 截图成功 (大小: {format_file_size(len(img_data))}){Colors.RESET}")
            
            # 发送截图数据
            response = create_message(MessageType.SCREENSHOT_DATA, {
                'success': True,
                'size': len(img_data)
            })
            send_message(self.client_socket, response)
            send_binary_data(self.client_socket, img_data)
        
        except Exception as e:
            print(f"  {Colors.RED}✗ 截图失败: {e}{Colors.RESET}")
            response = create_message(MessageType. SCREENSHOT_DATA, {
                'success': False,
                'error': str(e)
            })
            send_message(self.client_socket, response)
    
    def handle_camera(self):
        """处理摄像头拍照请求"""
        try:
            print(f"  {Colors.CYAN}正在启动摄像头...{Colors.RESET}")
            
            # 导入opencv
            try:
                import cv2
            except ImportError:
                raise Exception("未安装opencv-python库，请运行: pip install opencv-python")
            
            # 打开摄像头 (0表示默认摄像头)
            cap = cv2.VideoCapture(0)
            
            if not cap.isOpened():
                raise Exception("无法打开摄像头，请检查摄像头是否连接")
            
            # 设置摄像头参数
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            
            # 预热摄像头 (读取几帧以稳定图像质量)
            for _ in range(5):
                cap.read()
            
            # 捕获图像
            ret, frame = cap.read()
            
            # 释放摄像头
            cap.release()
            
            if not ret or frame is None:
                raise Exception("摄像头拍照失败")
            
            # 保存到camera目录
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"camera_{timestamp}.jpg"
            filepath = os.path.join(CAMERA_DIRECTORY, filename)
            cv2.imwrite(filepath, frame)
            
            # 转换为JPEG格式的字节流
            success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not success:
                raise Exception("图像编码失败")
            
            img_data = buffer.tobytes()
            
            print(f"  {Colors.GREEN}✓ 摄像头拍照成功 (大小: {format_file_size(len(img_data))}, 已保存: {filename}){Colors.RESET}")
            
            # 发送摄像头数据
            response = create_message(MessageType.CAMERA_DATA, {
                'success': True,
                'size': len(img_data),
                'filename': filename
            })
            send_message(self.client_socket, response)
            send_binary_data(self.client_socket, img_data)
        
        except Exception as e:
            print(f"  {Colors.RED}✗ 摄像头拍照失败: {e}{Colors.RESET}")
            response = create_message(MessageType.CAMERA_DATA, {
                'success': False,
                'error': str(e)
            })
            send_message(self.client_socket, response)
    
    def handle_video_start(self, width, height, fps, quality):
        """处理开始视频流请求"""
        try:
            # 检查视频支持
            if not VIDEO_SUPPORT:
                raise Exception("服务器不支持视频功能")
            
            if self.video_streaming:
                raise Exception("视频流已在运行")
            
            print(f"  {Colors.CYAN}正在启动视频流 ({width}x{height} @ {fps}fps)...{Colors.RESET}")
            
            # 创建视频流
            self.video_stream = VideoStream(camera_index=0, width=width, height=height, fps=fps)
            success, msg = self.video_stream.start()
            
            if not success:
                raise Exception(msg)
            
            self.video_streaming = True
            
            print(f"  {Colors.GREEN}✓ 视频流启动成功{Colors.RESET}")
            
            # 发送成功响应
            response = create_message(MessageType.VIDEO_START, {
                'success': True,
                'message': '视频流已启动'
            })
            send_message(self.client_socket, response)
            
            # 等待一下确保响应已被客户端接收
            import time
            time.sleep(0.2)
            
            # 开始发送视频帧
            import threading
            self._video_thread = threading.Thread(
                target=self._video_stream_loop,
                args=(quality,),
                daemon=True
            )
            self._video_thread.start()
        
        except Exception as e:
            print(f"  {Colors.RED}✗ 视频流启动失败: {e}{Colors.RESET}")
            response = create_message(MessageType.VIDEO_START, {
                'success': False,
                'error': str(e)
            })
            send_message(self.client_socket, response)
    
    def _video_stream_loop(self, quality):
        """视频流发送循环"""
        import time
        
        frame_count = 0
        error_count = 0
        max_errors = 10  # 最多容忍10次连续错误
        
        while self.video_streaming and self.is_authenticated:
            try:
                # 获取JPEG编码的帧
                success, jpeg_data = self.video_stream.get_frame_jpeg(quality)
                
                if not success:
                    time.sleep(0.01)
                    continue
                
                frame_count += 1
                
                # 发送视频帧
                try:
                    response = create_message(MessageType.VIDEO_FRAME, {
                        'size': len(jpeg_data),
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    if not send_message(self.client_socket, response):
                        raise Exception("发送消息头失败")
                    
                    if not send_binary_data(self.client_socket, jpeg_data):
                        raise Exception("发送帧数据失败")
                    
                    # 发送成功,重置错误计数
                    error_count = 0
                    
                    # 添加小延迟,避免过快发送
                    time.sleep(0.001)
                    
                except Exception as send_error:
                    error_count += 1
                    
                    if error_count >= max_errors:
                        print(f"  {Colors.RED}✗ 连续错误过多,停止发送{Colors.RESET}")
                        break
                    
                    time.sleep(0.1)  # 出错时等待更长时间
            
            except Exception as e:
                print(f"  {Colors.RED}✗ 视频帧处理失败: {e}{Colors.RESET}")
                break
    
    def handle_video_stop(self):
        """处理停止视频流请求"""
        try:
            if not self.video_streaming:
                raise Exception("视频流未在运行")
            
            # 先设置停止标志,让发送线程尽快退出
            self.video_streaming = False
            
            # 等待发送线程结束(最多等待2秒)
            import time
            wait_time = 0
            while hasattr(self, '_video_thread') and self._video_thread and self._video_thread.is_alive():
                time.sleep(0.1)
                wait_time += 0.1
                if wait_time > 2.0:
                    break
            
            # 停止视频流
            if self.video_stream:
                success, msg = self.video_stream.stop()
                self.video_stream = None
            
            # 清理线程引用
            if hasattr(self, '_video_thread'):
                self._video_thread = None
            
            print(f"  {Colors.GREEN}✓ 视频流已停止{Colors.RESET}")
            
            response = create_message(MessageType.VIDEO_STOP, {
                'success': True,
                'message': '视频流已停止'
            })
            send_message(self.client_socket, response)
        
        except Exception as e:
            print(f"  {Colors.RED}✗ 停止视频流失败: {e}{Colors.RESET}")
            response = create_message(MessageType.VIDEO_STOP, {
                'success': False,
                'error': str(e)
            })
            send_message(self.client_socket, response)
    
    def handle_record_start(self, filename):
        """处理开始录像请求(自动启动视频流)"""
        try:
            # 如果视频流未启动,自动启动
            if not self.video_stream or not self.video_streaming:
                print(f"  {Colors.CYAN}视频流未启动,正在自动启动...{Colors.RESET}")
                
                # 检查视频支持
                if not VIDEO_SUPPORT:
                    raise Exception("服务器不支持视频功能")
                
                # 创建并启动视频流(使用默认参数)
                self.video_stream = VideoStream(camera_index=0, width=640, height=480, fps=30)
                success, msg = self.video_stream.start()
                
                if not success:
                    raise Exception(f"自动启动视频流失败: {msg}")
                
                self.video_streaming = True
                print(f"  {Colors.GREEN}✓ 视频流已自动启动{Colors.RESET}")
            
            # 开始录像
            print(f"  {Colors.CYAN}正在初始化录像... (目录: {CAMERA_DIRECTORY}){Colors.RESET}")
            success, msg = self.video_stream.start_recording(
                output_dir=CAMERA_DIRECTORY,
                filename=filename
            )
            
            if not success:
                # 提供更详细的错误信息
                import traceback
                print(f"  {Colors.RED}录像失败详情:{Colors.RESET}")
                print(f"    - 错误: {msg}")
                print(f"    - 目录: {CAMERA_DIRECTORY}")
                print(f"    - 文件名: {filename}")
                traceback.print_exc()
                raise Exception(msg)
            
            print(f"  {Colors.GREEN}✓ 开始录像: {msg}{Colors.RESET}")
            
            response = create_message(MessageType.RECORD_STATUS, {
                'success': True,
                'recording': True,
                'filepath': msg,
                'auto_started': True  # 标记视频流是自动启动的
            })
            send_message(self.client_socket, response)
        
        except Exception as e:
            print(f"  {Colors.RED}✗ 开始录像失败: {e}{Colors.RESET}")
            response = create_message(MessageType.RECORD_STATUS, {
                'success': False,
                'error': str(e)
            })
            send_message(self.client_socket, response)
    
    def handle_record_stop(self):
        """处理停止录像请求(自动关闭视频流)"""
        try:
            if not self.video_stream:
                raise Exception("视频流未启动")
            
            # 停止录像
            success, msg = self.video_stream.stop_recording()
            
            if not success:
                raise Exception(msg)
            
            print(f"  {Colors.GREEN}✓ 停止录像: {msg}{Colors.RESET}")
            
            # 自动关闭视频流
            print(f"  {Colors.CYAN}正在自动关闭视频流...{Colors.RESET}")
            self.video_streaming = False
            
            if self.video_stream:
                self.video_stream.stop()
                self.video_stream = None
            
            print(f"  {Colors.GREEN}✓ 视频流已自动关闭{Colors.RESET}")
            
            response = create_message(MessageType.RECORD_STATUS, {
                'success': True,
                'recording': False,
                'message': msg,
                'auto_stopped': True  # 标记视频流已自动关闭
            })
            send_message(self.client_socket, response)
        
        except Exception as e:
            print(f"  {Colors.RED}✗ 停止录像失败: {e}{Colors.RESET}")
            response = create_message(MessageType.RECORD_STATUS, {
                'success': False,
                'error': str(e)
            })
            send_message(self.client_socket, response)

    # ===== 屏幕实时查看 =====
    def handle_screen_start(self, region=None, fps=10, quality=70):
        try:
            print(f"  {Colors.CYAN}正在启动屏幕实时查看...{Colors.RESET}")
            # 创建屏幕流
            self.screen_stream = ScreenStream(region=region, fps=fps, quality=quality)
            success, msg = self.screen_stream.start()
            if not success:
                raise Exception(msg)

            # 发送开始响应
            response = create_message(MessageType.SCREEN_START, {'success': True, 'message': msg})
            send_message(self.client_socket, response)

            # 发送帧循环（在此线程中）
            def _send_loop():
                while getattr(self, 'screen_stream', None) and self.screen_stream.is_streaming and self.is_authenticated:
                    success, frame = self.screen_stream.get_frame(timeout=1.0)
                    if not success:
                        continue
                    # 发送帧元信息
                    header = create_message(MessageType.SCREEN_FRAME, {'size': len(frame)})
                    if not send_message(self.client_socket, header):
                        break
                    if not send_binary_data(self.client_socket, frame):
                        break
                # 当循环结束, 发送停止通知
                try:
                    stop_msg = create_message(MessageType.SCREEN_STOP, {'success': True, 'message': '屏幕流已停止'})
                    send_message(self.client_socket, stop_msg)
                except Exception:
                    pass

            import threading
            self._screen_thread = threading.Thread(target=_send_loop, daemon=True)
            self._screen_thread.start()

        except Exception as e:
            print(f"  {Colors.RED}✗ 启动屏幕实时查看失败: {e}{Colors.RESET}")
            response = create_message(MessageType.SCREEN_START, {'success': False, 'error': str(e)})
            send_message(self.client_socket, response)

    def handle_screen_stop(self):
        try:
            if getattr(self, 'screen_stream', None):
                self.screen_stream.stop()
                self.screen_stream = None
            # 清理线程引用
            if hasattr(self, '_screen_thread'):
                self._screen_thread = None

            response = create_message(MessageType.SCREEN_STOP, {'success': True, 'message': '屏幕流已停止'})
            send_message(self.client_socket, response)
        except Exception as e:
            response = create_message(MessageType.SCREEN_STOP, {'success': False, 'error': str(e)})
            send_message(self.client_socket, response)

    def handle_mouse_event(self, event, x, y, button='left', clicks=1, dx=0, dy=0):
        try:
            # 延迟导入 pyautogui，避免未安装时报错在模块导入阶段
            try:
                import pyautogui
            except Exception:
                raise Exception('缺少依赖: 请安装 pyautogui')

            if event == 'move':
                if x is not None and y is not None:
                    pyautogui.moveTo(x, y)
                else:
                    pyautogui.moveRel(dx, dy)
            elif event == 'click':
                if x is not None and y is not None:
                    pyautogui.click(x=x, y=y, clicks=clicks, button=button)
                else:
                    pyautogui.click(clicks=clicks, button=button)
            elif event == 'scroll':
                pyautogui.scroll(dy)
            else:
                raise ValueError('未知鼠标事件')

            response = create_message(MessageType.MOUSE_EVENT_RESPONSE, {'success': True})
            send_message(self.client_socket, response)

        except Exception as e:
            response = create_message(MessageType.MOUSE_EVENT_RESPONSE, {'success': False, 'error': str(e)})
            send_message(self.client_socket, response)

    def handle_keyboard_monitor_start(self):
        """开始键盘监控"""
        try:
            print(f"  {Colors.CYAN}开始键盘监控...{Colors.RESET}")
            
            # 延迟导入 pynput
            try:
                from pynput import keyboard
            except Exception:
                raise Exception('缺少依赖: 请安装 pynput')
            
            # 如果已经在监控，先停止
            if hasattr(self, 'keyboard_listener') and self.keyboard_listener:
                self.keyboard_listener.stop()
            
            # 定义键盘事件处理函数
            def on_press(key):
                try:
                    # 获取按键名称
                    try:
                        key_name = key.char if hasattr(key, 'char') and key.char else str(key)
                    except:
                        key_name = str(key)
                    
                    # 发送键盘事件到客户端
                    from datetime import datetime
                    msg = create_keyboard_event_message(
                        key=key_name,
                        event_type='press',
                        timestamp=datetime.now().isoformat()
                    )
                    send_message(self.client_socket, msg)
                except Exception as e:
                    print(f"  {Colors.RED}✗ 键盘事件处理失败: {e}{Colors.RESET}")
            
            # 启动键盘监听器
            self.keyboard_listener = keyboard.Listener(on_press=on_press)
            self.keyboard_listener.start()
            
            print(f"  {Colors.GREEN}✓ 键盘监控已启动{Colors.RESET}")
            
        except Exception as e:
            print(f"  {Colors.RED}✗ 启动键盘监控失败: {e}{Colors.RESET}")
    
    def handle_keyboard_monitor_stop(self):
        """停止键盘监控"""
        try:
            print(f"  {Colors.CYAN}停止键盘监控...{Colors.RESET}")
            
            if hasattr(self, 'keyboard_listener') and self.keyboard_listener:
                self.keyboard_listener.stop()
                self.keyboard_listener = None
                print(f"  {Colors.GREEN}✓ 键盘监控已停止{Colors.RESET}")
            else:
                print(f"  {Colors.YELLOW}键盘监控未启动{Colors.RESET}")
                
        except Exception as e:
            print(f"  {Colors.RED}✗ 停止键盘监控失败: {e}{Colors.RESET}")
    
    def handle_file_download(self, filepath):
        """
        处理文件下载请求
        
        Args:
            filepath: 文件路径
        """
        try:
            # 构建完整路径
            full_path = os.path.join(SAFE_DIRECTORY, filepath)
            
            # 安全检查
            if not is_safe_path(SAFE_DIRECTORY, full_path):
                raise Exception("路径不安全")
            
            if not os.path.exists(full_path):
                raise Exception("文件不存在")
            
            if not os.path.isfile(full_path):
                raise Exception("不是文件")
            
            # 检查文件大小
            is_valid, file_size = check_file_size(full_path)
            if not is_valid:
                raise Exception(f"文件太大 (限制: {format_file_size(MAX_FILE_SIZE)})")
            
            # 读取文件
            file_data = read_file_binary(full_path)
            if file_data is None:
                raise Exception("读取文件失败")
            
            print(f"  {Colors.GREEN}✓ 读取文件: {filepath} ({format_file_size(len(file_data))}){Colors.RESET}")
            
            # 发送响应
            response = create_message(MessageType.FILE_DATA, {
                'success': True,
                'filename': os.path.basename(filepath),
                'size': len(file_data)
            })
            send_message(self.client_socket, response)
            send_binary_data(self.client_socket, file_data)
        
        except Exception as e:
            print(f"  {Colors.RED}✗ 文件下载失败: {e}{Colors.RESET}")
            response = create_message(MessageType.FILE_DATA, {
                'success': False,
                'error': str(e)
            })
            send_message(self.client_socket, response)
    
    def handle_file_upload(self, filepath, filename):
        """
        处理文件上传请求
        
        Args:
            filepath: 远程保存路径
            filename: 文件名
        """
        try:
            print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"{Colors.CYAN}{Colors.BOLD}处理文件上传请求{Colors.RESET}")
            print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"  远程路径: {filepath}")
            print(f"  文件名: {filename}")
            
            # 接收文件数据
            file_data = receive_binary_data(self.client_socket)
            if file_data is None:
                raise Exception("接收文件数据失败")
            
            # 构建完整路径
            full_path = os.path.join(SAFE_DIRECTORY, filepath)
            
            # 验证路径安全性
            if not is_safe_path(SAFE_DIRECTORY, full_path):
                raise Exception(f"路径不安全或试图访问禁止目录: {filepath}")
            
            # 确保目标目录存在
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # 写入文件
            if not write_file_binary(full_path, file_data):
                raise Exception("写入文件失败")
            
            print(f"  {Colors.GREEN}✓ 文件上传成功: {filepath} ({format_file_size(len(file_data))}){Colors.RESET}")
            
            # 发送响应
            response = create_message(MessageType.FILE_UPLOAD_RESPONSE, {
                'success': True,
                'filepath': filepath,
                'size': len(file_data)
            })
            send_message(self.client_socket, response)
        
        except Exception as e:
            print(f"  {Colors.RED}✗ 文件上传失败: {e}{Colors.RESET}")
            response = create_message(MessageType.FILE_UPLOAD_RESPONSE, {
                'success': False,
                'error': str(e)
            })
            send_message(self.client_socket, response)
    
    def handle_file_execute(self, filepath, args=''):
        """
        处理文件执行请求
        
        Args:
            filepath: 文件路径
            args: 执行参数
        """
        try:
            print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"{Colors.CYAN}{Colors.BOLD}处理文件执行请求{Colors.RESET}")
            print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"  文件路径: {filepath}")
            print(f"  执行参数: {args if args else '(无)'}")
            
            # 构建完整路径
            full_path = os.path.join(SAFE_DIRECTORY, filepath)
            
            # 验证路径安全性
            if not is_safe_path(SAFE_DIRECTORY, full_path):
                raise Exception(f"路径不安全或试图访问禁止目录: {filepath}")
            
            # 检查文件是否存在
            if not os.path.exists(full_path):
                raise Exception(f"文件不存在: {filepath}")
            
            if not os.path.isfile(full_path):
                raise Exception(f"不是一个文件: {filepath}")
            
            # 根据操作系统和文件类型执行
            import subprocess
            
            # 检测文件扩展名
            _, ext = os.path.splitext(full_path)
            ext = ext.lower()
            
            # 构建执行命令
            if sys.platform.startswith('win'):
                # Windows系统
                if ext in ['.exe', '.bat', '.cmd']:
                    # 直接可执行文件
                    cmd = [full_path]
                elif ext == '.py':
                    # Python脚本
                    cmd = [sys.executable, full_path]
                else:
                    # 尝试使用系统默认程序打开
                    cmd = ['cmd', '/c', 'start', '', full_path]
            else:
                # Linux/Unix系统
                if ext == '.py':
                    cmd = [sys.executable, full_path]
                elif ext == '.sh':
                    cmd = ['bash', full_path]
                else:
                    # 尝试直接执行
                    cmd = [full_path]
            
            # 添加参数
            if args:
                if sys.platform.startswith('win') and cmd[0] == 'cmd':
                    # Windows的start命令需要特殊处理
                    cmd.extend(args.split())
                else:
                    cmd.extend(args.split())
            
            # 执行文件（后台运行，不等待完成）
            process = subprocess.Popen(
                cmd,
                cwd=os.path.dirname(full_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            pid = process.pid
            
            # 等待一小段时间看是否有立即输出或错误
            try:
                stdout, stderr = process.communicate(timeout=1)
                output = stdout if stdout else stderr
            except subprocess.TimeoutExpired:
                # 进程仍在运行
                output = f"进程已启动（PID: {pid}），正在后台运行..."
            
            print(f"  {Colors.GREEN}✓ 文件执行成功 (PID: {pid}){Colors.RESET}")
            
            # 发送响应
            response = create_message(MessageType.FILE_EXECUTE_RESPONSE, {
                'success': True,
                'filepath': filepath,
                'pid': pid,
                'output': output
            })
            send_message(self.client_socket, response)
        
        except Exception as e:
            print(f"  {Colors.RED}✗ 文件执行失败: {e}{Colors.RESET}")
            response = create_message(MessageType.FILE_EXECUTE_RESPONSE, {
                'success': False,
                'error': str(e)
            })
            send_message(self.client_socket, response)
    
    def handle_registry_query(self, hive, key_path, name=None):
        """处理注册表查询请求 (Windows only)"""
        try:
            print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"{Colors.CYAN}{Colors.BOLD}处理注册表查询{Colors.RESET}")
            print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"  根: {hive}, 键: {key_path}, 值名: {name if name else '(全部)'}")

            try:
                import winreg
            except Exception:
                raise Exception('仅在 Windows 系统上支持注册表管理')

            hive_map = {
                'HKLM': winreg.HKEY_LOCAL_MACHINE,
                'HKCU': winreg.HKEY_CURRENT_USER,
                'HKCR': winreg.HKEY_CLASSES_ROOT,
                'HKU': winreg.HKEY_USERS,
                'HKCC': winreg.HKEY_CURRENT_CONFIG
            }

            if hive not in hive_map:
                raise Exception(f'不支持的根: {hive}')

            root = hive_map[hive]
            values = {}
            with winreg.OpenKey(root, key_path, 0, winreg.KEY_READ) as key:
                if name:
                    try:
                        val, vtype = winreg.QueryValueEx(key, name)
                        values[name] = val
                    except FileNotFoundError:
                        values = {}
                else:
                    # 枚举所有值
                    i = 0
                    try:
                        while True:
                            vname, vdata, vtype = winreg.EnumValue(key, i)
                            values[vname] = vdata
                            i += 1
                    except OSError:
                        pass

            response = create_message(MessageType.REGISTRY_RESPONSE, {
                'success': True,
                'values': values
            })
            send_message(self.client_socket, response)

        except Exception as e:
            print(f"  {Colors.RED}✗ 注册表查询失败: {e}{Colors.RESET}")
            response = create_message(MessageType.REGISTRY_RESPONSE, {
                'success': False,
                'error': str(e)
            })
            send_message(self.client_socket, response)

    def handle_registry_set(self, hive, key_path, name, value, value_type='REG_SZ'):
        """处理设置注册表值请求"""
        try:
            print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"{Colors.CYAN}{Colors.BOLD}处理注册表设置{Colors.RESET}")
            print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"  根: {hive}, 键: {key_path}, 名称: {name}, 值: {value}, 类型: {value_type}")

            try:
                import winreg
            except Exception:
                raise Exception('仅在 Windows 系统上支持注册表管理')

            hive_map = {
                'HKLM': winreg.HKEY_LOCAL_MACHINE,
                'HKCU': winreg.HKEY_CURRENT_USER
            }

            if hive not in hive_map:
                raise Exception(f'不支持的根: {hive}')

            root = hive_map[hive]
            # 创建或打开键
            key = winreg.CreateKeyEx(root, key_path, 0, winreg.KEY_WRITE)
            try:
                # 选择值类型
                if value_type == 'REG_DWORD':
                    v = int(value)
                    vt = winreg.REG_DWORD
                else:
                    v = str(value)
                    vt = winreg.REG_SZ

                winreg.SetValueEx(key, name, 0, vt, v)
            finally:
                winreg.CloseKey(key)

            response = create_message(MessageType.REGISTRY_RESPONSE, {
                'success': True
            })
            send_message(self.client_socket, response)

        except Exception as e:
            print(f"  {Colors.RED}✗ 注册表设置失败: {e}{Colors.RESET}")
            response = create_message(MessageType.REGISTRY_RESPONSE, {
                'success': False,
                'error': str(e)
            })
            send_message(self.client_socket, response)

    def handle_registry_delete(self, hive, key_path, name=None):
        """处理删除注册表值或键请求"""
        try:
            print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"{Colors.CYAN}{Colors.BOLD}处理注册表删除{Colors.RESET}")
            print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"  根: {hive}, 键: {key_path}, 名称: {name if name else '(删除键)'}")

            try:
                import winreg
            except Exception:
                raise Exception('仅在 Windows 系统上支持注册表管理')

            hive_map = {
                'HKLM': winreg.HKEY_LOCAL_MACHINE,
                'HKCU': winreg.HKEY_CURRENT_USER
            }

            if hive not in hive_map:
                raise Exception(f'不支持的根: {hive}')

            root = hive_map[hive]
            if name:
                # 删除指定值
                with winreg.OpenKey(root, key_path, 0, winreg.KEY_SET_VALUE) as key:
                    winreg.DeleteValue(key, name)
            else:
                # 删除键 (需要键为空或使用递归删除，这里尝试直接删除)
                winreg.DeleteKey(root, key_path)

            response = create_message(MessageType.REGISTRY_RESPONSE, {
                'success': True
            })
            send_message(self.client_socket, response)

        except Exception as e:
            print(f"  {Colors.RED}✗ 注册表删除失败: {e}{Colors.RESET}")
            response = create_message(MessageType.REGISTRY_RESPONSE, {
                'success': False,
                'error': str(e)
            })
            send_message(self.client_socket, response)

    def handle_mic_record(self, duration=5, samplerate=44100, channels=1):
        """处理麦克风录音请求: 在服务器端录音并通过二进制数据发送回客户端 (WAV)"""
        try:
            print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"{Colors.CYAN}{Colors.BOLD}处理麦克风录音请求{Colors.RESET}")
            print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"  录音时长: {duration}s, 采样率: {samplerate}, 通道: {channels}")

            try:
                from mic import record_audio
            except Exception as e:
                raise Exception(f'无法加载麦克风模块: {e}')

            # 录制 WAV 音频
            audio_bytes = record_audio(duration=duration, samplerate=samplerate, channels=channels)
            ext = 'wav'

            # 发送响应元信息
            response = create_message(MessageType.MIC_RECORD_RESPONSE, {
                'success': True,
                'filename': f'mic_{int(time.time())}.{ext}',
                'size': len(audio_bytes),
                'format': ext
            })
            send_message(self.client_socket, response)

            # 发送二进制音频数据
            send_binary_data(self.client_socket, audio_bytes)

        except Exception as e:
            print(f"  {Colors.RED}✗ 麦克风录音失败: {e}{Colors.RESET}")
            response = create_message(MessageType.MIC_RECORD_RESPONSE, {
                'success': False,
                'error': str(e)
            })
            send_message(self.client_socket, response)
    
    def handle_shell(self, command, working_dir=None):
        """
        处理Shell命令请求（带白名单验证）
        
        Args:
            command: 命令字符串
            working_dir: 工作目录
        """
        try:
            # 进入Shell模式
            if not self.shell_mode:
                self.shell_mode = True
                print(f"  {Colors.GREEN}✓ 进入{SHELL_TYPE}模式 (根目录: {self.shell_root_dir}){Colors.RESET}")
            
            # 处理特殊命令
            if command.strip().lower() in ['exit', 'quit']:
                self.shell_mode = False
                response = create_message(MessageType.SHELL_RESPONSE, {
                    'success': True,
                    'output': '已退出Shell模式',
                    'working_dir': self.shell_working_dir,
                    'returncode': 0
                })
                send_message(self.client_socket, response)
                return
            
            # 处理cd命令（切换目录）
            if command.strip().lower().startswith('cd '):
                target_dir = command.strip()[3:].strip()
                try:
                    if target_dir:
                        # 计算目标目录的绝对路径
                        if target_dir == '/' or target_dir == '\\':
                            # cd / 或 cd \ 返回到Shell根目录
                            new_dir = self.shell_root_dir
                        else:
                            new_dir = os.path.abspath(os.path.join(self.shell_working_dir, target_dir))
                        
                        # 安全检查：目标目录必须在shell_root_dir内
                        if not self.is_safe_shell_path(new_dir):
                            output = f"拒绝访问: 无法离开安全目录 {self.shell_root_dir}"
                            returncode = 1
                        elif not os.path.isdir(new_dir):
                            output = f"目录不存在: {target_dir}"
                            returncode = 1
                        else:
                            self.shell_working_dir = new_dir
                            # 显示相对于根目录的路径
                            rel_path = os.path.relpath(new_dir, self.shell_root_dir)
                            if rel_path == '.':
                                output = f"切换到: / (根目录)"
                            else:
                                output = f"切换到: /{rel_path.replace(os.sep, '/')}"
                            returncode = 0
                    else:
                        # cd 不带参数，显示当前目录
                        rel_path = os.path.relpath(self.shell_working_dir, self.shell_root_dir)
                        if rel_path == '.':
                            output = '/ (根目录)'
                        else:
                            output = f"/{rel_path.replace(os.sep, '/')}"
                        returncode = 0
                    
                    response = create_message(MessageType.SHELL_RESPONSE, {
                        'success': True,
                        'output': output,
                        'working_dir': self.shell_working_dir,
                        'returncode': returncode
                    })
                    send_message(self.client_socket, response)
                    return
                except Exception as e:
                    output = f"cd命令失败: {e}"
                    returncode = 1
                    response = create_message(MessageType.SHELL_RESPONSE, {
                        'success': True,
                        'output': output,
                        'working_dir': self.shell_working_dir,
                        'returncode': returncode
                    })
                    send_message(self.client_socket, response)
                    return
            
            # 验证命令安全性
            if not self.validate_shell_command(command):
                raise ValueError(f"命令未通过安全验证")
            
            print(f"  {Colors.CYAN}执行Shell命令: {command}{Colors.RESET}")
            print(f"  {Colors.CYAN}工作目录: {self.shell_working_dir}{Colors.RESET}")
            
            # 使用工作目录执行命令
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=COMMAND_TIMEOUT,
                cwd=self.shell_working_dir  # 在指定目录执行
            )
            
            output = result.stdout if result.stdout else result.stderr
            
            print(f"  {Colors.GREEN}✓ Shell命令执行完成 (返回码: {result.returncode}){Colors.RESET}")
            
            # 发送响应
            response = create_message(MessageType.SHELL_RESPONSE, {
                'success': True,
                'output': output,
                'working_dir': self.shell_working_dir,
                'returncode': result.returncode
            })
            send_message(self.client_socket, response)
        
        except subprocess.TimeoutExpired:
            print(f"  {Colors.RED}✗ Shell命令执行超时{Colors.RESET}")
            response = create_message(MessageType.SHELL_RESPONSE, {
                'success': False,
                'error': f'命令执行超时 (>{COMMAND_TIMEOUT}秒)',
                'working_dir': self.shell_working_dir
            })
            send_message(self.client_socket, response)
        
        except Exception as e:
            print(f"  {Colors.RED}✗ Shell命令执行失败: {e}{Colors.RESET}")
            response = create_message(MessageType.SHELL_RESPONSE, {
                'success': False,
                'error': str(e),
                'working_dir': self.shell_working_dir
            })
            send_message(self.client_socket, response)
    
    def is_safe_shell_path(self, path):
        """
        检查路径是否在Shell根目录内（防止目录遍历）
        
        Args:
            path: 待检查的路径
        
        Returns:
            bool: 路径是否安全
        """
        try:
            # 解析为绝对路径
            abs_path = os.path.abspath(path)
            abs_root = os.path.abspath(self.shell_root_dir)
            
            # 检查路径是否以根目录开头
            return os.path.commonpath([abs_root, abs_path]) == abs_root
        except (ValueError, TypeError):
            return False
    
    def validate_shell_command(self, command):
        """
        验证Shell命令是否符合安全策略
        
        Args:
            command: 命令字符串
        
        Returns:
            bool: 命令是否合法
        """
        # 分割命令（处理操作符）
        import re
        # 移除操作符后分割成命令列表
        parts = re.split(r'[&|;<>]+', command)
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # 提取主命令名
            cmd_parts = part.split()
            if not cmd_parts:
                continue
            
            cmd_name = cmd_parts[0].lower()
            
            # 检查是否在白名单中
            if cmd_name not in ALLOWED_COMMANDS:
                print(f"  {Colors.RED}✗ 命令不在{SHELL_TYPE}白名单中: {cmd_name}{Colors.RESET}")
                print(f"  {Colors.YELLOW}允许的命令: {', '.join(ALLOWED_COMMANDS[:10])}...(共{len(ALLOWED_COMMANDS)}个){Colors.RESET}")
                return False
        
        return True
    
    def handle_system_info(self):
        """处理系统信息请求"""
        try:
            print(f"  {Colors. CYAN}获取系统信息...{Colors.RESET}")
            
            info = get_system_info()
            
            print(f"  {Colors.GREEN}✓ 系统信息获取成功{Colors.RESET}")
            
            # 发送响应
            response = create_message(MessageType.SYSTEM_INFO_RESPONSE, {
                'success': True,
                'info': info
            })
            send_message(self.client_socket, response)
        
        except Exception as e:
            print(f"  {Colors.RED}✗ 获取系统信息失败: {e}{Colors.RESET}")
            response = create_message(MessageType. SYSTEM_INFO_RESPONSE, {
                'success': False,
                'error': str(e)
            })
            send_message(self.client_socket, response)
    
    def display_controlled_status(self, is_controlled):
        """
        显示受控状态指示
        
        Args:
            is_controlled: 是否处于受控状态
        """
        if is_controlled:
            print(f"\n{Colors.RED}{Colors.BOLD}{'='*60}{Colors.RESET}")
            print(f"{Colors.RED}{Colors.BOLD}{'  ⚠️  系统正在被远程控制  ⚠️':^70}{Colors.RESET}")
            print(f"{Colors.RED}{Colors.BOLD}{'='*60}{Colors.RESET}")
            print(f"{Colors.YELLOW}  控制者IP: {self.client_address[0]}{Colors.RESET}")
            print(f"{Colors. YELLOW}  连接时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
            print(f"{Colors.RED}{Colors.BOLD}{'='*60}{Colors.RESET}\n")
        else:
            print(f"\n{Colors. GREEN}{'='*60}{Colors. RESET}")
            print(f"{Colors.GREEN}{'  ✓ 远程控制已结束':^70}{Colors.RESET}")
            print(f"{Colors. GREEN}{'='*60}{Colors.RESET}\n")


def main():
    """主函数"""
    # 创建并启动服务器
    server = RemoteControlServer()
    
    try:
        server.start()
    except KeyboardInterrupt:
        print(f"\n{Colors. YELLOW}程序被用户中断{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}程序异常: {e}{Colors.RESET}")


if __name__ == '__main__':
    main()