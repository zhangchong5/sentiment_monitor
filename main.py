"""
主应用入口 - 协调各模块完成端到端舆情筛查流程

执行流程：
    1. 配置验证与初始化
    2. 执行Serper搜索（获取20条结果）
    3. 生成第一部分数据（概览表格 + 整体总结）
    4. 遍历结果：抓取内容 → 截图（前5条）→ AI分析
    5. 生成第二部分数据（详细分析）
    6. 渲染PDF/HTML报告（带智能降级）

错误处理策略：
    - 搜索失败：终止流程
    - 单条内容抓取失败：跳过，继续下一条
    - 截图失败：跳过，不影响主体流程
    - AI分析失败：返回错误占位符，继续流程
    - PDF生成失败：回退到HTML模式
"""
import sys
import traceback
from datetime import datetime
from config import Config, logger, AI_PLACEHOLDER
from search_engine import create_search_engine
from web_scraper import create_web_scraper
from screenshot import create_screenshot_service
from ai_analyzer import create_ai_analyzer
from pdf_generator import create_pdf_generator
from models import (
    ReportSectionOneItem,
    ReportSectionTwoItem,
    ReportMetadata
    
)


def truncate_text(text: str, max_length: int = 60) -> str:
    """
    安全截断文本（处理None和特殊字符）
    
    Args:
        text: 待截断文本
        max_length: 最大长度
    
    Returns:
        截断后的文本（带...省略号）
    """
    if not text:
        return ""
    text_str = str(text)
    return text_str[:max_length] + "..." if len(text_str) > max_length else text_str


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
        # 步骤1：配置验证
        # ============================================
        logger.info("\n【步骤1/6】配置验证")
        Config.validate()
        
        # ============================================
        # 步骤2：初始化服务
        # ============================================
        logger.info("\n【步骤2/6】初始化服务组件")
        
        try:
            search_engine = create_search_engine()
            logger.debug("✓ Serper搜索引擎初始化成功")
        except Exception as e:
            logger.error(f"❌ Serper搜索引擎初始化失败: {str(e)}")
            sys.exit(1)
        
        try:
            web_scraper = create_web_scraper()
            logger.debug("✓ 网页抓取器初始化成功")
        except Exception as e:
            logger.error(f"❌ 网页抓取器初始化失败: {str(e)}")
            sys.exit(1)
        
        try:
            screenshot_service = create_screenshot_service()
            logger.debug("✓ 截图服务初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ 截图服务初始化失败（Playwright未安装？）: {str(e)}")
            logger.warning("   截图功能将被禁用，但不影响主体流程")
            screenshot_service = None
        
        try:
            ai_analyzer = create_ai_analyzer()
            logger.debug("✓ AI分析引擎初始化成功")
        except Exception as e:
            if Config.AI_ENABLED:
                logger.error(f"❌ AI分析引擎初始化失败（AI已启用）: {str(e)}")
                sys.exit(1)
            else:
                logger.warning(f"⚠️ AI分析引擎初始化失败（但AI已禁用，继续执行）: {str(e)}")
                # 创建空分析器（占位符模式）
                from ai_analyzer import AIAnalyzer
                ai_analyzer = AIAnalyzer()
        
        try:
            pdf_generator = create_pdf_generator()
            logger.debug("✓ PDF/HTML生成器初始化成功")
        except Exception as e:
            logger.error(f"❌ PDF生成器初始化失败: {str(e)}")
            sys.exit(1)
        
        logger.info("✓ 所有服务组件初始化完成")
        
        # ============================================
        # 步骤3：执行搜索
        # ============================================
        logger.info(f"\n【步骤3/6】执行Serper搜索")
        logger.info(f"   搜索关键词: {Config.SEARCH_QUERY}")
        logger.info(f"   目标数量: {Config.SEARCH_RESULTS_COUNT}条")
        
        try:
            search_results = search_engine.search(
                Config.SEARCH_QUERY,
                Config.SEARCH_RESULTS_COUNT
            )
            
            if not search_results:
                logger.error("❌ 搜索未返回任何结果，终止流程")
                sys.exit(1)
            
            logger.info(f"✓ 搜索完成，返回{len(search_results)}条结果")
            
            # 显示前3条结果预览
            for i, item in enumerate(search_results[:3], 1):
                logger.debug(
                    f"   [{i}] 标题: {truncate_text(item.title, 50)} | "
                    f"URL: {truncate_text(str(item.url), 40)}"
                )
                
        except Exception as e:
            logger.error(f"❌ 搜索执行失败: {str(e)}")
            logger.debug(traceback.format_exc())
            sys.exit(1)
        
        # ============================================
        # 步骤4：生成第一部分数据（概览）
        # ============================================
        logger.info(f"\n【步骤4/6】生成舆情概览数据")
        
        # 4.1 生成整体总结（调用AI或占位符）
        try:
            section_one_summary = ai_analyzer.analyze_section_one(search_results)
            logger.debug("✓ 整体舆情总结生成完成")
        except Exception as e:
            logger.warning(f"⚠️ 整体总结生成失败，使用占位符: {str(e)}")
            section_one_summary = AI_PLACEHOLDER["section_one_summary"]
        
        # 4.2 生成表格数据（初始状态）
        section_one_items = []
        for idx, item in enumerate(search_results[:Config.SEARCH_RESULTS_COUNT], 1):
            # AI禁用时使用占位符摘要
            ai_summary = (
                AI_PLACEHOLDER["section_one_table_summary"]
                if not Config.AI_ENABLED
                else "【待详细分析】"  # AI启用时，此处将在步骤5更新
            )
            
            section_one_items.append(ReportSectionOneItem(
                keyword=Config.SEARCH_QUERY,
                url_title=item.title[:60] + "..." if len(item.title) > 60 else item.title,
                url=str(item.url),  # 转为字符串存储
                ai_summary=ai_summary,
                sentiment="中性"  # 初始为中性，步骤5会更新
            ))
        
        logger.info(f"✓ 第一部分数据生成完成（{len(section_one_items)}条）")
        
        # ============================================
        # 步骤5：生成第二部分数据（详细分析）
        # ============================================
        logger.info(f"\n【步骤5/6】详细内容分析与截图")
        logger.info(f"   处理前{Config.SEARCH_RESULTS_COUNT}条搜索结果...")
        
        section_two_items = []
        valid_count = 0
        processed_count = 0
        
        for idx, item in enumerate(search_results[:Config.SEARCH_RESULTS_COUNT], 1):
            # 安全转换URL为字符串（避免HttpUrl切片错误）
            url_str = str(item.url)
            
            logger.info(
                f"\n   处理 [{idx}/{Config.SEARCH_RESULTS_COUNT}]: "
                f"{truncate_text(item.title, 50)} | {truncate_text(url_str, 40)}"
            )
            
            # 5.1 抓取网页内容
            try:
                content = web_scraper.fetch_content(url_str)
                
                if not content or not content.is_valid:
                    logger.warning(f"   ↳ 跳过无效内容: {truncate_text(url_str, 60)}")
                    continue
                
                valid_count += 1
                processed_count += 1
                
            except Exception as e:
                logger.warning(
                    f"   ↳ 内容抓取失败（跳过）: {truncate_text(url_str, 60)} | 错误: {str(e)[:50]}"
                )
                continue
            
            # 5.2 生成截图（仅前MAX_SCREENSHOTS条，且截图服务可用）
            screenshot_path = None
            if screenshot_service and idx <= Config.MAX_SCREENSHOTS:
                try:
                    screenshot_filename = f"screenshot_{idx:02d}.png"
                    screenshot_path = screenshot_service.take_screenshot(
                        url_str,
                        screenshot_filename
                    )
                    if screenshot_path:
                        logger.debug(f"   ↳ 截图成功: {screenshot_filename}")
                    else:
                        logger.warning(f"   ↳ 截图失败（跳过）: {truncate_text(url_str, 60)}")
                except Exception as e:
                    logger.warning(
                        f"   ↳ 截图异常（跳过）: {truncate_text(url_str, 60)} | 错误: {str(e)[:50]}"
                    )
            
            # 5.3 AI分析（或占位符）
            try:
                ai_result = ai_analyzer.analyze_section_two(content)
            except Exception as e:
                logger.warning(
                    f"   ↳ AI分析失败（使用占位符）: {truncate_text(url_str, 60)} | 错误: {str(e)[:50]}"
                )
                # 创建错误占位符
                from models import AISummary
                ai_result = AISummary(
                    summary=f"⚠️ AI分析失败: {str(e)[:80]}",
                    sentiment="中性",
                    risk_keywords=["分析失败"],
                    compliance_issues=[str(e)[:50]],
                    confidence_score=0.0
                )
            
            # 5.4 构建第二部分数据项
            try:
                section_two_item = ReportSectionTwoItem(
                    title=item.title,
                    url=url_str,  # 存储字符串
                    google_snippet=item.snippet,
                    content_summary=ai_result.summary,
                    sentiment=ai_result.sentiment,
                    screenshot_path=screenshot_path
                )
                section_two_items.append(section_two_item)
                
                # 5.5 更新第一部分表格中的对应项（同步情感倾向和摘要）
                if idx <= len(section_one_items):
                    # 更新摘要（截断至100字符）
                    summary_preview = (
                        ai_result.summary[:100] + "..." 
                        if len(ai_result.summary) > 100 
                        else ai_result.summary
                    )
                    section_one_items[idx - 1].ai_summary = summary_preview
                    section_one_items[idx - 1].sentiment = ai_result.sentiment
                
                logger.debug(
                    f"   ↳ 分析完成 | 情感: {ai_result.sentiment} | "
                    f"置信度: {ai_result.confidence_score:.2f}"
                )
                
            except Exception as e:
                logger.error(
                    f"   ↳ 构建分析结果失败（跳过）: {truncate_text(url_str, 60)} | 错误: {str(e)}"
                )
                continue
        
        logger.info(f"\n✓ 详细分析完成，共处理{processed_count}条，有效分析{valid_count}篇")
        
        if not section_two_items:
            logger.error("❌ 无有效内容可供分析，无法生成报告")
            sys.exit(1)
        
        # ============================================
        # 步骤6：生成PDF/HTML报告
        # ============================================
        logger.info(f"\n【步骤6/6】生成报告文件")
        
        # 构建元数据
        metadata = ReportMetadata(
            keyword=Config.SEARCH_QUERY,
            total_results=len(search_results),
            valid_articles=len(section_two_items),
            generation_time=datetime.now().strftime("%Y年%m月%d日 %H:%M"),
            ai_enabled=Config.AI_ENABLED
        )
        
        # 生成报告（自动处理PDF/HTML降级）
        try:
            report_path = pdf_generator.generate(
                metadata=metadata,
                section_one_items=section_one_items,
                section_one_summary=section_one_summary,
                section_two_items=section_two_items
            )
            
            # 验证文件生成
            if not report_path.exists():
                raise FileNotFoundError(f"报告文件未生成: {report_path}")
            
            file_size_kb = report_path.stat().st_size / 1024
            logger.info(f"✅ 报告生成成功: {report_path.name} ({file_size_kb:.1f} KB)")
            
        except Exception as e:
            logger.error(f"❌ 报告生成失败: {str(e)}")
            logger.debug(traceback.format_exc())
            sys.exit(1)
        
        # ============================================
        # 流程完成
        # ============================================
        logger.info("\n" + "=" * 70)
        logger.info("✅ 舆情筛查流程完成！")
        logger.info("=" * 70)
        logger.info(f"📄 报告文件: {report_path.resolve()}")
        logger.info(f"📊 搜索结果: {len(search_results)}条")
        logger.info(f"📰 有效分析: {len(section_two_items)}篇")
        logger.info(f"🖼️  截图数量: {sum(1 for item in section_two_items if item.screenshot_path)}张")
        logger.info(f"🤖 AI状态: {'✅ 已启用' if Config.AI_ENABLED else '⚠️ 已禁用（占位符模式）'}")
        logger.info("=" * 70)
        
        # AI禁用提示
        if not Config.AI_ENABLED:
            logger.warning("\n💡 提示：AI分析功能当前已禁用")
            logger.warning("   如需启用智能风险识别，请执行：")
            logger.warning("   1. 编辑 .env 文件，设置 AI_ENABLED=True")
            logger.warning("   2. 配置 OPENAI_API_KEY")
            logger.warning("   3. 重新运行程序")
        
        # 截图服务不可用提示
        if not screenshot_service:
            logger.warning("\n💡 提示：截图服务不可用")
            logger.warning("   如需启用网页截图功能，请安装Playwright：")
            logger.warning("   pip install playwright")
            logger.warning("   playwright install chromium")
    
    except KeyboardInterrupt:
        logger.info("\n⚠️  用户中断执行（Ctrl+C）")
        sys.exit(0)
    
    except SystemExit as e:
        # 允许sys.exit()正常传播
        raise
    
    except Exception as e:
        logger.error(f"\n❌ 系统执行出错: {str(e)}")
        logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()