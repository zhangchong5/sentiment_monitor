"""
香港分行舆情监测系统 - 重构版本

模块结构：
- app.core: 核心配置和工具
- app.models: 数据模型定义
- app.services: 业务服务层（搜索、抓取、分析、生成）
- app.utils: 辅助工具函数
"""

__version__ = "2.0.0"
__author__ = "Sentiment Monitor Team"

# 显式导入子模块，确保 mock 路径正确
from app import core, models, services, utils
