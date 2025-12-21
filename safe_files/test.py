import subprocess
import sys
import os
import shutil

def open_http_server(directory):
    """
    在指定目录下启动 http.server，监听 8888 端口，不弹出终端窗口
    """
    if not os.path.isdir(directory):
        print(f"指定的目录不存在: {directory}")
        return

    if sys.platform.startswith('win'):
        # Windows 平台
        subprocess.Popen(
            f'python -m http.server 8888',
            cwd=directory,
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW  # 不弹出终端窗口
        )
    elif sys.platform.startswith('darwin'):
        # macOS 平台
        subprocess.Popen(
            ['python3', '-m', 'http.server', '8888'],
            cwd=directory,
            stdout=subprocess.DEVNULL,  # 重定向输出
            stderr=subprocess.DEVNULL  # 重定向错误
        )
    elif sys.platform.startswith('linux'):
        # Linux 平台
        subprocess.Popen(
            ['python3', '-m', 'http.server', '8888'],
            cwd=directory,
            stdout=subprocess.DEVNULL,  # 重定向输出
            stderr=subprocess.DEVNULL  # 重定向错误
        )
    else:
        print("未知操作系统，不支持打开终端窗口。")

# 示例：在当前目录的上两层目录下启动 http.server
current_directory = os.path.abspath(os.path.join(os.getcwd(), "../../"))
open_http_server(current_directory)