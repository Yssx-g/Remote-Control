# 远程控制系统 (Remote Control System)

一个基于Python的安全远程控制系统，支持控制台与可视化两种操作模式，提供屏幕监控、摄像头控制、文件管理、Shell终端、键盘监控等丰富功能。

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-Educational-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

> ⚠️ **重要提示**: 本项目仅用于教育学习目的，请在本地网络或虚拟机环境中运行，切勿用于非法用途。

## 📋 目录

- [功能特性](#功能特性)
- [系统要求](#系统要求)
- [安装部署](#安装部署)
- [快速开始](#快速开始)
- [操作模式](#操作模式)
- [功能详解](#功能详解)
- [安全特性](#安全特性)
- [常见问题](#常见问题)
- [项目结构](#项目结构)

## ✨ 功能特性

### 双模式操作界面
- **🖥️ 控制台模式** (`client.py`) - 经典命令行界面，稳定高效
- **🎨 可视化模式** (`client_visual.py`) - 现代化图形界面，极客风格设计

### 核心功能 (10大功能模块)

| 编号 | 功能 | 控制台 | 可视化界面 | 说明 |
|------|------|--------|-----------|------|
| 1 | 📸 远程截屏 | ✅ | ✅ 快捷按钮 | 实时捕获远程屏幕 |
| 2 | 📷 摄像头功能 | ✅ | ✅ 快捷按钮 | 拍照、录像、实时预览 |
| 3 | 📂 文件管理 | ✅ | ✅ FILES标签 | 下载/上传/执行文件 |
| 4 | 🐚 交互式Shell | ✅ | ✅ SHELL标签 | 远程命令执行 |
| 5 | 🔐 注册表管理 | ✅ | ✅ REGISTRY标签 | Windows注册表操作 |
| 6 | 🎤 麦克风录音 | ✅ | ✅ 快捷按钮 | 远程录音并下载 |
| 7 | 🖥️ 屏幕实时查看 | ✅ | ✅ SCREEN标签 | 实时屏幕流+鼠标控制 |
| 8 | 🕵️ 键盘监控 | ✅ | ✅ KEYBOARD标签 | 监控键盘输入事件 |
| 9 | 💻 查看系统信息 | ✅ | ✅ SYSINFO标签 | OS、CPU、内存、IP等 |
| 10 | 🚪 断开连接 | ✅ | ✅ | 安全断开连接 |

### 安全特性
- ✅ SHA256密码哈希认证
- ✅ 命令白名单验证
- ✅ 沙箱环境隔离 (`safe_files/`)
- ✅ 路径遍历防护
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
pyautogui            # 鼠标/键盘控制 (可选)
sounddevice          # 麦克风录音 (可选)
numpy                # 音频处理 (可选)
```

## 🚀 安装部署

### 1. 克隆项目
```bash
git clone https://github.com/Anti1i/Remote-Control.git
cd Remote-Control
```

### 2. 创建虚拟环境 (推荐)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
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
```

## 🎯 快速开始

### 方式一：使用服务器端GUI (推荐)

**1. 启动服务端GUI (被控端)**
```bash
python server_gui.py
```

服务器GUI提供：
- 📊 实时连接状态监控
- 🔔 连接请求授权弹窗
- 📝 操作日志记录
- 🎨 Geek风格深色主题

**2. 选择客户端模式**

**控制台模式 (经典)**
```bash
python client.py <服务器IP>
```

**可视化模式 (推荐) 🌟**
```bash
python client_visual.py
# 或使用快捷启动脚本
python start_visual_client.py
```

### 方式二：使用控制台服务端

**1. 启动服务端 (被控端)**
```bash
python server.py
```

**2. 启动客户端 (控制端)**
```bash
# 控制台模式
python client.py 192.168.1.100

# 可视化模式
python client_visual.py
```

## 🎨 操作模式

### 控制台模式 (`client.py`)

经典命令行界面，菜单驱动操作：

```
============================================================
                    主菜单
============================================================
  1.  📸 远程截屏
  2.  📷 摄像头功能
  3.  📂 文件管理
  4.  🐚 交互式LinuxShell
  5.  🔐 注册表管理 (Windows)
  6.  🎤 麦克风录音
  7.  🖥️ 屏幕实时查看与鼠标控制
  8.  🕵️ 键盘监控
  9.  💻 查看系统信息
  0.  🚪 断开连接
============================================================
```

**适用场景**：
- 远程SSH连接
- 无图形界面环境
- 追求稳定性和低资源占用

### 可视化模式 (`client_visual.py`) 🌟

现代化图形界面，Geek风格设计：

**界面特点**：
- 🎨 深色主题 + 霓虹绿配色 (黑客风格)
- 📑 7个功能标签页，一键切换
- ⚡ 3个底部快捷按钮 (截图/摄像头/录音)
- 📜 实时操作历史记录
- 🖱️ 点击即用，无需记忆命令

**界面布局**：
```
┌────────────────────────────────────────────────────────┐
│  REMOTE CONTROL - VISUAL CLIENT           [目标IP显示]  │
├────────────────────────────────────────────────────────┤
│ [💻SYSINFO] [📂FILES] [🖥️SCREEN] [🔐REGISTRY] ...      │
├────────────────────────────────────────────────────────┤
│                                                         │
│              当前标签页内容区域                          │
│                                                         │
├────────────────────────────────────────────────────────┤
│  [📸 SCREENSHOT] [📷 CAMERA] [🎤 MIC RECORD]           │
├────────────────────────────────────────────────────────┤
│  OPERATION HISTORY: [最近操作记录]                      │
└────────────────────────────────────────────────────────┘
```

**标签页说明**：
- **💻 SYSTEM INFO** - 静态系统信息显示 (OS/架构/IP等)
- **📂 FILES** - 文件管理 (下载/上传/执行)
- **🖥️ SCREEN** - 屏幕实时流 + 鼠标点击控制
- **🔐 REGISTRY** - 注册表查询/设置/删除
- **🕵️ KEYBOARD** - 键盘事件监控
- **💻 SHELL** - 交互式终端
- **📜 HISTORY** - 完整操作历史

**适用场景**：
- 本地局域网操作
- 需要频繁切换功能
- 追求操作便捷性

> 📖 详细功能映射请查看 [FEATURE_MAPPING.md](FEATURE_MAPPING.md)

## 📖 功能详解

### 1. 📸 远程截屏

**功能**: 捕获远程计算机屏幕并保存到本地

**控制台操作**:
```
主菜单 → 1 → 等待截图完成
```

**可视化操作**:
```
点击底部 [📸 SCREENSHOT] 按钮
```

**保存路径**: `screenshots/screenshot_YYYYMMDD_HHMMSS.jpg`

### 2. 📷 摄像头功能

**子功能**:
- 📸 拍照 - 捕获单张照片
- 📹 实时预览 - 查看实时视频流
- 🎥 录像 - 录制MP4视频 (服务端保存)

**可视化操作**: 点击底部 [📷 CAMERA] → 选择操作

**保存路径**: `camera/camera_YYYYMMDD_HHMMSS.jpg`

### 3. 📂 文件管理

**功能**: 安全的文件操作，限制在 `safe_files/` 目录

#### 3.1 下载文件 (被控端→控制端)
```bash
# 控制台
文件管理 → 1 → 输入文件路径

# 可视化
FILES标签 → 输入路径 → [⬇ DOWNLOAD]
```

#### 3.2 上传文件 (控制端→被控端)
```bash
# 控制台
文件管理 → 2 → 输入本地路径 → 输入远程路径

# 可视化
FILES标签 → 选择本地文件 → 输入远程路径 → [⬆ UPLOAD]
```

#### 3.3 执行文件
```bash
# 支持的文件类型
Windows: .exe, .bat, .cmd, .py
Linux:   .py, .sh, 可执行文件

# 可视化操作
FILES标签 → 输入文件路径和参数 → [▶ EXECUTE]
```

**保存路径**: 下载到 `Download/` 目录

### 4. 🐚 交互式Shell

**安全特性**:
- 命令白名单验证
- 沙箱环境 (`safe_files/`)
- 支持管道/重定向/逻辑运算

**支持的命令** (部分):

**Windows**:
```
dir, cd, cls, type, copy, move, del, mkdir
tasklist, taskkill, whoami, systeminfo
```

**Linux/Mac**:
```
ls, cd, pwd, cat, cp, mv, rm, mkdir
ps, top, grep, find, chmod, chown
```

**可视化操作**: SHELL标签 → 输入命令 → [EXECUTE] → 查看输出

### 5. 🔐 注册表管理 (Windows)

**功能**: 查询/设置/删除注册表键值

**支持的根键**:
```
HKEY_CURRENT_USER (HKCU)
HKEY_LOCAL_MACHINE (HKLM)
HKEY_CLASSES_ROOT (HKCR)
HKEY_USERS (HKU)
HKEY_CURRENT_CONFIG (HKCC)
```

**操作示例**:
```
# 查询值
根: HKCU
键: SOFTWARE\MyApp
值名: Version

# 设置DWORD
根: HKLM
键: SOFTWARE\Settings
名称: Enabled
值: 1
类型: REG_DWORD
```

**可视化操作**: REGISTRY标签 → 填写信息 → 选择操作

⚠️ **警告**: 注册表操作有风险，请谨慎使用！

### 6. 🎤 麦克风录音

**功能**: 远程录制麦克风音频

**参数设置**:
- 录音时长 (秒)
- 采样率 (默认44100Hz)
- 通道数 (1=单声道, 2=立体声)

**依赖**: `sounddevice`, `numpy`

**可视化操作**: 点击 [🎤 MIC RECORD] → 设置参数 → 等待录制

**保存路径**: `Download/mic_YYYYMMDD_HHMMSS.wav`

### 7. 🖥️ 屏幕实时查看与鼠标控制

**功能**:
- 实时查看远程屏幕 (视频流)
- 远程鼠标点击/移动/滚动

**参数设置**:
```
帧率: 5-15 (建议10，节省带宽)
质量: 1-100 (建议70)
```

**鼠标控制**:
- 左键点击 - 在流窗口点击
- 右键点击 - 右键菜单
- 滚轮 - 上下滚动

**可视化操作**:
```
SCREEN标签 → [▶ START STREAM] → 鼠标点击控制 → [⏹ STOP]
```

⚠️ **注意**: 需要服务端安装 `pyautogui`

### 8. 🕵️ 键盘监控

**功能**: 监控被控端的键盘按键事件

**显示信息**:
- 按键名称
- 事件类型 (PRESS/RELEASE)
- 时间戳

**可视化操作**:
```
KEYBOARD标签 → [▶ START MONITORING] → 查看日志 → [⏹ STOP]
```

**日志示例**:
```
[2025-12-08 10:30:15] PRESS: a
[2025-12-08 10:30:15] RELEASE: a
[2025-12-08 10:30:16] PRESS: enter
```

### 9. 💻 查看系统信息

**显示内容**:
- 操作系统和版本
- 系统架构
- 处理器信息
- 主机名
- IP地址
- Python版本
- 在线状态

**可视化操作**: SYSINFO标签 → [🔄 REFRESH] 刷新信息

## 🔒 安全特性

### 认证机制
```python
# SHA256密码哈希
AUTH_PASSWORD = 'your_password'

# 会话超时
SESSION_TIMEOUT = 1800  # 30分钟

# 连接超时
CONNECTION_TIMEOUT = 60  # 60秒
```

### 命令执行安全
```python
# 白名单验证
ALLOWED_COMMANDS = ['ls', 'cd', 'cat', 'dir', ...]

# 沙箱限制
SHELL_ROOT_DIRECTORY = 'safe_files/'

# 路径验证
def is_safe_path(path, root):
    return os.path.abspath(path).startswith(root)
```

### 文件操作安全
- ✅ 限制在 `safe_files/` 目录
- ✅ 文件大小限制: 100MB
- ✅ 路径遍历防护

## ❓ 常见问题

### Q1: 连接失败怎么办?
**A**: 检查以下项目:
1. 服务器是否已启动
2. IP地址是否正确
3. 端口9999是否被占用/防火墙拦截
4. 客户端和服务器在同一网络

### Q2: 可视化界面点击"停止"卡死?
**A**: 已修复 (v1.3.0)
- 修复了屏幕监控和键盘监控的死锁问题
- 更新到最新版本即可

### Q3: 摄像头启动超时?
**A**: 解决方法:
1. 增加超时时间 (`config.py` → `VIDEO_START_TIMEOUT = 60`)
2. 检查摄像头是否被占用
3. 重启计算机

### Q4: Shell命令被拒绝?
**A**: 可能原因:
- 命令不在白名单中
- 访问沙箱外目录
- 使用危险系统命令

查看允许的命令: 在Shell输入 `help`

### Q5: 视频预览卡顿?
**A**: 降低参数:
```
宽度: 320
高度: 240
帧率: 10-15
质量: 70
```

## 🔧 故障排除

### 1. 模块导入错误
```bash
ModuleNotFoundError: No module named 'xxx'
```
**解决**:
```bash
pip install -r requirements.txt --upgrade
```

### 2. 端口被占用
```bash
OSError: Address already in use
```
**解决**:
```bash
# 查找占用进程
# Windows
netstat -ano | findstr :9999

# Linux/Mac
lsof -i :9999

# 修改端口 (config.py)
SERVER_PORT = 8888
```

### 3. 权限错误
```bash
PermissionError: Permission denied
```
**解决**:
```bash
# 确保目录有写权限
chmod 755 screenshots/ camera/ safe_files/
```

## 📁 项目结构

```
Remote-Control/
├── server.py              # 服务端主程序 (控制台)
├── server_gui.py          # 服务端GUI程序 (可视化)
├── client.py              # 客户端主程序 (控制台)
├── client_visual.py       # 客户端GUI程序 (可视化) 🌟
├── start_visual_client.py # 可视化客户端快捷启动
├── gui_theme.py           # GUI主题配置 (Geek风格)
├── config.py              # 系统配置文件
├── protocol.py            # 通信协议定义
├── utils.py               # 工具函数库
├── video_stream.py        # 视频流处理
├── screen_stream.py       # 屏幕流处理
├── mic.py                 # 麦克风录音
├── requirements.txt       # 依赖包列表
├── README.md              # 项目文档 (本文件)
├── FEATURE_MAPPING.md     # 功能映射文档
├── safe_files/            # Shell沙箱目录
├── screenshots/           # 截图保存目录
├── camera/                # 摄像头照片/视频目录
├── Download/              # 文件下载目录
└── logs/                  # 日志目录
```

## 🔄 更新日志

### v1.3.0 (2025-12-08) - 可视化界面与死锁修复
- ✅ **新增可视化客户端** (`client_visual.py`)
  - Geek风格深色主题 (黑底霓虹绿)
  - 7个功能标签页 + 3个快捷按钮
  - 实时操作历史记录
  - 一键操作，无需记忆命令
- ✅ **新增服务端GUI** (`server_gui.py`)
  - 连接请求授权弹窗
  - 实时连接状态监控
  - 操作日志显示
- ✅ **修复死锁问题**
  - 修复屏幕监控停止时卡死
  - 修复键盘监控停止时卡死
  - 优化socket锁机制
- 📝 **完善文档**
  - 新增功能映射文档 (FEATURE_MAPPING.md)
  - 更新README，添加可视化界面说明

### v1.2.0 (2025-12-04) - 文件管理增强
- ✅ 新增文件上传功能
- ✅ 新增文件执行功能
- ✅ 文件管理子菜单整合
- 📝 完善文件管理文档

### v1.1.0 (2025-12-04) - 进程管理
- ✅ 新增进程管理功能
- ✅ Shell帮助增强
- 📝 添加进程管理示例

### v1.0.0 (2025-12-04) - 首个版本
- ✅ 基础远程控制功能
- ✅ 屏幕截图/摄像头/视频流
- ✅ Shell命令执行
- ✅ 文件管理
- ✅ 安全特性完善

## 📝 配置说明

### 关键配置项

```python
# config.py

# 服务器配置
SERVER_HOST = '0.0.0.0'    # 监听所有接口
SERVER_PORT = 9999         # 服务端口
MAX_CONNECTIONS = 5        # 最大连接数

# 安全配置
AUTH_PASSWORD = 'Yssx'     # ⚠️ 请修改此密码!
SESSION_TIMEOUT = 1800     # 会话超时(秒)

# 网络配置
CONNECTION_TIMEOUT = 60    # 连接超时
VIDEO_START_TIMEOUT = 30   # 视频启动超时

# 文件限制
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
```

## ⚠️ 安全建议

1. **修改默认密码**: 使用强密码 (大小写+数字+符号)
2. **本地测试**: 仅在可信网络使用
3. **防火墙**: 配置适当的防火墙规则
4. **定期更新**: 保持依赖包最新版本
5. **日志监控**: 定期检查日志文件
6. **权限最小化**: 不使用管理员权限运行
7. **虚拟环境**: 建议使用虚拟环境隔离

## 📞 技术支持

- **GitHub Issues**: [提交问题](https://github.com/Anti1i/Remote-Control/issues)
- **文档**:
  - 主文档: README.md (本文件)
  - 功能映射: [FEATURE_MAPPING.md](FEATURE_MAPPING.md)
- **代码注释**: 详细的代码内注释

## 📄 许可证

本项目仅供**教育学习**使用。使用者需自行承担使用本软件的风险和责任。

**禁止用途**:
- ❌ 未经授权访问他人计算机
- ❌ 窃取他人隐私信息
- ❌ 破坏计算机系统
- ❌ 任何违法犯罪活动

## 🎓 学习资源

### Python Socket编程
- [Python Socket官方文档](https://docs.python.org/3/library/socket.html)
- [网络编程基础](https://realpython.com/python-sockets/)

### GUI开发 (Tkinter)
- [Tkinter官方文档](https://docs.python.org/3/library/tkinter.html)
- [Python GUI编程](https://realpython.com/python-gui-tkinter/)

### OpenCV视频处理
- [OpenCV Python教程](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)

### 网络安全
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python安全编码](https://python.land/python-security)

---

**开发者**: Anti1i
**最后更新**: 2025年12月8日
**版本**: 1.3.0

⭐ 如果这个项目对你有帮助，请给个Star！
