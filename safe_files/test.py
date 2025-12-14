import subprocess
import sys
import os
import shutil

def open_terminal():
    if sys.platform.startswith('win'):
        # 优先用 Windows Terminal (wt)，否则退回 PowerShell，再否则退回 cmd
        def is_exist(prog):
            return shutil.which(prog) is not None

        if is_exist('wt'):
            subprocess.Popen('start cmd', shell=True)
        elif is_exist('powershell'):
            subprocess.Popen('start powershell', shell=True)
        else:
            subprocess.Popen('start cmd', shell=True)
    elif sys.platform.startswith('darwin'):
        # macOS: 使用 Terminal.app
        subprocess.Popen(['open', '-a', 'Terminal'])
    elif sys.platform.startswith('linux'):
        # 依次检测常用终端，找到一个就用
        terminals = [
            'gnome-terminal', 'konsole', 'xfce4-terminal', 'lxterminal',
            'x-terminal-emulator', 'xterm', 'mate-terminal', 'tilix', 'alacritty'
        ]
        term = next((t for t in terminals if shutil.which(t)), None)
        if term:
            subprocess.Popen([term])
        else:
            print("未找到可用终端，请手动安装一个终端模拟器。")
    else:
        print("未知操作系统，不支持打开终端窗口。")

open_terminal()