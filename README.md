# 远程控制系统 (Remote Control System)

一个基于Python的安全远程控制系统,支持屏幕截图、摄像头控制、实时视频流、文件管理和Shell命令执行等功能。

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-Educational-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

> ⚠️ **重要提示**: 本项目仅用于教育学习目的,请在本地网络或虚拟机环境中运行,切勿用于非法用途。

## 📋 目录

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
- 🔄 **进程管理**:
  - 查看进程列表 (tasklist/ps)
  - 启动程序 (start)
  - 进程监控 (top/htop)
- 📂 **文件管理**: ⭐ 完善
  - 文件下载 (被控端→控制端)
  - 文件上传 (控制端→被控端)
  - 文件执行 (支持 .exe/.py/.sh/.bat)
- 🖥️ **屏幕实时查看与鼠标控制**: ⭐ 新增
  - 实时屏幕预览
  - 远程鼠标移动/点击/滚动
  - 支持自定义区域和帧率
- ⌨️ **键盘输入控制**: ⭐ 新增
  - 发送单个按键
  - 输入文本字符串
  - 发送组合键 (Ctrl+C, Alt+F4等)
  - 预设快捷操作
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

#### 2.3 🖥️ 屏幕实时查看与鼠标控制

**功能**: 支持实时查看被控主机的屏幕并可在客户端发送鼠标事件（左/右键点击、拖动、滚动）。

**参数设置**:
```
帧率 [10]:       屏幕帧率（建议 5-15 以节省带宽）
JPEG质量 [70]:   图像压缩质量 (1-100)
```

**操作**:
- 在主菜单选择“屏幕实时查看与鼠标控制”。
- 在显示窗口中点击或拖动将把鼠标事件发送到被控主机。
- 按 `q` 退出预览。

**注意**:
- 鼠标控制通过 `pyautogui` 实现（Python 库），服务端必须安装对应依赖。
- 为安全起见，请谨慎使用鼠标控制功能，仅在受信任环境中启用。


**性能建议**:
- 本地网络: 640x480 @ 30fps, 质量85

### 3. 🎤 麦克风录音

通过客户端可以请求被控主机在服务器端录制麦克风并把 WAV 文件返回到控制端 `Download/` 目录。该功能依赖 `sounddevice` 和 `numpy`，仅在被控主机安装这些依赖并有可用麦克风时可用。

使用步骤:
1. 主菜单选择麦克风录音
2. 输入录音时长（秒）、采样率与通道数
3. 等待服务端录制并下载 WAV 文件到 `Download/` 目录

注意:
- 录音功能会在服务器端直接访问麦克风设备，请确保服务端所在主机允许访问麦克风并安装依赖。
- 录音时长过长会产生较大文件，请合理选择时长。
 - 服务端仅返回未压缩的 WAV 文件，不依赖外部编码器（如 ffmpeg）。

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

### 4. 📂 文件管理

**安全特性**:
- ✅ 所有文件操作限制在 `safe_files/` 目录内
- ✅ 路径遍历防护
- ✅ 文件大小限制 (可配置)

#### 4.1 📥 下载文件
从被控端下载文件到本地:

**操作步骤**:
1. 主菜单选择 `3` (文件管理)
2. 子菜单选择 `1` (下载文件)
3. 输入远程文件路径 (相对于 `safe_files/`)
4. 文件自动保存到本地 `Download/` 目录

**示例**:
```
请输入要下载的文件路径: test.txt
正在下载文件...
✓ 文件下载成功!
  文件名: test.txt
  文件大小: 1.25 KB
  保存位置: D:\Remote Control\Download\test.txt
```

**支持的文件类型**:
- 文本文件: `.txt`, `.py`, `.md`, `.json`, `.xml`, `.csv`
- 图片文件: `.jpg`, `.png`, `.gif`, `.bmp`
- 文档文件: `.pdf`, `.doc`, `.docx`
- 压缩文件: `.zip`, `.rar`, `.7z`
- 其他任何二进制文件

