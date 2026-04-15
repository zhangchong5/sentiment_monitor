"""
辅助工具函数
"""


def truncate_text(text: str, max_length: int = 60) -> str:
    """
    安全截断文本（处理 None 和特殊字符）
    
    Args:
        text: 待截断文本
        max_length: 最大长度
    
    Returns:
        截断后的文本（带...省略号）
    """
    if not text:
        return ""
    text_str = str(text)
    return text_str[:max_length] + "..." if len(text_str) > max_length else text_str
