"""
日志配置模块 - 统一日志管理，支持多级日志配置

功能特性：
    - 支持 DEBUG/INFO/WARNING/ERROR/CRITICAL 五级日志
    - 可通过环境变量 LOG_LEVEL 配置日志级别
    - 支持控制台输出与文件输出
    - 结构化日志格式（时间、级别、模块、消息）
    - 可选的 JSON 格式输出（便于日志分析系统）
    
使用示例：
    from app.utils.logger import get_logger
    
    logger = get_logger(__name__)
    logger.debug("调试信息")
    logger.info("普通信息")
    logger.warning("警告信息")
    logger.error("错误信息")
"""
import os
import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


# 日志级别映射
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# 默认配置
DEFAULT_LOG_FORMAT = '%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s'
DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


class LogConfig:
    """
    日志配置类 - 集中管理日志相关配置
    
    属性：
        level: 日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL）
        format: 日志格式字符串
        date_format: 日期格式字符串
        log_to_file: 是否输出到文件
        log_file_path: 日志文件路径
        max_file_size: 单个日志文件最大大小（MB）
        backup_count: 保留的备份文件数量
    """
    
    # 从环境变量读取配置，或使用默认值
    LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    FORMAT = os.getenv("LOG_FORMAT", DEFAULT_LOG_FORMAT)
    DATE_FORMAT = os.getenv("LOG_DATE_FORMAT", DEFAULT_DATE_FORMAT)
    LOG_TO_FILE = os.getenv("LOG_TO_FILE", "False").lower() in ("true", "1", "yes", "y")
    LOG_DIR = Path(os.getenv("LOG_DIR", "/workspace/logs"))
    MAX_FILE_SIZE_MB = int(os.getenv("LOG_MAX_FILE_SIZE_MB", "10"))
    BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    
    @classmethod
    def get_level(cls) -> int:
        """获取日志级别对应的整数值"""
        return LOG_LEVELS.get(cls.LEVEL, logging.INFO)
    
    @classmethod
    def validate_level(cls, level: str) -> bool:
        """验证日志级别是否有效"""
        return level.upper() in LOG_LEVELS


def setup_logging(
    level: Optional[str] = None,
    log_format: Optional[str] = None,
    date_format: Optional[str] = None,
    log_to_file: Optional[bool] = None,
    log_dir: Optional[Path] = None,
    console_output: bool = True
) -> logging.Logger:
    """
    初始化全局日志系统
    
    参数：
        level: 日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL），默认从配置读取
        log_format: 日志格式，默认使用标准格式
        date_format: 日期格式，默认使用标准格式
        log_to_file: 是否输出到文件，默认从配置读取
        log_dir: 日志文件目录，默认从配置读取
        console_output: 是否输出到控制台，默认 True
    
    返回：
        logging.Logger: 根日志记录器
    
    特性：
        - 自动创建日志目录
        - 支持日志轮转（按文件大小）
        - 防止重复添加 handler
    """
    # 使用配置默认值
    if level is None:
        level = LogConfig.LEVEL
    if log_format is None:
        log_format = LogConfig.FORMAT
    if date_format is None:
        date_format = LogConfig.DATE_FORMAT
    if log_to_file is None:
        log_to_file = LogConfig.LOG_TO_FILE
    if log_dir is None:
        log_dir = LogConfig.LOG_DIR
    
    # 验证日志级别
    level_upper = level.upper()
    if not LogConfig.validate_level(level_upper):
        print(f"警告：无效的日志级别 '{level}'，使用默认级别 INFO")
        level_upper = "INFO"
    
    numeric_level = LOG_LEVELS[level_upper]
    
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # 清除现有 handler（防止重复）
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    
    # 创建格式化器
    formatter = logging.Formatter(log_format, datefmt=date_format)
    
    # 添加控制台 handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # 添加文件 handler（如果启用）
    if log_to_file:
        try:
            # 确保日志目录存在
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成日志文件名（带日期）
            log_date = datetime.now().strftime("%Y%m%d")
            log_file = log_dir / f"app_{log_date}.log"
            
            # 使用轮转文件 handler（按大小）
            from logging.handlers import RotatingFileHandler
            
            max_bytes = LogConfig.MAX_FILE_SIZE_MB * 1024 * 1024
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=LogConfig.BACKUP_COUNT,
                encoding='utf-8'
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
            # 记录日志配置信息
            root_logger.info(f"日志文件：{log_file}")
            root_logger.info(f"日志级别：{level_upper}")
            
        except Exception as e:
            print(f"警告：日志文件初始化失败：{e}，仅使用控制台输出")
    
    # 记录日志系统初始化完成
    root_logger.info("=" * 70)
    root_logger.info("日志系统初始化完成")
    root_logger.info(f"日志级别：{level_upper}")
    root_logger.info(f"输出目标：{'控制台 + 文件' if log_to_file else '控制台'}")
    root_logger.info("=" * 70)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    获取命名日志记录器
    
    参数：
        name: 日志记录器名称（通常使用 __name__）
    
    返回：
        logging.Logger: 命名日志记录器
    
    使用示例：
        logger = get_logger(__name__)
        logger.info("这是一条日志")
    """
    return logging.getLogger(name)


def set_log_level(level: str) -> None:
    """
    动态修改日志级别
    
    参数：
        level: 新的日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL）
    
    示例：
        set_log_level("DEBUG")  # 切换到调试模式
        set_log_level("ERROR")  # 仅显示错误
    """
    level_upper = level.upper()
    if not LogConfig.validate_level(level_upper):
        raise ValueError(f"无效的日志级别：{level}")
    
    numeric_level = LOG_LEVELS[level_upper]
    logging.getLogger().setLevel(numeric_level)
    
    # 更新所有 handler 的级别
    for handler in logging.getLogger().handlers:
        handler.setLevel(numeric_level)
    
    logger = logging.getLogger(__name__)
    logger.info(f"日志级别已修改为：{level_upper}")


# ============================================
# 便捷日志函数（无需获取 logger 对象）
# ============================================

def debug(msg: str, *args, **kwargs) -> None:
    """记录 DEBUG 级别日志"""
    logging.getLogger(__name__).debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs) -> None:
    """记录 INFO 级别日志"""
    logging.getLogger(__name__).info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs) -> None:
    """记录 WARNING 级别日志"""
    logging.getLogger(__name__).warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs) -> None:
    """记录 ERROR 级别日志"""
    logging.getLogger(__name__).error(msg, *args, **kwargs)


def critical(msg: str, *args, **kwargs) -> None:
    """记录 CRITICAL 级别日志"""
    logging.getLogger(__name__).critical(msg, *args, **kwargs)


# ============================================
# 自动初始化（模块导入时执行）
# ============================================

# 在模块导入时自动初始化日志系统
setup_logging()