#### 4.2 📤 上传文件
从本地上传文件到被控端:

**操作步骤**:
1. 主菜单选择 `3` (文件管理)
2. 子菜单选择 `2` (上传文件)
3. 输入本地文件路径
4. 输入远程保存路径 (可选,默认保存到 `safe_files/`)
5. 文件自动上传到被控端

**示例**:
```
请输入本地文件路径: D:\data\config.json
请输入远程保存路径 (留空则保存到safe_files/目录): config/app.json
正在上传文件... (2.5 KB)
✓ 文件上传成功!
  本地文件: D:\data\config.json
  远程路径: config/app.json
  文件大小: 2.5 KB
```

**注意事项**:
- 如果远程路径留空,文件将以原名保存到 `safe_files/` 根目录
- 如果目标目录不存在,会自动创建
- 文件名可以包含子目录路径,如 `subdir/file.txt`

#### 4.3 ▶️ 执行文件
远程执行被控端上的文件:

**操作步骤**:
1. 主菜单选择 `3` (文件管理)
2. 子菜单选择 `3` (执行文件)
3. 输入要执行的文件路径
4. 输入执行参数 (可选)
5. 查看执行结果

**示例**:
```
⚠️  注意: 文件执行限制在safe_files/目录内
请输入要执行的文件路径: scripts/backup.py
请输入执行参数 (可选): --force
正在执行文件...
✓ 文件执行成功!
  文件路径: scripts/backup.py
  执行参数: --force
  进程ID: 5678
  
输出:
进程已启动（PID: 5678），正在后台运行...
```

**支持的文件类型**:
- **Windows**:
  - `.exe` - 可执行程序
  - `.bat`, `.cmd` - 批处理脚本
  - `.py` - Python脚本 (自动使用 Python 解释器)
  - 其他文件 - 尝试使用系统默认程序打开

- **Linux/Mac**:
  - `.py` - Python脚本
  - `.sh` - Shell脚本
  - 可执行文件 (有执行权限的任何文件)

**注意事项**:
- 文件在后台执行,不会阻塞客户端
- 如果进程启动失败,会显示错误信息
- Python脚本自动使用系统 Python 解释器
- Shell脚本在Linux上使用 `bash` 执行
- 执行参数会按空格分割传递给程序

### 5. 🔧 注册表管理 (Windows)

该功能仅在 Windows 系统上可用, 通过客户端向服务端发送注册表操作请求进行查询、设置和删除。

注意: 注册表操作有风险, 请谨慎使用并在测试环境验证。

#### 支持操作
- 查询值: 返回指定键下的一个或所有值
- 设置值: 创建或修改指定键的值 (支持 REG_SZ 和 REG_DWORD)
- 删除值/键: 删除单个值或删除整个键 (删除键要求键为空)

#### 操作示例
在客户端主菜单选择 `7` → 注册表管理 → 选择操作:

查询某个值:
```
根: HKCU
键: SOFTWARE\\MyApp
值名: InstallPath
```

设置 DWORD 值:
```
根: HKLM
键: SOFTWARE\\MyCompany\\Settings
名称: Enabled
值: 1
类型: REG_DWORD
```

删除整个键 (如果该键为空):
```
根: HKCU
键: SOFTWARE\\TempTest
值名: (留空)
```

### 6. ⌨️ 键盘输入控制

通过客户端可以向被控端发送键盘输入指令，模拟键盘操作。该功能依赖 `pyautogui` 库。

#### 功能特性
- **单个按键**: 发送 Enter、Space、Backspace 等单个按键
- **文本输入**: 输入英文字符串和数字
- **组合键**: 发送 Ctrl+C、Alt+F4 等组合键
- **快捷操作**: 预设常用快捷键（复制/粘贴/全选等）

