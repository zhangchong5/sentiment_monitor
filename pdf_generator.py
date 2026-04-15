"""
PDF生成器 - 使用WeasyPrint实现高质量、样式丰富的PDF输出

技术选型：WeasyPrint
✅ 现代CSS支持（Flexbox/Grid）
✅ 完美中文渲染（配合Noto Sans SC字体）
✅ 页眉页脚、分页控制
✅ 响应式设计（自动适应A4纸张）
✅ 无依赖系统字体（内嵌字体文件）

样式设计原则：
1. 专业金融报告风格（蓝色主色调）
2. 清晰的信息层级（标题/正文/表格区分）
3. 可读性优化（行高、字距、对比度）
4. 打印友好（分页控制、避免孤行）
"""
import logging
from pathlib import Path
from typing import List
from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader
from models import (
    ReportSectionOneItem,
    ReportSectionTwoItem,
    ReportMetadata
)
from config import Config, logger

class PDFGenerator:
    """
    PDF生成器类
    
    功能：
        - 渲染Jinja2 HTML模板
        - 应用CSS样式表
        - 生成高质量PDF文件
        - 支持有无AI模式的差异化显示
    
    核心流程：
        1. 加载HTML模板与CSS样式
        2. 渲染模板（注入数据）
        3. 调用WeasyPrint生成PDF
        4. 保存至指定路径
    """
    
    def __init__(self):
        """
        初始化PDF生成器
        
        加载Jinja2模板环境，配置模板路径
        """
        # 创建Jinja2环境（支持模板继承、过滤器等）
        self.env = Environment(
            loader=FileSystemLoader(str(Config.ASSETS_DIR)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # 加载主模板
        self.template = self.env.get_template("report_template.html")
        
        logger.info("✓ PDF生成器初始化完成")
        logger.debug(f"   模板路径: {Config.ASSETS_DIR / 'report_template.html'}")
        logger.debug(f"   CSS路径: {Config.CSS_PATH}")
    
    def generate(
        self,
        metadata: ReportMetadata,
        section_one_items: List[ReportSectionOneItem],
        section_one_summary: str,
        section_two_items: List[ReportSectionTwoItem]
    ) -> Path:
        """
        生成完整舆情报告PDF
        
        参数：
            metadata: ReportMetadata - 报告元数据
            section_one_items: List[ReportSectionOneItem] - 第一部分表格数据
            section_one_summary: str - 第一部分AI总结
            section_two_items: List[ReportSectionTwoItem] - 第二部分详细数据
        
        返回：
            Path - 生成的PDF文件路径
        
        处理步骤：
            1. 渲染HTML模板（注入所有数据）
            2. 加载CSS样式表
            3. 调用WeasyPrint生成PDF
            4. 保存文件并返回路径
        
        异常处理：
            - 模板渲染失败：记录错误
            - CSS加载失败：记录警告（使用内联样式降级）
            - PDF生成失败：抛出异常
        """
        logger.info(f"📄 开始生成PDF报告...")
        
        try:
            # 步骤1：渲染HTML模板
            html_content = self.template.render(
                metadata=metadata,
                section_one_items=section_one_items,
                section_one_summary=section_one_summary,
                section_two_items=section_two_items,
                has_screenshots=any(item.screenshot_path for item in section_two_items)
            )
            
            logger.debug("   ↳ HTML模板渲染完成")
            
            # 步骤2：创建WeasyPrint HTML对象
            # base_url用于解析相对路径（如字体、图片）
            html = HTML(
                string=html_content,
                base_url=str(Config.ASSETS_DIR)
            )
            
            # 步骤3：加载CSS样式表
            css_objects = []
            
            # 主样式表
            if Config.CSS_PATH.exists():
                css_objects.append(CSS(filename=str(Config.CSS_PATH)))
                logger.debug("   ↳ CSS样式表加载成功")
            else:
                logger.warning(f"   ↳ CSS文件不存在: {Config.CSS_PATH}")
            
            # 步骤4：生成PDF
            logger.debug(f"   ↳ 调用WeasyPrint生成PDF...")
            
            html.write_pdf(
                str(Config.PDF_OUTPUT_PATH),
                stylesheets=css_objects,
                presentational_hints=True  # 支持HTML内联样式
            )
            
            # 步骤5：验证生成结果
            if Config.PDF_OUTPUT_PATH.exists():
                file_size = Config.PDF_OUTPUT_PATH.stat().st_size / 1024  # KB
                logger.info(
                    f"✅ PDF生成成功: {Config.PDF_OUTPUT_PATH.name} "
                    f"({file_size:.1f} KB)"
                )
                return Config.PDF_OUTPUT_PATH
            else:
                raise RuntimeError("PDF文件生成失败（未知错误）")
                
        except Exception as e:
            logger.error(f"❌ PDF生成失败: {str(e)}")
            raise


# ============================================
# 工厂函数：创建PDF生成器实例
# ============================================

def create_pdf_generator() -> PDFGenerator:
    """
    创建PDF生成器实例的工厂函数
    
    返回：
        PDFGenerator实例
    """
    return PDFGenerator()