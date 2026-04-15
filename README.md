# 香港分行舆情筛查系统

> 基于 AI 的企业客户公开信息智能分析工具，专注于反洗钱（AML）合规风险识别

## 📋 目录

- [项目简介](#项目简介)
- [核心功能](#核心功能)
- [技术架构](#技术架构)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [使用示例](#使用示例)
- [项目结构](#项目结构)
- [测试](#测试)
- [常见问题](#常见问题)

---

## 项目简介

**sentiment_monitor** 是一款面向金融机构的智能化舆情监测工具，专为香港分行设计。系统自动搜索企业客户在互联网上的公开信息，通过 AI 分析识别潜在的反洗钱（AML）、监管处罚、违规操作等合规风险，并生成专业的 PDF 分析报告。

### 应用场景

- ✅ **贷前调查**：快速评估新客户舆情风险
- ✅ **定期审查**：自动化存量客户舆情监控
- ✅ **事件驱动**：针对特定事件进行专项筛查
- ✅ **合规报告**：生成标准化监管报送材料

### 核心价值

- 🔍 **全面覆盖**：自动检索 Google 新闻及网页结果（默认 20 条）
- 🤖 **智能分析**：基于 LLM 的情感分析与风险关键词提取
- 📊 **结构化输出**：标准化 PDF 报告，支持概览表格 + 详细分析
- 🛡️ **安全可控**：支持 AI 功能开关，敏感环境可降级运行
- 📸 **可视化证据**：自动截取网页截图（前 5 条结果）

---

## 核心功能

| 功能模块 | 描述 | 状态 |
|---------|------|------|
| **搜索引擎** | 调用 Serper API 执行 Google 新闻搜索 | ✅ 就绪 |
| **网页抓取** | 智能提取正文内容，过滤广告/导航噪声 | ✅ 就绪 |
| **AI 分析引擎** | LLM 驱动的情感分析与风险识别 | ✅ 就绪 |
| **截图服务** | Playwright 无头浏览器自动截图 | ✅ 就绪 |
| **PDF 生成器** | WeasyPrint 渲染专业金融报告 | ✅ 就绪 |
| **智能降级** | AI/截图不可用时自动切换占位符模式 | ✅ 就绪 |

---

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                      主应用 (main.py)                        │
│  协调各模块完成端到端舆情筛查流程                            │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  SearchEngine │   │   WebScraper    │   │ ScreenshotService│
│  Serper API   │   │  requests+BS4   │   │   Playwright    │
└───────────────┘   └─────────────────┘   └─────────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  AIAnalyzer   │   │  PDFGenerator   │   │  DataModels     │
│  OpenAI API   │   │  WeasyPrint     │   │   Pydantic      │
└───────────────┘   └─────────────────┘   └─────────────────┘
```

### 技术栈

| 类别 | 技术选型 | 用途 |
|------|---------|------|
| **语言** | Python 3.10+ | 核心开发语言 |
| **HTTP 请求** | `requests` | API 调用与网页抓取 |
| **HTML 解析** | `BeautifulSoup4`, `readability-lxml` | 网页内容清洗 |
| **浏览器自动化** | `playwright` | 网页截图 |
| **AI 集成** | `OpenAI API` (兼容格式) | 情感分析与风险识别 |
| **PDF 生成** | `WeasyPrint`, `Jinja2` | 模板渲染与 PDF 输出 |
| **数据验证** | `Pydantic` | 类型安全与数据校验 |
| **配置管理** | `python-dotenv` | 环境变量加载 |

---

## 快速开始

### 1. 环境要求

- Python 3.10 或更高版本
- pip 包管理器
- （可选）Playwright 浏览器（用于截图功能）

### 2. 安装依赖

```bash
# 克隆仓库
cd /workspace

# 安装 Python 依赖
pip install -r requirements.txt

# （可选）安装 Playwright 并下载 Chromium
pip install playwright
playwright install chromium
```

### 3. 配置环境变量

创建 `.env` 文件：

```bash
# .env 文件内容

# ========== 必需配置 ==========
# Serper API 密钥（Google 搜索替代方案）
# 获取地址：https://serper.dev
SERPER_API_KEY=your_serper_api_key_here

# ========== 可选配置 ==========
# AI 功能总开关（True=启用，False=使用占位符）
AI_ENABLED=False

# OpenAI API 配置（仅当 AI_ENABLED=True 时需要）
OPENAI_API_KEY=sk-your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# 搜索关键词（默认：香港分行相关风险词）
SEARCH_QUERY="香港分行 洗钱 监管处罚 违规 反洗钱 AML 合规"

# 搜索结果数量（默认：20 条）
SEARCH_RESULTS_COUNT=20

# 日志级别（DEBUG/INFO/WARNING/ERROR）
LOG_LEVEL=INFO
```

### 4. 运行程序

```bash
# 方式一：直接运行主程序
python app/main.py

# 方式二：使用 Python 模块方式
python -m app.main
```

### 5. 查看输出

程序执行完成后，在 `output/` 目录查看生成的报告：

```
output/
├── hk_branch_sentiment_report.pdf    # 主报告文件
└── screenshots/                       # 网页截图（如有）
    ├── screenshot_01.png
    ├── screenshot_02.png
    └── ...
```

---

## 配置说明

### 核心配置项

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `SERPER_API_KEY` | ✅ | - | Serper API 密钥（[免费注册](https://serper.dev)） |
| `AI_ENABLED` | ❌ | `False` | AI 功能总开关 |
| `OPENAI_API_KEY` | ⚠️ | `""` | 当 `AI_ENABLED=True` 时必需 |
| `SEARCH_QUERY` | ❌ | `"香港分行 洗钱..."` | 搜索关键词 |
| `SEARCH_RESULTS_COUNT` | ❌ | `20` | 搜索结果数量（1-100） |
| `MAX_SCREENSHOTS` | ❌ | `5` | 最大截图数量 |
| `LOG_LEVEL` | ❌ | `INFO` | 日志详细程度 |

### AI 功能说明

系统支持两种运行模式：

#### 模式 1：AI 启用（推荐）

```bash
AI_ENABLED=True
OPENAI_API_KEY=sk-xxx
```

- ✅ 真实情感分析与风险识别
- ✅ 智能生成内容摘要
- ✅ 提取风险关键词与合规问题
- ⚠️ 产生 API 调用费用

#### 模式 2：AI 禁用（降级模式）

```bash
AI_ENABLED=False
```

- ✅ 跳过所有 AI 调用
- ✅ 使用占位符文本填充报告
- ✅ 适合开发测试或敏感环境
- ⚠️ 报告内容为模板文本，无实际分析

---

## 使用示例

### 示例 1：基础使用（AI 禁用模式）

```bash
# .env 配置
SERPER_API_KEY=ae80a71d2d3aa9308fc54f6ba99f743fb9d7b23a
AI_ENABLED=False
SEARCH_QUERY="某银行 香港分行"

# 运行
python app/main.py
```

**输出**：生成包含占位符的 PDF 报告，验证流程完整性。

### 示例 2：完整分析（AI 启用模式）

```bash
# .env 配置
SERPER_API_KEY=your_key
AI_ENABLED=True
OPENAI_API_KEY=sk-your_key
SEARCH_QUERY="XX 银行 反洗钱 处罚"
SEARCH_RESULTS_COUNT=10

# 运行
python app/main.py
```

**输出**：生成包含真实 AI 分析的完整报告，含情感倾向、风险关键词等。

### 示例 3：自定义搜索词

```bash
# 针对特定企业进行筛查
SEARCH_QUERY="企业名称 + 洗钱 OR 监管处罚 OR 违规 OR 反洗钱"
```

---

## 项目结构

```
/workspace/
├── app/                          # 重构后的主应用包
│   ├── __init__.py               # 包初始化，版本信息
│   ├── main.py                   # 主入口文件
│   ├── core/                     # 核心模块
│   │   ├── __init__.py
│   │   └── config.py             # 配置管理
│   ├── models/                   # 数据模型
│   │   ├── __init__.py
│   │   └── data_models.py        # Pydantic 模型定义
│   ├── services/                 # 业务服务层
│   │   ├── __init__.py
│   │   ├── search_engine.py      # Serper 搜索服务
│   │   ├── web_scraper.py        # 网页抓取服务
│   │   ├── screenshot.py         # Playwright 截图服务
│   │   ├── ai_analyzer.py        # AI 分析引擎
│   │   └── pdf_generator.py      # PDF/HTML 生成器
│   └── utils/                    # 工具函数
│       ├── __init__.py
│       └── helpers.py            # 辅助函数（截断文本等）
├── assets/                       # 静态资源
│   ├── report_template.html      # Jinja2 PDF 模板
│   └── styles.css                # CSS 样式表
├── output/                       # 输出目录
│   ├── hk_branch_sentiment_report.pdf
│   └── screenshots/
├── tests/                        # 单元测试
│   └── test_app.py
├── requirements.txt              # Python 依赖列表
├── README.md                     # 本文件
└── .env                          # 环境变量配置（需自行创建）
```

### 模块职责

| 模块 | 文件 | 主要类/函数 | 职责 |
|------|------|-----------|------|
| **core** | `config.py` | `Config`, `logger` | 配置管理与日志 |
| **models** | `data_models.py` | `SearchResultItem`, `AISummary` | 数据模型定义 |
| **services** | `search_engine.py` | `SearchEngine` | Google 搜索调用 |
| **services** | `web_scraper.py` | `WebScraper` | 网页内容抓取 |
| **services** | `screenshot.py` | `ScreenshotService` | 浏览器截图 |
| **services** | `ai_analyzer.py` | `AIAnalyzer` | LLM 分析 |
| **services** | `pdf_generator.py` | `PDFGenerator` | 报告生成 |
| **utils** | `helpers.py` | `truncate_text` | 辅助工具 |

---

## 测试

### 运行单元测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_app.py -v

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=html
```

### 测试覆盖范围

当前测试覆盖以下核心功能：

- ✅ 配置验证（`Config.validate()`）
- ✅ 搜索引擎（`SearchEngine.search()`）
- ✅ 网页抓取（`WebScraper.fetch_content()`）
- ✅ AI 分析（`AIAnalyzer.analyze_section_one/two()`）
- ✅ 截图服务（`ScreenshotService.take_screenshot()`）
- ✅ PDF 生成（`PDFGenerator.generate()`）
- ✅ 辅助函数（`truncate_text()`）

---

## 常见问题

### Q1: Serper API 是什么？如何获取密钥？

**A:** Serper 是 Google Search API 的替代方案，提供免费额度（通常 2500 次/月）。  
注册地址：https://serper.dev  
注册后在 Dashboard 获取 API Key，填入 `.env` 文件的 `SERPER_API_KEY`。

### Q2: AI 分析失败怎么办？

**A:** 检查以下事项：
1. 确认 `AI_ENABLED=True`
2. 确认 `OPENAI_API_KEY` 已正确配置
3. 检查网络连接（需访问 OpenAI API）
4. 查看日志中的详细错误信息

如不需要 AI 分析，可设置 `AI_ENABLED=False`，系统将使用占位符模式继续运行。

### Q3: 截图功能不工作？

**A:** 截图依赖 Playwright 和 Chromium 浏览器：
```bash
# 安装 Playwright
pip install playwright

# 下载 Chromium 浏览器
playwright install chromium
```

如仍无法使用，系统会自动跳过截图，不影响主体流程。

### Q4: 如何修改搜索关键词？

**A:** 编辑 `.env` 文件中的 `SEARCH_QUERY` 变量：
```bash
SEARCH_QUERY="你的自定义关键词"
```

支持布尔运算符（AND/OR/NOT）和引号精确匹配。

### Q5: PDF 报告样式如何定制？

**A:** 修改以下文件：
- `assets/report_template.html`：调整 HTML 结构与布局
- `assets/styles.css`：修改 CSS 样式（颜色、字体等）

### Q6: 如何在生产环境部署？

**A:** 建议步骤：
1. 使用虚拟环境（`venv` 或 `conda`）
2. 将敏感配置移至环境变量（不使用 `.env` 文件）
3. 设置日志级别为 `WARNING` 或 `ERROR`
4. 配置定时任务（如 `cron`）定期执行
5. 将输出目录挂载到持久化存储

---

## 许可证

本项目仅供内部使用，未经许可不得外传。

---

## 更新日志

### v1.0.0 (2026-04-15)
- ✨ 初始版本发布
- 🏗️ 完成代码重构（模块化架构）
- 🧪 添加单元测试覆盖
- 📄 完善文档与配置说明

---

## 联系方式

如有疑问或建议，请联系开发团队。
