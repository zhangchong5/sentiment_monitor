"""
AI分析引擎 - 封装LLM调用，实现舆情分析与风险识别

核心特性：
✅ 受AI_ENABLED开关控制（关闭时返回占位符）
✅ 针对金融合规场景定制提示词
✅ 结构化输出（JSON Schema）
✅ 错误处理与降级策略

提示词设计原则：
1. 角色定位：金融合规分析师
2. 风险聚焦：洗钱、监管处罚、违规操作
3. 输出规范：明确格式要求（避免自由发挥）
4. 语言要求：中文输出（繁体/简体自适应）
"""
import json
import logging
import requests
from typing import List

from app.core.config import Config, logger, AI_PLACEHOLDER
from app.models.data_models import AISummary, SearchResultItem, ArticleContent


class AIAnalyzer:
    """
    AI分析引擎类
    
    功能：
        - 分析搜索结果概要（第一部分）
        - 分析单个网页内容（第二部分）
        - 受AI_ENABLED开关控制
    
    工作模式：
        模式1（AI_ENABLED=True）：
            - 调用OpenAI API
            - 返回真实分析结果
        
        模式2（AI_ENABLED=False）：
            - 跳过API调用
            - 返回预定义占位符文本
            - 适合开发测试阶段
    
    提示词策略：
        - 第一部分：综合风险评估（200字以内）
        - 第二部分：单网页深度分析（100字以内 + 结构化JSON）
    """
    
    def __init__(self):
        """
        初始化AI分析引擎
        
        验证：
            - 当AI_ENABLED=True时，检查API密钥
            - 记录当前工作模式
        """
        self.ai_enabled = Config.AI_ENABLED
        
        if self.ai_enabled:
            if not Config.OPENAI_API_KEY:
                raise ValueError("AI功能已启用，但OPENAI_API_KEY未配置")
            self.api_key = Config.OPENAI_API_KEY
            self.base_url = Config.OPENAI_BASE_URL
            self.model = Config.OPENAI_MODEL
            logger.info(f"✓ AI分析引擎初始化完成（模型: {self.model}）")
        else:
            logger.info("⚠️ AI分析引擎初始化完成（功能已禁用，使用占位符）")
    
    # ============================================
    # 第一部分：搜索结果概要分析
    # ============================================
    
    def _build_section_one_prompt(self, items: List[SearchResultItem]) -> str:
        """
        构建第一部分AI总结提示词（表格概要分析）
        
        目标：综合评估整体舆情风险
        
        关键要素：
            - 识别洗钱、监管处罚、违规等风险
            - 评估风险等级（高/中/低）
            - 提取关键事件与机构
            - 200字以内专业总结
        
        参数：
            items: List[SearchResultItem] - 搜索结果列表
        
        返回：
            str - 完整提示词
        """
        # 格式化搜索结果
        items_text = "\n".join([
            f"{i+1}. 标题: {item.title}\n"
            f"   URL: {item.url}\n"
            f"   摘要: {item.snippet}"
            for i, item in enumerate(items[:10])  # 限制输入长度
        ])
        
        prompt = f"""你是一名专业的金融合规分析师，负责分析香港银行业的舆情风险。

请基于以下搜索结果，进行综合风险评估：

{items_text}

【分析要求】
1. 识别与以下关键词相关的内容：
   - 洗钱 / 反洗钱(AML) / KYC
   - 监管处罚 / 罚款 / 警告
   - 违规操作 / 合规缺陷 / 内控失效
   - 金融犯罪 / 欺诈 / 操纵市场

2. 评估整体舆情风险等级：高 / 中 / 低

3. 提取关键风险事件与涉及机构（如有）

4. 给出专业、客观的总结（200字以内）

【输出格式】
纯文本总结，不包含任何标记、标题或编号。直接输出分析内容。"""
        
        return prompt
    
    def analyze_section_one(self, items: List[SearchResultItem]) -> str:
        """
        分析第一部分 - 整体舆情概要
        
        参数：
            items: List[SearchResultItem] - 搜索结果列表
        
        返回：
            str - AI生成的综合风险评估文本
        
        工作流程：
            AI启用模式：
                1. 构建提示词
                2. 调用LLM API
                3. 返回生成文本
            
            AI禁用模式：
                1. 返回占位符文本
        """
        if not self.ai_enabled:
            logger.debug("   ↳ AI功能禁用，返回占位符")
            return AI_PLACEHOLDER["section_one_summary"]
        
        # AI启用模式
        prompt = self._build_section_one_prompt(items)
        
        logger.debug("   ↳ 调用AI分析（第一部分：整体概要）...")
        response = self._call_llm(
            prompt=prompt,
            temperature=0.3,  # 降低随机性，确保稳定性
            max_tokens=300
        )
        
        logger.debug(f"   ↳ AI分析完成（{len(response)}字符）")
        return response
    
    # ============================================
    # 第二部分：单网页深度分析
    # ============================================
    
    def _build_section_two_prompt(self, content: ArticleContent) -> str:
        """
        构建第二部分AI总结提示词（单网页深度分析）
        
        目标：对单个网页进行风险识别与情感判断
        
        输出要求：
            - 结构化JSON（确保解析可靠性）
            - 包含摘要、情感、风险关键词、合规问题、置信度
        
        参数：
            content: ArticleContent - 网页内容对象
        
        返回：
            str - 完整提示词
        """
        # 限制输入文本长度（避免token超限）
        text_preview = content.cleaned_text[:3000]
        
        prompt = f"""你是一名金融合规专家，请分析以下网页内容的舆情风险。

【网页信息】
标题: {content.title}
URL: {content.url}

【内容摘要】
{text_preview}

【分析要求】
1. 判断内容情感倾向（基于对香港分行声誉的影响）：
   - 正面：表扬、正面报道、合规改进
   - 负面：批评、处罚、违规、风险事件
   - 中性：事实陈述、无明显倾向

2. 识别具体风险点（如存在）：
   - 洗钱 / 反洗钱(AML)缺陷
   - 监管处罚 / 罚款
   - 违规操作 / 合规问题
   - 内控失效 / 系统缺陷

3. 生成100字以内的专业总结

【输出格式】
严格输出JSON格式，不包含任何其他文本：
{{
  "summary": "内容总结（字符串）",
  "sentiment": "positive|neutral|negative（英文小写）",
  "risk_keywords": ["关键词1", "关键词2"]（字符串数组）,
  "compliance_issues": ["问题1", "问题2"]（字符串数组）,
  "confidence_score": 0.95（浮点数，0.0-1.0）
}}"""
        
        return prompt
    
    def analyze_section_two(self, content: ArticleContent) -> AISummary:
        """
        分析第二部分 - 单网页深度分析
        
        参数：
            content: ArticleContent - 网页内容对象
        
        返回：
            AISummary - 结构化分析结果
        
        工作流程：
            AI禁用模式：
                1. 返回占位符AISummary
            
            AI启用模式：
                1. 验证内容有效性
                2. 构建提示词
                3. 调用LLM API（要求JSON输出）
                4. 解析JSON响应
                5. 映射情感值（英文→中文）
                6. 返回AISummary对象
        """
        # 模式1：AI禁用 - 返回占位符
        if not self.ai_enabled:
            logger.debug("   ↳ AI功能禁用，返回占位符分析结果")
            return AISummary(
                summary=AI_PLACEHOLDER["section_two_summary"],
                sentiment=AI_PLACEHOLDER["sentiment"],
                risk_keywords=AI_PLACEHOLDER["risk_keywords"],
                compliance_issues=AI_PLACEHOLDER["compliance_issues"],
                confidence_score=AI_PLACEHOLDER["confidence_score"]
            )
        
        # 模式2：AI启用
        
        # 步骤1：验证内容有效性
        if not content.is_valid or len(content.cleaned_text.strip()) < 50:
            logger.warning("   ↳ 内容无效或过短，返回空分析结果")
            return AISummary(
                summary="⚠️ 内容无效或过短，无法进行分析",
                sentiment="中性",
                risk_keywords=[],
                compliance_issues=[],
                confidence_score=0.1
            )
        
        # 步骤2-3：构建提示词并调用LLM
        prompt = self._build_section_two_prompt(content)
        
        logger.debug("   ↳ 调用AI分析（第二部分：网页深度分析）...")
        response = self._call_llm(
            prompt=prompt,
            temperature=0.2,  # 更低随机性，确保准确性
            max_tokens=300,
            response_format={"type": "json_object"}  # 强制JSON输出
        )
        
        # 步骤4-6：解析响应并返回
        try:
            data = json.loads(response)
            
            # 映射情感值（英文→中文）
            sentiment_map = {
                "positive": "正面",
                "neutral": "中性", 
                "negative": "负面"
            }
            sentiment_cn = sentiment_map.get(
                data.get("sentiment", "neutral").lower(),
                "中性"
            )
            
            # 构建AISummary对象
            result = AISummary(
                summary=data.get("summary", "分析异常"),
                sentiment=sentiment_cn,
                risk_keywords=data.get("risk_keywords", []),
                compliance_issues=data.get("compliance_issues", []),
                confidence_score=float(data.get("confidence_score", 0.5))
            )
            
            logger.debug(
                f"   ↳ AI分析完成（情感: {result.sentiment}, "
                f"置信度: {result.confidence_score:.2f}）"
            )
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"   ↳ AI响应JSON解析失败: {str(e)}")
            logger.debug(f"   ↳ 原始响应: {response[:200]}...")
            return self._create_error_summary("AI响应格式错误")
        except KeyError as e:
            logger.error(f"   ↳ AI响应缺少必要字段: {str(e)}")
            return self._create_error_summary("AI响应字段缺失")
        except Exception as e:
            logger.error(f"   ↳ AI分析异常: {str(e)}")
            return self._create_error_summary(f"分析异常: {str(e)}")
    
    def _create_error_summary(self, error_msg: str) -> AISummary:
        """创建错误状态的AISummary对象"""
        return AISummary(
            summary=f"⚠️ {error_msg}",
            sentiment="中性",
            risk_keywords=["分析失败"],
            compliance_issues=[error_msg],
            confidence_score=0.0
        )
    
    # ============================================
    # LLM API调用底层实现
    # ============================================
    
    def _call_llm(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        response_format: dict = None
    ) -> str:
        """
        调用LLM API的通用方法
        
        参数：
            prompt: str - 提示词
            temperature: float - 采样温度（0.0-1.0）
            max_tokens: int - 最大生成token数
            response_format: dict - 响应格式要求（如{"type": "json_object"}）
        
        返回：
            str - LLM生成的文本
        
        异常：
            RuntimeError - API调用失败
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一名专业的金融合规分析师，专注于香港银行业风险识别。请用中文（繁体/简体均可）回答。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # 添加响应格式要求（如JSON）
        if response_format:
            payload["response_format"] = response_format
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            return content
            
        except requests.exceptions.Timeout:
            raise RuntimeError("LLM API调用超时（30秒）")
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json() if e.response else "未知错误"
            raise RuntimeError(f"LLM API HTTP错误: {error_detail}")
        except Exception as e:
            raise RuntimeError(f"LLM API调用失败: {str(e)}")


# ============================================
# 工厂函数：创建AI分析器实例
# ============================================

def create_ai_analyzer() -> AIAnalyzer:
    """
    创建AI分析器实例的工厂函数
    
    返回：
        AIAnalyzer实例
    """
    return AIAnalyzer()