#### 使用步骤
1. 主菜单选择 `10` (键盘输入控制)
2. 选择操作类型：
   - **选项1 - 发送单个按键**: 输入按键名称（如 enter, space, esc）
   - **选项2 - 输入文本**: 输入要发送的文本字符串
   - **选项3 - 发送组合键**: 输入多个按键，用空格分隔（如 ctrl c）
   - **选项4 - 快捷操作**: 选择预设的常用快捷键

#### 常用按键名称
```
导航键: up, down, left, right, home, end, pageup, pagedown
编辑键: enter, space, tab, esc, backspace, delete
功能键: f1-f12
修饰键: ctrl, alt, shift, win
字母数字: a-z, 0-9
```

#### 操作示例

**发送单个按键**:
```
请输入按键名称: enter
✓ 按键 'enter' 已发送
```

**输入文本**:
```
请输入文本内容: Hello World
✓ 文本已发送: Hello World
```

**发送组合键**:
```
请输入组合键 (用空格分隔): ctrl c
✓ 组合键 'ctrl+c' 已发送
```

**快捷操作**:
- `1` - Ctrl+C (复制)
- `2` - Ctrl+V (粘贴)
- `3` - Ctrl+A (全选)
- `4` - Ctrl+Z (撤销)
- `5` - Ctrl+Y (重做)
- `6` - Ctrl+S (保存)
- `7` - Alt+F4 (关闭窗口)
- `8` - Win+D (显示桌面)

#### 注意事项
- 文本输入仅支持 ASCII 字符（英文、数字、基本符号）
- 不支持中文等多字节字符的直接输入
- 组合键区分大小写，建议使用小写
- 某些系统级快捷键可能需要管理员权限
- 按键发送速度较快，如需延迟可多次发送

### 7. 🔄 进程管理

通过Shell命令进行进程管理:

#### Windows系统
```bash
# 查看所有进程
remote $ tasklist

# 查看特定进程
remote $ tasklist | findstr python

# 终止进程 (按PID)
remote $ taskkill /PID 1234 /F

# 终止进程 (按名称)
remote $ taskkill /IM notepad.exe /F

# 使用WMIC查询进程详情
remote $ wmic process list brief
remote $ wmic process where name="python.exe" get processid,commandline
```

#### Linux/Mac系统
```bash
# 查看所有进程
remote $ ps aux
remote $ ps -ef

# 查找特定进程
remote $ ps aux | grep python
remote $ pgrep python
remote $ pidof python

# 进程树
remote $ pstree

# 实时监控
remote $ top
remote $ htop  # 需要安装

# 终止进程
remote $ kill 1234
remote $ kill -9 1234      # 强制终止
remote $ killall python    # 按名称终止
remote $ pkill -f "script.py"  # 按模式终止
```

**安全提示**:
- ⚠️ 终止进程前请确认PID正确
- ⚠️ 使用 `-9` 信号会强制终止,可能导致数据丢失
- ⚠️ 不要终止系统关键进程

### 5. ℹ️ 系统信息

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

### v1.2.0 (2025-12-04) - 文件管理增强
- ✅ **新增文件上传功能**
  - 支持从控制端上传文件到被控端
  - 自动创建目标目录
  - 实时显示上传进度
- ✅ **新增文件执行功能**
  - 支持多种文件类型 (.exe, .py, .sh, .bat等)
  - 后台异步执行
  - 返回进程ID和输出
- ✅ **文件管理子菜单**
  - 整合文件下载、上传、执行功能
  - 统一的文件管理入口
- 📝 完善文档,添加文件管理详细说明

### v1.1.0 (2025-12-04) - 进程管理
- ✅ **新增进程管理功能**
  - Windows: tasklist, taskkill, start, wmic
  - Linux: ps, top, htop, kill, killall, pkill, pgrep等
- ✅ Shell帮助增强,显示进程管理命令
- 📝 完善文档,添加进程管理示例

### v1.0.0 (2025-12-04) - 首个版本
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
