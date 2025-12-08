"""
视频流模块 - 远程控制系统
支持实时视频传输和录像功能
"""

import cv2
import threading
import time
import queue
import base64
from datetime import datetime
import os


class VideoStream:
    """视频流处理类"""
    
    def __init__(self, camera_index=0, width=640, height=480, fps=30):
        """
        初始化视频流
        
        Args:
            camera_index: 摄像头索引 (0=默认摄像头)
            width: 视频宽度
            height: 视频高度
            fps: 帧率
        """
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.fps = fps
        self.cap = None
        self.is_streaming = False
        self.frame_queue = queue.Queue(maxsize=10)
        self.stream_thread = None
        self.recording = False
        self.video_writer = None
        self.record_filepath = None
        
    def start(self):
        """启动视频流"""
        if self.is_streaming:
            return True, "视频流已在运行"
        
        try:
            # 打开摄像头
            self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                return False, "无法打开摄像头"
            
            # 设置摄像头参数
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            
            # 预热摄像头
            for i in range(5):
                ret, frame = self.cap.read()
                if not ret:
                    return False, f"预热失败: 无法读取帧 {i+1}/5"
            
            self.is_streaming = True
            
            # 启动捕获线程
            self.stream_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.stream_thread.start()
            
            # 等待一下确保线程启动
            time.sleep(0.1)
            
            return True, "视频流启动成功"
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"视频流启动失败: {e}"
    
    def stop(self):
        """停止视频流"""
        self.is_streaming = False
        
        # 停止录像
        if self.recording:
            self.stop_recording()
        
        # 等待线程结束
        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=2)
        
        # 释放摄像头
        if self.cap:
            self.cap.release()
            self.cap = None
        
        # 清空队列
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break
        
        return True, "视频流已停止"
    
    def _capture_loop(self):
        """视频捕获循环 (在独立线程中运行)"""
        print(f"[VideoStream] 捕获线程已启动")
        frame_interval = 1.0 / self.fps
        captured_count = 0
        
        while self.is_streaming:
            start_time = time.time()
            
            try:
                ret, frame = self.cap.read()
                
                if not ret or frame is None:
                    continue
                
                captured_count += 1
                
                # 如果正在录像,写入文件
                if self.recording and self.video_writer:
                    try:
                        self.video_writer.write(frame)
                    except Exception as e:
                        print(f"写入视频帧失败: {e}")
                        self.recording = False  # 停止录像标记
                
                # 将帧放入队列
                if self.frame_queue.full():
                    try:
                        self.frame_queue.get_nowait()  # 丢弃旧帧
                    except queue.Empty:
                        pass
                
                self.frame_queue.put(frame)
                
                # 控制帧率
                elapsed = time.time() - start_time
                sleep_time = max(0, frame_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            except Exception as e:
                print(f"捕获帧时出错: {e}")
                time.sleep(0.1)
    
    def get_frame(self, timeout=1.0):
        """
        获取最新的视频帧
        
        Args:
            timeout: 超时时间(秒)
        
        Returns:
            tuple: (success, frame) 或 (success, error_message)
        """
        if not self.is_streaming:
            return False, "视频流未启动"
        
        try:
            frame = self.frame_queue.get(timeout=timeout)
            return True, frame
        except queue.Empty:
            return False, "获取帧超时"
    
    def get_frame_jpeg(self, quality=85):
        """
        获取JPEG编码的视频帧
        
        Args:
            quality: JPEG质量 (1-100)
        
        Returns:
            tuple: (success, jpeg_data) 或 (success, error_message)
        """
        success, result = self.get_frame()
        
        if not success:
            return False, result
        
        try:
            # 编码为JPEG
            encode_param = [cv2.IMWRITE_JPEG_QUALITY, quality]
            success, buffer = cv2.imencode('.jpg', result, encode_param)
            
            if not success:
                return False, "JPEG编码失败"
            
            return True, buffer.tobytes()
        
        except Exception as e:
            return False, f"编码失败: {e}"
    
    def get_frame_base64(self, quality=85):
        """
        获取Base64编码的JPEG帧
        
        Args:
            quality: JPEG质量
        
        Returns:
            tuple: (success, base64_string) 或 (success, error_message)
        """
        success, jpeg_data = self.get_frame_jpeg(quality)
        
        if not success:
            return False, jpeg_data
        
        try:
            base64_str = base64.b64encode(jpeg_data).decode('utf-8')
            return True, base64_str
        except Exception as e:
            return False, f"Base64编码失败: {e}"
    
    def start_recording(self, output_dir='camera', filename=None):
        """
        开始录像
        
        Args:
            output_dir: 输出目录
            filename: 文件名 (None=自动生成)
        
        Returns:
            tuple: (success, message/filepath)
        """
        if self.recording:
            return False, "已在录像中"
        
        if not self.is_streaming:
            return False, "视频流未启动"
        
        try:
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成文件名
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"video_{timestamp}.mp4"
            
            self.record_filepath = os.path.join(output_dir, filename)
            
            # 确保文件名有.mp4扩展名
            if not self.record_filepath.endswith('.mp4'):
                self.record_filepath += '.mp4'
            
            # 尝试不同的编解码器(按优先级)
            codecs_to_try = [
                ('mp4v', 'MP4V'),
                ('MJPG', 'Motion JPEG'),
                ('XVID', 'XVID'),
                ('avc1', 'H.264'),
            ]
            
            self.video_writer = None
            last_error = None
            
            for codec_code, codec_name in codecs_to_try:
                try:
                    fourcc = cv2.VideoWriter_fourcc(*codec_code)
                    writer = cv2.VideoWriter(
                        self.record_filepath,
                        fourcc,
                        self.fps,
                        (self.width, self.height)
                    )
                    
                    # 如果writer创建成功,使用它
                    if writer is not None:
                        self.video_writer = writer
                        print(f"使用编解码器: {codec_name} ({codec_code})")
                        break
                
                except Exception as e:
                    last_error = f"{codec_name}: {e}"
                    continue
            
            # 如果所有编解码器都失败
            if self.video_writer is None:
                error_msg = f"无法创建视频文件"
                if last_error:
                    error_msg += f" (最后尝试: {last_error})"
                return False, error_msg
            
            self.recording = True
            return True, self.record_filepath
        
        except Exception as e:
            return False, f"开始录像失败: {e}"
    
    def stop_recording(self):
        """
        停止录像
        
        Returns:
            tuple: (success, message)
        """
        if not self.recording:
            return False, "未在录像"
        
        try:
            self.recording = False
            
            if self.video_writer:
                self.video_writer.release()
                self.video_writer = None
            
            filepath = self.record_filepath
            self.record_filepath = None
            
            return True, f"录像已保存: {filepath}"
        
        except Exception as e:
            return False, f"停止录像失败: {e}"
    
    def is_recording(self):
        """返回是否正在录像"""
        return self.recording
    
    def get_info(self):
        """
        获取视频流信息
        
        Returns:
            dict: 视频流信息
        """
        info = {
            'camera_index': self.camera_index,
            'width': self.width,
            'height': self.height,
            'fps': self.fps,
            'is_streaming': self.is_streaming,
            'is_recording': self.recording,
            'queue_size': self.frame_queue.qsize()
        }
        
        if self.recording and self.record_filepath:
            info['record_file'] = self.record_filepath
        
        return info


class MultiCameraManager:
    """多摄像头管理器"""
    
    def __init__(self):
        """初始化管理器"""
        self.cameras = {}
        self.default_camera = None
    
    def add_camera(self, name, camera_index=0, width=640, height=480, fps=30):
        """
        添加摄像头
        
        Args:
            name: 摄像头名称
            camera_index: 摄像头索引
            width: 宽度
            height: 高度
            fps: 帧率
        
        Returns:
            tuple: (success, message)
        """
        if name in self.cameras:
            return False, f"摄像头 '{name}' 已存在"
        
        camera = VideoStream(camera_index, width, height, fps)
        self.cameras[name] = camera
        
        if self.default_camera is None:
            self.default_camera = name
        
        return True, f"摄像头 '{name}' 已添加"
    
    def remove_camera(self, name):
        """
        移除摄像头
        
        Args:
            name: 摄像头名称
        
        Returns:
            tuple: (success, message)
        """
        if name not in self.cameras:
            return False, f"摄像头 '{name}' 不存在"
        
        # 停止视频流
        camera = self.cameras[name]
        if camera.is_streaming:
            camera.stop()
        
        del self.cameras[name]
        
        # 如果删除的是默认摄像头,重新选择
        if self.default_camera == name:
            self.default_camera = next(iter(self.cameras), None)
        
        return True, f"摄像头 '{name}' 已移除"
    
    def get_camera(self, name=None):
        """
        获取摄像头
        
        Args:
            name: 摄像头名称 (None=默认摄像头)
        
        Returns:
            VideoStream 或 None
        """
        if name is None:
            name = self.default_camera
        
        return self.cameras.get(name)
    
    def list_cameras(self):
        """列出所有摄像头"""
        return list(self.cameras.keys())
    
    def stop_all(self):
        """停止所有摄像头"""
        for camera in self.cameras.values():
            if camera.is_streaming:
                camera.stop()


# 全局摄像头管理器实例
camera_manager = MultiCameraManager()


def get_available_cameras(max_test=5):
    """
    检测可用的摄像头
    
    Args:
        max_test: 最多测试的摄像头数量
    
    Returns:
        list: 可用摄像头索引列表
    """
    available = []
    
    for i in range(max_test):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available.append(i)
            cap.release()
    
    return available


if __name__ == '__main__':
    """测试代码"""
    print("测试视频流模块...")
    
    # 检测可用摄像头
    cameras = get_available_cameras()
    print(f"检测到 {len(cameras)} 个摄像头: {cameras}")
    
    if not cameras:
        print("未检测到摄像头")
        exit(1)
    
    # 创建视频流
    stream = VideoStream(camera_index=cameras[0], width=640, height=480, fps=30)
    
    # 启动视频流
    success, msg = stream.start()
    print(f"启动视频流: {msg}")
    
    if not success:
        exit(1)
    
    try:
        # 获取10帧测试
        for i in range(10):
            success, frame = stream.get_frame()
            if success:
                print(f"帧 {i+1}: {frame.shape}")
            else:
                print(f"获取帧失败: {frame}")
            time.sleep(0.1)
        
        # 测试录像
        print("\n开始录像...")
        success, msg = stream.start_recording()
        print(msg)
        
        time.sleep(3)  # 录像3秒
        
        success, msg = stream.stop_recording()
        print(msg)
    
    finally:
        # 停止视频流
        stream.stop()
        print("视频流已停止")
