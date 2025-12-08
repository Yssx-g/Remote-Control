"""
工具函数模块 - 远程控制系统
提供通用的工具函数
"""

import os
import hashlib
import platform
import socket
from datetime import datetime
from config import SAFE_DIRECTORY, ALLOWED_FILE_EXTENSIONS, MAX_FILE_SIZE

# 导入视频流模块
try:
    from video_stream import VideoStream, MultiCameraManager, camera_manager, get_available_cameras
    VIDEO_SUPPORT = True
except ImportError:
    VIDEO_SUPPORT = False
    print("警告: 视频流模块未安装,视频功能将不可用")

# ==================== 安全函数 ====================

def hash_password(password):
    """
    使用 SHA256 哈希密码
    
    Args:
        password: 明文密码
    
    Returns:
        str: 哈希后的密码
    """
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password, password_hash):
    """
    验证密码
    
    Args:
        password: 待验证的明文密码
        password_hash: 已存储的密码哈希
    
    Returns:
        bool: 密码是否匹配
    """
    return hash_password(password) == password_hash


def is_safe_path(basedir, path, follow_symlinks=True):
    """
    检查路径是否在安全目录内（防止目录遍历攻击）
    
    Args:
        basedir: 基准目录
        path: 待检查的路径
        follow_symlinks: 是否跟随符号链接
    
    Returns:
        bool: 路径是否安全
    """
    # 解析绝对路径
    if follow_symlinks:
        matchpath = os.path.realpath(path)
    else:
        matchpath = os.path. abspath(path)
    
    basedir_abs = os.path.abspath(basedir)
    
    # 检查路径是否以基准目录开头
    return os.path.commonpath([basedir_abs, matchpath]) == basedir_abs


def validate_filename(filename):
    """
    验证文件名是否合法
    
    Args:
        filename: 文件名
    
    Returns:
        bool: 文件名是否合法
    """
    # 检查是否包含非法字符
    illegal_chars = ['.. ', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in illegal_chars:
        if char in filename:
            return False
    return True


def get_file_extension(filename):
    """
    获取文件扩展名
    
    Args:
        filename: 文件名
    
    Returns:
        str: 文件扩展名（小写，包含点号）
    """
    _, ext = os.path.splitext(filename)
    return ext. lower()


def is_allowed_file(filename):
    """
    检查文件扩展名是否在允许列表中
    
    Args:
        filename: 文件名
    
    Returns:
        bool: 是否允许
    """
    ext = get_file_extension(filename)
    return ext in ALLOWED_FILE_EXTENSIONS


def check_file_size(filepath):
    """
    检查文件大小是否超过限制
    
    Args:
        filepath: 文件路径
    
    Returns:
        tuple: (是否合法, 文件大小)
    """
    try:
        size = os.path.getsize(filepath)
        return (size <= MAX_FILE_SIZE, size)
    except:
        return (False, 0)


# ==================== 文件系统函数 ====================

def list_files_in_directory(directory):
    """
    列出目录中的文件和子目录
    
    Args:
        directory: 目录路径
    
    Returns:
        list: 文件和目录信息列表
    """
    try:
        items = []
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            item_info = {
                'name': item,
                'is_dir': os.path.isdir(item_path),
                'size': os.path.getsize(item_path) if os.path.isfile(item_path) else 0,
                'modified': datetime.fromtimestamp(os.path.getmtime(item_path)).strftime('%Y-%m-%d %H:%M:%S')
            }
            items.append(item_info)
        return items
    except Exception as e:
        print(f"列出目录失败: {e}")
        return []


def read_file_binary(filepath):
    """
    读取文件为二进制数据
    
    Args:
        filepath: 文件路径
    
    Returns:
        bytes: 文件内容，失败返回 None
    """
    try:
        with open(filepath, 'rb') as f:
            return f. read()
    except Exception as e:
        print(f"读取文件失败: {e}")
        return None


def write_file_binary(filepath, data):
    """
    将二进制数据写入文件
    
    Args:
        filepath: 文件路径
        data: 二进制数据
    
    Returns:
        bool: 是否写入成功
    """
    try:
        os.makedirs(os.path. dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"写入文件失败: {e}")
        return False


# ==================== 系统信息函数 ====================

def get_system_info():
    """
    获取系统信息
    
    Returns:
        dict: 系统信息字典
    """
    try:
        info = {
            'os': platform.system(),
            'os_version': platform.version(),
            'os_release': platform.release(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'hostname': socket.gethostname(),
            'ip_address': get_local_ip(),
            'python_version': platform.python_version(),
            'online': True
        }
        return info
    except Exception as e:
        print(f"获取系统信息失败: {e}")
        return {}


def get_local_ip():
    """
    获取本地 IP 地址
    
    Returns:
        str: IP 地址
    """
    try:
        # 创建一个 UDP 套接字
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 不需要真正连接，只是为了获取本地 IP
        s.connect(('8.8.8. 8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0. 0.1'


# ==================== 格式化函数 ====================

def format_file_size(size_bytes):
    """
    格式化文件大小
    
    Args:
        size_bytes: 字节数
    
    Returns:
        str: 格式化后的大小字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def format_timestamp(timestamp):
    """
    格式化时间戳
    
    Args:
        timestamp: 时间戳
    
    Returns:
        str: 格式化后的时间字符串
    """
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


# ==================== 日志函数 ====================

def log_message(message, level='INFO'):
    """
    记录日志消息
    
    Args:
        message: 日志消息
        level: 日志级别
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] [{level}] {message}"
    print(log_entry)
    
    # 可选：写入日志文件
    try:
        with open('server. log', 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
    except:
        pass


# ==================== 测试函数 ====================

if __name__ == '__main__':
    # 测试系统信息获取
    print("系统信息:")
    info = get_system_info()
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    # 测试文件大小格式化
    print("\n文件大小格式化:")
    print(f"  1024 bytes = {format_file_size(1024)}")
    print(f"  1048576 bytes = {format_file_size(1048576)}")
    print(f"  1073741824 bytes = {format_file_size(1073741824)}")