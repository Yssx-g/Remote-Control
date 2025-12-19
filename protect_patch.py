import os


def is_safe_file_execution(filepath):
    """
    检查文件是否安全执行
    Args:
        filepath: 文件路径
    Returns:
        bool: 是否安全
    """
    # 限制文件扩展名
    allowed_extensions = ['.py', '.sh']
    _, ext = os.path.splitext(filepath)
    if ext.lower() not in allowed_extensions:
        print("[安全检查] 不允许的文件扩展名:", ext)
        return False

    # 检查文件内容是否包含敏感命令
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            dangerous_commands = ['cmd', 'powershell', 'bash', 'wt', 'gnome-terminal']
            if any(cmd in content for cmd in dangerous_commands):
                print("[安全检查] 文件内容包含危险命令")
                return False
    except Exception:
        return False

    return True