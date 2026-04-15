"""
PDF 生成器 - 使用 Playwright 实现高质量、样式丰富的 PDF 输出

技术选型：Playwright (Chromium 原生 PDF)
✅ 完美还原网页渲染效果（与浏览器显示一致）
✅ 支持现代 CSS（Flexbox/Grid/动画等）
✅ 完美中文渲染（无需额外字体配置）
✅ 页眉页脚、分页控制
✅ 响应式设计（自动适应纸张尺寸）
✅ 无外部依赖（仅需 Playwright）
✅ 支持超链接、交互元素保留

样式设计原则：
1. 专业金融报告风格（蓝色主色调）
2. 清晰的信息层级（标题/正文/表格区分）
3. 可读性优化（行高、字距、对比度）
4. 打印友好（分页控制、避免孤行）
"""
import asyncio
import logging
from pathlib import Path
from typing import List, Optional
from playwright.async_api import async_playwright
from jinja2 import Environment, FileSystemLoader
from app.models.data_models import (
    ReportSectionOneItem,
    ReportSectionTwoItem,
    ReportMetadata
)
from app.core.config import Config, logger


class PDFGenerator:
    """
    PDF 生成器类（基于 Playwright）
    
    功能：
        - 渲染 Jinja2 HTML 模板
        - 使用 Chromium 浏览器引擎生成 PDF
        - 生成高质量 PDF 文件（完美还原网页效果）
        - 支持有无 AI 模式的差异化显示
    
    核心流程：
        1. 加载 HTML 模板
        2. 渲染模板（注入数据）
        3. 启动 Playwright 浏览器
        4. 设置页面内容并生成 PDF
        5. 保存至指定路径
    """
    
    def __init__(self):
        """
        初始化 PDF 生成器
        
        加载 Jinja2 模板环境，配置模板路径
        """
        # 创建 Jinja2 环境（支持模板继承、过滤器等）
        self.env = Environment(
            loader=FileSystemLoader(str(Config.ASSETS_DIR)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # 加载主模板
        self.template = self.env.get_template("report_template.html")
        
        logger.info("✓ PDF 生成器初始化完成 (Playwright)")
        logger.debug(f"   模板路径：{Config.ASSETS_DIR / 'report_template.html'}")
    
    def generate(
        self,
        metadata: ReportMetadata,
        section_one_items: List[ReportSectionOneItem],
        section_one_summary: str,
        section_two_items: List[ReportSectionTwoItem]
    ) -> Path:
        """
        生成完整舆情报告 PDF（同步接口）
        
        参数：
            metadata: ReportMetadata - 报告元数据
            section_one_items: List[ReportSectionOneItem] - 第一部分表格数据
            section_one_summary: str - 第一部分 AI 总结
            section_two_items: List[ReportSectionTwoItem] - 第二部分详细数据
        
        返回：
            Path - 生成的 PDF 文件路径
        
        处理步骤：
            1. 渲染 HTML 模板（注入所有数据）
            2. 调用异步方法生成 PDF
            3. 保存文件并返回路径
        
        异常处理：
            - 模板渲染失败：记录错误
            - PDF 生成失败：抛出异常
        """
        logger.info(f"📄 开始生成 PDF 报告...")
        
        try:
            # 步骤 1：渲染 HTML 模板
            html_content = self.template.render(
                metadata=metadata,
                section_one_items=section_one_items,
                section_one_summary=section_one_summary,
                section_two_items=section_two_items,
                has_screenshots=any(item.screenshot_path for item in section_two_items)
            )
            
            logger.debug("   ↳ HTML 模板渲染完成")
            
            # 步骤 2：调用异步方法生成 PDF
            pdf_path = asyncio.run(self._generate_pdf_async(html_content))
            
            # 步骤 3：验证生成结果
            if pdf_path.exists():
                file_size = pdf_path.stat().st_size / 1024  # KB
                logger.info(
                    f"✅ PDF 生成成功：{pdf_path.name} "
                    f"({file_size:.1f} KB)"
                )
                return pdf_path
            else:
                raise RuntimeError("PDF 文件生成失败（未知错误）")
                
        except Exception as e:
            logger.error(f"❌ PDF 生成失败：{str(e)}")
            raise
    
    async def _generate_pdf_async(self, html_content: str) -> Path:
        """
        异步生成 PDF 文件（核心实现）
        
        参数：
            html_content: str - 渲染后的 HTML 内容
        
        返回：
            Path - 生成的 PDF 文件路径
        
        处理流程：
            1. 启动 Playwright 浏览器（无头模式）
            2. 创建浏览器上下文（设置视口、区域）
            3. 设置页面 HTML 内容
            4. 等待页面加载完成
            5. 生成 PDF 文件
            6. 关闭浏览器
        """
        async with async_playwright() as p:
            # 启动 Chromium（无头模式）
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--print-to-pdf-no-header'  # 移除默认页眉
                ]
            )
            
            # 创建浏览器上下文
            context = await browser.new_context(
                viewport={
                    "width": Config.SCREENSHOT_WIDTH,  # 使用配置的宽度
                    "height": 800
                },
                locale="zh-HK",  # 香港地区设置
                timezone_id="Asia/Hong_Kong"
            )
            
            page = await context.new_page()
            
            # 设置超时
            page.set_default_timeout(Config.PLAYWRIGHT_TIMEOUT)
            
            # 设置页面 HTML 内容
            logger.debug("   ↳ 正在渲染页面内容...")
            await page.set_content(
                html_content,
                wait_until="networkidle",
                timeout=Config.PLAYWRIGHT_TIMEOUT
            )
            
            # 等待额外时间确保动态内容加载
            await page.wait_for_timeout(2000)
            
            # 生成 PDF
            logger.debug("   ↳ 正在生成 PDF...")
            
            # 构建 PDF 生成选项
            pdf_options = {
                "path": str(Config.PDF_OUTPUT_PATH),
                "format": "A4",
                "print_background": True,  # 打印背景图形
                "display_header_footer": False,  # 不显示默认页眉页脚
                "prefer_css_page_size": True,  # 优先使用 CSS 定义的页面大小
                "margin": {
                    "top": "10mm",
                    "right": "10mm",
                    "bottom": "10mm",
                    "left": "10mm"
                }
            }
            
            await page.pdf(**pdf_options)
            
            await browser.close()
            
            logger.debug(f"   ↳ PDF 生成完成")
            return Config.PDF_OUTPUT_PATH


# ============================================
# 工厂函数：创建 PDF 生成器实例
# ============================================

def create_pdf_generator() -> PDFGenerator:
    """
    创建 PDF 生成器实例的工厂函数
    
    返回：
        PDFGenerator 实例
    """
    return PDFGenerator()
