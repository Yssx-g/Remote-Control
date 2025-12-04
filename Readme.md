# 远程控制系统 (Remote Control System)

一个基于Python的安全远程控制系统,支持屏幕截图、摄像头控制、实时视频流、文件管理和Shell命令执行等功能。

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-Educational-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

> ⚠️ **重要提示**: 本项目仅用于教育学习目的,请在本地网络或虚拟机环境中运行,切勿用于非法用途。

## 📋 目录

- [功能特性](#功能特性)
- [系统要求](#系统要求)
- [安装部署](#安装部署)
- [快速开始](#快速开始)
- [功能详解](#功能详解)
- [安全特性](#安全特性)
- [常见问题](#常见问题)
- [故障排除](#故障排除)

## ✨ 功能特性

### 核心功能
- 🔐 **身份验证**: SHA256密码哈希,安全认证
- 📸 **屏幕截图**: 实时捕获远程屏幕
- 📷 **摄像头控制**:
  - 拍照功能
  - 实时视频预览
  - 视频录制 (MP4格式)
- 💻 **Shell命令执行**:
  - 命令白名单保护
  - 沙箱环境隔离
  - Windows/Linux自动适配
- 📂 **文件管理**: 在沙箱内安全操作文件
- 🌐 **系统信息**: 获取远程主机详细信息

### 安全特性
- ✅ 命令白名单验证
- ✅ 路径遍历防护
- ✅ 沙箱环境隔离
- ✅ 会话超时控制
- ✅ 安全的二进制数据传输

## 💻 系统要求

### 基础要求
- **Python**: 3.8 或更高版本
- **操作系统**: Windows 10/11, Linux, macOS
- **网络**: 局域网环境或虚拟机网络

### Python依赖包
```
mss>=9.0.0           # 屏幕截图
Pillow>=10.0.0       # 图像处理
psutil>=5.9.0        # 系统信息
opencv-python>=4.8.0 # 摄像头和视频处理
```

## 🚀 安装部署

### 1. 克隆项目
```bash
git clone https://github.com/Yssx-g/Remote-Control.git
cd Remote-Control
```

### 2. 创建虚拟环境 (推荐)
```bash
# Windows
python -m venv start
start\Scripts\activate

# Linux/macOS
python3 -m venv start
source start/bin/activate
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 配置系统

编辑 `config.py` 文件:

```python
# 修改默认密码 (强烈建议!)
AUTH_PASSWORD = 'your_secure_password'

# 修改服务器端口 (可选)
SERVER_PORT = 9999

# 视频流启动超时 (摄像头初始化慢时可调大)
VIDEO_START_TIMEOUT = 30  # 秒
```

## 🎯 快速开始

### 启动服务端 (被控端)

1. 在被控制的计算机上运行:
```bash
python server.py
```

2. 服务器将显示:
```
============================================================
  远程控制系统 - 服务器 (被控端B)
============================================================
⚠️  注意: 本程序仅用于教育学习目的
[*] 服务器启动在 0.0.0.0:9999
[*] 等待客户端连接...
```

### 启动客户端 (控制端)

1. 在控制端计算机上运行:
```bash
python client.py <服务器IP>
```

例如:
```bash
# 本地测试
python client.py 127.0.0.1

# 局域网连接
python client.py 192.168.1.100
```

2. 输入密码进行身份验证

3. 验证成功后显示主菜单:
```
============================================================
                    主菜单
============================================================
  1.  📸 截图
  2.  📷 摄像头
  3.  💻 Shell模式
  4.  ℹ️  系统信息
  0.  ❌ 断开连接
============================================================
```

## 📖 功能详解

### 1. 📸 屏幕截图

**功能**: 捕获远程计算机屏幕并保存到本地

**使用步骤**:
1. 主菜单选择 `1`
2. 等待截图完成
3. 截图自动保存到 `screenshots/` 目录

**保存格式**: `screenshot_YYYYMMDD_HHMMSS.jpg`

### 2. 📷 摄像头功能

进入摄像头子菜单后有多个选项:

#### 2.1 📸 拍照
- 捕获单张照片
- 保存到 `camera/` 目录
- 格式: `camera_YYYYMMDD_HHMMSS.jpg`

#### 2.2 📹 实时视频预览
**参数设置**:
```
宽度 [640]:     视频分辨率宽度
高度 [480]:     视频分辨率高度
帧率 [30]:      每秒帧数
质量 [85]:      JPEG压缩质量 (1-100)
```

**操作提示**:
- 按 `q` 键退出预览
- 按 `Ctrl+C` 强制停止
- 初始化可能需要30秒,请耐心等待

**性能建议**:
- 本地网络: 640x480 @ 30fps, 质量85
- 较慢网络: 320x240 @ 15fps, 质量70

#### 2.3 🎥 录像功能
- 自动启动/停止视频流
- 录制为MP4格式
- 保存到服务器的 `camera/` 目录
- 支持自定义文件名

#### 2.4 🧽 清理缓冲区 (选项 9)
**何时使用**:
- 看到 "UTF-8 解码错误"
- 看到 "数据开头: ffd8ff..."
- 视频功能启动失败
- 数据传输混乱时

**操作**: 选择 `9` → 按 Enter → 查看清理结果

### 3. 💻 Shell模式

**安全特性**:
- ✅ 命令白名单保护
- ✅ 沙箱目录限制 (`safe_files/`)
- ✅ 路径遍历防护
- ✅ 自动系统适配 (Windows/Linux)

**支持的命令**:

**Windows系统**:
```
基础命令: dir, cd, cls, type, more, echo, date, time
文件操作: copy, move, del, mkdir, rmdir, ren
查看搜索: find, findstr, tree
系统信息: whoami, hostname, systeminfo, ver
```

**Linux/Mac系统**:
```
基础命令: ls, cd, clear, cat, less, more, pwd, echo
文件操作: cp, mv, rm, mkdir, rmdir, touch
查看搜索: grep, find, wc, tree
系统信息: whoami, hostname, uname, env
文件权限: chmod, chown, stat, file
```

**特殊命令**:
- `help` - 显示帮助信息
- `exit` / `quit` - 退出Shell模式

**命令组合**:
```bash
# 管道
ls | grep test

# 重定向
echo "Hello" > test.txt
cat file.txt >> log.txt

# 逻辑运算
mkdir test && cd test
rm file.txt || echo "File not found"
```

### 4. ℹ️ 系统信息

显示远程系统详细信息:
- 操作系统和版本
- 系统架构
- 处理器信息
- 主机名和IP地址
- Python版本
- 在线状态

## 🔒 安全特性

### 认证机制
- SHA256密码哈希
- 会话超时: 30分钟
- 连接超时: 60秒

### 命令执行安全
```python
# 白名单验证
ALLOWED_COMMANDS = ['ls', 'cd', 'cat', ...]

# 沙箱限制
SHELL_ROOT_DIRECTORY = 'safe_files/'

# 路径验证
def is_safe_path(path, root):
    # 防止路径遍历攻击
    return os.path.abspath(path).startswith(root)
```

### 文件操作安全
- 限制在 `safe_files/` 目录内
- 文件大小限制: 100MB
- 允许的文件扩展名白名单

## ❓ 常见问题

### Q1: 连接失败怎么办?
**A**: 检查以下项目:
1. 服务器是否已启动
2. IP地址是否正确
3. 端口9999是否被占用
4. 防火墙是否允许连接
5. 客户端和服务器在同一网络

### Q2: 摄像头启动超时?
**A**: 解决方法:
1. 增加超时时间:
```python
# config.py
VIDEO_START_TIMEOUT = 60  # 改为60秒
```
2. 检查摄像头是否被其他程序占用
3. 重启计算机后再试

### Q3: UTF-8解码错误?
**A**: 这是视频流残留数据导致的:
1. 进入摄像头菜单
2. 选择 `9` - 清理缓冲区
3. 重新尝试视频功能
4. 如果问题持续,重启客户端

### Q4: 视频预览卡顿?
**A**: 降低视频参数:
```
宽度: 320
高度: 240
帧率: 15
质量: 70
```

### Q5: Shell命令被拒绝?
**A**: 可能原因:
1. 命令不在白名单中
2. 尝试访问沙箱外的目录
3. 使用了危险的系统命令

查看允许的命令:
```bash
remote $ help
```

## 🔧 故障排除

### 1. 模块导入错误
```bash
ModuleNotFoundError: No module named 'xxx'
```
**解决**: 重新安装依赖
```bash
pip install -r requirements.txt --upgrade
```

### 2. OpenCV摄像头错误
```bash
cv2.error: Camera failed to open
```
**解决**:
- Windows: 检查摄像头权限设置
- Linux: 确保用户在 `video` 组
  ```bash
  sudo usermod -a -G video $USER
  ```
- 确保没有其他程序占用摄像头

### 3. 端口被占用
```bash
OSError: [Errno 98] Address already in use
```
**解决**:
```bash
# 查找占用端口的进程
# Windows
netstat -ano | findstr :9999

# Linux/Mac
lsof -i :9999

# 修改端口
# config.py
SERVER_PORT = 8888  # 改为其他端口
```

### 4. 权限错误
```bash
PermissionError: [Errno 13] Permission denied
```
**解决**:
```bash
# 确保目录有写权限
chmod 755 screenshots/ camera/ safe_files/
```

## 📁 项目结构

```
Remote-Control/
├── server.py              # 服务端主程序
├── client.py              # 客户端主程序
├── config.py              # 配置文件
├── protocol.py            # 通信协议
├── utils.py               # 工具函数
├── video_stream.py        # 视频流处理
├── requirements.txt       # 依赖列表
├── README.md             # 项目文档
├── safe_files/           # Shell沙箱目录
│   ├── readme.txt
│   └── test.txt
├── screenshots/          # 截图保存目录
├── camera/               # 摄像头照片/视频目录
├── Download/             # 下载文件目录
└── logs/                 # 日志目录
```

## 🔄 更新日志

### v1.0.0 (2025-12-04)
- ✅ 基础远程控制功能
- ✅ 屏幕截图
- ✅ 摄像头拍照
- ✅ 实时视频流
- ✅ 视频录制
- ✅ Shell命令执行
- ✅ 文件管理
- ✅ 安全特性完善
- ✅ 缓冲区清理功能

## 📝 配置说明

### 关键配置项

```python
# config.py

# 服务器配置
SERVER_HOST = '0.0.0.0'    # 监听所有接口
SERVER_PORT = 9999         # 服务端口
MAX_CONNECTIONS = 5        # 最大连接数

# 安全配置
AUTH_PASSWORD = 'Yssx'     # 修改此密码!
SESSION_TIMEOUT = 1800     # 会话超时(秒)

# 网络配置
CONNECTION_TIMEOUT = 60    # 连接超时
VIDEO_START_TIMEOUT = 30   # 视频启动超时

# 命令执行
COMMAND_TIMEOUT = 10       # 命令执行超时

# 文件限制
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
```

## ⚠️ 安全建议

1. **修改默认密码**: 使用强密码
2. **本地测试**: 仅在可信网络使用
3. **防火墙**: 配置适当的防火墙规则
4. **定期更新**: 保持依赖包最新
5. **日志监控**: 定期检查日志文件
6. **权限最小化**: 不要使用管理员权限运行

## 📞 技术支持

- **GitHub Issues**: [提交问题](https://github.com/Yssx-g/Remote-Control/issues)
- **文档**: 本README文件
- **代码注释**: 详细的代码内注释

## 📄 许可证

本项目仅供教育学习使用。使用者需自行承担使用本软件的风险和责任。

---

## 🎓 学习资源

### Python Socket编程
- [Python Socket官方文档](https://docs.python.org/3/library/socket.html)
- [网络编程基础](https://realpython.com/python-sockets/)

### OpenCV视频处理
- [OpenCV Python教程](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)
- [视频I/O操作](https://docs.opencv.org/4.x/dd/d43/tutorial_py_video_display.html)

### 网络安全
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python安全编码](https://python.land/python-security)

---

**开发者**: Yssx-g  
**最后更新**: 2025年12月4日  
**版本**: 1.0.0

⭐ 如果这个项目对你有帮助,请给个Star!
