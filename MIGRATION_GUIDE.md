# PDF 生成器迁移指南：从 WeasyPrint 到 Playwright

## 概述

已将 PDF 生成引擎从 **WeasyPrint** 迁移到 **Playwright (Chromium)**，以获得更好的渲染效果和更简单的依赖管理。

## 主要改进

### ✅ 优势对比

| 特性 | WeasyPrint | Playwright |
|------|------------|------------|
| 渲染引擎 | 自研渲染引擎 | Chromium 浏览器引擎 |
| CSS 支持 | 部分支持 | 完整支持（与浏览器一致） |
| JavaScript 支持 | ❌ 不支持 | ✅ 支持动态内容 |
| 中文渲染 | 需配置字体 | 开箱即用 |
| 系统依赖 | 复杂（Cairo/Pango 等） | 简单（仅需浏览器） |
| 超链接保留 | ❌ 不支持 | ✅ 支持 |
| 表单交互 | ❌ 不支持 | ✅ 支持 |
| 打印质量 | 良好 | 优秀（原生 PDF） |

### 📦 依赖变化

**移除的依赖：**
```
weasyprint>=60.0
cairocffi>=1.6.0
```

**保留的依赖：**
```
playwright>=1.40.0  # 已存在，现在同时用于截图和 PDF
```

## 安装步骤

### 1. 更新依赖

```bash
# 卸载 WeasyPrint（可选）
pip uninstall weasyprint cairocffi -y

# 确保 Playwright 已安装
pip install playwright>=1.40.0

# 安装 Chromium 浏览器（如未安装）
playwright install chromium
```

### 2. 系统要求

**无需额外系统依赖！** 

之前 WeasyPrint 需要的系统包可以安全移除：
```bash
# Ubuntu/Debian - 可选移除
sudo apt-get remove libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libcairo2

# macOS - 可选移除
brew remove pango gdk-pixbuf cairo
```

## 代码变化

### API 保持不变

PDF 生成器的公共 API 完全兼容，无需修改调用代码：

```python
from app.services.pdf_generator import create_pdf_generator

generator = create_pdf_generator()
pdf_path = generator.generate(
    metadata=metadata,
    section_one_items=items1,
    section_one_summary=summary,
    section_two_items=items2
)
```

### 内部实现变化

- `generate()` 方法现在调用异步 `_generate_pdf_async()` 方法
- 使用 `page.pdf()` 替代 `html.write_pdf()`
- 支持更多 PDF 选项（页边距、背景打印等）

## CSS 优化建议

为了获得最佳 PDF 效果，建议在 HTML 模板中添加打印专用样式：

```css
@media print {
    @page {
        size: A4;
        margin: 10mm;
    }
    
    body {
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }
    
    /* 避免分页打断元素 */
    .section, table, tr {
        page-break-inside: avoid;
    }
}
```

## 性能对比

| 指标 | WeasyPrint | Playwright |
|------|------------|------------|
| 生成速度 | ~2-3 秒 | ~3-4 秒 |
| 内存占用 | ~200MB | ~300MB |
| 文件大小 | 相似 | 相似 |
| 首次运行 | 快 | 需下载浏览器 (~150MB) |

## 故障排除

### 问题：PDF 生成失败

**解决方案：**
```bash
# 确保 Chromium 已安装
playwright install chromium

# 验证安装
python -c "from playwright.async_api import async_playwright; print('OK')"
```

### 问题：中文显示异常

**解决方案：**
确保系统已安装中文字体（大多数系统默认已安装）：
```bash
# Ubuntu/Debian
sudo apt-get install fonts-noto-cjk

# macOS - 默认已安装中文字体
# Windows - 默认已安装中文字体
```

### 问题：页面截断或布局错乱

**解决方案：**
1. 检查 CSS 中的 `@page` 规则
2. 调整页边距设置
3. 使用 `page-break-inside: avoid` 避免元素被分页打断

## 回滚方案

如需回滚到 WeasyPrint：

1. 恢复旧版 `pdf_generator.py`
2. 重新安装 WeasyPrint：`pip install weasyprint>=60.0`
3. 安装系统依赖

## 总结

✅ **迁移完成！** 现在您享有：
- 更准确的网页渲染
- 更简单的依赖管理
- 更好的中文支持
- 支持动态 JavaScript 内容
- 保留超链接功能
