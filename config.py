"""
配置管理模块 - 集中管理所有应用配置参数
支持环境变量与默认值双重机制，确保安全性与灵活性
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# ============================================
# 环境变量加载
# ============================================
load_dotenv()  # 从.env文件加载环境变量

class Config:
    """
    应用配置类 - 单一可信源配置管理
    
    所有配置项均支持通过环境变量覆盖，优先级：
    1. 环境变量（.env文件或系统环境变量）
    2. 代码中的默认值
    
    关键配置说明：
    - AI_ENABLED: AI功能总开关（False = 跳过所有AI调用，用占位符替代）
    - SERPER_API_KEY: Serper搜索API密钥（必需）
    - SEARCH_QUERY: 搜索关键词（可自定义）
    """
    
    # ============================================
    # 项目路径配置
    # ============================================
    BASE_DIR = Path(__file__).parent.resolve()
    OUTPUT_DIR = BASE_DIR / "output"
    SCREENSHOT_DIR = OUTPUT_DIR / "screenshots"
    ASSETS_DIR = BASE_DIR / "assets"
    
    # ============================================
    # AI功能总开关 - 核心配置！
    # ============================================
    # 设置为 False 时：跳过所有AI调用，使用占位符文本
    # 设置为 True 时：启用完整AI分析功能
    AI_ENABLED = os.getenv("AI_ENABLED", "False").lower() in ("true", "1", "yes", "y")
    
    # ============================================
    # API配置
    # ============================================
    # --- Serper API（Google搜索替代方案）---
    SERPER_API_KEY = os.getenv("SERPER_API_KEY", "ae80a71d2d3aa9308fc54f6ba99f743fb9d7b23a")
    SERPER_API_URL = "https://google.serper.dev/search"
    
    # --- AI API配置（仅当AI_ENABLED=True时需要）---
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # ============================================
    # 搜索配置
    # ============================================
    # 默认搜索关键词：聚焦香港分行相关风险
    SEARCH_QUERY = os.getenv(
        "SEARCH_QUERY",
        "香港分行 洗钱 监管处罚 违规 反洗钱 AML 合规"
    )
    SEARCH_RESULTS_COUNT = int(os.getenv("SEARCH_RESULTS_COUNT", "20"))
    SEARCH_REGION = "hk"  # 搜索区域：香港
    SEARCH_LANGUAGE = "zh-HK"  # 搜索语言：繁体中文
    
    # ============================================
    # 网页抓取配置
    # ============================================
    # 排除的文件扩展名（不抓取、不截图）
    EXCLUDE_EXTENSIONS = {
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', 
        '.ppt', '.pptx', '.zip', '.rar', '.7z',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp'
    }
    # 最小有效内容长度（字符数）
    MIN_CONTENT_LENGTH = 200
    # 网页抓取超时（秒）
    FETCH_TIMEOUT = 15
    
    # ============================================
    # 截图配置
    # ============================================
    # 截图超时时间（毫秒）
    PLAYWRIGHT_TIMEOUT = 30000
    # 截图分辨率
    SCREENSHOT_WIDTH = 1280
    SCREENSHOT_HEIGHT = 800
    # 最大截图数量（避免截图过多导致PDF过大）
    MAX_SCREENSHOTS = 5
    
    # ============================================
    # PDF输出配置
    # ============================================
    PDF_OUTPUT_PATH = OUTPUT_DIR / "hk_branch_sentiment_report.pdf"
    CSS_PATH = ASSETS_DIR / "styles.css"
    
    # ============================================
    # 日志配置
    # ============================================
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls) -> bool:
        """
        验证必要配置是否存在
        
        Returns:
            True: 配置验证通过
            Raises ValueError: 配置缺失
            
        说明：
            - 当AI_ENABLED=False时，OPENAI_API_KEY非必需
            - SERPER_API_KEY始终必需（用于搜索）
        """
        # 检查Serper API密钥（必需）
        if not cls.SERPER_API_KEY:
            raise ValueError(
                "❌ 缺少必要配置: SERPER_API_KEY\n"
                "   请在.env文件中配置，或设置环境变量\n"
                "   获取地址: https://serper.dev"
            )
        
        # 当AI启用时，检查OpenAI API密钥
        if cls.AI_ENABLED and not cls.OPENAI_API_KEY:
            raise ValueError(
                "❌ AI功能已启用，但缺少OPENAI_API_KEY\n"
                "   请在.env文件中配置，或设置环境变量\n"
                "   或将AI_ENABLED设置为False跳过AI分析"
            )
        
        logger.info(f"✓ 配置验证通过")
        logger.info(f"   AI功能: {'✅ 已启用' if cls.AI_ENABLED else '❌ 已禁用（使用占位符）'}")
        logger.info(f"   搜索关键词: {cls.SEARCH_QUERY}")
        logger.info(f"   检索数量: {cls.SEARCH_RESULTS_COUNT}条")
        
        return True

# ============================================
# 日志配置（在类外初始化）
# ============================================
import logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ============================================
# 确保输出目录存在
# ============================================
Config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
Config.SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================
# 占位符文本（当AI禁用时使用）
# ============================================
AI_PLACEHOLDER = {
    "section_one_summary": (
        "【AI分析已禁用】\n\n"
        "提示：当前配置已关闭AI分析功能。如需启用智能风险识别与情感分析，\n"
        "请在.env文件中设置：AI_ENABLED=True 并配置OPENAI_API_KEY\n\n"
        "本区域将显示由AI生成的综合舆情风险评估，包括：\n"
        "- 洗钱、监管处罚、违规等风险识别\n"
        "- 整体舆情风险等级评估（高/中/低）\n"
        "- 关键风险事件与涉及机构提取"
    ),
    "section_one_table_summary": "【AI分析已禁用】待详细分析",
    "section_two_summary": (
        "【AI分析已禁用】\n\n"
        "提示：当前配置已关闭AI分析功能。\n"
        "本区域将显示由AI生成的网页内容摘要与风险评估。"
    ),
    "sentiment": "中性",
    "risk_keywords": ["AI未启用"],
    "compliance_issues": ["AI分析功能已关闭"],
    "confidence_score": 0.0
}