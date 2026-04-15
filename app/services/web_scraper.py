"""
网页抓取服务 - 智能提取正文内容，过滤噪声
"""
import requests
from typing import Optional
from bs4 import BeautifulSoup
from readability import Document

from app.core.config import Config, logger
from app.models.data_models import ArticleContent


class WebScraper:
    """
    网页内容抓取与清洗类
    
    功能：
        - 抓取网页 HTML 内容
        - 智能提取正文（去除导航、广告等噪声）
        - 内容质量验证（长度检查）
        - 返回结构化 ArticleContent 对象
    """
    
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-HK,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive"
    }
    
    def __init__(self):
        """初始化网页抓取器"""
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        logger.info("✓ 网页抓取器初始化完成")
    
    def should_skip_url(self, url: str) -> bool:
        """判断 URL 是否应跳过（基于扩展名等规则）"""
        url_lower = url.lower().strip()
        
        if any(url_lower.endswith(ext) for ext in Config.EXCLUDE_EXTENSIONS):
            return True
        
        if any(keyword in url_lower for keyword in ["file=", "download", "attachment"]):
            return True
        
        if not url_lower.startswith(("http://", "https://")):
            return True
        
        return False
    
    def fetch_content(self, url: str) -> Optional[ArticleContent]:
        """
        抓取并清洗网页内容
        
        Args:
            url: 目标网页 URL
        
        Returns:
            Optional[ArticleContent]: 成功返回 ArticleContent，失败返回 None
        """
        if self.should_skip_url(url):
            return None
        
        logger.debug(f"   ↳ 抓取网页：{url[:60]}...")
        
        try:
            response = self.session.get(
                url,
                timeout=Config.FETCH_TIMEOUT,
                allow_redirects=True
            )
            response.raise_for_status()
            
            if response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding
            
            html_content = response.text
            
            doc = Document(html_content)
            cleaned_html = doc.summary()
            page_title = doc.title() or "无标题"
            
            soup = BeautifulSoup(cleaned_html, 'html.parser')
            
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 
                           'aside', 'form', 'button', 'input']):
                tag.decompose()
            
            cleaned_text = soup.get_text(separator='\n', strip=True)
            
            content_length = len(cleaned_text)
            is_valid = content_length >= Config.MIN_CONTENT_LENGTH
            
            if not is_valid:
                logger.warning(
                    f"   ↳ 内容过短（{content_length}字符），可能为无效页面：{url[:50]}..."
                )
            
            return ArticleContent(
                title=page_title,
                url=url,
                raw_html=html_content,
                cleaned_text=cleaned_text[:5000],
                is_valid=is_valid,
                content_length=content_length
            )
            
        except requests.exceptions.Timeout:
            logger.warning(f"   ↳ 抓取超时（{Config.FETCH_TIMEOUT}秒）: {url[:50]}...")
            return None
        except requests.exceptions.ConnectionError:
            logger.warning(f"   ↳ 连接失败：{url[:50]}...")
            return None
        except requests.exceptions.HTTPError as e:
            logger.warning(f"   ↳ HTTP 错误 {e.response.status_code}: {url[:50]}...")
            return None
        except Exception as e:
            logger.error(f"   ↳ 抓取异常 {url[:50]}...: {str(e)}")
            return None


def create_web_scraper() -> WebScraper:
    """创建网页抓取器实例的工厂函数"""
    return WebScraper()
