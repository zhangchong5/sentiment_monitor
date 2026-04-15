#!/usr/bin/env python3
"""
主应用入口 - 协调各模块完成端到端舆情筛查流程

执行流程：
    1. 配置验证与初始化
    2. 执行 Serper 搜索（获取 20 条结果）
    3. 生成第一部分数据（概览表格 + 整体总结）
    4. 遍历结果：抓取内容 → 截图（前 5 条）→ AI 分析
    5. 生成第二部分数据（详细分析）
    6. 渲染 PDF/HTML 报告（带智能降级）

错误处理策略：
    - 搜索失败：终止流程
    - 单条内容抓取失败：跳过，继续下一条
    - 截图失败：跳过，不影响主体流程
    - AI 分析失败：返回错误占位符，继续流程
    - PDF 生成失败：回退到 HTML 模式
"""
import sys
import traceback
from datetime import datetime

from app.core.config import Config, logger, AI_PLACEHOLDER
from app.services.search_engine import create_search_engine
from app.services.web_scraper import create_web_scraper
from app.services.screenshot import create_screenshot_service
from app.services.ai_analyzer import create_ai_analyzer
from app.services.pdf_generator import create_pdf_generator
from app.models.data_models import (
    ReportSectionOneItem,
    ReportSectionTwoItem,
    ReportMetadata
)
from app.utils.helpers import truncate_text


