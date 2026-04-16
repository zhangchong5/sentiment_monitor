# 日志配置说明

## 概述

全局日志系统已优化，支持灵活的日志级别配置和多种输出方式。

## 功能特性

- ✅ **多级日志支持**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- ✅ **环境变量配置**: 通过环境变量轻松切换日志级别
- ✅ **双输出模式**: 支持控制台输出和文件输出
- ✅ **日志轮转**: 自动按文件大小轮转，避免日志文件过大
- ✅ **结构化格式**: 统一的日志格式（时间、级别、模块、消息）

## 快速开始

### 1. 基本使用

```python
from app.utils.logger import get_logger

logger = get_logger(__name__)

logger.debug("调试信息")
logger.info("普通信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")
```

### 2. 配置日志级别

#### 方法一：环境变量（推荐）

```bash
# 设置日志级别为 DEBUG（显示所有日志）
export LOG_LEVEL=DEBUG
python app/main.py

# 设置日志级别为 INFO（默认）
export LOG_LEVEL=INFO
python app/main.py

# 仅显示错误
export LOG_LEVEL=ERROR
python app/main.py
```

#### 方法二：代码中动态修改

```python
from app.utils.logger import set_log_level

# 切换到调试模式
set_log_level("DEBUG")

# 切换到仅错误模式
set_log_level("ERROR")
```

### 3. 启用文件日志

```bash
# 启用文件日志输出
export LOG_TO_FILE=true

# 自定义日志目录（可选）
export LOG_DIR=/path/to/logs

# 运行应用
python app/main.py
```

日志文件将保存在：`/workspace/logs/app_YYYYMMDD.log`

## 配置选项

| 环境变量 | 说明 | 默认值 | 示例 |
|---------|------|--------|------|
| `LOG_LEVEL` | 日志级别 | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `LOG_TO_FILE` | 是否输出到文件 | `False` | `true`, `false` |
| `LOG_DIR` | 日志文件目录 | `/workspace/logs` | `/var/log/myapp` |
| `LOG_FORMAT` | 日志格式 | （默认格式） | 自定义格式字符串 |
| `LOG_DATE_FORMAT` | 日期格式 | `%Y-%m-%d %H:%M:%S` | 自定义日期格式 |
| `LOG_MAX_FILE_SIZE_MB` | 单个日志文件最大大小 (MB) | `10` | `50` |
| `LOG_BACKUP_COUNT` | 保留的备份文件数量 | `5` | `10` |

## 日志级别说明

| 级别 | 说明 | 使用场景 |
|-----|------|---------|
| `DEBUG` | 调试信息 | 开发调试时查看详细执行流程 |
| `INFO` | 普通信息 | 正常运行时的关键节点记录（默认） |
| `WARNING` | 警告信息 | 潜在问题，但不影响程序运行 |
| `ERROR` | 错误信息 | 操作失败，但程序可继续运行 |
| `CRITICAL` | 严重错误 | 可能导致程序终止的严重问题 |

## 使用示例

### 开发调试模式

```bash
# 显示所有调试信息
export LOG_LEVEL=DEBUG
export LOG_TO_FILE=true
python app/main.py
```

### 生产环境模式

```bash
# 仅记录警告及以上级别
export LOG_LEVEL=WARNING
export LOG_TO_FILE=true
export LOG_MAX_FILE_SIZE_MB=50
python app/main.py
```

### 仅查看错误

```bash
# 安静模式，仅显示错误
export LOG_LEVEL=ERROR
python app/main.py
```

## 便捷函数

除了使用 logger 对象，还可以直接使用便捷函数：

```python
from app.utils.logger import debug, info, warning, error, critical

info("这是一条信息")
error("发生了一个错误")
```

## 日志文件格式

日志文件按日期命名：`app_YYYYMMDD.log`

示例内容：
```
2026-04-16 09:49:32 | INFO     | app.main                       | 🇭🇰 香港分行舆情筛查系统启动
2026-04-16 09:49:32 | INFO     | app.main                       | 【步骤 1/6】配置验证
2026-04-16 09:49:32 | DEBUG    | app.services.search_engine     | ✓ Serper 搜索引擎初始化成功
2026-04-16 09:49:32 | WARNING  | app.services.screenshot        | ⚠️ 截图服务初始化失败
2026-04-16 09:49:32 | ERROR    | app.main                       | ❌ 搜索执行失败
```

## 注意事项

1. **避免重复初始化**: 日志系统在模块导入时自动初始化，无需手动调用 `setup_logging()`
2. **性能考虑**: 在生产环境建议使用 `INFO` 或更高级别，避免 `DEBUG` 产生过多日志
3. **磁盘空间**: 启用文件日志时，注意定期清理旧日志文件
4. **线程安全**: 日志系统完全线程安全，可在多线程环境中使用
