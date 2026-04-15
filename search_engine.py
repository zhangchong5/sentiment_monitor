"""
搜索引擎模块 - Serper API封装（Google搜索替代方案）

Serper优势：
✅ 真正的Google搜索结果（非限定域）
✅ 免费额度2500次/月（舆情监测足够）
✅ 无需验证码，稳定可靠
✅ 支持新闻搜索（tbm=nws），更适合舆情场景

API文档：https://serper.dev
"""
import requests
import logging
from typing import List
from models import SearchResultItem
from config import Config, logger

class SerperSearchEngine:
    """
    Serper搜索引擘封装类
    
    功能：
        - 调用Serper API执行Google搜索
        - 解析返回结果为结构化数据
        - 支持新闻搜索模式（更适合舆情）
    
    使用示例：
        >>> engine = SerperSearchEngine()
        >>> results = engine.search("香港分行 洗钱", num_results=20)
        >>> print(f"找到{len(results)}条结果")
    """
    
    def __init__(self):
        """
        初始化Serper搜索引擎
        
        验证：
            - 检查API密钥是否存在
            - 设置请求头
        """
        if not Config.SERPER_API_KEY:
            raise ValueError("Serper API密钥未配置（SERPER_API_KEY）")
        
        self.api_key = Config.SERPER_API_KEY
        self.api_url = Config.SERPER_API_URL
        self.headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        logger.info(f"✓ Serper搜索引擎初始化完成")
        logger.debug(f"   API地址: {self.api_url}")
    
    def search(self, query: str, num_results: int = 20) -> List[SearchResultItem]:
        """
        执行Google搜索
        
        参数：
            query: str - 搜索关键词
            num_results: int - 请求返回的结果数量（默认20，最大100）
        
        返回：
            List[SearchResultItem] - 搜索结果列表
        
        异常：
            requests.exceptions.RequestException - 网络请求失败
            ValueError - API返回错误
        
        执行流程：
            1. 构建请求payload（含关键词、数量、地区、语言）
            2. 发送POST请求到Serper API
            3. 解析返回的JSON数据
            4. 转换为SearchResultItem对象列表
            5. 返回结果（按位置排序）
        """
        logger.info(f"🔍 执行搜索: '{query}'（请求{num_results}条结果）")
        
        # 构建请求参数
        # tbm="nws" 表示新闻搜索，更适合舆情监测场景
        payload = {
            "q": query,
            "num": min(num_results, 100),  # Serper单次最大100条
            "gl": Config.SEARCH_REGION,    # 地区：香港
            "hl": Config.SEARCH_LANGUAGE,  # 语言：繁体中文
            "tbm": "nws"                   # 搜索类型：新闻（更适合舆情）
        }
        
        try:
            # 发送请求
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            # 解析响应
            data = response.json()
            
            # 检查API错误
            if "error" in data:
                error_msg = data.get("error", {}).get("message", "未知错误")
                raise ValueError(f"Serper API错误: {error_msg}")
            
            # 提取新闻结果（优先使用news字段）
            news_items = data.get("news", [])
            
            if not news_items:
                logger.warning("⚠️ 未找到新闻结果，尝试使用常规搜索结果")
                # 回退到常规搜索结果
                news_items = data.get("organic", [])[:num_results]
            
            # 转换为SearchResultItem对象
            results = []
            for idx, item in enumerate(news_items[:num_results], 1):
                result_item = SearchResultItem(
                    title=item.get("title", "无标题"),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", "无摘要"),
                    position=idx,
                    date=item.get("date", None)
                )
                results.append(result_item)
            
            logger.info(f"✅ 搜索成功，返回{len(results)}条结果")
            
            # 记录前3条结果预览
            for i, item in enumerate(results[:3], 1):
                logger.debug(f"   [{i}] {item.title[:50]}...")
            
            return results
            
        except requests.exceptions.Timeout:
            logger.error("❌ 搜索超时（10秒）")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 搜索请求失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"❌ 搜索处理异常: {str(e)}")
            raise
    
    def search_general(self, query: str, num_results: int = 20) -> List[SearchResultItem]:
        """
        执行常规搜索（非新闻）
        
        用途：当新闻搜索结果不足时的备选方案
        区别：不设置tbm参数，返回综合搜索结果
        """
        logger.info(f"🔍 执行常规搜索: '{query}'")
        
        payload = {
            "q": query,
            "num": min(num_results, 100),
            "gl": Config.SEARCH_REGION,
            "hl": Config.SEARCH_LANGUAGE
            # 不设置tbm，使用默认综合搜索
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if "error" in data:
                raise ValueError(f"Serper API错误: {data['error']}")
            
            organic_items = data.get("organic", [])
            results = []
            for idx, item in enumerate(organic_items[:num_results], 1):
                results.append(SearchResultItem(
                    title=item.get("title", "无标题"),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", "无摘要"),
                    position=idx,
                    date=item.get("date", None)
                ))
            
            logger.info(f"✅ 常规搜索成功，返回{len(results)}条结果")
            return results
            
        except Exception as e:
            logger.error(f"❌ 常规搜索失败: {str(e)}")
            raise


# ============================================
# 工厂函数：创建搜索引擎实例
# ============================================

def create_search_engine() -> SerperSearchEngine:
    """
    创建搜索引擎实例的工厂函数
    
    用途：
        - 统一搜索引擎创建入口
        - 便于未来扩展多引擎支持
    
    返回：
        SerperSearchEngine实例
    """
    return SerperSearchEngine()