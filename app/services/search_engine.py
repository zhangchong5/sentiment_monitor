"""
搜索引擎服务 - Serper API 封装（Google 搜索替代方案）
"""
import requests
import logging
from typing import List

from app.core.config import Config, logger
from app.models.data_models import SearchResultItem


class SearchEngine:
    """
    Serper 搜索引擎封装类
    
    功能：
        - 调用 Serper API 执行 Google 搜索
        - 解析返回结果为结构化数据
        - 支持新闻搜索模式（更适合舆情）
    """
    
    def __init__(self):
        """初始化 Serper 搜索引擎"""
        if not Config.SERPER_API_KEY:
            raise ValueError("Serper API 密钥未配置（SERPER_API_KEY）")
        
        self.api_key = Config.SERPER_API_KEY
        self.api_url = Config.SERPER_API_URL
        self.headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        logger.info(f"✓ Serper 搜索引擎初始化完成")
        logger.debug(f"   API 地址：{self.api_url}")
    
    def search(self, query: str, num_results: int = 20) -> List[SearchResultItem]:
        """
        执行 Google 搜索（新闻模式）
        
        Args:
            query: 搜索关键词
            num_results: 请求返回的结果数量（默认 20，最大 100）
        
        Returns:
            List[SearchResultItem]: 搜索结果列表
        """
        logger.info(f"🔍 执行搜索：'{query}'（请求{num_results}条结果）")
        
        payload = {
            "q": query,
            "num": min(num_results, 100),
            "gl": Config.SEARCH_REGION,
            "hl": Config.SEARCH_LANGUAGE,
            "tbm": "nws"  # 新闻搜索
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
                error_msg = data.get("error", {}).get("message", "未知错误")
                raise ValueError(f"Serper API 错误：{error_msg}")
            
            news_items = data.get("news", [])
            
            if not news_items:
                logger.warning("⚠️ 未找到新闻结果，尝试使用常规搜索结果")
                news_items = data.get("organic", [])[:num_results]
            
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
            return results
            
        except requests.exceptions.Timeout:
            logger.error("❌ 搜索超时（10 秒）")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 搜索请求失败：{str(e)}")
            raise
        except Exception as e:
            logger.error(f"❌ 搜索处理异常：{str(e)}")
            raise
    
    def search_general(self, query: str, num_results: int = 20) -> List[SearchResultItem]:
        """执行常规搜索（非新闻）"""
        logger.info(f"🔍 执行常规搜索：'{query}'")
        
        payload = {
            "q": query,
            "num": min(num_results, 100),
            "gl": Config.SEARCH_REGION,
            "hl": Config.SEARCH_LANGUAGE
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
                raise ValueError(f"Serper API 错误：{data['error']}")
            
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
            logger.error(f"❌ 常规搜索失败：{str(e)}")
            raise


def create_search_engine() -> SearchEngine:
    """创建搜索引擎实例的工厂函数"""
    return SearchEngine()
