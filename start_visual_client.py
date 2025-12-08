#!/usr/bin/env python3
"""
快速启动脚本 - 可视化控制端
一键启动带有完整可视化功能的远程控制客户端
"""

import sys
import os

# 确保在正确的目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print(" 远程控制系统 - 可视化控制端启动器")
print("=" * 60)
print()
print("正在加载可视化界面...")
print()

try:
    from client_visual import VisualClientUI

    print("✓ 界面加载成功")
    print()
    print("功能说明：")
    print("  📊 仪表盘    - 实时系统监控（CPU/内存/磁盘）")
    print("  ⚙️  进程管理  - 查看和管理远程进程")
    print("  📁 文件浏览  - 图形化文件系统管理")
    print("  🖥️  屏幕监控  - 实时屏幕流和截图")
    print("  💻 Shell终端 - 远程命令执行")
    print("  📜 操作历史  - 完整操作日志")
    print()
    print("=" * 60)
    print()

    app = VisualClientUI()
    app.mainloop()

except ImportError as e:
    print(f"✗ 错误：缺少依赖模块")
    print(f"  详情：{e}")
    print()
    print("解决方法：")
    print("  pip install pillow")
    sys.exit(1)

except Exception as e:
    print(f"✗ 启动失败：{e}")
    sys.exit(1)
