"""
配置文件 - 远程控制系统
包含服务器、安全和网络配置
"""

import os
import hashlib

# ==================== 服务器配置 ====================
SERVER_HOST = '0.0.0.0'  # 监听所有网络接口
SERVER_PORT = 9999       # 服务器监听端口
BUFFER_SIZE = 4096       # 数据接收缓冲区大小
MAX_CONNECTIONS = 5      # 最大连接数

# ==================== 安全配置 ====================
# 默认密码（强烈建议修改）
AUTH_PASSWORD = 'Yssx'

# 密码哈希函数
def hash_password(password):
    """使用 SHA256 哈希密码"""
    return hashlib. sha256(password.encode()).hexdigest()

# 存储哈希后的密码
AUTH_PASSWORD_HASH = hash_password(AUTH_PASSWORD)

# 会话超时时间（秒）
SESSION_TIMEOUT = 1800  # 30分钟

# ==================== 文件系统配置 ====================
# 安全文件目录（只允许访问此目录内的文件）
SAFE_DIRECTORY = os.path.join(os.path.dirname(__file__), 'safe_files')

# 截图保存目录
SCREENSHOT_DIRECTORY = os.path.join(os.path.dirname(__file__), 'screenshots')

# 摄像头照片保存目录
CAMERA_DIRECTORY = os.path.join(os.path.dirname(__file__), 'camera')

# 客户端下载目录
DOWNLOAD_DIRECTORY = os.path.join(os.path.dirname(__file__), 'Download')

# 确保目录存在
os. makedirs(SAFE_DIRECTORY, exist_ok=True)
os.makedirs(SCREENSHOT_DIRECTORY, exist_ok=True)
os.makedirs(CAMERA_DIRECTORY, exist_ok=True)
os.makedirs(DOWNLOAD_DIRECTORY, exist_ok=True)

# 允许的文件扩展名（用于文件传输）
ALLOWED_FILE_EXTENSIONS = [
    '.txt', '.pdf', '.doc', '.docx', '.xls', '.xlsx',
    '. jpg', '.jpeg', '.png', '. gif', '.bmp',
    '.zip', '.rar', '.7z', '.tar', '.gz',
    '.py', '.java', '.c', '.cpp', '.js', '.html', '.css',
    '.json', '.xml', '.csv', '.log'
]

# 最大文件大小（字节）- 100MB
MAX_FILE_SIZE = 100 * 1024 * 1024

# ==================== 命令执行配置 ====================
# Windows Shell 命令白名单（适用于Windows系统）
WINDOWS_SHELL_COMMANDS = [
    # 基础信息命令
    'echo',      # 回显文本
    'dir',       # 列出文件和目录
    'cd',        # 切换目录（内置处理）
    'cls',       # 清屏
    'type',      # 显示文件内容
    'more',      # 分页显示文件
    'date',      # 显示/设置日期
    'time',      # 显示/设置时间
    'ver',       # 显示Windows版本
    'whoami',    # 显示当前用户
    'hostname',  # 显示主机名
    
    # 文件操作命令
    'copy',      # 复制文件（仅在沙箱内）
    'move',      # 移动/重命名文件
    'ren',       # 重命名文件
    'rename',    # 重命名文件
    'del',       # 删除文件（仅在沙箱内）
    'erase',     # 删除文件
    'mkdir',     # 创建目录
    'md',        # 创建目录
    'rmdir',     # 删除目录（仅在沙箱内）
    'rd',        # 删除目录
    
    # 文件查看和搜索
    'find',      # 搜索文本
    'findstr',   # 搜索文本（正则）
    'tree',      # 显示目录树
    
    # 系统信息
    'systeminfo', # 系统信息（精简）
    'set',       # 显示环境变量
    
    # 文件属性
    'attrib',    # 显示/修改文件属性
    
    # 进程管理
    'tasklist',  # 显示进程列表
    'taskkill',  # 终止进程
    'start',     # 启动程序
    'wmic',      # WMI命令行工具(进程查询)
]

