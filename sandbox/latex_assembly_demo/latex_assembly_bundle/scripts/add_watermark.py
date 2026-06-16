#!/usr/bin/env python3
"""
為 PDF 加入浮水印

使用 PyMuPDF (fitz) 在 PDF 每一頁加上浮水印圖片
"""

import io
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("❌ 錯誤: 未安裝 PyMuPDF", file=sys.stderr)
    print("請執行: pip install pymupdf", file=sys.stderr)
    sys.exit(1)


def add_watermark(input_pdf: Path, output_pdf: Path, watermark_image: Path, alpha: float = 0.3):
    """
    為 PDF 加入浮水印
    
    Args:
        input_pdf: 輸入 PDF 路徑
        output_pdf: 輸出 PDF 路徑
        watermark_image: 浮水印圖片路徑 (PNG)
        alpha: 透明度 (0-1)
    """
    if not input_pdf.exists():
        raise FileNotFoundError(f"找不到輸入 PDF: {input_pdf}")
    
    if not watermark_image.exists():
        raise FileNotFoundError(f"找不到浮水印圖片: {watermark_image}")
    
    # 開啟 PDF 和浮水印
    doc = fitz.open(input_pdf)
    watermark = fitz.open(watermark_image)
    
    # 取得浮水印頁面（假設只有一頁）
    watermark_page = watermark[0]
    watermark_pixmap = watermark_page.get_pixmap()
    
    # 轉為字節流
    img_stream = io.BytesIO(watermark_pixmap.tobytes())
    
    print(f"處理 {len(doc)} 頁...")
    
    # 為每一頁加入浮水印
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        page_rect = page.rect
        
        # 插入浮水印 (overlay=False 表示在背景)
        page.insert_image(page_rect, stream=img_stream, overlay=False, alpha=alpha)
        
        if (page_num + 1) % 10 == 0:
            print(f"  已處理 {page_num + 1} 頁...")
    
    # 儲存
    doc.save(output_pdf)
    doc.close()
    watermark.close()
    
    print(f"✓ 浮水印版本已儲存: {output_pdf}")


def main():
    if len(sys.argv) < 4:
        print("用法: python add_watermark.py <input.pdf> <output.pdf> <watermark.png>")
        sys.exit(1)
    
    input_pdf = Path(sys.argv[1])
    output_pdf = Path(sys.argv[2])
    watermark_image = Path(sys.argv[3])
    
    try:
        add_watermark(input_pdf, output_pdf, watermark_image)
    except Exception as e:
        print(f"❌ 錯誤: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
