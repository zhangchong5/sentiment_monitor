"""
网页内容抓取模块 - 智能提取正文内容，过滤噪声

核心技术：
✅ readability-lxml：专业正文提取算法（源自Mozilla Readability）
✅ BeautifulSoup：HTML清洗与结构化
✅ 智能内容过滤：跳过无效资源，确保数据质量

处理流程：
1. 检查URL是否应跳过（基于扩展名规则）
2. 发送HTTP请求（带超时控制）
3. 使用readability提取正文HTML
4. 清洗HTML（移除脚本、样式等噪声）
5. 提取纯文本并验证长度
6. 返回结构化ArticleContent对象
"""
import requests
import logging
from typing import Optional
from bs4 import BeautifulSoup
from readability import Document
from models import ArticleContent
from config import Config, logger

class WebScraper:
    """
    网页内容抓取与清洗类
    
    功能：
        - 抓取网页HTML内容
        - 智能提取正文（去除导航、广告等噪声）
        - 内容质量验证（长度检查）
        - 返回结构化ArticleContent对象
    
    特性：
        - 自动跳过非HTML资源（PDF、文档等）
        - 支持编码自动检测
        - 内置请求头模拟浏览器
    """
    
    # 浏览器User-Agent（避免被简单反爬）
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
        """
        初始化网页抓取器
        
        创建requests会话，复用TCP连接提升性能
        """
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        logger.info("✓ 网页抓取器初始化完成")
    
    def should_skip_url(self, url: str) -> bool:
        """
        判断URL是否应跳过（基于扩展名等规则）
        
        跳过规则：
            1. 文件扩展名在排除列表中（PDF、Office文档等）
            2. 包含明显下载参数（file=, download等）
            3. 非HTTP/HTTPS协议
        
        参数：
            url: str - 待检查的URL
        
        返回：
            bool - True表示应跳过，False表示可抓取
        
        示例：
            >>> scraper = WebScraper()
            >>> scraper.should_skip_url("https://example.com/report.pdf")
            True
            >>> scraper.should_skip_url("https://example.com/news/article")
            False
        """
        url_lower = url.lower().strip()
        
        # 规则1：检查排除的文件扩展名
        if any(url_lower.endswith(ext) for ext in Config.EXCLUDE_EXTENSIONS):
            logger.debug(f"   ↳ 跳过（文件扩展名）: {url}")
            return True
        
        # 规则2：检查明显非网页内容参数
        if any(keyword in url_lower for keyword in ["file=", "download", "attachment"]):
            logger.debug(f"   ↳ 跳过（下载链接）: {url}")
            return True
        
        # 规则3：检查协议
        if not url_lower.startswith(("http://", "https://")):
            logger.debug(f"   ↳ 跳过（非HTTP协议）: {url}")
            return True
        
        return False
    
    def fetch_content(self, url: str) -> Optional[ArticleContent]:
        """
        抓取并清洗网页内容
        
        参数：
            url: str - 目标网页URL
        
        返回：
            Optional[ArticleContent] - 成功返回ArticleContent，失败返回None
        
        处理步骤：
            1. 检查URL是否应跳过
            2. 发送HTTP GET请求（带超时）
            3. 检测并设置正确编码
            4. 使用readability提取正文HTML
            5. 使用BeautifulSoup清洗噪声元素
            6. 提取纯文本并验证长度
            7. 返回结构化对象
        
        异常处理：
            - 网络超时：记录警告，返回None
            - HTTP错误：记录错误，返回None
            - 解析失败：记录错误，返回None
        """
        # 步骤1：检查是否应跳过
        if self.should_skip_url(url):
            return None
        
        logger.debug(f"   ↳ 抓取网页: {url[:60]}...")
        
        try:
            # 步骤2：发送HTTP请求
            response = self.session.get(
                url,
                timeout=Config.FETCH_TIMEOUT,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # 步骤3：检测编码（避免乱码）
            # 先尝试从响应头获取，失败则使用chardet检测
            if response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding
            
            html_content = response.text
            
            # 步骤4：使用readability提取正文
            # readability源自Mozilla，专为正文提取优化
            doc = Document(html_content)
            cleaned_html = doc.summary()
            page_title = doc.title() or "无标题"
            
            # 步骤5：使用BeautifulSoup进一步清洗
            soup = BeautifulSoup(cleaned_html, 'html.parser')
            
            # 移除噪声元素
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 
                           'aside', 'form', 'button', 'input']):
                tag.decompose()
            
            # 提取纯文本（保留段落结构）
            cleaned_text = soup.get_text(separator='\n', strip=True)
            
            # 步骤6：内容质量验证
            content_length = len(cleaned_text)
            is_valid = content_length >= Config.MIN_CONTENT_LENGTH
            
            if not is_valid:
                logger.warning(
                    f"   ↳ 内容过短（{content_length}字符），可能为无效页面: {url[:50]}..."
                )
            
            # 步骤7：返回结构化对象
            return ArticleContent(
                title=page_title,
                url=url,
                raw_html=html_content,
                cleaned_text=cleaned_text[:5000],  # 限制长度（供AI处理）
                is_valid=is_valid,
                content_length=content_length
            )
            
        except requests.exceptions.Timeout:
            logger.warning(f"   ↳ 抓取超时（{Config.FETCH_TIMEOUT}秒）: {url[:50]}...")
            return None
        except requests.exceptions.ConnectionError:
            logger.warning(f"   ↳ 连接失败: {url[:50]}...")
            return None
        except requests.exceptions.HTTPError as e:
            logger.warning(f"   ↳ HTTP错误 {e.response.status_code}: {url[:50]}...")
            return None
        except Exception as e:
            logger.error(f"   ↳ 抓取异常 {url[:50]}...: {str(e)}")
            return None


# ============================================
# 工厂函数：创建抓取器实例
# ============================================

def create_web_scraper() -> WebScraper:
    """
    创建网页抓取器实例的工厂函数
    
    返回：
        WebScraper实例
    """
    return WebScraper()