def main():
    """主流程函数"""
    
    # ============================================
    # 启动日志
    # ============================================
    logger.info("=" * 70)
    logger.info("🇭🇰 香港分行舆情筛查系统启动")
    logger.info("=" * 70)
    
    try:
        # ============================================
        # 步骤 1：配置验证
        # ============================================
        logger.info("\n【步骤 1/6】配置验证")
        Config.validate()
        
        # ============================================
        # 步骤 2：初始化服务
        # ============================================
        logger.info("\n【步骤 2/6】初始化服务组件")
        
        try:
            search_engine = create_search_engine()
            logger.debug("✓ Serper 搜索引擎初始化成功")
        except Exception as e:
            logger.error(f"❌ Serper 搜索引擎初始化失败：{str(e)}")
            sys.exit(1)
        
        try:
            web_scraper = create_web_scraper()
            logger.debug("✓ 网页抓取器初始化成功")
        except Exception as e:
            logger.error(f"❌ 网页抓取器初始化失败：{str(e)}")
            sys.exit(1)
        
        try:
            screenshot_service = create_screenshot_service()
            logger.debug("✓ 截图服务初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ 截图服务初始化失败（Playwright 未安装？）: {str(e)}")
            logger.warning("   截图功能将被禁用，但不影响主体流程")
            screenshot_service = None
        
        try:
            ai_analyzer = create_ai_analyzer()
            logger.debug("✓ AI 分析引擎初始化成功")
        except Exception as e:
            if Config.AI_ENABLED:
                logger.error(f"❌ AI 分析引擎初始化失败（AI 已启用）: {str(e)}")
                sys.exit(1)
            else:
                logger.warning(f"⚠️ AI 分析引擎初始化失败（但 AI 已禁用，继续执行）: {str(e)}")
                from app.services.ai_analyzer import AIAnalyzer
                ai_analyzer = AIAnalyzer()
        
        try:
            pdf_generator = create_pdf_generator()
            logger.debug("✓ PDF/HTML 生成器初始化成功")
        except Exception as e:
            logger.error(f"❌ PDF 生成器初始化失败：{str(e)}")
            sys.exit(1)
        
        logger.info("✓ 所有服务组件初始化完成")
        
        # ============================================
        # 步骤 3：执行搜索
        # ============================================
        logger.info(f"\n【步骤 3/6】执行 Serper 搜索")
        logger.info(f"   搜索关键词：{Config.SEARCH_QUERY}")
        logger.info(f"   目标数量：{Config.SEARCH_RESULTS_COUNT}条")
        
        try:
            search_results = search_engine.search(
                Config.SEARCH_QUERY,
                Config.SEARCH_RESULTS_COUNT
            )
            
            if not search_results:
                logger.error("❌ 搜索未返回任何结果，终止流程")
                sys.exit(1)
            
            logger.info(f"✓ 搜索完成，返回{len(search_results)}条结果")
            
            for i, item in enumerate(search_results[:3], 1):
                logger.debug(
                    f"   [{i}] 标题：{truncate_text(item.title, 50)} | "
                    f"URL: {truncate_text(str(item.url), 40)}"
                )
                
        except Exception as e:
            logger.error(f"❌ 搜索执行失败：{str(e)}")
            logger.debug(traceback.format_exc())
            sys.exit(1)
        
        # ============================================
        # 步骤 4：生成第一部分数据（概览）
        # ============================================
        logger.info(f"\n【步骤 4/6】生成舆情概览数据")
        
        try:
            section_one_summary = ai_analyzer.analyze_section_one(search_results)
            logger.debug("✓ 整体舆情总结生成完成")
        except Exception as e:
            logger.warning(f"⚠️ 整体总结生成失败，使用占位符：{str(e)}")
            section_one_summary = AI_PLACEHOLDER["section_one_summary"]
        
        section_one_items = []
        for idx, item in enumerate(search_results[:Config.SEARCH_RESULTS_COUNT], 1):
            ai_summary = (
                AI_PLACEHOLDER["section_one_table_summary"]
                if not Config.AI_ENABLED
                else "【待详细分析】"
            )
            
            section_one_items.append(ReportSectionOneItem(
                keyword=Config.SEARCH_QUERY,
                url_title=item.title[:60] + "..." if len(item.title) > 60 else item.title,
                url=str(item.url),
                ai_summary=ai_summary,
                sentiment="中性"
            ))
        
        logger.info(f"✓ 第一部分数据生成完成（{len(section_one_items)}条）")
        
        # ============================================
        # 步骤 5：生成第二部分数据（详细分析）
        # ============================================
        logger.info(f"\n【步骤 5/6】详细内容分析与截图")
        logger.info(f"   处理前{Config.SEARCH_RESULTS_COUNT}条搜索结果...")
        
        section_two_items = []
        valid_count = 0
        processed_count = 0
        
        for idx, item in enumerate(search_results[:Config.SEARCH_RESULTS_COUNT], 1):
            url_str = str(item.url)
            
            logger.info(
                f"\n   处理 [{idx}/{Config.SEARCH_RESULTS_COUNT}]: "
                f"{truncate_text(item.title, 50)} | {truncate_text(url_str, 40)}"
            )
            
            try:
                content = web_scraper.fetch_content(url_str)
                
                if not content or not content.is_valid:
                    logger.warning(f"   ↳ 跳过无效内容：{truncate_text(url_str, 60)}")
                    continue
                
                valid_count += 1
                processed_count += 1
                
            except Exception as e:
                logger.warning(
                    f"   ↳ 内容抓取失败（跳过）: {truncate_text(url_str, 60)} | 错误：{str(e)[:50]}"
                )
                continue
            
            screenshot_path = None
            if screenshot_service and idx <= Config.MAX_SCREENSHOTS:
                try:
                    screenshot_filename = f"screenshot_{idx:02d}.png"
                    screenshot_path = screenshot_service.take_screenshot(
                        url_str,
                        screenshot_filename
                    )
                    if screenshot_path:
                        logger.debug(f"   ↳ 截图成功：{screenshot_filename}")
                    else:
                        logger.warning(f"   ↳ 截图失败（跳过）: {truncate_text(url_str, 60)}")
                except Exception as e:
                    logger.warning(
                        f"   ↳ 截图异常（跳过）: {truncate_text(url_str, 60)} | 错误：{str(e)[:50]}"
                    )
            
            try:
                ai_result = ai_analyzer.analyze_section_two(content)
            except Exception as e:
                logger.warning(
                    f"   ↳ AI 分析失败（使用占位符）: {truncate_text(url_str, 60)} | 错误：{str(e)[:50]}"
                )
                from app.models.data_models import AISummary
                ai_result = AISummary(
                    summary=f"⚠️ AI 分析失败：{str(e)[:80]}",
                    sentiment="中性",
                    risk_keywords=["分析失败"],
                    compliance_issues=[str(e)[:50]],
                    confidence_score=0.0
                )
            
            try:
                section_two_item = ReportSectionTwoItem(
                    title=item.title,
                    url=url_str,
                    google_snippet=item.snippet,
                    content_summary=ai_result.summary,
                    sentiment=ai_result.sentiment,
                    screenshot_path=screenshot_path
                )
                section_two_items.append(section_two_item)
                
                if idx <= len(section_one_items):
                    summary_preview = (
                        ai_result.summary[:100] + "..." 
                        if len(ai_result.summary) > 100 
                        else ai_result.summary
                    )
                    section_one_items[idx - 1].ai_summary = summary_preview
                    section_one_items[idx - 1].sentiment = ai_result.sentiment
                
                logger.debug(
                    f"   ↳ 分析完成 | 情感：{ai_result.sentiment} | "
                    f"置信度：{ai_result.confidence_score:.2f}"
                )
                
            except Exception as e:
                logger.error(
                    f"   ↳ 构建分析结果失败（跳过）: {truncate_text(url_str, 60)} | 错误：{str(e)}"
                )
                continue
        
        logger.info(f"\n✓ 详细分析完成，共处理{processed_count}条，有效分析{valid_count}篇")
        
        if not section_two_items:
            logger.error("❌ 无有效内容可供分析，无法生成报告")
            sys.exit(1)
        
        # ============================================
        # 步骤 6：生成 PDF/HTML 报告
        # ============================================
        logger.info(f"\n【步骤 6/6】生成报告文件")
        
        metadata = ReportMetadata(
            keyword=Config.SEARCH_QUERY,
            total_results=len(search_results),
            valid_articles=len(section_two_items),
            generation_time=datetime.now().strftime("%Y年%m月%d日 %H:%M"),
            ai_enabled=Config.AI_ENABLED
        )
        
        try:
            report_path = pdf_generator.generate(
                metadata=metadata,
                section_one_items=section_one_items,
                section_one_summary=section_one_summary,
                section_two_items=section_two_items
            )
            
            if not report_path.exists():
                raise FileNotFoundError(f"报告文件未生成：{report_path}")
            
            file_size_kb = report_path.stat().st_size / 1024
            logger.info(f"✅ 报告生成成功：{report_path.name} ({file_size_kb:.1f} KB)")
            
        except Exception as e:
            logger.error(f"❌ 报告生成失败：{str(e)}")
            logger.debug(traceback.format_exc())
            sys.exit(1)
        
        # ============================================
        # 流程完成
        # ============================================
        logger.info("\n" + "=" * 70)
        logger.info("✅ 舆情筛查流程完成！")
        logger.info("=" * 70)
        logger.info(f"📄 报告文件：{report_path.resolve()}")
        logger.info(f"📊 搜索结果：{len(search_results)}条")
        logger.info(f"📰 有效分析：{len(section_two_items)}篇")
        logger.info(f"🖼️  截图数量：{sum(1 for item in section_two_items if item.screenshot_path)}张")
        logger.info(f"🤖 AI 状态：{'✅ 已启用' if Config.AI_ENABLED else '⚠️ 已禁用（占位符模式）'}")
        logger.info("=" * 70)
        
        if not Config.AI_ENABLED:
            logger.warning("\n💡 提示：AI 分析功能当前已禁用")
            logger.warning("   如需启用智能风险识别，请执行：")
            logger.warning("   1. 编辑 .env 文件，设置 AI_ENABLED=True")
            logger.warning("   2. 配置 OPENAI_API_KEY")
            logger.warning("   3. 重新运行程序")
        
        if not screenshot_service:
            logger.warning("\n💡 提示：截图服务不可用")
            logger.warning("   如需启用网页截图功能，请安装 Playwright：")
            logger.warning("   pip install playwright")
            logger.warning("   playwright install chromium")
    
    except KeyboardInterrupt:
        logger.info("\n⚠️  用户中断执行（Ctrl+C）")
        sys.exit(0)
    
    except SystemExit as e:
        raise
    
    except Exception as e:
        logger.error(f"\n❌ 系统执行出错：{str(e)}")
        logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
