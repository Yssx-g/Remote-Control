"""
客户端主程序 - 远程控制系统（控制器A）
实现客户端的所有功能
"""

import socket
import os
import sys
import getpass
import time
from datetime import datetime

# 导入自定义模块
from config import *
from protocol import *
from utils import *


class RemoteControlClient:
    """远程控制客户端类"""
    
    def __init__(self, server_ip, server_port=SERVER_PORT):
        """
        初始化客户端
        
        Args:
            server_ip: 服务器IP地址
            server_port: 服务器端口
        """
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_socket = None
        self.is_connected = False
        self.is_authenticated = False
        
        print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}{'  远程控制系统 - 客户端 (控制器A)':^60}{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"{Colors.YELLOW}⚠️  注意: 本程序仅用于教育学习目的{Colors.RESET}")
        print(f"{Colors.YELLOW}⚠️  仅在本地网络或虚拟机环境中运行{Colors.RESET}")
        print(f"{Colors. CYAN}{'='*60}{Colors. RESET}\n")
    
    def connect(self):
        """连接到服务器"""
        try:
            print(f"{Colors.CYAN}正在连接到服务器 {self.server_ip}:{self.server_port}...{Colors.RESET}")
            
            # 创建套接字
            self.client_socket = socket.socket(socket. AF_INET, socket. SOCK_STREAM)
            self.client_socket.settimeout(CONNECTION_TIMEOUT)
            
            # 连接到服务器
            self.client_socket.connect((self.server_ip, self.server_port))
            self.is_connected = True
            
            print(f"{Colors. GREEN}✓ 连接成功! {Colors.RESET}\n")
            
            # 进行身份验证
            if self.authenticate():
                print(f"{Colors.GREEN}✓ 身份验证成功! {Colors.RESET}\n")
                self.is_authenticated = True
                return True
            else:
                print(f"{Colors.RED}✗ 身份验证失败!{Colors.RESET}")
                self.disconnect()
                return False
        
        except socket.timeout:
            print(f"{Colors.RED}✗ 连接超时{Colors.RESET}")
            return False
        except ConnectionRefusedError:
            print(f"{Colors.RED}✗ 连接被拒绝, 请确认服务器已启动{Colors.RESET}")
            return False
        except Exception as e:
            print(f"{Colors.RED}✗ 连接失败: {e}{Colors.RESET}")
            return False
    
    def authenticate(self):
        """
        身份验证
        
        Returns:
            bool: 验证是否成功
        """
        try:
            # 输入密码
            password = getpass. getpass(f"{Colors. BOLD}请输入密码: {Colors.RESET}")
            
            # 计算密码哈希
            password_hash = hash_password(password)
            
            # 发送验证请求
            auth_msg = create_auth_message(password_hash)
            send_message(self.client_socket, auth_msg)
            
            # 接收验证响应
            response = receive_message(self.client_socket)
            
            if response and response['type'] == MessageType.AUTH_RESPONSE:
                return response['data']['success']
            
            return False
        
        except Exception as e:
            print(f"{Colors.RED}✗ 身份验证错误: {e}{Colors. RESET}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.is_connected:
            try:
                # 发送断开连接消息
                disconnect_msg = create_disconnect_message()
                send_message(self.client_socket, disconnect_msg)
            except:
                pass
            
            self.client_socket.close()
            self.is_connected = False
            self.is_authenticated = False
            print(f"\n{Colors.GREEN}✓ 已断开连接{Colors. RESET}")
    
    def show_menu(self):
        """显示操作菜单"""
        print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}{'  操作菜单':^60}{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}  1. {Colors.RESET} 📸 远程截屏")
        print(f"{Colors.BOLD}  2. {Colors.RESET} 📷 摄像头功能")
        print(f"{Colors.BOLD}  3. {Colors.RESET} 📂 文件下载")
        print(f"{Colors.BOLD}  4. {Colors.RESET} 💻 系统信息")
        print(f"{Colors.BOLD}  5. {Colors.RESET} 🐚 交互式{SHELL_TYPE} (完整功能)")
        print(f"{Colors.BOLD}  6. {Colors.RESET} 🚺 断开连接")
        print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
    
    def run(self):
        """运行客户端主循环"""
        # 连接到服务器
        if not self.connect():
            return
        
        # 主操作循环
        while self. is_authenticated:
            try:
                self.show_menu()
                choice = input(f"\n{Colors.BOLD}请选择操作 (1-6): {Colors.RESET}").strip()
                
                if choice == '1':
                    self.request_screenshot()
                elif choice == '2':
                    self.camera_menu()
                elif choice == '3':
                    self.request_file_download()
                elif choice == '4':
                    self.request_system_info()
                elif choice == '5':
                    self.enter_shell_mode()
                elif choice == '6':
                    print(f"\n{Colors.YELLOW}正在断开连接...{Colors.RESET}")
                    break
                else:
                    print(f"{Colors.RED}✗ 无效的选择, 请重新输入{Colors.RESET}")
            
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}操作被用户中断{Colors.RESET}")
                break
            except Exception as e:
                print(f"{Colors.RED}✗ 操作失败: {e}{Colors.RESET}")
        
        # 断开连接
        self.disconnect()
    
    def request_screenshot(self):
        """请求远程截屏"""
        try:
            print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"{Colors.CYAN}{Colors.BOLD}  远程截屏{Colors.RESET}")
            print(f"{Colors.CYAN}{'='*60}{Colors. RESET}")
            
            # 发送截图请求
            msg = create_screenshot_message()
            send_message(self.client_socket, msg)
            
            print(f"{Colors. CYAN}正在请求截图...{Colors.RESET}")
            
            # 接收响应
            response = receive_message(self.client_socket)
            
            if response and response['type'] == MessageType.SCREENSHOT_DATA:
                if response['data']['success']:
                    # 接收截图数据
                    img_data = receive_binary_data(self.client_socket)
                    
                    if img_data:
                        # 保存截图
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"screenshot_{timestamp}.jpg"
                        filepath = os.path.join(SCREENSHOT_DIRECTORY, filename)
                        
                        if write_file_binary(filepath, img_data):
                            print(f"{Colors.GREEN}✓ 截图成功!{Colors. RESET}")
                            print(f"  文件大小: {format_file_size(len(img_data))}")
                            print(f"  保存位置: {filepath}")
                        else:
                            print(f"{Colors.RED}✗ 保存截图失败{Colors.RESET}")
                    else:
                        print(f"{Colors.RED}✗ 接收截图数据失败{Colors. RESET}")
                else:
                    error = response['data']. get('error', '未知错误')
                    print(f"{Colors.RED}✗ 截图失败: {error}{Colors. RESET}")
        
        except Exception as e:
            print(f"{Colors.RED}✗ 截图请求失败: {e}{Colors.RESET}")
    
    def show_camera_menu(self):
        """显示摄像头子菜单"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}{'  📷 摄像头功能菜单':^60}{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}  1. {Colors.RESET} 📸 拍照")
        print(f"{Colors.BOLD}  2. {Colors.RESET} 📹 实时视频预览")
        print(f"{Colors.BOLD}  3. {Colors.RESET} 🎥 开始/停止录像")
        print(f"{Colors.BOLD}  0. {Colors.RESET} ⬅️  返回主菜单")
        print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
    
    def camera_menu(self):
        """摄像头功能子菜单"""
        while True:
            try:
                self.show_camera_menu()
                choice = input(f"\n{Colors.BOLD}请选择功能 (0-3): {Colors.RESET}").strip()
                
                if choice == '1':
                    self.request_camera()
                elif choice == '2':
                    self.video_preview()
                elif choice == '3':
                    self.video_record_menu()
                elif choice == '0':
                    print(f"{Colors.CYAN}← 返回主菜单{Colors.RESET}")
                    break
                else:
                    print(f"{Colors.RED}✗ 无效的选择,请重新输入{Colors.RESET}")
            
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}← 返回主菜单{Colors.RESET}")
                break
            except Exception as e:
                print(f"{Colors.RED}✗ 操作失败: {e}{Colors.RESET}")
    
    def request_camera(self):
        """请求摄像头拍照"""
        try:
            print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"{Colors.CYAN}{Colors.BOLD}  摄像头拍照{Colors.RESET}")
            print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
            
            # 发送摄像头请求
            msg = create_camera_message()
            send_message(self.client_socket, msg)
            
            print(f"{Colors.CYAN}正在启动摄像头...{Colors.RESET}")
            
            # 接收响应
            response = receive_message(self.client_socket)
            
            if response and response['type'] == MessageType.CAMERA_DATA:
                if response['data']['success']:
                    # 接收摄像头数据
                    img_data = receive_binary_data(self.client_socket)
                    
                    if img_data:
                        # 保存到camera目录
                        filename = response['data'].get('filename', f"camera_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
                        filepath = os.path.join(CAMERA_DIRECTORY, filename)
                        
                        if write_file_binary(filepath, img_data):
                            print(f"{Colors.GREEN}✓ 摄像头拍照成功!{Colors.RESET}")
                            print(f"  文件大小: {format_file_size(len(img_data))}")
                            print(f"  保存位置: {filepath}")
                        else:
                            print(f"{Colors.RED}✗ 保存照片失败{Colors.RESET}")
                    else:
                        print(f"{Colors.RED}✗ 接收照片数据失败{Colors.RESET}")
                else:
                    error = response['data'].get('error', '未知错误')
                    print(f"{Colors.RED}✗ 摄像头拍照失败: {error}{Colors.RESET}")
        
        except Exception as e:
            print(f"{Colors.RED}✗ 摄像头请求失败: {e}{Colors.RESET}")
    
    def video_preview(self):
        """实时视频预览"""
        try:
            print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"{Colors.CYAN}{Colors.BOLD}  实时视频预览{Colors.RESET}")
            print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
            
            # 获取视频参数
            print(f"\n{Colors.YELLOW}视频参数设置 (直接回车使用默认值):{Colors.RESET}")
            width = input(f"  宽度 [640]: ").strip() or "640"
            height = input(f"  高度 [480]: ").strip() or "480"
            fps = input(f"  帧率 [30]: ").strip() or "30"
            quality = input(f"  质量 1-100 [85]: ").strip() or "85"
            
            try:
                width = int(width)
                height = int(height)
                fps = int(fps)
                quality = int(quality)
            except:
                print(f"{Colors.RED}✗ 参数格式错误{Colors.RESET}")
                return
            
            # 发送开始视频流请求
            msg = create_video_start_message(width, height, fps, quality)
            send_message(self.client_socket, msg)
            
            print(f"\n{Colors.CYAN}正在启动视频流...{Colors.RESET}")
            
            # 接收响应
            response = receive_message(self.client_socket)
            
            if not response or response['type'] != MessageType.VIDEO_START:
                print(f"{Colors.RED}✗ 启动视频流失败{Colors.RESET}")
                return
            
            if not response['data']['success']:
                error = response['data'].get('error', '未知错误')
                print(f"{Colors.RED}✗ 启动视频流失败: {error}{Colors.RESET}")
                return
            
            print(f"{Colors.GREEN}✓ 视频流已启动{Colors.RESET}")
            print(f"{Colors.YELLOW}提示: 按 Ctrl+C 停止预览{Colors.RESET}\n")
            
            # 导入opencv显示视频
            try:
                import cv2
                import numpy as np
            except ImportError:
                print(f"{Colors.RED}✗ 未安装opencv-python,无法显示视频{Colors.RESET}")
                print(f"{Colors.YELLOW}正在接收视频帧但不显示...{Colors.RESET}")
                cv2 = None
            
            frame_count = 0
            start_time = time.time()
            
            error_count = 0
            max_errors = 5
            
            try:
                while True:
                    # 接收视频帧
                    frame_msg = receive_message(self.client_socket)
                    
                    if not frame_msg:
                        error_count += 1
                        if error_count >= max_errors:
                            print(f"{Colors.RED}✗ 连接断开{Colors.RESET}")
                            break
                        time.sleep(0.1)
                        continue
                    
                    # 检查消息类型
                    if frame_msg['type'] != MessageType.VIDEO_FRAME:
                        # 如果是ERROR或DISCONNECT消息,退出
                        if frame_msg['type'] in [MessageType.ERROR, MessageType.DISCONNECT]:
                            break
                        continue  # 其他消息,继续等待视频帧
                    
                    frame_data = receive_binary_data(self.client_socket)
                    
                    if not frame_data:
                        error_count += 1
                        if error_count >= max_errors:
                            print(f"{Colors.RED}✗ 接收失败{Colors.RESET}")
                            break
                        time.sleep(0.1)
                        continue
                    
                    frame_count += 1
                    error_count = 0  # 成功接收,重置错误计数
                    
                    # 显示视频帧
                    if cv2:
                        # 解码JPEG
                        nparr = np.frombuffer(frame_data, np.uint8)
                        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        
                        if frame is not None:
                            # 添加帧信息
                            elapsed = time.time() - start_time
                            actual_fps = frame_count / elapsed if elapsed > 0 else 0
                            cv2.putText(frame, f"FPS: {actual_fps:.1f}", (10, 30),
                                      cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                            cv2.putText(frame, f"Frame: {frame_count}", (10, 70),
                                      cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                            cv2.putText(frame, "Press 'q' to quit", (10, 110),
                                      cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                            
                            cv2.imshow('Remote Camera', frame)
                            
                            # 检查退出
                            if cv2.waitKey(1) & 0xFF == ord('q'):
                                break
                    else:
                        # 不显示,只打印统计
                        if frame_count % 30 == 0:
                            elapsed = time.time() - start_time
                            actual_fps = frame_count / elapsed if elapsed > 0 else 0
                            print(f"  接收帧数: {frame_count}, FPS: {actual_fps:.1f}")
            
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}停止预览...{Colors.RESET}")
            
            finally:
                if cv2:
                    cv2.destroyAllWindows()
                
                # 发送停止视频流请求
                msg = create_video_stop_message()
                send_message(self.client_socket, msg)
                
                # 接收停止响应
                response = receive_message(self.client_socket)
                
                # 清空socket缓冲区中可能残留的视频帧数据
                self.client_socket.settimeout(0.5)  # 设置500ms超时
                try:
                    while True:
                        # 尝试接收并丢弃残留数据
                        leftover = self.client_socket.recv(4096)
                        if not leftover:
                            break
                except:
                    pass  # 超时或没有更多数据,正常
                finally:
                    self.client_socket.settimeout(None)  # 恢复阻塞模式
                
                elapsed = time.time() - start_time
                actual_fps = frame_count / elapsed if elapsed > 0 else 0
                print(f"\n{Colors.GREEN}✓ 视频流已停止{Colors.RESET}")
                print(f"  总帧数: {frame_count}")
                print(f"  总时长: {elapsed:.1f}秒")
                print(f"  平均FPS: {actual_fps:.1f}")
        
        except Exception as e:
            print(f"{Colors.RED}✗ 视频预览失败: {e}{Colors.RESET}")
            import traceback
            traceback.print_exc()
    
    def video_record_menu(self):
        """录像管理菜单"""
        try:
            print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"{Colors.CYAN}{Colors.BOLD}  录像管理{Colors.RESET}")
            print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"{Colors.YELLOW}ℹ️  提示: 视频流将自动启动/关闭{Colors.RESET}")
            print(f"{Colors.BOLD}  1. {Colors.RESET} 🔴 开始录像 (自动启动视频流)")
            print(f"{Colors.BOLD}  2. {Colors.RESET} ⏹️  停止录像 (自动关闭视频流)")
            print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
            
            choice = input(f"\n{Colors.BOLD}请选择 (1-2): {Colors.RESET}").strip()
            
            if choice == '1':
                # 开始录像
                filename = input(f"{Colors.BOLD}录像文件名 (留空自动生成): {Colors.RESET}").strip() or None
                
                msg = create_record_start_message(filename)
                send_message(self.client_socket, msg)
                
                print(f"{Colors.CYAN}正在开始录像...{Colors.RESET}")
                
                response = receive_message(self.client_socket)
                
                if response and response['type'] == MessageType.RECORD_STATUS:
                    if response['data']['success']:
                        filepath = response['data'].get('filepath', '')
                        auto_started = response['data'].get('auto_started', False)
                        print(f"{Colors.GREEN}✓ 录像已开始{Colors.RESET}")
                        if auto_started:
                            print(f"  {Colors.CYAN}ℹ️  视频流已自动启动{Colors.RESET}")
                        print(f"  保存位置: {filepath}")
                    else:
                        error = response['data'].get('error', '未知错误')
                        print(f"{Colors.RED}✗ 开始录像失败: {error}{Colors.RESET}")
            
            elif choice == '2':
                # 停止录像
                msg = create_record_stop_message()
                send_message(self.client_socket, msg)
                
                print(f"{Colors.CYAN}正在停止录像...{Colors.RESET}")
                
                response = receive_message(self.client_socket)
                
                if response and response['type'] == MessageType.RECORD_STATUS:
                    if response['data']['success']:
                        message = response['data'].get('message', '')
                        auto_stopped = response['data'].get('auto_stopped', False)
                        print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")
                        if auto_stopped:
                            print(f"  {Colors.CYAN}ℹ️  视频流已自动关闭{Colors.RESET}")
                    else:
                        error = response['data'].get('error', '未知错误')
                        print(f"{Colors.RED}✗ 停止录像失败: {error}{Colors.RESET}")
        
        except Exception as e:
            print(f"{Colors.RED}✗ 录像操作失败: {e}{Colors.RESET}")
    
    def request_file_download(self):
        """请求文件下载"""
        try:
            print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"{Colors.CYAN}{Colors.BOLD}  文件下载{Colors.RESET}")
            print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
            
            filepath = input(f"{Colors. BOLD}请输入要下载的文件路径: {Colors.RESET}").strip()
            
            if not filepath:
                print(f"{Colors.RED}✗ 文件路径不能为空{Colors.RESET}")
                return
            
            # 发送文件下载请求
            msg = create_file_download_message(filepath)
            send_message(self.client_socket, msg)
            
            print(f"{Colors.CYAN}正在下载文件...{Colors. RESET}")
            
            # 接收响应
            response = receive_message(self.client_socket)
            
            if response and response['type'] == MessageType.FILE_DATA:
                if response['data']['success']:
                    # 接收文件数据
                    file_data = receive_binary_data(self.client_socket)
                    
                    if file_data:
                        # 保存文件到Download目录
                        filename = response['data']['filename']
                        save_path = os.path.join(DOWNLOAD_DIRECTORY, filename)
                        
                        if write_file_binary(save_path, file_data):
                            print(f"{Colors.GREEN}✓ 文件下载成功!{Colors.RESET}")
                            print(f"  文件名: {filename}")
                            print(f"  文件大小: {format_file_size(len(file_data))}")
                            print(f"  保存位置: {save_path}")
                        else:
                            print(f"{Colors.RED}✗ 保存文件失败{Colors.RESET}")
                    else:
                        print(f"{Colors.RED}✗ 接收文件数据失败{Colors.RESET}")
                else:
                    error = response['data'].get('error', '未知错误')
                    print(f"{Colors.RED}✗ 文件下载失败: {error}{Colors. RESET}")
        
        except Exception as e:
            print(f"{Colors.RED}✗ 文件下载请求失败: {e}{Colors. RESET}")
    
    def enter_shell_mode(self):
        """进入交互式Shell模式"""
        try:
            print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"{Colors.CYAN}{Colors.BOLD}  交互式{SHELL_TYPE}模式 (沙箱保护){Colors.RESET}")
            print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"{Colors.RED}🔒 安全限制: Shell根目录锁定在 safe_files/ 目录内{Colors.RESET}")
            print(f"{Colors.RED}🔒 无法访问 safe_files/ 以外的任何目录{Colors.RESET}")
            print(f"{Colors.YELLOW}⚠️  命令受{SHELL_TYPE}白名单保护, 共{len(ALLOWED_COMMANDS)}个安全命令{Colors.RESET}")
            print(f"{Colors.GREEN}支持的功能: cd切换目录, 命令组合(&&, ||, |){Colors.RESET}")
            print(f"{Colors.CYAN}提示: cd / 返回根目录(safe_files), cd .. 返回上级{Colors.RESET}")
            print(f"{Colors.MAGENTA}输入 'help' 查看完整命令列表, 'exit' 退出Shell模式{Colors.RESET}")
            print(f"{Colors.CYAN}{'='*60}{Colors.RESET}\n")
            
            current_dir = None
            
            # Shell交互循环
            while True:
                try:
                    # 显示提示符
                    if current_dir:
                        prompt = f"{Colors.GREEN}{current_dir}{Colors.RESET} $ "
                    else:
                        prompt = f"{Colors.GREEN}remote{Colors.RESET} $ "
                    
                    command = input(prompt).strip()
                    
                    if not command:
                        continue
                    
                    # 本地help命令
                    if command.lower() == 'help':
                        self.show_shell_help()
                        continue
                    
                    # 退出Shell模式
                    if command.lower() in ['exit', 'quit']:
                        msg = create_shell_exit_message()
                        send_message(self.client_socket, msg)
                        print(f"{Colors.GREEN}✓ 已退出Shell模式{Colors.RESET}")
                        break
                    
                    # 发送Shell命令
                    msg = create_shell_message(command, current_dir)
                    send_message(self.client_socket, msg)
                    
                    # 接收响应
                    response = receive_message(self.client_socket)
                    
                    if response and response['type'] == MessageType.SHELL_RESPONSE:
                        if response['data']['success']:
                            output = response['data']['output']
                            current_dir = response['data'].get('working_dir', current_dir)
                            returncode = response['data'].get('returncode', 0)
                            
                            # 显示输出
                            if output:
                                print(output)
                            
                            # 如果返回码非0，显示警告
                            if returncode != 0:
                                print(f"{Colors.YELLOW}(返回码: {returncode}){Colors.RESET}")
                        else:
                            error = response['data'].get('error', '未知错误')
                            print(f"{Colors.RED}✗ 错误: {error}{Colors.RESET}")
                            current_dir = response['data'].get('working_dir', current_dir)
                
                except KeyboardInterrupt:
                    print(f"\n{Colors.YELLOW}使用 'exit' 命令退出Shell模式{Colors.RESET}")
                    continue
                except Exception as e:
                    print(f"{Colors.RED}✗ Shell命令执行失败: {e}{Colors.RESET}")
        
        except Exception as e:
            print(f"{Colors.RED}✗ 进入Shell模式失败: {e}{Colors.RESET}")
    
    def show_shell_help(self):
        """显示Shell命令帮助"""
        print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}  {SHELL_TYPE} 命令列表{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
        
        if SHELL_TYPE == 'WindowsShell':
            print(f"\n{Colors.BOLD}基础信息命令:{Colors.RESET}")
            print("  echo      - 回显文本")
            print("  dir       - 列出文件和目录")
            print("  cd        - 切换目录")
            print("  cls       - 清屏")
            print("  type      - 显示文件内容")
            print("  more      - 分页显示文件")
            print("  whoami    - 显示当前用户")
            print("  hostname  - 显示主机名")
            print("  ver       - 显示Windows版本")
            
            print(f"\n{Colors.BOLD}文件操作命令:{Colors.RESET}")
            print("  copy      - 复制文件 (仅在沙箱内)")
            print("  move      - 移动/重命名文件")
            print("  ren       - 重命名文件")
            print("  del       - 删除文件 (仅在沙箱内)")
            print("  mkdir     - 创建目录")
            print("  rmdir     - 删除目录 (仅在沙箱内)")
            
            print(f"\n{Colors.BOLD}文件查看和搜索:{Colors.RESET}")
            print("  find      - 搜索文本")
            print("  findstr   - 搜索文本 (正则)")
            print("  tree      - 显示目录树")
            print("  attrib    - 显示/修改文件属性")
            
        else:  # LinuxShell
            print(f"\n{Colors.BOLD}基础信息命令:{Colors.RESET}")
            print("  echo      - 回显文本")
            print("  ls        - 列出文件和目录")
            print("  cd        - 切换目录")
            print("  clear     - 清屏")
            print("  cat       - 显示文件内容")
            print("  less      - 分页显示文件")
            print("  more      - 分页显示文件")
            print("  head      - 显示文件开头")
            print("  tail      - 显示文件结尾")
            print("  pwd       - 显示当前目录")
            print("  whoami    - 显示当前用户")
            print("  hostname  - 显示主机名")
            print("  uname     - 显示系统信息")
            
            print(f"\n{Colors.BOLD}文件操作命令:{Colors.RESET}")
            print("  cp        - 复制文件 (仅在沙箱内)")
            print("  mv        - 移动/重命名文件")
            print("  rm        - 删除文件 (仅在沙箱内)")
            print("  mkdir     - 创建目录")
            print("  rmdir     - 删除空目录")
            print("  touch     - 创建空文件/更新时间戳")
            
            print(f"\n{Colors.BOLD}文件查看和搜索:{Colors.RESET}")
            print("  grep      - 搜索文本")
            print("  find      - 查找文件")
            print("  wc        - 统计行数/字数")
            print("  tree      - 显示目录树")
            print("  stat      - 显示文件状态")
            print("  file      - 识别文件类型")
            
            print(f"\n{Colors.BOLD}文件权限:{Colors.RESET}")
            print("  chmod     - 修改权限")
            print("  chown     - 修改所有者")
        
        print(f"\n{Colors.YELLOW}命令组合:{Colors.RESET}")
        print("  &&        - 顺序执行 (前一个成功才执行下一个)")
        print("  ||        - 或执行 (前一个失败才执行下一个)")
        print("  |         - 管道 (传递输出)")
        print("  >         - 重定向输出到文件")
        print("  >>        - 追加输出到文件")
        
        print(f"\n{Colors.RED}安全限制:{Colors.RESET}")
        print("  • 所有操作限制在 safe_files/ 目录内")
        print("  • 无法访问系统敏感目录")
        print("  • 所有命令受白名单保护")
        print(f"  • 总共允许 {len(ALLOWED_COMMANDS)} 个命令")
        
        print(f"\n{Colors.CYAN}特殊命令:{Colors.RESET}")
        print("  help      - 显示此帮助信息")
        print("  exit/quit - 退出Shell模式")
        print(f"{Colors.CYAN}{'='*60}{Colors.RESET}\n")
    
    def request_system_info(self):
        """请求系统信息"""
        try:
            print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"{Colors.CYAN}{Colors.BOLD}  系统信息{Colors.RESET}")
            print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
            
            # 发送系统信息请求
            msg = create_system_info_message()
            send_message(self.client_socket, msg)
            
            print(f"{Colors.CYAN}正在获取系统信息...{Colors.RESET}")
            
            # 接收响应
            response = receive_message(self. client_socket)
            
            if response and response['type'] == MessageType.SYSTEM_INFO_RESPONSE:
                if response['data']['success']:
                    info = response['data']['info']
                    
                    print(f"\n{Colors.GREEN}✓ 系统信息:{Colors.RESET}\n")
                    print(f"{Colors. BOLD}{'项目':<20} {'值':<40}{Colors.RESET}")
                    print(f"{'-'*60}")
                    print(f"{'操作系统':<20} {info. get('os', 'N/A'):<40}")
                    print(f"{'系统版本':<20} {info. get('os_release', 'N/A'):<40}")
                    print(f"{'架构':<20} {info.get('architecture', 'N/A'):<40}")
                    print(f"{'处理器':<20} {info.get('processor', 'N/A'):<40}")
                    print(f"{'主机名':<20} {info.get('hostname', 'N/A'):<40}")
                    print(f"{'IP地址':<20} {info.get('ip_address', 'N/A'):<40}")
                    print(f"{'Python版本':<20} {info.get('python_version', 'N/A'):<40}")
                    print(f"{'在线状态':<20} {'在线' if info.get('online') else '离线':<40}")
                else:
                    error = response['data'].get('error', '未知错误')
                    print(f"{Colors.RED}✗ 获取系统信息失败: {error}{Colors.RESET}")
        
        except Exception as e:
            print(f"{Colors.RED}✗ 系统信息请求失败: {e}{Colors.RESET}")


def main():
    """主函数"""
    # 检查命令行参数
    if len(sys.argv) < 2:
        print(f"{Colors.RED}用法: python client.py <服务器IP>{Colors.RESET}")
        print(f"{Colors. YELLOW}示例: python client. py 127.0.0.1{Colors.RESET}")
        sys. exit(1)
    
    server_ip = sys.argv[1]
    
    # 创建并运行客户端
    client = RemoteControlClient(server_ip)
    
    try:
        client.run()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}程序被用户中断{Colors.RESET}")
        client.disconnect()
    except Exception as e:
        print(f"\n{Colors.RED}程序异常: {e}{Colors.RESET}")


if __name__ == '__main__':
    main()