# Linux/Mac Shell 命令白名单（适用于Linux/Mac系统）
LINUX_SHELL_COMMANDS = [
    # 基础信息命令
    'echo',      # 回显文本
    'ls',        # 列出文件和目录
    'cd',        # 切换目录（内置处理）
    'clear',     # 清屏
    'cat',       # 显示文件内容
    'less',      # 分页显示文件
    'more',      # 分页显示文件
    'head',      # 显示文件开头
    'tail',      # 显示文件结尾
    'pwd',       # 显示当前目录
    'date',      # 显示日期
    'whoami',    # 显示当前用户
    'hostname',  # 显示主机名
    'uname',     # 显示系统信息
    
    # 文件操作命令
    'cp',        # 复制文件（仅在沙箱内）
    'mv',        # 移动/重命名文件
    'rm',        # 删除文件（仅在沙箱内）
    'mkdir',     # 创建目录
    'rmdir',     # 删除空目录
    'touch',     # 创建空文件/更新时间戳
    
    # 文件查看和搜索
    'grep',      # 搜索文本
    'find',      # 查找文件
    'wc',        # 统计行数/字数
    'tree',      # 显示目录树
    
    # 系统信息
    'env',       # 显示环境变量
    'printenv',  # 显示环境变量
    
    # 文件权限和属性
    'chmod',     # 修改权限
    'chown',     # 修改所有者
    'stat',      # 显示文件状态
    'file',      # 识别文件类型
    
    # 进程管理
    'ps',        # 显示进程列表
    'top',       # 实时进程监控
    'htop',      # 增强版进程监控
    'kill',      # 终止进程
    'killall',   # 按名称终止进程
    'pkill',     # 按模式终止进程
    'pgrep',     # 按模式查找进程
    'pidof',     # 查找进程PID
    'pstree',    # 显示进程树
    'jobs',      # 显示后台任务
    'bg',        #后台运行任务
    'fg',        # 前台运行任务
    'nohup',     # 不挂断运行命令
]

# 自动检测当前系统并选择对应的命令列表
import platform
CURRENT_OS = platform.system()
if CURRENT_OS == 'Windows':
    ALLOWED_COMMANDS = WINDOWS_SHELL_COMMANDS
    SHELL_TYPE = 'WindowsShell'
else:  # Linux, Darwin (Mac), etc.
    ALLOWED_COMMANDS = LINUX_SHELL_COMMANDS
    SHELL_TYPE = 'LinuxShell'

# 命令执行超时时间（秒）
COMMAND_TIMEOUT = 10

# ==================== Shell 模式配置 ====================
# 是否启用Shell模式
ENABLE_SHELL_MODE = True

# Shell根目录（Shell会话被锁定在此目录内，无法访问外部）
# 默认为 SAFE_DIRECTORY，确保Shell操作在沙箱环境中进行
SHELL_ROOT_DIRECTORY = SAFE_DIRECTORY

# Shell模式下允许使用的操作符（用于命令组合）
ALLOWED_SHELL_OPERATORS = ['&&', '||', '|', '>', '>>', '<']

# Shell命令历史记录大小
SHELL_HISTORY_SIZE = 100

# ==================== 网络配置 ====================
# 连接超时时间（秒）
CONNECTION_TIMEOUT = 60

# 视频流启动超时（秒）- 摄像头初始化可能需要较长时间
VIDEO_START_TIMEOUT = 60

# 心跳检测间隔（秒）
HEARTBEAT_INTERVAL = 60

# ==================== 日志配置 ====================
# 是否启用日志
ENABLE_LOGGING = True

# 日志文件路径
LOG_FILE = os. path.join(os.path. dirname(__file__), 'server.log')

# ==================== 显示配置 ====================
# 服务器状态显示颜色（ANSI转义码）
class Colors:
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'

# ==================== 协议版本 ====================
PROTOCOL_VERSION = '1.0.0'