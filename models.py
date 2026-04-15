from typing import List, Optional, Literal
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime

# ============================================
# 搜索结果相关模型
# ============================================

class SearchResultItem(BaseModel):
    """
    Google搜索结果单条目模型
    
    来源：Serper API返回的搜索结果
    用途：存储原始搜索结果，供后续处理
    """
    title: str = Field(..., description="搜索结果标题", min_length=1)
    url: HttpUrl = Field(..., description="目标URL")
    snippet: str = Field(..., description="Google提供的摘要", min_length=1)
    position: int = Field(..., ge=1, description="搜索结果位置（1开始）")
    date: Optional[str] = Field(None, description="发布日期（如有）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "香港金管局对某银行分行处罚公告",
                "url": "https://www.hkma.gov.hk/chi/news-and-media/press-releases/...",
                "snippet": "香港金管局今日公布对某银行香港分行的处罚决定，涉及反洗钱合规问题...",
                "position": 1,
                "date": "2026-02-01"
            }
        }


# ============================================
# 网页内容相关模型
# ============================================

class ArticleContent(BaseModel):
    """
    网页内容模型
    
    用途：存储抓取并清洗后的网页内容
    特点：包含原始HTML（供调试）和清洗后的纯文本
    """
    title: str = Field(..., description="网页标题")
    url: HttpUrl = Field(..., description="网页URL")
    raw_html: str = Field(..., description="原始HTML内容", exclude=True)  # 不序列化到PDF
    cleaned_text: str = Field(..., description="清洗后的正文文本")
    is_valid: bool = Field(True, description="是否有效内容（非PDF/乱码等）")
    content_length: int = Field(0, description="清洗后文本长度（字符数）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "某银行香港分行反洗钱合规整改报告",
                "url": "https://example.com/news/aml-compliance",
                "cleaned_text": "本行香港分行已完成反洗钱系统升级...",
                "is_valid": True,
                "content_length": 1500
            }
        }


# ============================================
# AI分析结果模型
# ============================================

class AISummary(BaseModel):
    """
    AI分析结果模型
    
    用途：存储AI对单个网页的分析结果
    字段说明：
        - summary: 内容摘要（100字以内）
        - sentiment: 情感倾向（正面/中性/负面）
        - risk_keywords: 识别到的风险关键词
        - compliance_issues: 合规问题列表
        - confidence_score: 置信度分数（0.0-1.0）
    """
    summary: str = Field(..., description="内容摘要", min_length=1)
    sentiment: Literal["正面", "中性", "负面"] = Field(..., description="情感倾向")
    risk_keywords: List[str] = Field(
        default_factory=list,
        description="识别到的风险关键词（如：洗钱、处罚、违规）"
    )
    compliance_issues: List[str] = Field(
        default_factory=list,
        description="具体合规问题描述"
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="分析置信度分数（0.0-1.0）"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "summary": "报道指出某银行香港分行因反洗钱系统缺陷被金管局处罚500万港元",
                "sentiment": "负面",
                "risk_keywords": ["洗钱", "处罚", "反洗钱", "系统缺陷"],
                "compliance_issues": ["反洗钱监控失效", "客户尽职调查不足"],
                "confidence_score": 0.92
            }
        }


# ============================================
# PDF报告数据模型
# ============================================

class ReportSectionOneItem(BaseModel):
    """
    PDF第一部分表格行数据模型
    
    用途：生成舆情概览表格的每一行
    对应：关键词、标题、AI总结、情感倾向、URL
    """
    keyword: str = Field(..., description="搜索关键词")
    url_title: str = Field(..., description="URL标题（截断显示）")
    url: HttpUrl = Field(..., description="完整URL")
    ai_summary: str = Field(..., description="AI风险摘要")
    sentiment: Literal["正面", "中性", "负面"] = Field(..., description="情感倾向（中文）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "keyword": "香港分行 洗钱",
                "url_title": "香港金管局处罚公告...",
                "url": "https://www.hkma.gov.hk/...",
                "ai_summary": "监管机构对某银行分行反洗钱违规处罚",
                "sentiment": "负面"
            }
        }


class ReportSectionTwoItem(BaseModel):
    """
    PDF第二部分详细内容模型
    
    用途：生成每个网页的详细分析区块
    包含：标题、URL、Google摘要、内容总结、情感倾向、截图路径
    """
    title: str = Field(..., description="网页标题")
    url: HttpUrl = Field(..., description="网页URL")
    google_snippet: str = Field(..., description="Google搜索摘要")
    content_summary: str = Field(..., description="AI内容总结")
    sentiment: Literal["正面", "中性", "负面"] = Field(..., description="情感倾向")
    screenshot_path: Optional[str] = Field(None, description="截图文件路径（相对或绝对）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "某银行香港分行完成反洗钱系统升级",
                "url": "https://example.com/news",
                "google_snippet": "该行宣布已完成香港分行反洗钱监控系统全面升级...",
                "content_summary": "正面报道：银行主动升级合规系统，体现负责任态度",
                "sentiment": "正面",
                "screenshot_path": "output/screenshots/screenshot_01.png"
            }
        }


class ReportMetadata(BaseModel):
    """
    报告元数据模型
    
    用途：存储报告生成相关信息
    """
    keyword: str = Field(..., description="搜索关键词")
    total_results: int = Field(..., ge=0, description="搜索返回的总结果数")
    valid_articles: int = Field(..., ge=0, description="有效分析的文章数量")
    generation_time: str = Field(..., description="报告生成时间（格式化字符串）")
    ai_enabled: bool = Field(..., description="AI功能是否启用")
    
    class Config:
        json_schema_extra = {
            "example": {
                "keyword": "香港分行 洗钱 监管处罚",
                "total_results": 20,
                "valid_articles": 15,
                "generation_time": "2026年02月10日 14:30",
                "ai_enabled": True
            }
        }