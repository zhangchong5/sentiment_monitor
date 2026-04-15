"""
配置管理模块 - 集中管理所有应用配置参数
支持环境变量与默认值双重机制，确保安全性与灵活性
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# ============================================
# 环境变量加载
# ============================================
load_dotenv()  # 从.env 文件加载环境变量

# ============================================
# 日志配置（在类外初始化）
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class Config:
    """
    应用配置类 - 单一可信源配置管理
    
    所有配置项均支持通过环境变量覆盖，优先级：
    1. 环境变量（.env 文件或系统环境变量）
    2. 代码中的默认值
    
    关键配置说明：
    - AI_ENABLED: AI 功能总开关（False = 跳过所有 AI 调用，用占位符替代）
    - SERPER_API_KEY: Serper 搜索 API 密钥（必需）
    - SEARCH_QUERY: 搜索关键词（可自定义）
    """
    
    # ============================================
    # 项目路径配置
    # ============================================
    BASE_DIR = Path(__file__).parent.parent.parent.resolve()
    OUTPUT_DIR = BASE_DIR / "output"
    SCREENSHOT_DIR = OUTPUT_DIR / "screenshots"
    ASSETS_DIR = BASE_DIR / "assets"
    
    # ============================================
    # AI 功能总开关 - 核心配置！
    # ============================================
    AI_ENABLED = os.getenv("AI_ENABLED", "False").lower() in ("true", "1", "yes", "y")
    
    # ============================================
    # API 配置
    # ============================================
    # --- Serper API（Google 搜索替代方案）---
    SERPER_API_KEY = os.getenv("SERPER_API_KEY", "ae80a71d2d3aa9308fc54f6ba99f743fb9d7b23a")
    SERPER_API_URL = "https://google.serper.dev/search"
    
    # --- AI API 配置（仅当 AI_ENABLED=True 时需要）---
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # ============================================
    # 搜索配置
    # ============================================
    SEARCH_QUERY = os.getenv(
        "SEARCH_QUERY",
        "香港分行 洗钱 监管处罚 违规 反洗钱 AML 合规"
    )
    SEARCH_RESULTS_COUNT = int(os.getenv("SEARCH_RESULTS_COUNT", "20"))
    SEARCH_REGION = "hk"
    SEARCH_LANGUAGE = "zh-HK"
    
    # ============================================
    # 网页抓取配置
    # ============================================
    EXCLUDE_EXTENSIONS = {
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', 
        '.ppt', '.pptx', '.zip', '.rar', '.7z',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp'
    }
    MIN_CONTENT_LENGTH = 200
    FETCH_TIMEOUT = 15
    
    # ============================================
    # 截图配置
    # ============================================
    PLAYWRIGHT_TIMEOUT = 30000
    SCREENSHOT_WIDTH = 1280
    SCREENSHOT_HEIGHT = 800
    MAX_SCREENSHOTS = 5
    
    # ============================================
    # PDF 输出配置
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
            - 当 AI_ENABLED=False 时，OPENAI_API_KEY 非必需
            - SERPER_API_KEY 始终必需（用于搜索）
        """
        if not cls.SERPER_API_KEY:
            raise ValueError(
                "❌ 缺少必要配置：SERPER_API_KEY\n"
                "   请在.env 文件中配置，或设置环境变量\n"
                "   获取地址：https://serper.dev"
            )
        
        if cls.AI_ENABLED and not cls.OPENAI_API_KEY:
            raise ValueError(
                "❌ AI 功能已启用，但缺少 OPENAI_API_KEY\n"
                "   请在.env 文件中配置，或设置环境变量\n"
                "   或将 AI_ENABLED 设置为 False 跳过 AI 分析"
            )
        
        logger.info(f"✓ 配置验证通过")
        logger.info(f"   AI 功能：{'✅ 已启用' if cls.AI_ENABLED else '❌ 已禁用（使用占位符）'}")
        logger.info(f"   搜索关键词：{cls.SEARCH_QUERY}")
        logger.info(f"   检索数量：{cls.SEARCH_RESULTS_COUNT}条")
        
        return True


# ============================================
# 确保输出目录存在
# ============================================
Config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
Config.SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================
# 占位符文本（当 AI 禁用时使用）
# ============================================
AI_PLACEHOLDER = {
    "section_one_summary": (
        "【AI 分析已禁用】\n\n"
        "提示：当前配置已关闭 AI 分析功能。如需启用智能风险识别与情感分析，\n"
        "请在.env 文件中设置：AI_ENABLED=True 并配置 OPENAI_API_KEY\n\n"
        "本区域将显示由 AI 生成的综合舆情风险评估，包括：\n"
        "- 洗钱、监管处罚、违规等风险识别\n"
        "- 整体舆情风险等级评估（高/中/低）\n"
        "- 关键风险事件与涉及机构提取"
    ),
    "section_one_table_summary": "【AI 分析已禁用】待详细分析",
    "section_two_summary": (
        "【AI 分析已禁用】\n\n"
        "提示：当前配置已关闭 AI 分析功能。\n"
        "本区域将显示由 AI 生成的网页内容摘要与风险评估。"
    ),
    "sentiment": "中性",
    "risk_keywords": ["AI 未启用"],
    "compliance_issues": ["AI 分析功能已关闭"],
    "confidence_score": 0.0
}
