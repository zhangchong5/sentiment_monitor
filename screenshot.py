import asyncio
import logging
from pathlib import Path
from typing import Optional
from playwright.async_api import (
    async_playwright, 
    TimeoutError as PlaywrightTimeout,
    Error as PlaywrightError
)
from config import Config, logger

class ScreenshotService:
    """
    网页截图服务类
    
    功能：
        - 异步截图（使用Playwright）
        - 自动跳过非HTML资源
        - 超时控制与错误恢复
        - 保存至指定目录
    
    特性：
        - 支持全页截图
        - 设置固定视口确保一致性
        - 中文区域设置（zh-HK）
    """
    
    def __init__(self):
        """
        初始化截图服务
        
        设置输出目录与默认参数
        """
        self.output_dir = Config.SCREENSHOT_DIR
        logger.info(f"✓ 截图服务初始化完成（输出目录: {self.output_dir}）")
    
    async def take_screenshot_async(self, url: str, filename: str) -> Optional[str]:
        """
        异步截图函数（核心实现）
        
        参数：
            url: str - 目标网页URL
            filename: str - 保存的文件名（不含路径，如"screenshot_01.png"）
        
        返回：
            Optional[str] - 截图完整路径（成功）或None（失败）
        
        处理流程：
            1. 检查URL是否应跳过（基于扩展名）
            2. 启动Playwright浏览器（无头模式）
            3. 创建浏览器上下文（设置视口、区域）
            4. 导航到目标页面（等待网络空闲）
            5. 等待额外时间确保动态内容加载
            6. 执行全页截图
            7. 关闭浏览器，返回文件路径
        
        异常处理：
            - 超时：记录警告，返回None
            - 导航失败：记录错误，返回None
            - 截图失败：记录错误，返回None
        """
        # 步骤1：检查是否应跳过
        if any(url.lower().endswith(ext) for ext in Config.EXCLUDE_EXTENSIONS):
            logger.debug(f"   ↳ 跳过截图（非HTML资源）: {url[:50]}...")
            return None
        
        output_path = self.output_dir / filename
        
        try:
            # 步骤2-4：启动浏览器并导航
            async with async_playwright() as p:
                # 启动Chromium（无头模式）
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage'
                    ]
                )
                
                # 创建浏览器上下文
                context = await browser.new_context(
                    viewport={
                        "width": Config.SCREENSHOT_WIDTH,
                        "height": Config.SCREENSHOT_HEIGHT
                    },
                    locale="zh-HK",  # 香港地区设置
                    timezone_id="Asia/Hong_Kong"
                )
                
                page = await context.new_page()
                
                # 设置超时
                page.set_default_timeout(Config.PLAYWRIGHT_TIMEOUT)
                
                # 导航到页面（等待网络空闲）
                logger.debug(f"   ↳ 开始截图: {url[:60]}...")
                await page.goto(
                    url,
                    wait_until="networkidle",
                    timeout=Config.PLAYWRIGHT_TIMEOUT
                )
                
                # 等待额外时间确保动态内容加载
                await page.wait_for_timeout(2000)
                
                # 步骤5-6：执行截图并保存
                await page.screenshot(
                    path=str(output_path),
                    full_page=True,  # 全页截图
                    type="png",
                    quality=80
                )
                
                await browser.close()
                
                logger.debug(f"   ↳ 截图成功: {filename}")
                return str(output_path)
                
        except PlaywrightTimeout:
            logger.warning(f"   ↳ 截图超时（{Config.PLAYWRIGHT_TIMEOUT}ms）: {url[:50]}...")
            return None
        except PlaywrightError as e:
            # Playwright特定错误
            if "ERR_ABORTED" in str(e) or "net::ERR" in str(e):
                logger.warning(f"   ↳ 网络错误（可能资源被屏蔽）: {url[:50]}...")
            else:
                logger.error(f"   ↳ Playwright错误: {str(e)[:100]}")
            return None
        except Exception as e:
            logger.error(f"   ↳ 截图异常 {url[:50]}...: {str(e)}")
            return None
    
    def take_screenshot(self, url: str, filename: str) -> Optional[str]:
        """
        同步截图接口（包装异步函数）
        
        参数：
            url: str - 目标网页URL
            filename: str - 保存的文件名
        
        返回：
            Optional[str] - 截图完整路径或None
        
        用途：
            - 供同步代码调用（如main.py）
            - 内部自动创建事件循环
        """
        try:
            return asyncio.run(self.take_screenshot_async(url, filename))
        except RuntimeError as e:
            # 如果已在事件循环中运行（如Jupyter），使用当前循环
            if "event loop is running" in str(e):
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(self.take_screenshot_async(url, filename))
            raise


# ============================================
# 工厂函数：创建截图服务实例
# ============================================

def create_screenshot_service() -> ScreenshotService:
    """
    创建截图服务实例的工厂函数
    
    返回：
        ScreenshotService实例
    """
    return ScreenshotService()